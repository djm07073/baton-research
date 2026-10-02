# 선언된 state 접근에 따른 결정적 producer 배치 — v2 보관본

> 이 문서는 고정 배치 설정을 사용했던 v2 보관본이다. 현재 기준은 [cut별 회전 배치 v3](./state-affinity-placement.md)이며, 아래 미명세 전달 경계는 v3에서 soft-routing 규칙으로 대체했다.

> 갱신일: 2026-09-21  
> 상태: 설계 v2; 코드·consensus E2E·성능 검증 전  
> 실행 의미: [Block-STM R/W/Defer 모델](./blockstm-execution-model.md)  
> 논문 구조: [paper-outline.md](./paper-outline.md)  
> 이전 설계: [batch-local v1 보관본](./state-affinity-placement-v1.md)

## 1. 이번에 확정한 방향

**Transaction에 주요 입력 object와 접근할 state의 범위·방식을 담고, 그 선언으로 producer 후보 순서를 결정한다.** 접근 목록을 알아내기 위해 transaction을 먼저 실행하지 않는다.

- 같은 signed tx와 같은 공통 배치 설정이면, mempool·수신 순서·로컬 부하가 달라도 같은 후보 순서를 계산한다.
- Producer가 이번에 포함하지 않기로 결정하면 정해진 다음 후보로 tx 전체를 전달한다.
- Tx는 분할하지 않는다. Lane은 producer chain이지 해당 state의 독점 owner가 아니다.
- **배치용 profiling 실행만 제거한다.** Block을 받은 validator가 cut 합의와 겹쳐 수행하는 speculative Block-STM 실행은 유지한다.
- 선언은 실제 접근의 상한이다. 실제 읽은 값·실행 결과·가용성·finality를 증명하지 않는다.
- 기존 ordering 정족수와 결과 인증 경계는 이번 갱신에서 바꾸지 않는다. 이전 proof/PAC·state-owner SDK도 변경하지 않는다.

```text
signed tx + 선언된 object/state 접근
  → 정적 형식·권한 관련 기본 검사와 정규화
  → 공통 설정으로 producer 후보 순서 계산
  → producer에 전파; 미포함 결정이면 다음 후보로 전달
  → 실제 block 생성·전파
      ├─ DA / cut consensus
      └─ pre-cut Block-STM 실행·관측 기록
  → finalized cut 기준 검증·필요한 재실행
  → deferred materialization·기존 결과 인증
```

## 2. Tx에 무엇을 선언하는가

개념적인 예시이며 아직 wire format이 아니다.

```text
tx1.access = { A: defer(add), B: defer(add), C: write }
tx2.access = { A: defer(add), C: read, E: read + write }
```

각 항목은 application/schema version, object 또는 state scope 식별자, 허용 모드 `read/write/defer`, 필요한 defer 타입·연산/profile을 가진다. 선언은 tx 서명에 포함한다. 전달 시 변경하지 않는다.

접근 선언 자체가 object 소유권이나 application 권한을 부여하지는 않는다. 기존 authorization 검사는 별도로 유지한다. 새 object 생성도 임의의 미선언 write로 허용하지 않고, 등록된 생성 규칙이 정한 tx-local fresh-ID 범위 등 명시적인 protocol-derived scope를 사용해야 한다.

정규화한 전체 접근 범위는 다음과 같다.

```text
AllowedAccess(tx) = Normalize(
    SignedDeclaredAccess(tx)
    UNION ProtocolDerivedAccess(tx, runtime_version)
)

ActualAccess(tx) must be contained in AllowedAccess(tx), by scope AND mode
```

