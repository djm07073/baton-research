# Autobahn 위의 회전형 라운드로빈 실행 DAG

> 기록일: 2026-09-19  
> 실행 모델 갱신: 2026-09-21 — [Block-STM + Read/Write/Defer](./blockstm-execution-model.md)  
> 배치 갱신: 2026-09-21 — [slot별 state→producer 매핑 v3](./state-affinity-placement.md)  
> 상태: 대화에서 합의한 최신 논문 탐색안; 구현 및 E2E 검증 전  
> 논문 개요: [paper-outline.md](./paper-outline.md)  
> 구분: 기존 [proof 기반 protocol](./proof-aware-multimmit-paper.md)과 [SDK](./commonware-proof-sdk.md)를 구현에 소급 적용하거나 교체한 것이 아니다. 이 문서는 새 논문 방향의 결정 기록이다.

## 1. 목표와 이번 결정

연구 목적은 **cut 확정 뒤에 실행 순서를 구성하고 실행하는 직렬 경로를, ordering과 execution이 중첩되는 pipeline으로 바꾸어 state finalization latency를 줄이는 것**이다. 여기서 cut 확정은 ordering 합의의 결과이며, 그 뒤의 순서 구성은 결정적 실행 규칙을 적용하는 과정이지 추가 ordering 합의가 아니다.

블록 수신부터 shared state에 speculative execution을 수행하여 같은 cut에 대한 합의와 실행·결과 인증 준비를 겹친다. Finalized cut과 canonical parent가 정해지면 유효한 계산을 재사용하고 필요한 부분만 복구하며, 동일 결과를 검증한 validator들의 `f+1` 서명으로 결과를 인증한다. 이전 cut의 실행과 다음 cut의 합의를 겹쳐 throughput만 높이는 것이 아니라 **동일 cut의 확정 이후 남는 실행·인증 시간을 줄이는 것**을 평가한다.

회전형 라운드로빈, conflict DAG, 선택적 재실행과 `f+1` 실행 결과 서명은 연구 목적 자체가 아니라 이를 달성하기 위한 설계 수단이다. 사전 실행만으로 canonical finality를 부여하지 않으며, state finality와 durable apply/read readiness를 구분한다.

- 기준 consensus는 순수 Autobahn의 `n=3f+1`, 동일 투표권, 최대 `f` Byzantine model이다.
- Producer lane은 블록 전파 경로이며 state ownership shard가 아니다. 여러 lane이 같은 mutable state에 접근할 수 있다.
- DAG의 정점은 transaction이 아닌 **block**이다. Block 내부 transaction 순서는 고정한다.
- 합의·reference ordering 단위와 실제 worker scheduling 단위를 구분한다. Worker의 캐시·검증·재실행 단위는 **transaction**이며 block 전체를 항상 다시 실행하지 않는다.
- Transaction bytes와 고정 application schema에서 conservative read/write/deferred-access 범위를 검증할 수 있는 workload를 지원한다. 실제 접근과 조건은 실행 중 추적·검증한다.
- Lane 우선순위는 매 cut/slot마다 한 칸 회전한다. 리더가 별도 정책이나 최적 DAG를 선택하지 않는다.
- 같은 lane은 높이 순서를 유지하고, 교차-lane state conflicts는 공통 순위로 방향을 정한다. 독립 blocks는 병렬 실행한다.
- Late insertion, cut에서의 제외, 다음 구간으로의 이동은 speculative DAG와 실행 입력을 바꿀 수 있다. 영향받은 계산을 다시 검증·실행한다.
- 기존 ordering 합의의 전체 확정 절차는 유지한다. 실행 완료나 결과 서명을 ordering 투표의 선행조건으로 만들지 않는다.
- State finality는 exact cut finality와 `f+1`개의 일치하는 실행 결과 서명을 함께 확인하는 조건이다.
- 별도 state isolation, cross-lane fragments/handshake, receipt bridge, cut-tail phase, ZK/rolling proof, PAC, leader-selected view synthesis는 이 탐색안에 없다.
- 이 모델은 여러 validators의 중복 실행과 각 validator 내부 병렬성을 사용하는 모델이다. 검증되지 않은 부분 계산을 validators 사이에 나누는 execution sharding이라고 주장하지 않는다.

