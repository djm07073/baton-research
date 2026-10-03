# Rust interfaces

**The interfaces show what each module receives, does, and returns.** TxPool, Orderer, Baton, Executor, and Storage have proposed application traits. BlockService is the body attachment built by implementing existing Commonware callbacks; it needs no second trait that repeats them. Layer pages explain completion conditions.

The five application declarations propose integration, not implemented crates. The separately labelled Commonware signature excerpts are existing upstream APIs, not new Baton declarations. Concrete associated-type fields, codecs, channels, errors, and worker placement remain undecided. These interfaces adopt no new wire schema or policy and do not require one actor or crate per role.

When connecting upstream handles, use types from the same resolved Commonware dependency graph. Matching import names or encoded hash bytes do not make a registry-release Sender, codec trait or digest equal to its native git counterpart. [Version and constructor checklist](../reference/integration.md#reference-versions-are-not-one-compatible-dependency-graph).

**The application Rust blocks on this page are the source of truth.** The [single Rust file](../assets/interfaces/baton.rs) is generated from them. Existing-library excerpts marked `rust,ignore` stay out of that standalone export because they require the pinned Commonware dependencies. Syntax checking of the export is separate from checking upstream compatibility, implementing services, or verifying the protocol. Future-returning declarations need `use std::future::Future;`.

## Modules and call flow

| Module | Methods | Reuse and application responsibility | Detailed contract |
|---|---|---|---|
| [TxPool](#txpool) | `admit`, `analyze`, `classify`, `select`, `on_proposal`, `on_commit` | Candidate lifecycle and static policy in one module; selected pool reuse still needs integration | [Tx contracts](../tx/interfaces.md) |
| [BlockService](#blockservice) | Upstream `Automaton::propose/verify`, `Relay::broadcast`, `Reporter::report`; buffer/resolver/archive handles | Body codec, native header/body join, durable custody and retention glue; reuse dissemination, cache and retry engines | [Body contracts and primitives](../consensus/block-body.md) |
| [Orderer](#orderer) | `record`, `next_range`, `acknowledge`, `recover` | Native evidence/history reuse plus new continuous ordered-delivery integration | [Ordered input](../consensus/ordered-input.md) |
| [Baton](#baton) | `plan`, `on_block`, `on_context`, `on_report`, `on_direction`, `on_execution`, `on_planned`, `on_commit`, `prepared_policy` | Intended-order reports, bounded direction selection, dissemination, prepared-policy cache | [Direction selection](../baton/direction.md) |
| [Executor](#executor) | `execute`, `commit`, `recover`, `sign_result`, `collect_result`, `verify_result`, `result_certificate` | Execution-tree control, completed unsealed effects, certification and peer sync orchestration | [Execution and certification](../execution/interfaces.md) |
| [Storage](#storage) | `prepare`, `apply`, `recover`, `read` | QMDB batch/root preparation, canonical writer, durable state and physical retention; no transaction execution or result signing | [Storage lifecycle](../execution/qmdb.md) |

**Canonical call order:** Client → `TxPool::admit` → upstream `Automaton::propose` → native consensus → `Orderer::next_range` → `Executor::commit` → `Storage::prepare/apply` → `Orderer::acknowledge` / `TxPool::on_commit`. Baton chooses direction through `Baton::plan` and requests `Executor::execute(block)` for undecided inputs. Executor returns completed effects without requiring a root for every speculative attempt; Storage prepares the selected commitment before result signing. No separate Planner, Runtime, ResultService, or reschedule interface is required. Static analysis belongs to TxPool.

Reuse Commonware Automaton, Relay, and Reporter rather than adding a separate Consensus trait. [Block construction and body contracts](../consensus/block-body.md) identify upstream attachment points. [Reading the interfaces](interfaces.md) explains type equality and call semantics.

<a id="txpolicy"></a>

## TxPool

**TxPool manages transaction candidates and static payload policy.** `admit` receives Tx and Source and returns Admission. `select` receives Selection and returns a candidate Batch. `on_proposal` tracks local proposal outcomes; `on_commit` updates lifecycle from a durable CommitResult. [Detailed contract](../tx/interfaces.md).

```rust
use std::future::Future;

pub trait TxPool: Send {
    type Tx: Send;
    type Source: Send;
    type Features;
    type Decision;
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
    /// Extract static features from the transaction payload without executing state changes.
    fn analyze(&self, tx: &Self::Tx) -> Result<Self::Features, Self::Error>;
    /// Evaluate selection or routing policy against the extracted static features.
    fn classify(&self, features: &Self::Features) -> Result<Self::Decision, Self::Error>;

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

## BlockService

**BlockService connects Commonware's body primitives to Multimmit.** Implement the existing callbacks directly over `buffered::Mailbox`, generic resolver and archive handles. A shared attachment may hold these handles and the body/header correlation data; a separate actor is a deployment choice. [Detailed contract](../consensus/block-body.md).

The signatures below come from pinned [Automaton](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L116), [Relay](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L224), and [Reporter](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L245). These are method excerpts with application comments; enclosing trait bounds, associated-type declarations and imports are omitted. They are not standalone declarations.

```rust,ignore
// Existing commonware_consensus::Automaton methods.
/// Select transactions, build and retain a body for the supplied producer context.
/// Resolve the receiver with its digest only when custody requirements hold.
fn propose(
    &mut self,
    context: Self::Context,
) -> impl Future<Output = oneshot::Receiver<Self::Digest>> + Send;
/// Locate or fetch the exact body and required parents; verify and retain custody.
/// Missing data keeps the receiver pending; false means permanent invalidity.
fn verify(
    &mut self,
    context: Self::Context,
    payload: Self::Digest,
) -> impl Future<Output = oneshot::Receiver<bool>> + Send;

// Existing commonware_consensus::Relay method; Multimmit uses Plan = ().
/// Schedule body lookup and buffered dissemination without waiting for peer ACKs.
/// Feedback describes local admission, not remote receipt or durable peer custody.
fn broadcast(&mut self, payload: Self::Digest, plan: Self::Plan) -> Feedback;

// Existing commonware_consensus::Reporter method.
/// Hand an accepted artifact notice to the header/body join attachment.
/// This observation callback is not the durable canonical evidence export.
fn report(&mut self, activity: Self::Activity) -> Feedback;
```

Use `buffered::Mailbox::{broadcast_shared,get,subscribe}` for dissemination and local cached availability, and generic resolver `fetch` plus `Producer`/`Consumer` for active peer lookup and validation. The body type implements upstream codec and `Digestible`; archives provide writes, reads and sync. Implement body format, exact context/header correspondence, custody and retention handoffs. Do not add parallel generic cache, network retry or broadcast implementations. Native retirement is a separate lifecycle bridge; Relay has no `on_retire` method. See [the real-chain assembly recipe](../reference/integration.md#copy-the-assembly-from-real-chains).

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

<a id="planner"></a>

## Baton

**Baton chooses and shares the intended execution order.** Its handlers receive CandidateBlock, Context, Report, Direction, and local completion results. `plan` evaluates a frozen report snapshot over bounded admissible candidates and returns an optional completed PreparedPolicy. The handlers return local admission/scheduling success or Error. `prepared_policy` immediately returns an optional completed PreparedPolicy. These returns are not state-finalization approval or remote direction ACKs. [Detailed contract](../baton/interfaces.md).

```rust
use std::future::Future;

pub trait Baton: Send {
    type CandidateBlock;
    type Context: Send;
    type ReportSnapshot: Send;
    type Candidates: Send;
    type Report;
    type Direction;
    type ExecutionResult;
    type CommitResult;
    type PreparedPolicy: Send;
    type Error;

    /// Evaluate a frozen report snapshot over the bounded admissible candidate set.
    /// Return Some only after valid completed selection; native cut never awaits this work.
    /// This selects direction; Executor independently manages its parent-linked execution tree.
    fn plan(
        &mut self,
        context: Self::Context,
        reports: Self::ReportSnapshot,
        candidates: Self::Candidates,
    ) -> impl Future<Output = Result<Option<Self::PreparedPolicy>, Self::Error>> + Send;

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
    /// Cache a completed Baton planning result only for its original context and window.
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

<a id="runtime"></a>
<a id="resultservice"></a>

## Executor

**Executor computes transaction changes and controls which execution path becomes canonical.** `execute(block)` resolves the execution parent, links the child, and returns completed changes and outputs. Those changes may be an upstream unmerkleized batch or an application draft for a rootless branch; execute does not require hashing every attempt. `commit(range)` verifies the exact finalized path, delegates preparation/application to Storage, and logically prunes conflicts. Valid descendants remain pending. Baton owns direction selection; Executor owns certification and normal-path peer state-sync orchestration. [Detailed contract](../execution/interfaces.md).

```rust
use std::future::Future;

pub trait Executor: Send {
    type Block: Send;
    type OrderedRange: Send;
    type Recovery: Send;
    type Checkpoint: Send;
    type ExecutionResult: Send;
    type PreparedResult: Clone + Send;
    type CommitResult: Send;
    type SignedStatement: Send;
    type ExecutionStatement: Send;
    type ResultCertificate: Send;
    type ResultQuery: Send;
    type Error: Send;

    /// Resolve block.parent_block_hash to the exact valid execution-parent checkpoint.
    /// Validate context, link the child in the execution tree, and compute the transaction effects on that branch.
    /// Return completed changes and outputs; Storage calculates a root when needed.
    /// Reuse only matching completed work; unsealed child forks need a separate read-view adapter.
    /// A missing or unfinished parent cannot be executed from an unrelated state.
    fn execute(
        &mut self,
        block: Self::Block,
    ) -> impl Future<Output = Result<Self::ExecutionResult, Self::Error>> + Send;
    /// Verify the exact irrevocable range and canonical predecessor; complete missing work.
    /// Select the matching path; ask Storage to prepare and durably apply exact material.
    /// Fence conflicting workers, prune conflicting branches, and retain valid descendants.
    /// Return CommitResult only after durable completion; physical GC follows safe retention.
    fn commit(
        &mut self,
        range: Self::OrderedRange,
    ) -> impl Future<Output = Result<Self::CommitResult, Self::Error>> + Send;
    /// Use Storage recovery to restore the canonical base, outputs, cursor and provenance.
    /// Rebuild only execution branches with verified ancestry; reject stale worker results.
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<Self::Checkpoint, Self::Error>> + Send;
    /// Sign a Storage-prepared result with retained own direct execution/validation evidence.
    /// Require irrevocable exact input, canonical base, runtime and the computed result commitment.
    /// Sign the stable full subject; local worker generations are not shared signature fields.
    /// Never sign imported material as own execution or sign before the commitment exists.
    fn sign_result(
        &mut self,
        result: Self::PreparedResult,
    ) -> impl Future<Output = Result<Self::SignedStatement, Self::Error>> + Send;
    /// Verify and collect matching statements from distinct eligible epoch validators.
    /// Return a certificate once f+1 signatures match the full subject; fewer returns None.
    fn collect_result(
        &mut self,
        signed: Self::SignedStatement,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
    /// Verify certificate signatures, exact irrevocable order, and canonical input-state chain.
    /// Verification does not establish state-material availability or durable local application.
    fn verify_result(
        &mut self,
        certificate: Self::ResultCertificate,
    ) -> impl Future<Output = Result<Self::ExecutionStatement, Self::Error>> + Send;
    /// Return a retained certificate for the exact query, if available.
    /// Serving a certificate does not create an own direct-execution signature.
    fn result_certificate(
        &mut self,
        query: Self::ResultQuery,
    ) -> impl Future<Output = Result<Option<Self::ResultCertificate>, Self::Error>> + Send;
}
```

## Storage

**Storage turns completed changes into authenticated, recoverable state.** It owns QMDB handles, root calculation, canonical database mutation, queries, physical retention and storage recovery. It does not choose direction, execute transactions, establish native order or sign execution results. Executor supplies the verified canonical range or certified-import authorization; Storage also checks applicable base/ancestry and writer access.

This is a thin proposed boundary over existing QMDB operations, not a new database implementation or mandatory independent actor. Concrete `ExecutionResult` can carry `DatabaseSet::Unmerkleized`; `PreparedResult` can carry `DatabaseSet::Merkleized`. An optional rootless effects-chain adapter needs a different draft/read view. Keep direct QMDB calls inside the adapter rather than recreating batching, Merkle or persistence algorithms. [Native lifecycle and release differences](../execution/qmdb.md#existing-apis-at-the-native-pin-and-indexed-release).

```rust
use std::future::Future;

pub trait Storage: Send {
    type ExecutionResult: Send;
    type Preparation: Send;
    type PreparedResult: Clone + Send;
    type CanonicalInput: Send;
    type CommitResult: Send;
    type Recovery: Send;
    type Checkpoint: Send;
    type Query: Send;
    type ReadResult: Send;
    type Error: Send;

    /// Prepare the exact selected prefix from completed changes, without executing transactions.
    /// Use concrete QMDB merkleize calls and calculate the chosen result commitment.
    /// A QMDB unsealed draft is consumed; retain effects first if more rootless branches need them.
    /// Keep valid access/fencing through lazy reads, staged expansion and materialization.
    /// Bind the selected storage rule, exact base/input, outputs and material to the prepared result.
    /// Root type and deterministic batch/normalization rules remain open design choices.
    fn prepare(
        &mut self,
        result: Self::ExecutionResult,
        preparation: Self::Preparation,
    ) -> impl Future<Output = Result<Self::PreparedResult, Self::Error>> + Send;
    /// Check authorized exact canonical input, applicable ancestry and single-writer access.
    /// Use concrete validate_batch preflight under that authority; it is not application proof verification.
    /// Apply through QMDB and observe successful durability plus recoverable metadata linkage.
    /// Return CommitResult only when state, outputs, cursor and provenance recover together.
    /// Canonical mutation is not canceled with advisory workers; failed flush is not success.
    fn apply(
        &mut self,
        input: Self::CanonicalInput,
        result: Self::PreparedResult,
    ) -> impl Future<Output = Result<Self::CommitResult, Self::Error>> + Send;
    /// Recover the authoritative durable state, outputs, cursor and provenance together.
    /// Restore retained storage bases; a prior readable notification is not a durable receipt.
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<Self::Checkpoint, Self::Error>> + Send;
    /// Read a retained canonical version and its readiness/output metadata.
    /// An arbitrary historical snapshot API is not promised by QMDB readers.
    /// Result-certificate queries remain Executor responsibilities.
    fn read(
        &mut self,
        query: Self::Query,
    ) -> impl Future<Output = Result<Self::ReadResult, Self::Error>> + Send;
}
```

PreparedResult is a retained/cloneable material handle so signing and application can share the same sealed result; use upstream retained batches rather than copying a second database. Batch creation, sealed-parent forks, pruning, sync sources and barrier observation use the upstream handles described in [QMDB](../execution/qmdb.md). This facade does not hide the crucial limit: `DatabaseSet::fork_batches` accepts a merkleized parent. Continuing one unsealed batch can defer roots; rootless branching across completed blocks requires an application read/effects adapter. A local generation, writer permit or retention coordinate must not become part of the cross-validator signing subject merely because it appears in a local binding record.

The concrete Storage attachment also supplies authorized branch handles internally: upstream new_batches at an applied base, fork_batches at a sealed parent, or the application overlay for a rootless parent. Executor reads/writes through those concrete handles. Storage::read cannot substitute for pending-parent access. The inspected Any/Current unsealed/staged handles are one-shot and non-Clone; retain required effects before preparing them. See [concrete branch access](../execution/qmdb.md#give-executor-concrete-branch-access) for production wrapper and generic type constraints.

## Interface boundary for state finalization and state sync

Transaction execution and result certification are Executor responsibilities. Storage computes the selected root and manages canonical application/durability. Commonware supplies signature, storage, collection, fetch and network primitives. Executor adds the full application statement, exact-order/input-state binding, validated distinct-identity collection, and safe peer switching. Storage adds application commit linkage and access/retention integration. Imported results cannot become own DirectExecuted signatures.

`Executor::commit` returns after Storage proves durable local completion. Complete direct effects → Storage preparation/root → Executor full-subject signing → verified f+1 certificate is the certification path. Direct canonical application may progress independently of peer collection once exact order/base hold. Imported application additionally requires a verified certificate and applicable material before stopping local work. Concrete peer codec, material requests, verification and switching remain undecided. These declarations do not claim a complete state-sync API. See [State sync](../execution/state-sync.md) and [Execution responsibilities](../execution/README.md).