- **Implicit 접근:** nonce/replay, fee payer, fee 집계 등 protocol에 필요한 접근은 tx 선언 또는 공통 runtime 규칙에서 반드시 포함한다. 사용자가 생략했다고 의존성이 사라지지 않는다.
- **Read/write 구분:** `write`만 선언했다고 정확한 읽기까지 자동 허용하지 않는다. 읽고 값을 계산해 쓰는 연산은 R+W를 선언한다. 저장소 내부의 상태 갱신 작업과 application의 정확한 읽기는 구분한다.
- **Object와 세부 state:** schema가 exact key와 object 전체/허용된 하위 namespace를 구분한다. Root만 선언하면 더 넓은 범위를 보수적으로 대표할 수 있지만, root 밖의 임의 state까지 허용하지 않는다. V2의 최초 배치 단위는 미리 정한 canonical object/state scope다. 세부 필드는 runtime 검증에 남길 수 있다.
- **분기:** 선언된 범위 중 일부만 사용해도 된다. 모든 지원 실행 경로를 덮는 상한을 작성하며, 실제 접근 집합이 매번 동일하다고 가정하지 않는다.
- **Defer:** 등록된 연산만 허용한다. 일반 RMW를 D 표시만으로 합성 가능한 연산으로 바꾸지 않는다. Delta 수치는 실행 중 계산할 수 있지만 범위·predicate·snapshot은 실제 실행에서 검증한다. 수치를 분기·주소 계산 등에 사용하면 필요한 R도 선언한다.

Admission에서는 서명, 크기, mode/type/schema, 정규화 형식 등 실행 없이 확인할 수 있는 조건을 검사한다. 잔고 부족이나 상태 의존 권한처럼 실행이 필요한 조건까지 여기서 해결했다고 주장하지 않는다.

### 선언 밖에 접근하면

Runtime은 허용되지 않은 접근을 수행하기 전에 해당 시도를 중단하고 staged application effects를 버린다. **Pre-cut의 위반 결과도 speculative**다. Exact cut에서 선행 입력·분기가 바뀌면 재실행 후 정상 완료할 수 있으므로, 이를 즉시 영구 실패로 확정하지 않는다.

Canonical context에서도 위반하면 결정적인 `AccessViolation`으로 처리하고 기존 failure/fee 규칙을 적용한다. Lane을 바꾸거나 재시도한다고 선언을 넓히지 않는다. 선언 변경은 다시 서명한 별도 tx다. 잘못된 읽기 버전 때문에 재실행하는 경우와, 실제로 허용 범위를 위반하는 경우를 구분한다.

## 3. 공통 배치 artifact와 후보 순서

기존 v1의 **로컬 batch를 순서대로 보며 배치하는 greedy**는 현재 정책이 아니다. 다른 batch에서도 같은 tx의 후보 순서가 같아야 하기 때문이다.

새 artifact는 일정 배치 epoch 동안 공유하는 **배치 설정**이다.

- Chain/domain, 설정 digest와 활성화 epoch/범위.
- Eligible producer lanes와 고정 tie-break 순서.
- 정규화 schema, state scope별 선호 lane을 계산하는 고정 함수/seed 또는 명시적인 매핑.
- 접근 모드의 정수 가중치와 중복·중첩 scope 처리 규칙.
- 전달 기록의 형식, 공통 cut-count 기반 fallback에 필요한 설정.

설정은 genesis 또는 기존 ordered configuration 경로로 공통으로 확정한다. Producer가 임의로 선택한 최신 설정이나 로컬 queue length를 입력으로 쓰지 않는다. **새 quorum certificate를 만드는 것은 아니지만, 서로 다른 설정을 제각각 사용해도 결정적이라고 주장할 수는 없다.** Tx/envelope는 어느 설정을 따르는지 모호하지 않게 bind해야 한다.

### 초기 점수 규칙 — 제안, 성능 최적값 아님

정규화한 scope 하나당 R 또는 W가 있으면 1점, 조건 관측이 있는 D/분류 불명확 D는 1점, policy가 허용한 순수 합성 D-only는 0점으로 시작한다. R+W는 중복하여 2점으로 세지 않는다. 같은 scope를 반복하거나 부모·자식 항목을 겹쳐 적어도 부당하게 점수가 증가하지 않도록 공통 schema가 병합한다.

이 점수는 **개별 tx의 배치 점수**다. v1의 tx 쌍 사이 conflict 점수 `4/1/0`과 다른 규칙이다. D의 0점은 검증 비용이나 범위 오류 가능성이 0이라는 뜻이 아니다.

