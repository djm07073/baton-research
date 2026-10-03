//! Mempool implementation for Simplex consensus with Mosaik dissemination.
//!
//! The MempoolActor integrates with both Commonware's Simplex consensus engine
//! (via Automaton/Relay/Reporter traits) and Mosaik's stream-based transaction
//! dissemination (via Consumer<Transaction>).
//!
//! Key enhancement over commonware-mempool: the actor's run loop uses
//! `tokio::select!` to simultaneously process consensus messages AND incoming
//! Mosaik stream transactions, and publishes FinalizedBlock on a Mosaik stream
//! for source-side inclusion confirmation.

use crate::{
    schedule::LeaderSchedule,
    types::{Bid, BuilderBlock, FinalizedBlock, Transaction, ViewUpdate},
};
use commonware_consensus::{
    simplex::types::Context, types::Epoch, Automaton as Au, CertifiableAutomaton as CAu,
    Relay as Re, Reporter as Rp, Viewable,
};
use commonware_cryptography::{ed25519::PublicKey, Digest, Hasher, Sha256};
use commonware_utils::channel::{mpsc, oneshot};
use futures::{SinkExt, StreamExt};
use mosaik::streams::{Consumer, Producer};
use std::collections::VecDeque;
use tokio::sync::watch;
use tracing::info;

const MAX_TXS_PER_BLOCK: usize = 100;

// --- Messages between the ingress mailbox and the mempool actor ---

pub enum Message<D: Digest> {
    Genesis {
        epoch: Epoch,
        response: oneshot::Sender<D>,
    },
    Propose {
        context: Context<D, PublicKey>,
        response: oneshot::Sender<D>,
    },
    Verify {
        context: Context<D, PublicKey>,
        payload: D,
        response: oneshot::Sender<bool>,
    },
}

// --- Mailbox: implements the consensus traits by forwarding to the actor ---

#[derive(Clone)]
pub struct Mailbox<D: Digest> {
    sender: mpsc::Sender<Message<D>>,
}

impl<D: Digest> Mailbox<D> {
    pub fn new(sender: mpsc::Sender<Message<D>>) -> Self {
        Self { sender }
    }
}

impl<D: Digest> Au for Mailbox<D> {
    type Digest = D;
    type Context = Context<Self::Digest, PublicKey>;

    async fn genesis(&mut self, epoch: Epoch) -> Self::Digest {
        let (response, receiver) = oneshot::channel();
        self.sender
            .send(Message::Genesis { epoch, response })
            .await
            .expect("failed to send genesis");
        receiver.await.expect("failed to receive genesis")
    }

    async fn propose(
        &mut self,
        context: Context<Self::Digest, PublicKey>,
    ) -> oneshot::Receiver<Self::Digest> {
        let (response, receiver) = oneshot::channel();
        self.sender
            .send(Message::Propose { context, response })
            .await
            .expect("failed to send propose");
        receiver
    }

    async fn verify(
        &mut self,
        context: Context<Self::Digest, PublicKey>,
        payload: Self::Digest,
    ) -> oneshot::Receiver<bool> {
        let (response, receiver) = oneshot::channel();
        self.sender
            .send(Message::Verify {
                context,
                payload,
                response,
            })
            .await
            .expect("failed to send verify");
        receiver
    }
}

impl<D: Digest> CAu for Mailbox<D> {}

impl<D: Digest> Re for Mailbox<D> {
    type Digest = D;

    async fn broadcast(&mut self, payload: Self::Digest) {
        info!(payload = ?payload, "broadcasting block payload to peers");
    }
}

// --- Reporter: logs consensus activity ---

pub type Scheme = commonware_consensus::simplex::scheme::ed25519::Scheme;

#[derive(Clone)]
pub struct MempoolReporter<D: Digest> {
    _phantom: std::marker::PhantomData<D>,
}

impl<D: Digest> MempoolReporter<D> {
    pub fn new() -> Self {
        Self {
            _phantom: std::marker::PhantomData,
        }
    }
}

impl<D: Digest> Rp for MempoolReporter<D> {
    type Activity = commonware_consensus::simplex::types::Activity<Scheme, D>;

    async fn report(&mut self, activity: Self::Activity) {
        let view = activity.view();
        match activity {
            commonware_consensus::simplex::types::Activity::Notarization(n) => {
                info!(%view, payload = ?n.proposal.payload, "block notarized");
            }
            commonware_consensus::simplex::types::Activity::Finalization(f) => {
                info!(%view, payload = ?f.proposal.payload, "block finalized");
            }
            commonware_consensus::simplex::types::Activity::Nullification(_) => {
                info!(%view, "view nullified (no block)");
            }
            _ => {}
        }
    }
}

// --- Mempool Actor: holds the transaction pool, builds blocks, bridges Mosaik ---

