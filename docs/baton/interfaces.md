# Baton 인터페이스와 로컬 진행 알림

Baton은 Executor에 execute / reschedule을 요청한다. 확정 적용 진행은 선택적 로컬 알림이며 Baton의 응답이 실행 레이어를 막지 않는다.

## 인터페이스 개요

```rust
pub trait Baton: Send {
    type CandidateBlock;
    type Context;
    type Report;
    type Direction;
    type ExecutionResult;
    type CommitResult;
    type PreparedPolicy;
    type Error;

    fn on_block(&mut self, block: Self::CandidateBlock) -> Result<(), Self::Error>;
    fn on_context(&mut self, context: Self::Context) -> Result<(), Self::Error>;
    fn on_report(&mut self, report: Self::Report) -> Result<(), Self::Error>;
    fn on_direction(&mut self, direction: Self::Direction) -> Result<(), Self::Error>;
    fn on_execution(&mut self, result: Self::ExecutionResult) -> Result<(), Self::Error>;
    fn on_planned(
        &mut self,
        context: Self::Context,
        policy: Option<Self::PreparedPolicy>,
    ) -> Result<(), Self::Error>;
    fn on_commit(&mut self, result: Self::CommitResult) -> Result<(), Self::Error>;
    fn prepared_policy(&self) -> Option<Self::PreparedPolicy>;
}
```

`Context`는 leader view·history·actual parent·rule·window·불변 순서 경계를 결속한 planning context다. `BlockService::ProducerContext`와 같은 타입으로 가정하지 않는다. `on_block`은 body와 authenticated header가 join된 CandidateBlock 수신 경계이며, 단순 StoredBody 알림을 이 입력으로 바꾸지 않는다. Join과 실제 handler 호출은 Baton의 수신 부분 / Commonware 연결부에서 처리한다.

`on_*`은 context 확인·local admission·작업 예약을 처리한다. Executor 작업과 Planner 계산은 runtime driver가 진행하고 완료 결과를 handler로 돌려준다. Driver/queue/task 배치는 미결정이며 새 actor 개수는 정하지 않는다. Planner 완료는 `on_planned(context, policy)`로 돌려주고 원래 요청의 window/context를 확인한 뒤 준비 상태를 갱신한다. Late/stale 완료가 새 context의 결과를 덮어쓰지 않는다. `on_execution`에는 완료한 유효 checkpoint만 전달하고, 미완료 / 실패 job의 notification·retry 계약은 §6.6에 남긴다. `prepared_policy()`는 완료된 유효 후보가 현재 준비된 경우만 반환하는 즉시 조회다. Native owner가 다시 actual context를 검사하고 freeze하며, cut은 `Some`을 기다리지 않는다.

| 제안 인터페이스 | 어디서 받는가 | 처리와 다음 출력 |
|---|---|---|
| `Baton::on_block` | Consensus body attachment | Reference/context 검증 → local intended order → Executor::execute |
| `Baton::on_context` | Native owner hook | Exact context / immutable frontier 관리 → window / planner 입력 |
| `Baton::on_report` | Report connection | 서명·context·identity·limits 검증 → leader snapshot admission |
| `Baton::on_direction` | 현재 leader | Auth/context 확인 → Executor::reschedule |
| `Baton::on_planned` / `prepared_policy` | Planner 완료 → Baton → native owner | 원래 요청 context 확인·준비 상태 보관 → 즉시 조회 → actual proposal context 재검증 |
| `Baton::on_execution` | Executor | ExecutionResult의 generation·context 확인 → branch handle와 local 준비 상태 관리 |
| `Baton::on_commit` | Executor의 선택적 로컬 적용 알림 | Applied progress를 scheduling에 반영; delivery ACK / pool cleanup / 결과 인증을 승인하지 않음 |

`on_commit` 알림을 보내거나 처리하는 것이 Executor의 적용·인증·state sync·delivery ACK 완료 조건은 아니다. Executor는 Baton의 응답 없이 이 경로를 진행한다. `Baton::on_*`은 local handler이며 별도 wire message가 아니다. 성공 반환은 local 처리·작업 예약의 결과이고 direction 승인이나 remote ACK가 아니다. ExecutionResult는 완료된 speculative 실행 결과이며, codec·필드 선택은 미결정이다.

## 확정 상태 진행 알림

확정 입력은 Orderer가 Executor에 직접 전달한다. Executor는 직접 실행 결과 또는 검증된 peer state material을 적용하고, durable CommitResult 이후 Orderer에 delivery ACK와 TxPool에 canonical tx 결과를 전달한다. Baton이 commit을 승인하거나 이 전달을 중계하지 않는다.

Baton은 필요한 경우 Executor의 로컬 적용 진행 알림을 받아 이미 확정된 입력을 다시 예약하지 않도록 scheduling에 반영한다. 알림 전송·처리·회신은 Executor의 state finalization·state sync·canonical 적용 완료 조건이 아니다. f+1 결과 인증과 change set 교환은 Executor끼리 진행한다.