```text
rank_producers(tx, config):
    access = normalize_declared_and_protocol_access(tx, config.schema)
    score[lane] = 0
    for scope in access:
        lane = preferred_lane(config, scope.id)
        score[lane] += routing_weight(config, scope)
    if every score is zero:
        return lanes sorted by fixed hash(config, signed_tx_id, lane_id)
    return lanes sorted by descending score,
           then config's fixed lane priority
```

고정 함수의 hash/encoding과 정수 overflow 처리는 policy version에 고정한다. Scope map은 **선호 배치**이지 state 권한이나 독점 ownership이 아니다. 모든 validator는 실제 block의 전체 tx를 shared state 위에서 실행할 수 있다.

### 사용자의 예시

설정이 `C → L0`, `E → L1`, 동점 순서가 `L0 < L1`이고 A/B가 순수 D라고 하자. 설명에서는 application 접근만 표시하며 실제 배치에는 implicit 접근도 포함한다.

| Tx | L0 점수 | L1 점수 | 후보 순서 |
|---|---:|---:|---|
| tx1: D(A), D(B), W(C) | 1 | 0 | L0 → L1 |
| tx2: D(A), R(C), R/W(E) | 1 | 1 | L0 → L1 |

이 조건에서는 둘 다 L0를 먼저 선택한다. **모든 multi-state tx가 항상 같은 lane에 모인다는 보장은 아니다.** 다른 scope·implicit 접근·설정의 점수에 따라 달라지고, 모든 연결된 tx를 완전히 함께 묶으려 하면 큰 충돌 component가 한 lane에 집중될 수 있다.

## 4. 포함하지 않을 때 다음 producer로 전달

정상 producer는 유효한 tx를 지금 포함하지 않기로 결정했다면 다음 후보로 전달한다. 영구적인 정적 형식/서명 오류는 전달 대상이 아니다.

```text
route(tx, config) = [P0, P2, P1, ...]

P0: include → actual block
    pass    → original signed tx + signed Pass to P2
P2: include → actual block
    pass    → original signed tx + signed Pass to P1
```

`Pass`는 tx identity, 설정 digest/epoch, 현재 순번, from/to에 bind한다. 순번은 증가하고 작성자는 그 순번의 producer여야 한다. 정상 노드는 포함 확인 또는 기존 보관 한도까지 재전송 가능한 사본을 보관하고, 제출자/relay도 전달을 도울 수 있다. 별도 quorum이나 participant-wide handshake를 요구하지 않는다.

로컬 부하는 **include/pass 결정**에 영향을 줄 수 있지만 다음 목적지는 바꾸지 않는다. 따라서 결정성은 같은 tx/config의 **후보 순서**와 같은 전달 이력의 다음 후보에 대한 것이다. 실제 포함 producer·포함 시점·block contents까지 tx만으로 같아지는 것은 아니다.

### 침묵·중복과 아직 명세할 경계

- Producer가 Pass도 보내지 않으면 그 서명을 영원히 기다리지 않는다. 공통으로 검증 가능한 routing 시작 cut과 경과 finalized-cut 수에 따른 fallback이 필요하다. 노드별 최초 수신 시각은 시작점으로 쓰지 않는다.
- 시작 cut을 tx/envelope에 bind하는 방식, epoch 전환 중 구 설정의 유효 범위, 모든 후보 소진 후 재시도 규칙은 구현 전 명세 항목이다. 로컬 타이머는 재전송을 촉진할 수 있지만 독자적으로 공통 routing 권한을 바꾸지는 않는다.
- Pass는 기존 producer가 이미 발행했거나 전송 중인 block을 취소하지 않는다. Byzantine 이중 포함과 정상 in-flight 중복 모두 가능하다.
- 모든 selected occurrences는 기존 canonical tx ID/nonce/replay/status/fee 규칙을 따른다. 같은 cached effects를 두 번 설치하지 않되, 서로 다른 occurrences의 fee 처리는 순차 oracle에 맞춘다.
- 실제 producer 제한을 consensus admission으로 강제하려면 initial/pass/fallback의 admissible placement predicate를 별도 정의해야 한다. **현재 문서는 그 강제가 구현되었다고 주장하지 않는다.** 이 명세 없이 임의의 wrong-lane block을 새로 거부하지 않는다.

