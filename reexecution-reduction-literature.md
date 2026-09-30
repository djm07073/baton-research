# Pre-cut DAG 실행의 재실행 감소: 선행연구와 적용 후보

> 조사일: 2026-09-19  
> 상태: 원문 기반 연구 메모. 프로토콜 채택·구현·성능 검증 완료 기록이 아니다.  
> 기준: [회전형 RR-DAG 설계](./rotating-round-robin-dag.md), [논문 개요 v13.2](./paper-outline.md). 기존 proof/PAC SDK와 구분한다.

## 1. 결론

공통 순위와 conflict DAG는 도착 순서에 따른 불필요한 순서 차이를 줄인다. 그러나 **같은 DAG 규칙**이 **같은 사전 실행 입력**을 보장하지는 않는다. 늦은 블록, cut에서 제외되는 writer, 바뀐 parent 때문에 계산의 입력은 달라질 수 있다.

추가할 가치가 높은 기법은 다음 세 가지다.

1. 실제 읽은 상태와 그 출처를 기록해 재검증과 재실행을 구분한다.
2. 블록은 ordering 단위로 유지하되, 내부 계산의 재사용 단위는 더 작게 둔다.
3. 여러 입력 변경을 하나의 재실행 작업으로 합치고, 불안정한 선행 계산의 결과를 읽는 작업만 잠시 미룬다.

초기 구현 후보는 **정적 block DAG + 버전 기반 읽기 검증 + transaction 단위 계산 캐시 + 중복 재실행 요청 병합**이다. Operation-level repair와 값 동등성 기반 재사용은 추가 복잡도가 크므로 별도 확장으로 평가한다. 이는 본 조사에서의 추천이며 기존 합의된 설계를 자동 변경하지 않는다.

## 2. DAG만으로 해결되는 것과 남는 것

현재 모델은 block-level DAG, 고정된 block 내부 transaction 순서, 정적으로 검증 가능한 conservative read/write sets, slot별 공통 rank를 사용한다. Ordering consensus 전체 절차와 exact-cut 실행결과 인증은 유지한다.

### 세 가지 재실행 원인

| 원인 | 공통 DAG 규칙의 효과 | 남는 문제 |
|---|---|---|
| 같은 블록들을 서로 다른 도착 순서로 실행 | 같은 집합·context의 충돌 방향을 통일 | 입력 집합이 아직 다를 수 있음 |
| 늦은 lower-rank writer의 삽입 | 삽입 위치와 의존성을 결정적으로 계산 | 이미 읽은 값이 달라지면 복구 필요 |
| 최종 cut의 제외·추가·parent 변경 | 최종 reference execution을 통일 | 사전 결과의 입력을 다시 검증해야 함 |

예를 들어 초기 `x=10`, 순위 `A < B`, `A: x=20`, `B: y=x+1`이라고 하자.

- `B`만 받은 노드는 `y=11`을 계산한다.
- 최종 cut에 `A,B`가 들어가면 정답은 `y=21`이다.
- 두 블록을 미리 받았더라도 cut이 `B`만 선택하면 `y=11`이 정답이다. 서로 다른 producer lanes라면 B의 포함이 A의 포함을 자동 보장하지 않는다.

따라서 **입력 도착이 완전한지**와 **어떤 입력이 선택되는지**는 별개의 불확실성이다. DA 증거나 시간이 지났다는 사실만으로 앞에 올 충돌 블록이 더 없다고 단정할 수 없다.

이는 간단한 정보 제약이다. 서로 다른 두 가능한 cut에서 B의 정답이 다르면, cut 전에 하나의 결과만 계산하고 항상 재사용하는 것은 불가능하다. 대기, 보정, 복수 결과 준비 또는 추가적인 입력 제한 중 어떤 비용은 필요하다. 본 추천은 기존 ordering을 바꾸지 않고 보정 비용을 줄이는 쪽이다.

## 3. 직접 참고할 논문

아래는 원문에서 확인한 기법이다. 오른쪽 적용 평가는 우리 모델에 대한 추론이며 원 논문의 성능 결과가 아니다.