2026-09-21 갱신은 execution layer에 한정한다. 아래 Autobahn 기준 정족수 설명은 기존 reference context이며, 이번 Block-STM 갱신이 consensus adapter나 결과 인증 threshold를 새로 확정한 것은 아니다.

## 2. Autobahn에서 유지하는 것과 바꾸는 것

[Autobahn §5.1–5.2](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)의 기본 경로를 유지한다.

- Data lane의 인증된 tip과 그 history를 참조하는 cut을 leader가 제안한다. 기본 PoA는 `f+1` data votes다.
- 일반 경로는 `2f+1` Prepare votes에 이어 `2f+1` Confirm acknowledgments로 cut을 확정한다. Fast path는 전체 `n` Prepare votes를 사용한다.
- 첫 번째 `2f+1` Prepare votes만으로 ordering finality가 끝났다고 취급하지 않는다.
- 유효한 certified cut에 대한 ordering vote는 누락된 block data의 복구나 application execution을 기다리지 않는다.
- Cut의 선택 대상, slot 순서, view change 및 equivocation 처리는 기존 consensus 규칙을 따른다.

변경 대상은 cut을 실행 순서로 펼치는 application serialization rule이다. 기존 deterministic zip 대신 회전형 라운드로빈 순위를 기준으로 충돌 DAG를 만든다. 따라서 **합의의 투표 구조를 유지하더라도 application 실행 의미는 명시적으로 바뀐다.**

리더는 여전히 어떤 certified tips를 cut에 넣을지 제안한다. 이 제안 권한까지 제거한 모델은 아니다. 리더의 재량인 DAG 정책 제안은 하지 않는다.

## 3. Cut 구간과 회전 규칙

### 3.1 공통 입력

첫 구현 범위는 고정된 validator/lane 집합과 고정된 application version이다. Lane 목록은 epoch 설정의 canonical order로 고정한다. 회전은 wall-clock이나 consensus round/view-change 횟수가 아니라 **ordering slot index**로 계산한다.

- `C_k`: slot k에서 최종 확정된 exact cut. 높이뿐 아니라 block identity와 인증된 경계를 포함한다.
- `B_k`: C_k가 선택한 블록 중 앞선 slots에서 아직 처리하지 않은 정확한 block occurrences.
- `a_k(lane)`: slot k 이전까지 누적해 처리한 해당 lane의 마지막 canonical position.
- `S_(k-1)`: 이전 canonical 실행 결과. 인증받을 결과는 이 정확한 parent root에서 출발해야 한다.

Autobahn의 parallel slots는 raw tip vectors가 non-monotonic일 수 있다. 따라서 `B_k`를 단순히 직전 raw cut의 높이를 빼서 정의하지 않는다. Native slot-order 처리와 already-ordered filtering을 유지하고 cumulative boundary를 사용한다. Byzantine producer의 다른 branches를 높이만 같다는 이유로 같은 block으로 취급하지 않는다. [Autobahn §5.2.2, §5.4](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)

이전 cut 또는 parent state가 아직 불명확한 overlapping slot의 실행은 조건부 계산이다. Parent/cut context가 확정된 뒤 다시 검증해야 하며, 다음 ordering을 그 검증에 묶지는 않는다. 이전 상태의 결과가 꼭 필요한 계산 자체가 기다릴 수 있다는 점은 인정한다.

### 3.2 회전형 라운드로빈

Lane 목록이 `[A,B,C]`, 첫 slot index가 1이면:

