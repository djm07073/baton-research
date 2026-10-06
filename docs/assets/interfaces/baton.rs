// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.
// Application interface proposals only; no protocol implementation.

use std::future::Future;

pub trait TxPool: Send {
    type Tx: Send;
    type Source: Send;
    type Admission: Send;
    type Selection: Send;
    type Batch: Send;
    type Error: Send;

    /// Validate and insert a transaction received through RPC or a peer.
    /// Internal payload policy classifies retained candidates as selected or unselected.
    /// Selected candidates may enter local batches; unselected candidates remain
    /// available for the chosen P2P retention/propagation policy. Invalid input is dropped.
    /// Admission does not establish block inclusion or canonical execution.
    fn admit(
        &mut self,
        tx: Self::Tx,
        source: Self::Source,
    ) -> impl Future<Output = Result<Self::Admission, Self::Error>> + Send;

    /// Build a bounded candidate batch from the selected candidates only.
    /// Selection preserves retained candidates; it does not establish canonical retirement.
    /// Full-body packing and any backend dependency rules still apply.
    fn select(
        &mut self,
        request: Self::Selection,
    ) -> impl Future<Output = Result<Self::Batch, Self::Error>> + Send;
}

pub trait Baton: Send {
    type CandidateBlock;
    type Context: Send;
    type ReportSnapshot: Send;
    type Candidates: Send;
    type Report;
    type Direction;
    type Evidence: Send;
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

    /// Admit an authenticated header/body pair and sort eligible not-yet-started candidates.
    /// Preserve completed/current execution order; arrival does not rebuild the started prefix.
    /// While the predecessor runs, only sort pending; dispatch after its valid completion.
    /// Dispatch/reports use the fixed prefix plus the same rule-sorted pending snapshot.
    /// Native confirmed-order commit may separately require exact-parent repair.
    fn on_block(&mut self, block: Self::CandidateBlock) -> Result<(), Self::Error>;
    /// Admit the current leader context and manage its report window and immutable frontier.
    fn on_context(&mut self, context: Self::Context) -> Result<(), Self::Error>;
    /// Authenticate a same-context original intended-order report and count each identity once.
    /// Honest construction preserves the local started prefix and sorts only pending candidates.
    /// This intention is not a progress proof; reception never reconstructs missing inputs
    /// or rewrites the original signed sequence.
    fn on_report(&mut self, report: Self::Report) -> Result<(), Self::Error>;
    /// Authenticate leader direction and submit its parent-linked blocks through Executor::execute.
    /// This local handler adds no direction vote, receipt ACK, or Ready quorum.
    fn on_direction(&mut self, direction: Self::Direction) -> Result<(), Self::Error>;
    /// Admit native finality/history evidence for independent exact-order processing.
    /// Internally verify and retain the exact source; deliver only continuous irrevocable
    /// ranges to Executor::commit and track its durable result for recovery/redelivery.
    /// Local admission is not finality proof or durable completion. This path never waits
    /// for advisory reports, direction, planning, or optional on_commit handling.
    fn on_finality(&mut self, evidence: Self::Evidence) -> Result<(), Self::Error>;
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
    /// Executor application, result certification, and internal delivery tracking do not await this handler.
    fn on_commit(&mut self, result: Self::CommitResult) -> Result<(), Self::Error>;
    /// Immediately return the currently prepared valid policy, if any.
    /// The native owner still rechecks actual proposal context; cut never waits for Some.
    fn prepared_policy(&self) -> Option<Self::PreparedPolicy>;
}

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
