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

pub trait TxPolicy: Send {
    type Tx;
    type Features;
    type Decision;
    type Error;

    fn analyze(&self, tx: &Self::Tx) -> Result<Self::Features, Self::Error>;
    fn classify(&self, features: &Self::Features) -> Result<Self::Decision, Self::Error>;
}

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
