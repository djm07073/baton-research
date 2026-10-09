// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.
// Existing Commonware API excerpts; not standalone declarations or protocol implementation.

// Existing commonware_consensus::Automaton method excerpts.
fn propose(
    &mut self,
    context: Self::Context,
) -> impl Future<Output = oneshot::Receiver<Self::Digest>> + Send;

fn verify(
    &mut self,
    context: Self::Context,
    payload: Self::Digest,
) -> impl Future<Output = oneshot::Receiver<bool>> + Send;

// Existing commonware_consensus::Reporter method excerpt.
fn report(&mut self, activity: Self::Activity) -> Feedback;

// Existing multimmit::marshal::Mailbox method excerpts; enclosing bounds omitted.
pub async fn stage_block(
    &self,
    block: impl Into<Arc<TransactionBlock<H, B>>>,
) -> Result<Custody, Error>;

pub async fn put_block(
    &self,
    block: impl Into<Arc<TransactionBlock<H, B>>>,
) -> Result<(), Error>;

// Existing multimmit::marshal::Update; imports/derives omitted.
pub struct Update<B: Block> {
    pub index: OutputIndex,
    pub block: Arc<B>,
    pub acknowledgement: Exact,
}

// Existing commonware_consensus::Relay method excerpt.
fn broadcast(&mut self, digest: Self::Digest, plan: Self::Plan) -> Feedback;
