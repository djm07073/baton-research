# Rust interfaces

**Each trait defines a module's inputs, outputs, and responsibility.** Start with its plain-language role, then read the method arguments and return types in the code. The six core modules and two supporting roles are collected here; layer pages explain their detailed completion conditions.

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
| [Executor](#executor) | `plan`, `execute`, `commit`, `recover`, `read` | [Inputs, outputs, completion](../execution/interfaces.md) |
| [Runtime](#runtime) | `execute` | [Inputs, outputs, completion](../execution/interfaces.md) |
| [ResultService](#resultservice) | `sign`, `collect`, `verify`, `certificate` | [Inputs, outputs, completion](../execution/interfaces.md) |

**Canonical call order:** Client → `TxPool::admit` → `BlockService::build` → native consensus → `Orderer::next_range` → `Executor::commit` → `Orderer::acknowledge` / `TxPool::on_commit`. Baton requests `Executor::plan` for direction selection and `Executor::execute(block)` for undecided inputs. Executor owns their execution tree; there is no separate Planner trait or reschedule method. ResultService and state sync belong inside Executor and on the Executor ↔ Executor path.

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

    /// Check and retain a transaction from its source; return its admission outcome.
    /// Admission does not establish block inclusion or canonical execution.
    fn admit(
        &mut self,
        tx: Self::Tx,
        source: Self::Source,
    ) -> impl Future<Output = Result<Self::Admission, Self::Error>> + Send;
    /// Select a bounded candidate batch under the supplied selection policy.
    /// Selection alone does not retire transactions from the pool.
    fn select(
        &mut self,
        request: Self::Selection,
    ) -> impl Future<Output = Result<Self::Batch, Self::Error>> + Send;
    /// Record a local proposal outcome for candidate lifecycle tracking.
    /// A proposal outcome is not a canonical commit.
    fn on_proposal(
        &mut self,
        outcome: Self::ProposalOutcome,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    /// Update transaction lifecycle from a recoverably durable canonical result.
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

    /// Extract static features from the transaction payload without executing state changes.
    fn analyze(&self, tx: &Self::Tx) -> Result<Self::Features, Self::Error>;
    /// Evaluate selection or routing policy against the extracted static features.
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

    /// Build a producer body for the exact request context and retain durable custody.
    /// Return None when no admissible body is prepared for that request.
    fn build(
        &mut self,
        context: Self::ProducerContext,
    ) -> impl Future<Output = Result<Option<Self::StoredBody>, Self::Error>> + Send;
    /// Verify the referenced body and required parent material for this producer context.
    /// Return true only when validation and durable custody requirements are satisfied.
    fn verify(
        &mut self,
        context: Self::ProducerContext,
        digest: Self::Digest,
    ) -> impl Future<Output = Result<bool, Self::Error>> + Send;
    /// Resolve a block reference to its retained body or fetch and verify missing material.
    fn fetch(
        &mut self,
        block: Self::BlockRef,
    ) -> impl Future<Output = Result<Self::StoredBody, Self::Error>> + Send;
    /// Return the body digest; this does not authenticate its native header.
    fn commitment(&self, body: &Self::StoredBody) -> Self::Digest;
    /// Schedule local body dissemination through the Commonware relay attachment.
    fn publish(&mut self, digest: Self::Digest) -> Result<(), Self::Error>;
    /// Update retention after native retirement while preserving required custody and recovery data.
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

    /// Verify and retain native evidence and its authenticated history interpretation.
    fn record(
        &mut self,
        evidence: Self::Evidence,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    /// Return the next continuous, irrevocable range of exact execution inputs.
    /// Do not skip an unresolved slot or treat a missing body as an empty slot.
    fn next_range(
        &mut self,
    ) -> impl Future<Output = Result<Self::OrderedRange, Self::Error>> + Send;
    /// Advance delivery bookkeeping from Executor's durable CommitResult.
    fn acknowledge(
        &mut self,
        result: Self::CommitResult,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    /// Restore verified history and delivery cursors without reversing emitted decisions.
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

    /// Admit an authenticated header/body pair and request parent-linked speculative execution.
    fn on_block(&mut self, block: Self::CandidateBlock) -> Result<(), Self::Error>;
    /// Admit the current leader context and manage its report window and immutable frontier.
    fn on_context(&mut self, context: Self::Context) -> Result<(), Self::Error>;
    /// Authenticate a same-context report and count each eligible identity once.
    fn on_report(&mut self, report: Self::Report) -> Result<(), Self::Error>;
    /// Authenticate leader direction and submit its parent-linked blocks through Executor::execute.
    /// This local handler adds no direction vote, receipt ACK, or Ready quorum.
    fn on_direction(&mut self, direction: Self::Direction) -> Result<(), Self::Error>;
    /// Accept a completed execution result only for a matching context.
    /// Executor retains ownership of branch links, checkpoints, and worker lifetimes.
    fn on_execution(&mut self, result: Self::ExecutionResult) -> Result<(), Self::Error>;
    /// Cache a completed Executor planning result only for its original context and window.
    /// Late or incomplete evaluation cannot overwrite current prepared policy.
    fn on_planned(
        &mut self,
        context: Self::Context,
        policy: Option<Self::PreparedPolicy>,
    ) -> Result<(), Self::Error>;
    /// Optionally observe durable applied progress to avoid scheduling canonical inputs.
    /// Executor application, result certification, and delivery ACK do not await this handler.
    fn on_commit(&mut self, result: Self::CommitResult) -> Result<(), Self::Error>;
    /// Immediately return the currently prepared valid policy, if any.
    /// The native owner still rechecks actual proposal context; cut never waits for Some.
    fn prepared_policy(&self) -> Option<Self::PreparedPolicy>;
}
```

<a id="planner"></a>

## Planning inside Executor

**Executor owns planning and execution-tree handling together.** `plan` receives Context, a frozen ReportSnapshot, and bounded Candidates; it returns an optional PreparedPolicy after completed valid evaluation. Baton collects and authenticates reports, disseminates direction, and keeps the immediate prepared-policy cache. Native cut never awaits planning. [Selection rule](../baton/direction.md).

The former Planner responsibility is merged into Executor. Direction changes produce new parent-linked blocks through the same `execute(block)` entry point. Branch matching, reuse, task priority, stale-result rejection, and cleanup are internal Executor responsibilities; no public reschedule method is needed.

## Executor

**Executor builds the execution tree and advances its canonical path.** `execute(block)` resolves the parent block hash to a valid checkpoint, links the child, and executes it through Runtime. `commit(range)` promotes the exact finalized path, applies it durably, and prunes conflicting branches. Valid descendants of the new canonical tip remain pending. `plan` performs bounded direction selection; `recover` restores the tree's durable base; `read` queries retained canonical state. Executor also owns peer certification and state sync. [Detailed contract](../execution/interfaces.md).

```rust
use std::future::Future;

pub trait Executor: Send {
    type Context: Send;
    type ReportSnapshot: Send;
    type Candidates: Send;
    type PreparedPolicy: Send;
    type Block: Send;
    type OrderedRange: Send;
    type Recovery: Send;
    type Query: Send;
    type Checkpoint: Send;
    type ExecutionResult: Send;
    type CommitResult: Send;
    type ReadResult: Send;
    type Error: Send;

    /// Evaluate a frozen report snapshot over the bounded admissible candidate set.
    /// Return Some only after valid completed selection; native cut never awaits this work.
    /// Planning reads a tree/context snapshot and cannot hold up canonical commit.
    fn plan(
        &mut self,
        context: Self::Context,
        reports: Self::ReportSnapshot,
        candidates: Self::Candidates,
    ) -> impl Future<Output = Result<Option<Self::PreparedPolicy>, Self::Error>> + Send;
    /// Resolve block.parent_block_hash to the exact valid execution-parent checkpoint.
    /// Validate context, link the child in the execution tree, and execute through Runtime.
    /// Reuse only matching completed work; success returns its completed ExecutionResult.
    /// A missing or unfinished parent cannot be executed from an unrelated state.
    fn execute(
        &mut self,
        block: Self::Block,
    ) -> impl Future<Output = Result<Self::ExecutionResult, Self::Error>> + Send;
    /// Verify the exact irrevocable range and canonical predecessor; complete missing work.
    /// Promote the matching execution path and durably apply state, outputs, and cursor.
    /// Fence conflicting workers, prune conflicting branches, and retain valid descendants.
    /// Return CommitResult only after durable completion; physical GC follows safe retention.
    fn commit(
        &mut self,
        range: Self::OrderedRange,
    ) -> impl Future<Output = Result<Self::CommitResult, Self::Error>> + Send;
    /// Recover canonical state, outputs, cursor, and checkpoint identity together.
    /// Rebuild only branches with verified ancestry; reject stale recovered worker results.
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<Self::Checkpoint, Self::Error>> + Send;
    /// Read a retained canonical version with its readiness and output metadata.
    /// A readable local value alone does not establish an f+1 result certificate.
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

    /// Compute transaction effects on the valid branch state supplied by Executor.
    /// Return completed outputs; Runtime cannot promote branches or decide canonical order.
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

    /// Sign a directly executed or directly validated result for irrevocable exact input.
    /// Bind the canonical input state, runtime, and full result; never sign imported work as own execution.
    fn sign(
        &mut self,
        result: Self::ExecutionResult,
    ) -> impl Future<Output = Result<Self::SignedStatement, Self::Error>> + Send;
    /// Verify and collect matching statements from distinct eligible epoch validators.
    /// Return a certificate once f+1 signatures match the full subject; fewer returns None.
    fn collect(
        &mut self,
        signed: Self::SignedStatement,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
    /// Verify certificate signatures, exact irrevocable order, and canonical input-state chain.
    /// Verification does not establish state-material availability or durable local application.
    fn verify(
        &mut self,
        certificate: Self::ResultCertificate,
    ) -> impl Future<Output = Result<Self::ExecutionStatement, Self::Error>> + Send;
    /// Return a retained certificate for the exact query, if available.
    /// Serving a certificate does not create an own direct-execution signature.
    fn certificate(
        &mut self,
        query: Self::Query,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
}
```

## Interface boundary for state finalization and state sync

ResultService is internal to Executor. Executor exchanges peer signatures, certificates, and change sets, verifies results, and applies usable material through its canonical writer, fencing, and durability contract. Imported results cannot become own DirectExecuted signatures.

`Executor::commit` currently identifies the durable canonical application boundary. Concrete methods and structs for peer codec, material requests, verification, and switching remain undecided. These declarations do not claim a complete state-sync API. See [State sync](../execution/state-sync.md) and [Execution responsibilities](../execution/README.md).