| Slot | Lane 우선순위 | 충돌 방향을 정하는 비교 순서 |
|---|---|---|
| 1 | A, B, C | A1 < B1 < C1 < A2 < B2 < C2 |
| 2 | B, C, A | B1 < C1 < A1 < B2 < C2 < A2 |
| 3 | C, A, B | C1 < A1 < B1 < C2 < A2 < B2 |
| 4 | A, B, C | 첫 순서로 복귀 |

여기서 1, 2는 해당 slot의 cumulative lane boundary 이후 상대 위치다. 지난 slot에서 처리한 A1을 다시 실행한다는 뜻이 아니다.

Lane 수를 m, 고정 목록에서 lane의 index를 i라고 하면:

```text
rotation(k)       = (k - 1) mod m
lane_priority(i,k)= (i - rotation(k)) mod m
relative_height(b)= height(b) - a_k(lane(b))
rank_k(b)         = (relative_height(b), lane_priority(lane(b),k))
```

Modulo는 0부터 m-1의 정수로 정규화한다. Rank는 검증된 block positions에서 계산하며 producer가 주장한 timestamp, 수신 시각, CPU 속도나 임의 gas 신고를 사용하지 않는다. 같은 후보 lane path의 각 position에는 하나의 block identity만 있다.

회전은 같은 슬롯의 view change에서 바뀌지 않는다. Dynamic membership과 epoch 경계의 회전 재설정은 별도 명세 대상이며 초기 실험에서 제외한다.

### 3.3 같은 회전을 사용하는 producer 배치

[배치 명세 v3](./state-affinity-placement.md)는 state scope의 고정 논리 위치 j를 `lanes[(j + rotation(q)) mod m]`에 대응시킨다. Signed R/W/typed-Defer 범위를 합산해 후보 순위를 정하며, 모든 tx를 최우선 lane에 보내지 않는다. 같은 state의 priority 위치는 고정되고 물리 producer만 회전한다. 이것은 state ownership 이동이나 회전 자체에 의한 conflict 감소가 아니다.

배치 목표 q는 검증된 연속 finalized prefix h의 다음 slot h+1이다. 아직 미확정인 `C_q`, cumulative anchor, parent root는 배치 입력이 아니다. 실제로 block이 포함된 slot k는 q와 다를 수 있다. 실행은 오직 k의 rank를 사용하며 q는 block의 유효성·실행 위치를 예약하지 않는다.

이미 발행된 block은 회전해도 lane·bytes·identity가 바뀌지 않는다. 미확정 tx의 재전파가 중복 block occurrences를 만들면 기존 replay/nonce/status/fee 의미를 적용한다. Soft routing이므로 권장 lane 불일치만으로 기존 유효 block을 거부하지 않는다. 정해진 cut-count 뒤의 모든 producer 재전파는 전달 fallback이며 ordering에 추가 vote를 만들지 않는다.

## 4. DAG 구성과 speculative recovery

### 4.1 필수 간선

Block의 모든 transactions에 대한 보수적 접근 범위를 합친다. `D`는 runtime이 허용하는 deferred 연산의 대상이며 일반 `W`와 구분한다.

```text
R(b) = union of declared and verified reads in b
W(b) = union of declared and verified writes in b
D(b) = union of declared deferred-update targets in b

RWConflict(x,y) iff
    W(x) intersects R(y)
 OR R(x) intersects W(y)
 OR W(x) intersects W(y)

추가 의존성 후보:
  D(x) intersects (R(y) union W(y))
  D(y) intersects (R(x) union W(x))
  D(x) intersects D(y): 연산·조건·snapshot 의미를 별도 검증
```

