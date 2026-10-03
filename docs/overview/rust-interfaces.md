# Rust interfaces

**Each trait defines a module's inputs, outputs, and responsibility.** Start with its plain-language role, then read the method arguments and return types in the code. The six core modules and three supporting roles are collected here; layer pages explain their detailed completion conditions.

These declarations propose new application integration. They are not implemented crates or existing Commonware APIs. Concrete associated-type fields, codecs, channels, errors, and worker placement remain undecided. The declarations adopt no new wire schema or policy.

**The Rust blocks on this page are the source of truth.** The [single Rust file](../assets/interfaces/baton.rs) is generated from them. Syntax checking is separate from service implementation or protocol verification. Future-returning declarations need `use std::future::Future;`.

## Modules and call flow

| Module / supporting role | Methods | Detailed contract |
|---|---|---|
| [TxPool](#txpool) | `admit`, `select`, `on_proposal`, `on_commit` | [Inputs, outputs, completion](../tx/interfaces.md) |
| [TxPolicy](#txpolicy) | `analyze`, `classify` | [Inputs, outputs, completion](../tx/interfaces.md) |
| [BlockService](#blockservice) | `build`, `verify`, `fetch`, `commitment`, `publish`, `on_retire` | [Inputs, outputs, completion](../consensus/block-body.md) |
| [Orderer](#orderer) | `record`, `next_range`, `acknowledge`, `recover` | [Inputs, outputs, completion](../consensus/ordered-input.md) |
| [Baton](#baton) | `on_block`, `on_context`, `on_report`, `on_direction`, `on_execution`, `on_planned`, `on_commit`, `prepared_policy` | [Inputs, outputs, completion](../baton/interfaces.md) |
| [Planner](#planner) | `plan` | [Inputs, outputs, completion](../baton/direction.md) |
| [Executor](#executor) | `execute`, `reschedule`, `commit`, `recover`, `read` | [Inputs, outputs, completion](../execution/interfaces.md) |
| [Runtime](#runtime) | `execute` | [Inputs, outputs, completion](../execution/interfaces.md) |
| [ResultService](#resultservice) | `sign`, `collect`, `verify`, `certificate` | [Inputs, outputs, completion](../execution/interfaces.md) |

**Canonical call order:** Client → `TxPool::admit` → `BlockService::build` → native consensus → `Orderer::next_range` → `Executor::commit` → `Orderer::acknowledge` / `TxPool::on_commit`. Baton requests `Executor::execute` / `reschedule` for undecided inputs. ResultService and state sync belong inside Executor and on the Executor ↔ Executor path.

Reuse Commonware Automaton, Relay, and Reporter rather than adding a separate Consensus trait. [Block construction and body contracts](../consensus/block-body.md) identify upstream attachment points. [Reading the interfaces](interfaces.md) explains type equality and call semantics.

## TxPool

**TxPool manages transaction candidates.** `admit` receives Tx and Source and returns Admission. `select` receives Selection and returns a candidate Batch. `on_proposal` tracks local proposal outcomes; `on_commit` updates lifecycle from a durable CommitResult. [Detailed contract](../tx/interfaces.md).

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

**TxPolicy classifies transactions from their payloads.** `analyze` takes a borrowed Tx and returns Features; `classify` takes borrowed Features and returns Decision. Placement and routing/filtering rules remain undecided. [Detailed contract](../tx/interfaces.md).

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

**BlockService makes producer bodies available and recoverable.** `build` takes ProducerContext and returns an optional StoredBody; `verify` takes ProducerContext and Digest and returns a validity verdict; true requires durable custody; `fetch` takes BlockRef and returns StoredBody. `commitment` extracts Digest, while publish and retire handle local scheduling and retention. [Detailed contract](../consensus/block-body.md).

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

**Orderer delivers the exact finalized execution sequence.** `record` receives Evidence; `next_range` returns OrderedRange. `acknowledge` receives Executor's durable CommitResult, and `recover` restores the delivery/history state described by Recovery. [Detailed contract](../consensus/ordered-input.md).

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

**Baton schedules speculative work.** Its handlers receive CandidateBlock, Context, Report, Direction, and local completion results. They return local admission/scheduling success or Error. `prepared_policy` immediately returns an optional completed PreparedPolicy. These returns are not state-finalization approval or remote direction ACKs. [Detailed contract](../baton/interfaces.md).

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

**Planner selects a valid direction candidate.** `plan` receives Context, frozen ReportSnapshot, and bounded Candidates. It returns an optional PreparedPolicy after completed evaluation. Native cut does not await it. [Detailed contract](../baton/direction.md).

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

**Executor manages execution and durable state.** `execute` / `reschedule` take their request types and return completed ExecutionResult. `commit` takes OrderedRange and returns durable CommitResult. `recover` returns a restored Checkpoint, and `read` returns ReadResult for Query. Executor also owns peer certification and state sync. [Detailed contract](../execution/interfaces.md).

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

**Runtime computes transaction effects on a supplied branch.** `execute` receives mutable State and Input and returns Output. Executor supplies the valid branch and retains canonical application authority. [Detailed contract](../execution/interfaces.md).

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

**ResultService certifies execution results inside Executor.** `sign` takes completed ExecutionResult and returns SignedStatement. `collect` takes a signed statement and returns an optional ResultCertificate; `verify` returns the verified ExecutionStatement. `certificate` queries an optional existing certificate. Each future carries Error separately. [Detailed contract](../execution/interfaces.md).

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

## Interface boundary for state finalization and state sync

ResultService is internal to Executor. Executor exchanges peer signatures, certificates, and change sets, verifies results, and applies usable material through its canonical writer, fencing, and durability contract. Imported results cannot become own DirectExecuted signatures.

`Executor::commit` currently identifies the durable canonical application boundary. Concrete methods and structs for peer codec, material requests, verification, and switching remain undecided. These declarations do not claim a complete state-sync API. See [State sync](../execution/state-sync.md) and [Execution responsibilities](../execution/README.md).
