# Direction 선택과 재실행

Leader는 원본 reports로 유효 direction을 선택하고, 각 노드의 Baton은 이를 사전 실행 계획에 반영한다. Direction 승인 quorum을 추가하지 않는다.

## Leader: report로 Baton 생성

Rust 선언: [Planner](../overview/rust-interfaces.md#planner) — 전체 원형은 「Rust 인터페이스」에서 관리한다.

`ReportSnapshot`은 한 번 닫은 distinct same-context 원본 보고 집합이고 `Candidates`는 bounded admissible full-candidate 집합이다. `Some`은 그 집합의 평가가 끝나고 선택이 유효한 경우만 반환한다. 미완료·유효 후보 부재는 prepared policy로 발표하지 않는다. 이 local background future를 native cut 경로에서 await하지 않는다. Same-prefix tail, budget, 채택·continuation 연결은 아래 기존 미결정 항목 그대로다.

| 단계 | 입력 | 처리 | 출력 |
|---|---|---|---|
| Window 시작 | 새 작업과 actual planning context | Context를 고정하고 deadline 설정 | Window context |
| Admission | Signed reports | Same-context·distinct identity 검증 | Original report snapshot |
| Snapshot 종료 | 첫 `4f+1` admission 또는 fixed deadline | 한 번만 닫기, arrivals로 deadline 연장 금지 | `m≤4f+1` frozen reports |
| 후보 평가 | Bounded admissible full candidates | Ancestry / predecessor closure / actual context 검증 후 LCP 계산 | 완료된 평가 또는 incomplete |
| 일차 선택 | Same-context original reports | `2f+1`이 전체를 공유하는 최장 유효 nonempty prefix 길이 최대화 | Selected prefix를 포함한 full candidate |
| Fallback | 해당 prefix 없음 | 유효 후보의 raw sum-LCP 최대화 | 유효한 direction candidate |
| NativeBase | Reports / 준비된 유효 후보 없음 | Actual-parent 유효 기본 policy 사용 | Native cut 진행 |
| 전파 | 준비된 direction | Producer와 executor validator의 Baton에 전송 | Advisory reschedule |

`ℓᵢ(P)=|LCP(P,Rᵢ)|`, fallback score는 `Σᵢℓᵢ(P)`다. 원본 report를 filtering·completion으로 바꾸어 support를 만들지 않는다. 후보 집합의 평가가 끝나지 않았으면 최장 선택을 완료했다고 선언하지 않는다. `2f+1`은 최소 `f+1` 정상 **intention**을 남기며 실제 완료·재사용이나 native inclusion을 보증하지 않는다.

`2f+1` 지지는 **후보의 처음 k개가 각 원본 report의 처음 k개와 모두 같은 report가 2f+1개 이상**이라는 뜻이다. 각 block을 지지하는 사람 수를 따로 더하거나, full candidate 전체가 일치해야 한다고 해석하지 않는다.

계산 예로 `f=1,n=6`에서 같은 context의 distinct identities 다섯 개가 다음 원본 orders를 냈다고 하자. `R1=[A,B,C,D]`, `R2=R3=[A,B,D,C]`, `R4=R5=[A,C,B,D]`다. 완료된 bounded admissible 후보 집합이 아래 두 후보라고 가정한다. 두 후보와 검토 prefix가 모두 유효하다는 조건의 분석 예이며 실제 native trace가 아니다.

| Full candidate | 원본 report별 LCP 길이 | 3개 이상이 전체를 지지하는 최장 prefix | Raw sum-LCP |
|---|---|---|---|
| `P1=[A,B,C,D]` | `(4,2,2,1,1)` | `[A,B]`, 길이 2 | 10 |
| `P2=[A,C,B,D]` | `(1,1,1,4,4)` | `[A]`, 길이 1 | 11 |

일차 선택은 **P1**이다. P2의 sum이 더 커도 supported prefix 길이가 먼저다. 다른 deadline snapshot에 `R1=[A,B,C,D]`, `R2=[A,C,D,B]` 두 개만 있다면 3-report 지지가 불가능하므로 fallback이다. 같은 두 후보의 raw sum은 P1이 `4+1=5`, P2가 `1+2=3`이어서 P1을 고른다. 큰 f개의 LCP를 빼지 않는다. 이 계산은 후보 집합 밖의 global optimum·native inclusion·완료된 execution work를 증명하지 않는다.

같은 최장 supported prefix 이후 tail의 선택과 그 선택에 사용할 보조 점수 정책은 미결정이다. Cut은 report·timer·planner를 기다리지 않는다. 준비 전 valid base fallback과, 이미 인증된 protected prefix를 보존할 의무를 구분한다. Prefix-adoption / exact continuation의 native 통합 증명은 아직 없다.

예를 들어 같은 immutable frontier 이후 유효 prefix `p=[A1,B1]`을 선택했다면 아래처럼 구분한다. 동일 canonical input state/runtime과 predecessor closure가 성립한다는 전제의 설명이며 실행 trace나 완성된 보존 증명이 아니다.

| 방출 순서 O | p의 모든 입력 포함 | p가 정확한 leading prefix |
|---|---|---|
| `[A1,B1,A2]` | 예 | 예 |
| `[A1,X,B1]` | 예 | 아니오 |
| `[B1,A1]` | 예 | 아니오 |

X가 B1의 필수 predecessor라면 애초에 `[A1,B1]`은 이 context의 유효 후보가 될 수 없다. 후보 validity와 채택 후 leading order 보존을 모두 확인해야 한다.

## Leader: producer들에게 Baton 전파

전파 대상은 producer의 Baton endpoint와 실제 실행을 하는 validator의 Baton endpoint다. Same-node 역할이 겹치면 한 번 처리하도록 연결할 수 있으나, committee 전체가 producer라는 가정은 하지 않는다. Direction 전파로 이미 만든 body나 signed producer ancestry를 임의로 바꾸지 않는다.

Direction 수신 vote·ACK·Ready quorum은 없다. Leader-local 수집·선택·전파 cycle이 닫히면 새 작업/context에서 다음 cycle을 시작한다. 이전 direction을 모든 node가 끝냈는지 확인하는 barrier를 두지 않는다.

## Non-leader: 실행·재실행 요청

현재 leader와 context에 맞는 direction만 수용한다. Required bodies와 input state를 확인한 뒤 Baton가 `Executor::reschedule`을 만든다. 이전 order와 새 order의 exact prefix를 비교하되, 실제 완료 checkpoint·input state·runtime이 같은 부분만 재사용한다.

이전 generation의 실행 job을 취소하거나 결과를 무효화하고, 유효한 checkpoint에서 새 suffix를 실행한다. Late completion을 최신 branch 또는 canonical state로 잘못 채택하지 않는다. Missing body나 base state로 local speculation이 pending이어도 native cut의 direction 회신 대기는 추가하지 않는다.

## 미결정 사항

| 항목 | 결정 |
|---|---|
| Window 안내 / report / direction message codec | |
| Report / direction logical channels와 quotas | |
| Intended order 생성 규칙 | |
| Candidate set / horizon / finite work budget | |
| 같은 window의 conflicting reports 처리 | |
| 같은 supported prefix의 tail 선택 / hysteresis | |
| Deadline와 cycle 재개 조건의 구체 설정 | |
| Wire direction version / freshness / update ordering | |
| Producer / validator 전파 대상 선정 | |
| Native proposal adoption과 policy binding 구현 | |
| Execution 결과 서명 범위 / common boundary | |