- 같은 lane의 새 blocks는 canonical position 증가 순으로 연결한다.
- 서로 다른 lane에서 conflict가 있으면 작은 rank에서 큰 rank로 간선을 넣는다.
- Read–Read만 겹치거나 disjoint하면 별도 conflict edge를 넣지 않는다.
- Reference DAG는 모든 충돌 쌍을 포함한다. 최적화된 간선 축약은 같은 precedence를 보존하고 canonical digest를 정의한 뒤 별도 평가한다.
- 모든 reference precedence 간선이 동일한 strict rank를 따르면 cycle이 없다. 실제 worker는 이 순서에 동등한 결과를 내도록 tx를 speculative execute하고 Block-STM으로 검증한다. Block-level edge 하나를 모든 내부 tx의 실행 완료 barrier로 강제하지 않는다.
- Nonce, fee account, shared counters, range/absence reads 등 실제 실행 의미에 영향을 주는 접근도 포함한다. 선언 누락을 허용하지 않는다.
- 결과/status/effects는 worker 완료 순서가 아니라 block/transaction occurrence 기준의 고정 encoding으로 commit한다.

`D–D`는 합성 가능한 연산과 유효한 범위 조건 아래에서 계산을 병렬화할 수 있다. `D–R`은 reader 위치 앞의 deltas를 포함하고, `D–W`는 overwrite/삭제 경계를 지킨다. 조건 검증 실패는 tx 단위 재실행을 유발할 수 있다. Block 내부에 같은 key의 정확한 읽기가 있으면 D-only로 요약하지 않는다. 자세한 의미와 예시는 [실행 모델 §3](./blockstm-execution-model.md#3-실행-의미와-접근-규칙)을 따른다.

같은 selected blocks와 context를 가진 정상 노드들은 같은 reference DAG를 계산한다. 내부 Block-STM의 speculative read-from 관계와 실행 완료 순서까지 같아야 하는 것은 아니다. 같은 priority를 사용해도 수신한 blocks가 다르면 pre-cut local DAG와 실행 결과는 다를 수 있다. DAG 결정성과 사전 실행 완료를 혼동하지 않는다.

### 4.2 늦은 삽입

아직 오지 않은 lane의 차례를 기다리는 전역 barrier는 두지 않는다. 이미 수신한 blocks의 tx들을 speculative overlay에 실행한다.

예를 들어 A1이 `x <- 20`, B1이 `y <- x`이고 정책상 A1이 앞선다고 하자. B1만 먼저 도착하면 기존 x를 읽어 실행할 수 있다. 이후 A1이 들어오면 A1 -> B1 의존성을 반영하고 B1의 read를 검증한다. x가 달라졌다면 B1을 재실행하며, 후속 blocks도 실제 입력 변화에 따라 재검증한다. 관련 없는 block은 재사용한다.

공통 규칙은 고정이지만 DAG와 실행 입력은 동적으로 갱신된다. 특히 cut에서 제외된 predecessor나 다음 구간의 회전은 기존 방향·경로를 바꿀 수 있다. 다만 이 단순 rank 규칙은 같은 구간의 두 기존 blocks 사이 상대 rank를 새 block 하나 때문에 뒤집지는 않는다. **새 predecessor가 추가되어 입력이 달라지는 것만으로도 재실행이 필요하며, 매 삽입마다 기존 edge 방향을 반전시킬 필요는 없다.**

재사용은 같은 프로그램/context와 실제 read observations의 일치로 검증한다. Root가 같거나 graph가 비슷하다는 이유만으로 재사용하지 않는다. Stale execution은 overlay에서 제거·재구성하며 canonical하게 적용한 과거 state를 되돌리지 않는다.

추가로 deferred predicates의 true/false 이력과 output snapshot의 기준 위치를 검증한다. 정확한 값이 달라졌다면 해당 tx를 재실행하지만, predicate-only 관측이 계속 성립하거나 output-only snapshot만 달라졌다면 계산 재사용·재구체화가 가능하다. 이는 일반적인 값 동등성 재사용을 무제한 허용하는 규칙이 아니다. Seer식 instruction checkpoint는 필수로 사용하지 않는다.

### 4.3 Cut 확정과 다음 구간

1. Candidate cut이 알려지면 그 exact block set의 DAG를 계산하고 준비된 실행을 검증·보정한다.
2. Cut이 확정되면 선택되지 않은 blocks의 효과를 해당 결과에서 제거하고, 남은 계산의 입력을 다시 검증한다.
3. 로컬에 없는 선택된 block은 복구한다. 없는 것을 임의로 cut에서 빼거나 실패 transaction으로 취급하지 않는다.
4. 실행 결과는 그 exact cut과 parent에만 바인딩한다. 더 큰 local view의 root를 그대로 서명하지 않는다.
5. 미선택 blocks는 다음 구간의 새 anchor와 회전 규칙에서 다시 평가한다. 과거 cut에 뒤늦게 삽입하지 않는다.

Policy rotation과 boundary 변화로 speculative work가 추가 폐기될 수 있다. 따라서 회전이 fixed priority보다 반드시 빠르다고 주장하지 않는다.

### 4.4 Block-STM adapter와 deferred outputs

원래 Block-STM은 preset tx order를 전제로 하므로 mutable cut을 직접 지원한다고 가정하지 않는다. Adapter는 candidate generation과 stable occurrence identity를 관리하고, 새 exact order에서 캐시를 다시 검증한다. 알려진 미완료 writer는 unresolved로 표시하고 stale completion을 거부한다.

모든 선택된 tx의 조건·읽기를 최종 검증하고 deferred 값을 실제 값으로 구체화한 뒤 state root와 결과 commitments를 만든다. Candidate에서 제외된 tx는 application 효과뿐 아니라 fee delta도 해당 cut 결과에서 빠진다. State finality를 얻기 위해 미해결 정산을 뒤로 숨기지 않는다. 세부 규칙·pseudocode·안전성 테스트는 [Block-STM 실행 모델](./blockstm-execution-model.md)에 둔다.

## 5. f+1 실행 결과 서명과 state finality

### 5.1 무엇을 서명하는가

서로 다른 validators가 같은 context와 같은 result에 서명해야 한다.

```text
Context = (
  protocol/signature domain, chain/epoch, validator-set identity,
  ordering slot, exact cut digest, cumulative lane anchor,
  canonical parent state root,
  scheduling rule version, application/runtime version, DAG digest
)

Result = (
  post-state root, occurrence-keyed status/effects commitments,
  state-change data commitment
)

Execution signature = Sign_validator(Context, Result)
```

정상 서명자는 전체 선택 대상의 결과를 직접 실행하거나 안전하게 재사용·검증한 뒤 서명한다. 일부 blocks만 계산하고 전체 root에 동의하거나, 남의 ordering/DA 서명을 실행 서명으로 세지 않는다. 서명은 중복 identity를 제거하고 검증한다.

### 5.2 f+1이 충분한 이유와 범위

확정 cut, canonical parent와 deterministic application이 결과를 유일하게 정한다. `f+1`개의 일치하는 서명에는 정상 signer가 최소 하나 있으므로 틀린 결과가 이 기준을 통과할 수 없다. 이는 서로 다른 quorum의 honest intersection이 아니라 **정직한 실행 검증자 최소 한 명**에 의존하는 논증이다.

Ordering에 참여한 `2f+1` 집단에서 모아도 충분하다. 다만 반드시 그 집단이어야 할 안전성 이유는 없다. Byzantine `f`명이 전부 서명을 거부하면 그 집단에 남은 정상 `f+1`명 모두가 실행을 마쳐야 하므로 latency 보장은 별도다.

이 수치 자체는 novelty가 아니다. PBFT도 commit 뒤의 일반 실행 결과를 `f+1` matching replies로 확인한다. PBFT의 Prepare/Commit 합의 단계를 `2f+1 -> f+1`로 줄인다는 뜻은 아니며, tentative replies의 조기 확정 규칙과도 구별한다. [PBFT §4.1–4.3, §6.1](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/01/p398-castro-bft-tocs.pdf)

이 서명은 ZK validity proof나 PAC가 아니다. 동일 위원회의 Byzantine bound와 정직한 실행 검증을 신뢰한다. App/runtime의 공통 버그까지 검출한다고 주장하지 않는다.

### 5.3 State finality와 readiness

```text
StateFinal_v(k) iff
  v verified complete ordering-finality evidence for C_k
  AND the exact canonical parent is verified/established
  AND v verified f+1 distinct matching execution signatures
      over Context(C_k, parent, rule) and Result

StateReady_v(k) iff
  StateFinal_v(k)
  AND v obtained authenticated state-change data or replayed B_k
  AND v durably applied the result and can serve reads
```

서명은 cut 확정 전에 조건부로 준비할 수 있지만, 미선택 cut의 서명은 canonicality를 주지 않는다. Parent 조건까지 충족된 fast path에서 실행 서명이 먼저 준비되면 cut 확정 시 state 결과도 확정되고, cut이 먼저 끝나면 matching signatures를 확인할 때 state 결과가 확정된다.

Root 서명만으로 상태 데이터가 생기지는 않는다. Applying node는 정확한 parent에 대해 commitment가 일치하는 complete delta를 적용하고 post-root를 검증하거나, finalized inputs를 재실행한다. 인증된 root를 얻은 시점과 실제 read-serving readiness를 분리해서 측정한다.

Execution result/delta 보관 기간, fetch 경로, restart recovery와 checkpoint retention은 구현 명세에서 정의해야 한다. `f+1` execution signatures를 받았다는 사실만으로 별도의 durable custody 보장이 자동으로 생긴다고 주장하지 않는다.

## 6. 안전성·활성·한계

- **결정성:** 동일한 cut/history/rule/runtime에서 DAG와 실행 결과가 일치해야 한다.
- **순차 의미 보존:** 모든 충돌을 rank 방향으로 정렬하므로 유효한 병렬 schedule은 해당 reference serial order와 같은 결과를 만들어야 한다.
- **사전 동의와 구별:** cut 전체에 합의해도 모든 signer가 이미 같은 local DAG·state를 보유하거나 실행을 끝냈다는 보장은 없다.
- **복구 안전성:** late/excluded predecessor의 영향을 받은 read를 검증하고, 이전 canonical boundary는 재배열하지 않는다.
- **인증 안전성:** cut/parent/runtime 재사용, 다른 branch root, 잘못된 signature와 중복 signer를 거부한다.
- **Non-blocking 범위:** block production과 ordering은 실행 서명을 기다리지 않는다. Shared-state dependency, 이전 parent state, missing selected data는 state progress를 늦출 수 있다.
- **제한된 speculation:** 반복 삽입에 대한 local replay coalescing, overlay/cache 한도, speculation budget 초과 시 해당 작업을 cut 이후 처리하는 fallback이 필요하다. 로컬 자원 정책은 최종 DAG 의미를 바꾸지 않는다.
- **조건부 활성:** eventual synchrony, selected-data recovery, 충분한 정상 실행자 및 실행 처리 용량을 전제한다. 입력률이 실행 용량을 넘으면 state lag는 증가할 수 있다.
- **공정성 범위:** 회전은 특정 lane의 영구적인 선순위만 완화한다. Block 크기·생성률 차이, cut inclusion 편향, MEV를 제거하거나 공정한 처리량을 보장하지 않는다.
- **복제 비용:** f+1 인증을 위해 실행 중복을 지불한다. 정확한 읽기와 조건이 연결된 hot key에는 본질적 순차 의존성이 남는다. Tx 단위 캐시로 큰 block의 무조건 전체 재실행은 피할 수 있지만 최악에는 모든 tx가 무효화될 수 있다.

## 7. 논문에서 주장할 것과 검증할 것

Contribution 후보는 개별 primitive의 발명이 아니라 다음 결합과 그 효과의 검증이다.

1. Shared-state multi-producer execution에서 cut별 회전 순위로 speculative scheduling과 최종 scheduling을 일치시키는 명시적 실행 의미.
2. Late data와 cut selection에 대한 read-validation recovery, exact-cut-bound f+1 결과 인증을 ordering과 겹치는 state-finalization pipeline.
3. State finality/readiness, reuse와 replay 비용, 공정성 및 Byzantine 지연을 함께 분석하는 형식적·실험적 평가.

주요 지표:

```text
Delta_finality_v = T_StateFinal_v - T_CutFinal_v
Delta_readiness_v= T_StateReady_v - T_CutFinal_v
```

Parent availability, fetching, DAG build, residual execution, signature aggregation, durable apply를 따로 계측한다. 비교 baseline이 local execution으로 이미 정확한 state를 아는 시점을 인증서 대기와 혼동하지 않는다. Local execution 완료, transferable result certification, durable read readiness를 같은 이름으로 보고하지 않는다.

비교: ordering-only; 원래 zip 순서의 post-cut 실행; 같은 RR-DAG의 post-cut 병렬 실행; 같은 RR-DAG의 speculative 실행; 회전 없는 fixed lane priority; full replay 대 read-validated reuse; 결과 서명 전파/수집 비용.

2026-09-21 추가 비교: 동일 tx/fee 의미의 **pre/post-cut × plain/deferred Block-STM**으로 overlap과 합산 최적화의 효과를 분리한다. Predicate 재사용·snapshot patch를 ablation하고 materialization·root 계산 및 범위 검증 비용을 포함한다.

Baseline 순서와 새 serialization 순서에서 application 성공률이 달라질 수 있다. 동일 순서의 비교로 latency hiding 효과를 분리하고, 순서 변화의 효과는 별도 실험으로 보고한다.

초기 workload는 state를 lane에 귀속시키지 않는 Bank-like shared accounts, multi-account update, hot-key/nonces와 delayed conflicting blocks다. 본문에는 측정 전 성능 수치를 넣지 않는다. 고정 membership의 formal 구성을 위해 n=4/7/10 등을 먼저 사용하며, 기존 6-node Multimmit 결과를 이 모델의 E2E 결과로 인용하지 않는다.

2026-09-19 추가 실험 결정: **validator RTT × transaction당 application state 갱신 횟수**를 주요 benchmark matrix로 사용한다. 예비 범위는 RTT 1/10/50/100/200 ms와 갱신량 1/4/16/64회/tx이며 pilot 후 조정한다. 갱신량은 canonical 성공 실행의 logical writes로 정의하고, 충돌률·payload bytes·block당 tx 수·offered load와 실제 실행 시간은 별도 통제·기록한다. Cut-to-state-finalization 및 E2E latency와 함께 유효 updates/s, 재실행 비용, state readiness를 측정한다. 두 축과 비교·계측의 상세 기준은 [논문 개요 §5.4](./paper-outline.md#54-rtt--application-operation-count)에 기록한다. Computing Gas를 되살리는 설계 변경이 아니라 실험 workload의 매개변수다.

## 8. 기존 파일 및 구현 상태

- [block-selected-view-protocol.md](./block-selected-view-protocol.md)는 이전 adaptive view-synthesis 탐색안이다. 그 문서의 report quorum, beam search, native Multimmit adapter 가정을 이 모델에 그대로 적용하지 않는다.
- [research/block_views/selection.py](./research/block_views/selection.py)는 기존 합성·재사용 reference model이며, cut별 회전과 본 f+1 인증 경로를 구현한 consensus E2E가 아니다.
- 기존 proof/PAC SDK와 `commonware/`의 legacy EC PoC는 이 모델의 구현이 아니다. 이번 기록에서 코드를 변경하지 않았다.
- 순수 Autobahn 구현 또는 Commonware 위에서 같은 cut 의미를 제공할 adapter 선택, checkpoint/data custody 및 crash recovery는 후속 구현 결정이다. Multimmit adapter를 택하면 n=5f+1 tip extraction과 emitted-prefix closure를 별도로 명세한다.

본문 개요는 [paper-outline.md](./paper-outline.md), 이전 cut-tail 개요는 [보관본](./paper-outline-v12-cut-tail.md)에 있다.