이 경계는 전파 정책의 결정성과 exclusive inclusion 보장이 서로 다름을 명시한다. 전달은 tx의 접근 선언·권한·실행 의미를 바꾸지 않는다.

## 5. 재실행 감소와 안전성의 경계

같은 producer, 가능하면 같은 block에 관련 tx를 묶으면 입력과 상대 순서를 함께 받기 쉬워진다. 실행기는 알려진 writer를 unresolved/ESTIMATE로 관리하여 reader의 불필요한 초기 실행을 줄일 수 있다. Same-block 성질은 실제 packing 결과에서만 성립하며 nonce/admission·block 한도가 우선한다.

하지만 선언은 읽을 **위치**를 알려줄 뿐 읽을 **값**이나 최종 predecessor를 고정하지 않는다. 늦은 block, cut 제외, parent 변화, 실제 predicate 변화는 재실행을 유발할 수 있다. 재전달도 locality를 낮출 수 있다.

```text
same exact finalized cut + canonical parent + runtime/order/fee rules
  ⇒ same serial-oracle state, status, events and fees
```

배치가 달라져 다른 block/cut/order가 생기면 결과도 달라질 수 있다. 후보 순서·설정 digest·선언 일치만으로 speculative cache를 재사용하지 않는다. 실제 R/W/D와 부재·존재·range 관측을 기존 Block-STM adapter가 검증한다.

과대 선언은 배치 집중·불필요한 의존성·metadata 비용을 늘릴 수 있다. 선언 크기·scope 수·wildcard 범위·계산 비용을 제한한다. State/tx ID grinding, hot-key 집중, producer withholding에 대한 완전한 공정성·부하 균형 보장은 없다.

## 6. 검증과 실험

필수 설계/구현 테스트:

1. 다른 mempool·수신 순서·로컬 부하에서도 같은 signed tx/config는 같은 후보 순서.
2. 중복/중첩 scope와 R+W 정규화, 순수/조건부 D, implicit nonce/fee 접근, 전부 0점인 tx.
3. 형식 오류의 ingress 거부와 runtime 접근 위반의 구분. Pre-cut 위반→canonical 정상 분기, canonical 위반의 effects 폐기·fee 처리.
4. Exact key/root namespace containment, mode 위반, D-only의 exact read 시도, 존재/부재/range 검증.
5. Include/pass, 순번 역행·위조·잘못된 설정, 미응답 fallback, epoch 전환, 중복 포함·재전송.
6. Same-block/다른 blocks, late predecessor·cut 제외·parent 변경에서 순차 oracle과 결과 일치.

실험은 hash routing, 선언 기반 후보 순위, 같은 block packing, dependency-aware scheduling의 효과를 분리한다. 선실행 profiling은 기본 경로가 아니라 별도 비교군이다. 선언 과대 정도, hot-key 분포, lane 수, 전달 횟수, queue wait, RTT와 application operation 수를 바꾼다.

Cut→state뿐 아니라 submit→state/read-ready, 총 CPU/committed tx, retry 원인, 선언 bytes, mapping/전달 비용, ordering latency, goodput을 함께 측정한다. Routing으로 순서·성공률이 달라지는 E2E와 동일 확정 trace의 실행기 비교를 구분한다. **재실행 감소는 실험 가설이며 아직 측정하지 않았다.**

### 참고 및 보관 자료

- [Block-STM](https://arxiv.org/html/2203.06871v3): 실제 관측 검증·재실행의 기반. 본 routing 변경을 자동 제공하는 것은 아니다.
- [Sui 입력 object](https://sdk.mystenlabs.com/sui/transactions/reference), [Dynamic Fields](https://docs.sui.io/develop/objects/dynamic-fields): 입력 root/권한과 동적 세부 접근의 구분을 참고한다. Sui 전체 프로토콜을 복제한다는 뜻이 아니다.
- [AIP-47](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md): typed deferred operation·관측 검증의 참고점.
- [v1 문헌 비교·25개 예시 점검 기록](./state-affinity-placement-v1.md), [v1 JSON fixture](./research/placement/example-plan.json): 과거 batch-local 알고리즘의 기록이며 v2의 테스트 완료 증거로 사용하지 않는다.
