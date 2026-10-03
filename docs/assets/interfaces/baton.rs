// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.
// Application interface proposals only; no protocol implementation.

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
