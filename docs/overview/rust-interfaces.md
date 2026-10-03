# Rust 인터페이스

핵심 모듈 6개와 보조 역할 3개의 **Rust trait 선언을 여기서 함께 검토한다.** 각 레이어의 동작·입출력 설명은 아래 상세 계약 링크에서 읽는다.

이 선언은 새 application 연결부의 설계 초안이다. 기존 Commonware API와 구현된 crate로 취급하지 않는다. Associated type의 concrete fields·codec·채널·오류·작업 배치는 미결정이며 이 페이지가 새 wire schema나 정책을 채택하지 않는다.

**원본은 이 페이지의 Rust 코드다.** [단일 Rust 파일](../assets/interfaces/baton.rs)은 이 선언에서 생성한다. 선언의 문법 확인은 service 구현·프로토콜 검증과 구분한다. `Future`를 쓰는 선언에는 `use std::future::Future;`가 필요하다.

## 모듈과 호출 흐름

| 모듈 / 보조 역할 | 주요 메서드 | 상세 계약 |
|---|---|---|
| [TxPool](#txpool) | `admit`, `select`, `on_proposal`, `on_commit` | [입력·출력과 완료 조건](../tx/interfaces.md) |
| [TxPolicy](#txpolicy) | `analyze`, `classify` | [입력·출력과 완료 조건](../tx/interfaces.md) |
| [BlockService](#blockservice) | `build`, `verify`, `fetch`, `commitment`, `publish`, `on_retire` | [입력·출력과 완료 조건](../consensus/block-body.md) |
| [Orderer](#orderer) | `record`, `next_range`, `acknowledge`, `recover` | [입력·출력과 완료 조건](../consensus/ordered-input.md) |
| [Baton](#baton) | `on_block`, `on_context`, `on_report`, `on_direction`, `on_execution`, `on_planned`, `on_commit`, `prepared_policy` | [입력·출력과 완료 조건](../baton/interfaces.md) |
| [Planner](#planner) | `plan` | [입력·출력과 완료 조건](../baton/direction.md) |
| [Executor](#executor) | `execute`, `reschedule`, `commit`, `recover`, `read` | [입력·출력과 완료 조건](../execution/interfaces.md) |
| [Runtime](#runtime) | `execute` | [입력·출력과 완료 조건](../execution/interfaces.md) |
| [ResultService](#resultservice) | `sign`, `collect`, `verify`, `certificate` | [입력·출력과 완료 조건](../execution/interfaces.md) |

**연결 순서:** Client → `TxPool::admit` → `BlockService::build` → native consensus → `Orderer::next_range` → `Executor::commit` → `Orderer::acknowledge` / `TxPool::on_commit`. Baton은 미확정 입력의 `Executor::execute` / `reschedule`을 요청한다. ResultService와 state sync는 Executor 내부·Executor ↔ Executor 경로에 있다.

기존 Commonware의 `Automaton`, `Relay`, `Reporter`를 재사용하므로 별도 Consensus trait를 추가하지 않는다. 실제 upstream API와 application bridge의 연결 지점은 [블록 생성과 body 계약](../consensus/block-body.md)에서 확인한다. 타입 간 동일성과 호출 의미는 [인터페이스 읽는 방법](interfaces.md)에 설명한다.

## TxPool

Tx 접수·후보 선택·proposal 결과와 durable tx 결과를 반영한다. [상세 계약](../tx/interfaces.md).

```rust
use std::future::Future;

pub trait TxPool: Send {
    type Tx: Send;
    type Source: Send;
    type Admission: Send;
    type Selection: Send;
    type Batch: Send;
    type ProposalOutcome: Send;
    type CommitResult: Send;
    type Error: Send;

    fn admit(
        &mut self,
        tx: Self::Tx,
        source: Self::Source,
    ) -> impl Future<Output = Result<Self::Admission, Self::Error>> + Send;
    fn select(
        &mut self,
        request: Self::Selection,
    ) -> impl Future<Output = Result<Self::Batch, Self::Error>> + Send;
    fn on_proposal(
        &mut self,
        outcome: Self::ProposalOutcome,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn on_commit(
        &mut self,
        result: Self::CommitResult,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
}
```

## TxPolicy

Tx payload만 정적으로 분석하고 routing / filtering 판단을 만든다. 적용 위치·정책은 미결정이다. [상세 계약](../tx/interfaces.md).

```rust
pub trait TxPolicy: Send {
    type Tx;
    type Features;
    type Decision;
    type Error;

    fn analyze(&self, tx: &Self::Tx) -> Result<Self::Features, Self::Error>;
    fn classify(&self, features: &Self::Features) -> Result<Self::Decision, Self::Error>;
}
```

## BlockService

Native Automaton / Relay callback에 body 생성·검증·조회·custody를 연결한다. [상세 계약](../consensus/block-body.md).

```rust
use std::future::Future;

pub trait BlockService: Send {
    type ProducerContext: Send;
    type Digest: Send;
    type BlockRef: Send;
    type StoredBody: Send;
    type Retire: Send;
    type Error: Send;

    fn build(
        &mut self,
        context: Self::ProducerContext,
    ) -> impl Future<Output = Result<Option<Self::StoredBody>, Self::Error>> + Send;
    fn verify(
        &mut self,
        context: Self::ProducerContext,
        digest: Self::Digest,
    ) -> impl Future<Output = Result<bool, Self::Error>> + Send;
    fn fetch(
        &mut self,
        block: Self::BlockRef,
    ) -> impl Future<Output = Result<Self::StoredBody, Self::Error>> + Send;
    fn commitment(&self, body: &Self::StoredBody) -> Self::Digest;
    fn publish(&mut self, digest: Self::Digest) -> Result<(), Self::Error>;
    fn on_retire(&mut self, retired: Self::Retire) -> Result<(), Self::Error>;
}
```

## Orderer

인증된 native 증거와 이력을 연속 확정 입력으로 해석하고 Executor의 durable 전달 확인을 기록한다. [상세 계약](../consensus/ordered-input.md).

```rust
use std::future::Future;

pub trait Orderer: Send {
    type Evidence: Send;
    type OrderedRange: Send;
    type CommitResult: Send;
    type Recovery: Send;
    type Error: Send;

    fn record(
        &mut self,
        evidence: Self::Evidence,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn next_range(
        &mut self,
    ) -> impl Future<Output = Result<Self::OrderedRange, Self::Error>> + Send;
    fn acknowledge(
        &mut self,
        result: Self::CommitResult,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
}
```

## Baton

Report·direction과 사전 실행·재실행을 조율한다. State finalization / state sync의 승인·중계 역할이 아니다. [상세 계약](../baton/interfaces.md).

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

## Planner

고정된 report snapshot과 planning context에서 완료된 유효 candidate를 계산한다. Native cut은 이 계산을 기다리지 않는다. [상세 계약](../baton/direction.md).

```rust
use std::future::Future;

pub trait Planner: Send {
    type Context: Send;
    type ReportSnapshot: Send;
    type Candidates: Send;
    type PreparedPolicy: Send;
    type Error: Send;

    fn plan(
        &mut self,
        context: Self::Context,
        reports: Self::ReportSnapshot,
        candidates: Self::Candidates,
    ) -> impl Future<Output = Result<Option<Self::PreparedPolicy>, Self::Error>> + Send;
}
```

## Executor

실행 branch·canonical 적용·durability·복구·조회와 Executor 간 결과 인증·state sync를 소유한다. [상세 계약](../execution/interfaces.md).

```rust
use std::future::Future;

pub trait Executor: Send {
    type ExecuteRequest: Send;
    type RescheduleRequest: Send;
    type OrderedRange: Send;
    type Recovery: Send;
    type Query: Send;
    type Checkpoint: Send;
    type ExecutionResult: Send;
    type CommitResult: Send;
    type ReadResult: Send;
    type Error: Send;

    fn execute(
        &mut self,
        request: Self::ExecuteRequest,
    ) -> impl Future<Output = Result<Self::ExecutionResult, Self::Error>> + Send;
    fn reschedule(
        &mut self,
        request: Self::RescheduleRequest,
    ) -> impl Future<Output = Result<Self::ExecutionResult, Self::Error>> + Send;
    fn commit(
        &mut self,
        range: Self::OrderedRange,
    ) -> impl Future<Output = Result<Self::CommitResult, Self::Error>> + Send;
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<Self::Checkpoint, Self::Error>> + Send;
    fn read(
        &mut self,
        query: Self::Query,
    ) -> impl Future<Output = Result<Self::ReadResult, Self::Error>> + Send;
}
```

## Runtime

Executor가 제공한 branch-scoped state에서 application 입력을 계산한다. Canonical 적용 권한은 Executor에 있다. [상세 계약](../execution/interfaces.md).

```rust
use std::future::Future;

pub trait Runtime: Send {
    type State: Send;
    type Input: Send;
    type Output: Send;
    type Error: Send;

    fn execute(
        &mut self,
        state: &mut Self::State,
        input: Self::Input,
    ) -> impl Future<Output = Result<Self::Output, Self::Error>> + Send;
}
```

## ResultService

Executor 내부에서 직접 실행 결과를 서명하고 f+1 동일 결과 인증서를 수집·검증·조회한다. [상세 계약](../execution/interfaces.md).

```rust
use std::future::Future;

pub trait ResultService: Send {
    type ExecutionResult: Send;
    type SignedStatement: Send;
    type ExecutionStatement: Send;
    type ResultCertificate: Send;
    type Query: Send;
    type Error: Send;

    fn sign(
        &mut self,
        result: Self::ExecutionResult,
    ) -> impl Future<Output = Result<Self::SignedStatement, Self::Error>> + Send;
    fn collect(
        &mut self,
        signed: Self::SignedStatement,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
    fn verify(
        &mut self,
        certificate: Self::ResultCertificate,
    ) -> impl Future<Output = Result<Self::ExecutionStatement, Self::Error>> + Send;
    fn certificate(
        &mut self,
        query: Self::Query,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
}
```

## State finalization / state sync의 인터페이스 경계

`ResultService`는 Executor 내부 역할이다. Executor가 peer 실행 서명·인증서·change set을 교환하고 인증 결과를 검증한 뒤 자신의 canonical writer·fencing·durability 계약으로 적용한다. Imported 결과를 자신의 DirectExecuted 서명으로 바꾸지 않는다.

현재 `Executor::commit`은 durable canonical 적용의 경계를 나타낸다. Peer message codec·state material 요청·검증·전환을 위한 구체 method / struct는 아직 정하지 않았다. 이 선언만으로 state sync API가 완성되었다고 주장하지 않는다. 요구사항과 미결정 연결은 [State sync](../execution/state-sync.md)와 [Execution 책임](../execution/README.md)에서 검토한다.