| 연구 | 확인한 기법 | 우리 모델에 가져올 부분 / 한계 |
|---|---|---|
| **[Efficient Parallel Execution of Blockchain Transactions Leveraging Conflict Specifications](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.AFT.2025.29), AFT 2025**, §4–5 | dBTM은 preset order와 정확하거나 보수적인 conflict 정보를 DAG로 만들고 predecessor 완료 뒤 실행한다. | 정적 DAG의 직접 선행연구·baseline. 입력 집합과 순서가 주어진 실행이므로 unknown-cut 문제를 해결한 것은 아니다. |
| **[Block-STM](https://arxiv.org/html/2203.06871v3), PPoPP 2023**, §2–3 | 직전 writer의 index/incarnation을 기록하고 재검증한다. 무효화된 writer의 값을 ESTIMATE로 표시해 소비자의 불필요한 실행을 억제한다. | 버전 추적과 선행 계산 대기. 읽기 검증 실패는 해당 transaction 재시작이며 전체 후속 transaction의 무조건 재실행이 아니다. |
| **[Spectrum](https://www.vldb.org/pvldb/vol17/p2541-zhang.pdf), PVLDB 17(10), 2024**, §4.3–4.4 | 특정 외부 SLOAD 전에 checkpoint를 저장하고 가장 이른 충돌 읽기로 복귀한다. 이후 suffix의 speculative read/write를 제거하고 다시 실행한다. | 유효한 prefix를 살리는 비교적 단순한 부분 재실행. 뒤쪽의 독립 계산까지 모두 보존하는 dataflow repair와는 다르다. |
| **[ParallelEVM](https://yajin.org/papers/eurosys2025_parallelevm.pdf), EuroSys 2025**, §4–5 | SSA operation log로 연산의 데이터 의존성을 추적하고 충돌 영향 연산을 redo한다. 제어 조건을 constraint guards로 확인한다. | 더 정밀한 연산 단위 복구. 추적 비용이 있으며 guard가 맞지 않으면 abort/restart 경로가 필요하다. |
| **[Seer](https://www.vldb.org/pvldb/vol18/p822-xiao.pdf), PVLDB 18(3), 822–835**, §3.2, §3.4–3.7 | 순서를 예상해 pre-execute하고, 늦은 상위 순위 입력이 들어오면 분기 조건을 재확인한다. Checkpoint와 계산 trace로 이전 작업을 재사용한다. | late insertion 뒤 부분 보정의 직접 참고점. 같은 branch라는 이유만으로 이전 write를 그대로 적용하지 않고 state-dependent write는 갱신한다. |
| **[BOHM: Rethinking Serializable Multiversion Concurrency Control](https://www.vldb.org/pvldb/vol8/p1190-faleiro.pdf), PVLDB 8(11), 2015**, §3 | 미리 정해진 batch order와 write sets로 version placeholders를 만들고 reader가 필요한 writer 결과를 기다린다. | 알려진 미완료 writer와 존재 여부도 모르는 writer를 구분하는 데 유용하다. 미지의 earlier writer나 cut 제외는 별도 처리해야 한다. |
| **[Pilotfish](https://arxiv.org/html/2401.16292v3), FC 2025**, §4, §6, Appendix E.3 | 합의가 정한 영구적인 transaction sequence를 object/version queues와 producer-consumer dependencies로 실행한다. | 의존 계산만 기다리는 scheduler와 버전 보존의 참고점. 여러 validator 사이 실행 분담이나 pre-cut membership 예측의 근거는 아니다. |
| **[Processing Transactions over Optimistic Atomic Broadcast Protocols](https://www.inf.usi.ch/faculty/pedone/Paper/199x/1999ICDCS.pdf), ICDCS 1999**, §3 | tentative order에서 실행하고 definitive order로 확정한다. Conflict class별 queue를 사용하고 무관한 재정렬 때문에 결과를 버리지 않는다. | 합의와 실행 overlap의 오래된 선행연구. Crash-only 모델이므로 Byzantine 안전성을 그대로 인용할 수 없다. |

서지 확인:

- Block-STM의 학회는 [PPoPP 2023 공식 목차](https://www.sigplan.org/OpenTOC/ppopp23.html)에서 확인했다. 오래된 preprint의 ACM template 표기를 학회 정보로 사용하지 않는다.
- Seer PDF의 자체 reference year는 **2024**다. Volume 18이라는 이유만으로 발행년을 2025로 바꾸지 않는다.
- Pilotfish는 [FC 2025 수록 논문이며 proceedings 공개일은 2026-01-02](https://link.springer.com/chapter/10.1007/978-3-032-07024-1_17)다.
- AFT 논문의 비교 대상 PEVM은 RISE의 구현이다. 이름이 비슷한 EuroSys의 ParallelEVM과 동일 대상으로 단정하지 않는다.

### 추가 근거와 이번에 그대로 채택하지 않는 부분

- **[Hackwrench, PVLDB 16(8), 2023](https://www.vldb.org/pvldb/vol16/p1930-dong.pdf), §3.4:** batch 안의 의존 연산을 선택적으로 repair한다. 하지만 repair 중 tuple locks와 timestamp 기반 distributed commit을 사용하므로, 그 성공 보장을 non-blocking Byzantine 환경에 그대로 옮길 수 없다.
- **[Calvin, SIGMOD 2012](https://dsf.berkeley.edu/cs286/papers/calvin-sigmod2012.pdf), §3.1–3.2:** 순서와 access sets를 먼저 정하고 deterministic locking을 수행한다. 알려진 입력의 abort 회피 baseline이지 미완성 cut의 실행 해결책은 아니다.
- **[Nezha, PVLDB 16(4)](https://www.vldb.org/pvldb/vol16/p629-geng.pdf), §2–4:** deadline까지 메시지를 잠시 모아 정렬하는 아이디어는 bounded reorder buffer에 참고할 수 있다. 원래는 synchronized clocks와 fail-stop 모델이다. 로컬 실행 대기로만 사용하고 timestamp를 새 canonical rank나 admission 조건으로 도입하지 않는다.

## 4. 추천 적용안

### 4.1 실행 순서의 간선과 재실행 원인을 구분

기존 block DAG는 그대로 두고, 각 계산이 실제로 읽은 key와 version을 추가 기록한다.

- Same-lane edge: lane 내부 순서 제약.
- WW edge: 두 write의 최종 적용 순서 제약.
- 실제 read-from dependency: 어떤 계산 결과가 다른 계산의 입력이 되었는지.

앞의 두 간선이 있다는 이유만으로 application 계산을 반드시 다시 해야 하는 것은 아니다. 예를 들어 이전 block이 `x`를 변경하고 다음 block이 `y`만 읽는다면, lane 순서는 유지하면서 다음 block의 계산은 재사용할 수 있다. 단 nonce, fee, parent root 등 숨은 입력까지 영향을 받지 않아야 한다. State root나 전체 결과 commitment는 별도로 다시 구성해야 할 수 있다.

읽기 검증은 **예전에 읽었던 writer가 그대로 남았는지**만 검사하면 안 된다. 새 writer가 중간에 들어와 실제 직전 writer가 바뀌었는지도 확인해야 한다. 최종 선택 집합, 삭제·존재 여부, conditional no-write, 실패에 따른 write 제거도 반영한다.

초기안은 `(block identity, transaction occurrence, incarnation)`으로 버전을 구분한다. 미완성 목록의 dense index만 identity로 쓰면 앞쪽 삽입이 전부 다른 계산처럼 보일 수 있다. Slot/anchor 변경 시 rank는 다시 계산하되 stable occurrence identity와 분리한다.

이것은 Block-STM/BOHM에서 가져온 version reasoning을 변화하는 cut 입력에 적용하는 설계 후보다.

### 4.2 블록은 ordering 단위, 내부 캐시는 재사용 단위

블록을 합의하는 것과 블록을 매번 처음부터 다시 계산하는 것은 별개다. 블록 간 순서 및 블록 내부 transaction 순서는 바꾸지 않는다.

가장 단순한 방법은 새로운 block input overlay에서 원래 transaction 순서대로 진행하면서 다음을 수행하는 것이다.

1. 해당 transaction의 캐시가 현재 읽기 입력·runtime/context와 일치하는지 검증한다.
2. 일치하면 보관한 effects를 새 overlay에 적용한다.
3. 불일치하면 그 transaction만 실행하고 새 결과를 저장한다.
4. 이후 transaction도 갱신된 overlay에서 같은 검사를 수행한다.

이렇게 하면 block 안의 한 transaction이 바뀌었다고 무관한 나머지 계산까지 전부 실행할 필요가 없다. 여러 transaction의 effects를 순차적으로 조립하는 비용과 state-root 계산 비용은 남는다. 블록을 opaque 실행 함수 하나로 유지한다면 이 최적화는 불가능하므로 내부 실행 기록이 추가로 필요하다.

더 무거운 application에서는 Spectrum 방식의 checkpoint suffix recovery, 그다음 ParallelEVM/Hackwrench 방식의 의존 연산 repair를 검토한다. 단순 Bank transfer는 계산 자체가 싸므로 trace/checkpoint 비용이 이득보다 클 수 있다.

이것은 transaction별 별도 합의나 부분 canonical commit이 아니다. Transaction의 실패·성공 의미와 protocol의 block validity 규칙을 그대로 보존하며 최종 결과를 하나로 검증한다.

### 4.3 불안정한 선행 입력 때문에 같은 일을 반복하지 않기

예를 들어 A가 재계산 중이면, B가 A의 오래된 값을 읽고 다시 실패하는 작업을 반복하지 않도록 A의 출력 버전을 unresolved로 표시한다. B를 그 dependency의 대기열에 넣고, 무관한 C는 계속 실행한다.

Block-STM의 ESTIMATE는 이런 낭비 억제의 근거다. 원 논문은 소비자의 VM 실행을 중단·폐기하고 predecessor의 다음 incarnation 완료 뒤 재시작한다. 임의의 VM continuation을 그대로 재개하는 기법으로 표현하지 않는다. 정적 footprints를 이용해 첫 실행 전부터 placeholder를 설치하는 것은 BOHM을 참고한 별도 적용안이다.

여러 late block이 가까운 시간에 도착하면 다음과 같이 로컬 작업을 병합한다.

- 동일 계산에 대한 dirty 표시와 재실행 예약은 하나로 유지한다.
- 알려진 lower-rank dirty writer를 먼저 처리한다.
- 그 결과가 준비되면 readers를 재검증한다.
- 새 invalidation이 실행 도중 생기면 generation을 갱신한다. 이전 generation의 늦은 완료가 새 overlay에 잘못 publish되지 않게 한다.
- Speculative attempt/CPU/overlay budget을 넘으면 해당 작업만 cut 이후로 미룬다. Finalized work의 자원은 별도로 확보한다.

매번 새 block이 왔다고 attempt budget을 초기화하면 악의적인 지연에 대한 제한이 무효가 된다. Per-occurrence 제한과 전체 speculative 자원 제한을 함께 둔다. 정상적인 finalized 실행까지 영구적으로 막는 제한은 두지 않는다.

짧은 hold-back을 사용할 경우 최초 대기 시작부터의 최대 시간을 정해 drip-feed가 timer를 무한 연장하지 못하게 한다. 로컬 대기 시간은 효율 정책이며 finality나 블록 제외의 근거가 아니다.

### 4.4 후보 cut을 알게 되면 그 입력의 준비를 우선

Candidate cut이 도착하면 그 exact set에서 missing bodies를 복구하고 읽기 검증·복구를 우선한다. 후보 밖 speculative 결과는 별도 cache/overlay에 남겨 오염을 방지한다. 이를 위해 새 ordering round를 추가하지 않는다.

후보는 바뀔 수 있으므로 이 단계는 계산 우선순위이지 최종 확정이 아니다. 계산 캐시가 재사용되더라도 cut·parent·DAG·result에 묶인 전체 실행결과 서명은 새 context에서 다시 만들어야 한다. 기존 cut 합의는 실행 완료를 기다리지 않는다.

## 5. 직관적인 적용 예시

아래는 실험 수치가 아닌 설명용 예시다. 공통 순위는 `A1 < B1 < C1`, 초기 `Alice=100`이다. A1은 Alice 잔고를 80으로 만든다. B1 안에는 아래 두 transaction이 고정 순서로 들어 있다.

| 계산 | 처음 실행 | A1이 늦게 들어온 뒤 |
|---|---|---|
| B1의 tx1: Alice에서 10 차감 | Alice=90 | 입력 100→80이므로 재실행, Alice=70 |
| B1의 tx2: 독립적인 Carol 계정 갱신 | Carol 결과 계산 | 모든 관측 입력이 같다면 캐시 재사용 |
| C1: Alice 잔고가 50 이상인지 읽어 별도 flag 기록 | flag=true | 입력을 다시 확인해야 함; flag는 여전히 true일 수 있음 |
| 다른 block: Carol 결과만 읽음 | 결과 계산 | Carol 입력이 유효하면 재실행 불필요 |

여기서 요구하는 것은 “B1을 두 블록으로 나눈다”가 아니라, **B1 내부 계산의 재사용 가능성을 기록한다**는 것이다. 공통 fee/nonce 등으로 tx1·tx2가 실제로 연결되면 재사용 판단은 달라진다.

추가 최적화로 C1을 다시 계산해도 flag가 그대로라면, flag만 읽는 후속 계산은 재사용할 수 있다. 하지만 최초 구현의 version-equality 검증에서는 C1의 incarnation이 바뀌어 보수적으로 다시 실행할 수 있다. 이 손실을 줄이려면 별도의 value-equivalent reuse 검증이 필요하다.

값 동등성 재사용은 모든 observable inputs가 동일하고 version identity 자체가 application 의미에 노출되지 않는 경우에만 허용한다. ABA처럼 값이 되돌아와도 provenance를 검증 없이 같다고 취급하지 않는다. 재사용 결과의 branch lineage와 commitment는 새 context에 맞춰 갱신한다.

## 6. 안전성 경계와 한계

- Static footprint는 후보 영향 범위를 찾는 데 쓰고, 실제 관측 입력 검증으로 재사용을 판단한다. 선언되지 않은 접근을 허용하면 안전성 근거가 깨진다.
- Range/absence read는 반환된 key만이 아니라 predicate, bounds, 정렬·limit, 존재하지 않음까지 검증한다. Spectrum의 실험은 range-query TPC-C transactions를 제외하므로 그 논문을 range 지원 증거로 쓰지 않는다.
- Nonce, fee/gas, timestamp, runtime version, generated IDs, 상태 기반 실패와 event/status 등도 입력·effects에 포함한다.
- Blind write가 정말 이전 값을 읽지 않는다면 overwrite 대상의 변화만으로 계산을 다시 할 필요는 없다. 그러나 balance 증가·감소는 보통 read-modify-write이며 blind write가 아니다.
- 서로 겹치는 write를 재조립할 때 canonical rank 순서와 transaction 원자성을 지킨다. 계산 재사용이 delta의 임의 병합을 허용하지 않는다.
- 알려진 predecessor가 아직 실행 중인 경우와, 어떤 predecessor가 존재할지 모르는 경우를 구분한다. 후자는 정적 footprint가 있는 수신 블록만으로 해결되지 않는다.
- Hot-key의 긴 진짜 의존 chain은 DAG로 제거할 수 없다. 선행 입력 하나가 모든 후속 계산을 바꾸면 전체 재실행이 필요한 최악 사례가 남는다.
- Non-blocking은 ordering과 독립 계산이 계속한다는 뜻이다. 모든 state-dependent 계산이 기다리지 않는다는 보장은 아니다.
- 수신 metadata와 speculative overlays의 메모리, 캐시 검증 비용, stale completion 처리 비용을 포함해서 평가해야 한다.

## 7. 기존 문서 대비 추가되는 연구 항목

기존 RR-DAG 문서는 이미 읽기 검증, 영향받은 작업의 재실행, replay coalescing과 자원 제한을 언급한다. 따라서 이 단어들을 새 novelty로 제시하지 않는다.

이번에 구체화할 가치가 있는 것은 다음이다.

1. Scheduling edge와 실제 입력 provenance를 분리하여 어떤 변경이 계산을 무효화하는지 정식화.
2. 블록 단위 순서와 더 작은 계산 재사용 단위를 함께 유지하는 알고리즘.
3. Arrival 변화와 cut membership 변화 모두에 대한 cache validation·generation 관리.
4. Speculation 대기/횟수 제한이 post-cut 잔여 작업과 E2E latency에 미치는 trade-off.

공통 DAG 자체는 AFT 2025 등의 직접 선행연구가 있고, consensus와 실행 overlap 자체도 ICDCS 1999 같은 오래된 선행연구가 있다. 논문 기여 후보는 **Autobahn의 불완전한 multi-producer 입력에 대한 사전 실행을 exact finalized cut으로 저비용 보정하고 결과 인증까지 연결하는 방법 및 평가**다. 이 조합이 최초라는 주장은 추가적인 체계적 선행성 검토 없이 하지 않는다.

## 8. 권장 실험

동일 rank, 동일 block 내용·내부 순서, 동일 cut 선택 trace, 동일 CPU·workers·load로 비교한다. Full trace는 replay 용도로만 사용하며 pre-cut scheduler에게 미래 포함 정보를 제공하지 않는다.

| 비교군 | 목적 |
|---|---|
| 같은 DAG의 post-cut 실행 | 최종 결과 oracle과 latency 기준 |
| Pre-cut 실행 + block 전체 재실행 | 가장 단순한 speculation 비용 |
| + 실제 읽기 버전 검증 | 무관한 blocks 재사용 효과 |
| + block 내부 transaction 캐시 / checkpoint | 복구 단위 축소 효과 |
| + dirty 요청 병합·알려진 dependency 대기 | 반복 재실행 억제 효과 |
| + 선택적 값 동등성 검증 | 변화 전파를 더 일찍 멈추는 효과; 별도 확장 |

주요 변수는 기존 **RTT × transaction당 state 변경 횟수**에 아래를 추가한다.

- Lower-rank block의 지연·도착 역전 비율과 burst 정도.
- Candidate cut 교체, speculative writer 제외, body 누락, 앞 slot parent 지연.
- 실제 conflict density, hot-key skew, block 안의 독립 transaction 비율, 의존 chain 길이.
- Block/transaction 계산 비용, cache 크기, speculative attempt budget.

보고할 값:

- Cut→state-finality, 제출→state-finality, durable readiness p50/p95/p99.
- 재실행한 blocks/transactions뿐 아니라 **버린 CPU 시간과 재실행 연산량**.
- 재검증 비용, state-root 재구성, 결과 서명 수집, 메모리와 DAG 관리 비용.
- Ordering throughput/latency와 유효 state 처리량; application 실패와 실행 retry를 분리.
- Pre-cut work가 많이 끝났는지뿐 아니라 cut 후 critical path에 남은 작업량.

대기를 늘리거나 ordering을 늦추면 재실행 횟수만 쉽게 줄일 수 있다. 따라서 재실행 최소화가 아니라 **총비용을 제한하면서 cut 이후 잔여 지연과 E2E 지연을 함께 줄이는 것**을 평가한다. 실제 성능 수치는 구현·실험 전에는 제시하지 않는다.

## 9. 읽기 우선순위

1. **AFT 2025 conflict specifications**: 우리 정적 DAG의 직접 선행기술과 비교 기준.
2. **Block-STM + Spectrum**: 첫 구현에 필요한 검증·대기·부분 재실행.
3. **Seer**: late insertion과 pre-execution mismatch의 부분 보정.
4. **ParallelEVM / Hackwrench**: 더 정밀한 연산 단위 repair가 필요한 경우.
5. **BOHM / Pilotfish / optimistic atomic broadcast**: 대기·버전 관리·overlap의 전제와 한계.

이번 작업에서는 본 연구 메모만 추가하고 기존 논문 개요, 프로토콜, SDK와 consensus 코드를 변경하지 않았다.