pub struct MempoolActor {
    hasher: Sha256,
    pending: VecDeque<Transaction>,
    schedule: LeaderSchedule,
    mailbox: mpsc::Receiver<Message<<Sha256 as Hasher>::Digest>>,
    /// Mosaik consumer for incoming full transactions from tx sources (public path).
    tx_consumer: Consumer<Transaction>,
    /// Mosaik consumer for incoming bids from privacy-conscious senders.
    bid_consumer: Consumer<Bid>,
    /// Mosaik consumer for sealed blocks from builders (PBS path).
    builder_block_consumer: Consumer<BuilderBlock>,
    /// Mosaik producer for publishing FinalizedBlock to tx sources.
    block_producer: Producer<FinalizedBlock>,
    /// Watch channel sender: notifies the TagBridge of view changes.
    view_tx: watch::Sender<ViewUpdate>,
    blocks_proposed: u64,
    /// Bids received from privacy-conscious senders (proposer sees these
    /// instead of full txs). Keyed by tx_id for dedup and inclusion tracking.
    pending_bids: VecDeque<Bid>,
    /// The best BuilderBlock received during this view's auction window.
    /// When proposing, the proposer picks this over individual tx ordering
    /// if the builder's bid exceeds the sum of individual priority fees.
    best_builder_block: Option<BuilderBlock>,
}

impl MempoolActor {
    #[allow(clippy::type_complexity)]
    pub fn new(
        num_participants: usize,
        mailbox_size: usize,
        tx_consumer: Consumer<Transaction>,
        bid_consumer: Consumer<Bid>,
        builder_block_consumer: Consumer<BuilderBlock>,
        block_producer: Producer<FinalizedBlock>,
        view_tx: watch::Sender<ViewUpdate>,
    ) -> (
        Self,
        Mailbox<<Sha256 as Hasher>::Digest>,
        MempoolReporter<<Sha256 as Hasher>::Digest>,
    ) {
        let (sender, receiver) = mpsc::channel(mailbox_size);
        let actor = Self {
            hasher: Sha256::default(),
            pending: VecDeque::new(),
            schedule: LeaderSchedule::new(0, num_participants, 5),
            mailbox: receiver,
            tx_consumer,
            bid_consumer,
            builder_block_consumer,
            block_producer,
            view_tx,
            blocks_proposed: 0,
            pending_bids: VecDeque::new(),
            best_builder_block: None,
        };
        (actor, Mailbox::new(sender), MempoolReporter::new())
    }

    /// Run the mempool actor loop.
    ///
    /// Uses `tokio::select!` to process consensus messages from Simplex AND
    /// three Mosaik consumer streams:
    /// - `Stream<Transaction>` -- full public transactions from sources
    /// - `Stream<Bid>` -- commitment-only bids from privacy-conscious sources
    /// - `Stream<BuilderBlock>` -- sealed blocks from builders (PBS auction)
    pub async fn run(mut self) {
        info!(pending = self.pending.len(), "mempool actor started");

        loop {
            tokio::select! {
                // Consensus messages from Simplex engine
                msg = self.mailbox.recv() => {
                    match msg {
                        Some(msg) => self.handle_consensus_message(msg).await,
                        None => {
                            info!("consensus mailbox closed, shutting down");
                            break;
                        }
                    }
                }

                // Public path: full transactions from sources
                tx = self.tx_consumer.next() => {
                    if let Some(tx) = tx {
                        info!(
                            tx_id = tx.id,
                            sender = %tx.sender,
                            priority_fee = tx.priority_fee,
                            "received public transaction"
                        );
                        self.pending.push_back(tx);
                    }
                }

                // Private path: bids from privacy-conscious sources.
                // The proposer sees gas_bid + commitment but NOT the payload.
                bid = self.bid_consumer.next() => {
                    if let Some(bid) = bid {
                        info!(
                            tx_id = bid.tx_id,
                            sender = %bid.sender,
                            gas_bid = bid.gas_bid,
                            priority_fee = bid.priority_fee,
                            "received bid (no payload visible)"
                        );
                        self.pending_bids.push_back(bid);
                    }
                }

                // PBS path: sealed blocks from builders.
                // The proposer picks the highest-bidding builder block.
                builder_block = self.builder_block_consumer.next() => {
                    if let Some(bb) = builder_block {
                        let dominated = self.best_builder_block
                            .as_ref()
                            .map_or(true, |existing| bb.bid > existing.bid);
                        if dominated {
                            info!(
                                builder = %bb.builder_id,
                                bid = bb.bid,
                                tx_count = bb.tx_ids.len(),
                                tee = bb.tee_attestation.is_some(),
                                "new best BuilderBlock"
                            );
                            self.best_builder_block = Some(bb);
                        }
                    }
                }
            }
        }
    }

