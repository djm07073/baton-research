# 인터페이스 읽는 방법

Rust trait는 앞으로 연결할 application API의 초안이다. 실제 Commonware API와 구현할 계약을 구분해서 읽는다.

## Rust trait를 읽는 방법

아래 trait는 **새 application 연결부의 Rust 설계 초안**이다. Native Commonware trait를 복제한 API나 구현된 crate가 아니다. `type`으로 남긴 입력·결과·오류의 concrete fields, codec, IDs, limits와 runtime 배치는 각 장의 빈 결정 칸에서 정한다. 타입 이름을 붙인 것은 wire schema나 정책을 채택한 것이 아니다.

| 호출 흐름 | Trait method |
|---|---|
| Client / tx peer → pool | `TxPool::admit` |
| Producer 요청 → tx 선택 → 본문 준비 | `BlockService::build` → `TxPool::select` |
| Peer body → custody / lookup | `BlockService::verify` / `fetch` |
| 인증된 후보 → 사전 실행 | `Baton::on_block` → `Executor::execute` → `Runtime::execute` |
| Reports → direction → 실행 계획 변경 | `Baton::on_report` → `Planner::plan` → `Baton::on_direction` → `Executor::reschedule` |
| Native 증거 → 확정 순서 → local state 적용 | `Orderer::record` / `next_range` → `Executor::commit`; Baton 경유 없음 |
| Durable 완료 → 전달 확인·pool 갱신 | Executor → `Orderer::acknowledge` + `TxPool::on_commit`; Baton 알림은 선택적 |
| Executor 내부 직접 실행 결과 → 서명·인증 조회 | 내부 `ResultService::sign` / `collect` / `certificate`; peer 전송은 Executor ↔ Executor |

조립할 때 아래 associated types는 같은 concrete 타입으로 연결한다. Trait 이름이 같다고 Rust가 자동으로 연결해 주는 것은 아니며, 각 receiver의 context·identity·evidence 검증도 계속 필요하다.

| 연결할 타입 | 흐름 |
|---|---|
| `Baton::Context = Planner::Context` | 동일 planning context; native producer Context와는 구분 |
| `Planner::PreparedPolicy = Baton::PreparedPolicy` | 완료된 선택 결과 → native actual-context 재검증 hook |
| `Orderer::OrderedRange = Executor::OrderedRange` | 확정 순서 → 직접 commit 요청 |
| `Executor::ExecutionResult = Baton::ExecutionResult = ResultService::ExecutionResult` | 완료한 실행 → generation/context 확인 또는 canonical 결과 서명 검증 |
| `Executor::CommitResult = Baton::CommitResult = Orderer::CommitResult = TxPool::CommitResult` | Executor의 durable 완료 → delivery 확인·tx lifecycle 반영; Baton::CommitResult는 선택적 알림 |

메서드의 `&mut self`는 호출 handle의 Rust ownership 표기이며, 모든 branch 계산을 한 작업자로 실행하거나 DB의 single writer가 자동 보장된다는 뜻이 아니다. 공유 handle / worker concurrency·canonical writer / fencing은 implementation에서 연결한다. `impl Future + Send`는 Commonware callback과 비슷한 선언 방식이며 async runtime·dyn dispatch·boxing 정책은 선택하지 않았다.

`Baton::on_*`과 `BlockService::publish`는 local admission / 작업 예약 경계다. Native `Reporter`·`Relay`의 synchronous callback에서 느린 I/O를 기다리는 호출로 쓰지 않는다. Future를 반환하는 메서드의 기다림은 application 작업에 한정되며, native cut이 report·planner·direction 회신을 기다리는 조건을 추가하지 않는다. `Executor::commit`은 canonical mutation lifecycle을 소유하므로 advisory job 취소와 같이 취소하지 않는다.

## 2. E2E lifecycle과 sequence diagram

| 확인할 케이스 | Sequence |
|---|---|
| Client admission부터 durable canonical 적용까지 | [전체 E2E](../e2e/normal.md#전체-e2e-tx-입력부터-canonical-state까지) |
| 신규·중복·구조적 invalid tx | [Tx lifecycle](../e2e/normal.md#tx-lifecycle-신규중복잘못된-tx) |
| Producer DA부터 leader proposal·vote·local finality까지 | [Native 합의 정상 경로](../e2e/native-consensus.md#native-합의-정상-경로-producer-da--leader-proposal--finality) |
| Body build / peer custody / 누락·invalid body | [Propose](../e2e/block-body.md#block-lifecycle-mempool--propose--body-전파), [Verify](../e2e/block-body.md#block-body-송수신-조회검증누락-처리) |
| Leader 선택·전파와 non-leader 재예약 | [Leader](../e2e/leader.md#baton-lifecycle-leader-report-수집과-direction-전파), [Non-leader](../e2e/reschedule.md#baton-lifecycle-non-leader의-direction재실행-요청) |
| Cut 해석·gap / matching branch / flush 실패 | [Ordered range](../e2e/canonical.md#cut-commit--ordered-range--실행-commit), [QMDB commit](../e2e/canonical.md#execution-lifecycle-qmdb-분기-생성과-canonical-승격) |
| 이미 적용한 range 재전달과 native startup | [Restart delivery](../e2e/recovery.md#재시작과-backfill), [Startup custody](../e2e/recovery.md#startup-custody를-준비한-뒤-native-recovery) |
| Validator의 인증 결과 수신·남은 실행 중단·상태 적용 | [State sync](../e2e/state-sync.md#state-sync-인증된-실행-결과로-상태-동기) |
| f+1 결과 인증과 late planner completion | [Result endpoint](../e2e/results.md#결과-endpoint-direct-execution과-f1-인증), [Proposal freeze](../e2e/leader.md#planner-completion과-proposal-freeze의-경합) |