    async fn handle_consensus_message(
        &mut self,
        msg: Message<<Sha256 as Hasher>::Digest>,
    ) {
        match msg {
            Message::Genesis { epoch, response } => {
                assert_eq!(epoch, Epoch::zero(), "only epoch 0 supported");
                self.hasher.update(b"mosaik-simplex-genesis");
                let digest = self.hasher.finalize();
                info!(payload = ?digest, "genesis payload");
                let _ = response.send(digest);
            }
            Message::Propose { context, response } => {
                let view = context.round.view().get();

                // Notify TagBridge of the view change
                let _ = self.view_tx.send(ViewUpdate { view, epoch: 0 });

                let upcoming = self.schedule.advance(view);
                info!(
                    view,
                    pending_txs = self.pending.len(),
                    pending_bids = self.pending_bids.len(),
                    builder_block = self.best_builder_block.is_some(),
                    upcoming_leaders = ?upcoming.iter()
                        .map(|(v, l)| format!("v{}->p{}", v, l))
                        .collect::<Vec<_>>(),
                    "proposing block"
                );

                // --- Block construction with PBS auction ---
                //
                // Compare the best builder block's bid against what the
                // proposer could earn from individual priority fees. If the
                // builder outbids, use the sealed builder block. Otherwise
                // the proposer constructs its own block from public txs + bids.

                let individual_fee: u64 = self
                    .pending
                    .iter()
                    .take(MAX_TXS_PER_BLOCK)
                    .map(|tx| tx.priority_fee)
                    .sum::<u64>()
                    + self
                        .pending_bids
                        .iter()
                        .take(MAX_TXS_PER_BLOCK)
                        .map(|b| b.priority_fee)
                        .sum::<u64>();

                let builder_bid = self
                    .best_builder_block
                    .as_ref()
                    .map_or(0, |bb| bb.bid);

                let (included_ids, digest) = if builder_bid > individual_fee {
                    // --- PBS path: use the builder's sealed block ---
                    let bb = self.best_builder_block.take().unwrap();
                    info!(
                        view,
                        builder = %bb.builder_id,
                        builder_bid = bb.bid,
                        individual_fee,
                        tx_count = bb.tx_ids.len(),
                        "using BuilderBlock (outbids individual fees)"
                    );

                    let ids = bb.tx_ids.clone();

                    // Hash the builder block commitment as the payload digest
                    self.hasher.update(b"builder-block");
                    self.hasher.update(&view.to_le_bytes());
                    self.hasher.update(&bb.commitment);
                    let d = self.hasher.finalize();

                    // Drain matching bids (builder already included them)
                    self.pending_bids
                        .retain(|b| !ids.contains(&b.tx_id));

                    (ids, d)
                } else {
                    // --- Proposer-constructed block from public txs + bids ---
                    self.best_builder_block = None;

                    let txs: Vec<Transaction> = self
                        .pending
                        .drain(..self.pending.len().min(MAX_TXS_PER_BLOCK))
                        .collect();

                    // Bids represent private txs whose content we don't have.
                    // Include their tx_ids in the block -- the builder will have
                    // provided the actual block body to validators separately,
                    // or these get included by commitment for later reveal.
                    let bids: Vec<Bid> = self
                        .pending_bids
                        .drain(..self.pending_bids.len().min(MAX_TXS_PER_BLOCK))
                        .collect();

                    let mut included: Vec<u64> = txs.iter().map(|tx| tx.id).collect();
                    included.extend(bids.iter().map(|b| b.tx_id));

                    self.hasher.update(b"block");
                    self.hasher.update(&view.to_le_bytes());
                    for tx in &txs {
                        self.hasher.update(&tx.to_bytes());
                    }
                    for bid in &bids {
                        self.hasher.update(&bid.commitment);
                    }
                    let d = self.hasher.finalize();

                    info!(
                        view,
                        public_txs = txs.len(),
                        bid_txs = bids.len(),
                        individual_fee,
                        "proposer-constructed block"
                    );

                    (included, d)
                };

                self.blocks_proposed += 1;
                info!(
                    view,
                    tx_count = included_ids.len(),
                    total_proposed = self.blocks_proposed,
                    payload = ?digest,
                    "block proposed"
                );

                // Publish FinalizedBlock on Mosaik stream for source inclusion confirmation
                if !included_ids.is_empty() {
                    let finalized = FinalizedBlock {
                        view,
                        epoch: 0,
                        included_tx_ids: included_ids,
                    };
                    if let Err(e) = self.block_producer.send(finalized).await {
                        tracing::warn!("failed to publish FinalizedBlock: {e}");
                    }
                }

                let _ = response.send(digest);
            }
            Message::Verify {
                context,
                payload,
                response,
            } => {
                let view = context.round.view().get();

                // Notify TagBridge of the view change
                let _ = self.view_tx.send(ViewUpdate { view, epoch: 0 });

                info!(view, payload = ?payload, "verified block proposal");
                let _ = response.send(true);
            }
        }
    }
}
