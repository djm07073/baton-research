# Tx layer: roles and flow

**TxPool manages the transactions available for the next block.** It accepts candidates, keeps them available, supplies bounded batches to BlockService, and updates their lifecycle after canonical results. TxPool also supplies static payload analysis and policy hooks; whether it runs in a router or during block packing remains undecided.

## Roles and responsibilities

TxPool receives transactions from clients and peers and retains candidates for producer body construction. Static analysis extracts features available from the transaction payload itself. Routing and packing policies may use those features. Live balances, nonces, and current node load are not static-analysis results.

A reuse candidate is the separate Constantinople `TransactionSource` and pool implementation. TransactionSource accepts a parent `Header`, consensus `Round`, and the byte count of signed transactions already selected; it returns `Vec<VerifiedTransaction>` and expects marshal finalized-block Updates. Native producer Context and digest callbacks do not supply these types. Selection and canonical-outcome adapters are therefore needed.

Its Commonware dependency revision also differs from the native pin, so direct Rust type compatibility is unverified. Reusing a whole crate or selected implementation pieces, along with queue and cleanup policies, remains open. [TransactionSource](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/lib.rs#L9), [Dependency pin](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/Cargo.toml#L50).

When BlockService calls `TxPool::select`, the pool returns candidates for the supplied context and limits. Creating or canceling a proposal does not turn admission into a canonical outcome. Transaction lifecycle cleanup follows canonical execution results.

## Reuse an existing pool without importing the wrong lifecycle

**A pool backend should replace candidate storage and selection, not sit beside a second custom pool.** The real-chain sources offer two useful paths. The implementation choice remains open; the current design does not adopt Ethereum or Constantinople transaction semantics.

| Reference | Existing pieces to reuse or adapt | Compatibility work |
|---|---|---|
| Constantinople | Bounded foreground/background queues, message-digest dedup, whole-batch byte accounting, proposal/status bookkeeping | Fixed transaction/Header/SealedBlock types; private admission/kernel surfaces; destructive selection and height/grace cleanup; different Commonware revision |
| Tempo / Reth | Reth transaction pool, transaction network manager, canonical maintenance and payload-builder architecture | Ethereum nonce/gas/fee/provider/transaction types and RLPx network; Tempo adds application-specific nonce and execution extensions |

For a generic payload workload, first assess whether the Constantinople package can be adapted. Its inspected Cargo package has publish=false: reuse means the pinned source/git workspace or a maintained extraction, not an already published generic mempool crate. If its fixed types/lifecycle prevent whole-crate reuse, extracting a maintained queue/dedup/budget kernel is new integration work with source provenance, not a ready-made generic primitive. Its selection pops entries immediately; body retention, local cancellation/reselection and canonical outcomes need explicit reconciliation. Its finalized-block status handler tracks outstanding local proposals rather than proving global durable execution cleanup. [Pool package](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/Cargo.toml), [pool selection](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L402), [dedup/admission](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L559), [outcome handler](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L844).

For an explicitly Ethereum-compatible execution backend, evaluate the complete Reth pool/network/maintenance composition rather than importing just a queue or all Tempo-specific extensions. Tempo builds a Reth pool, starts network integration with that pool, and drives maintenance from canonical state notifications. Reth's pool transaction bounds require Ethereum-shaped transactions; opaque Baton tx bytes are not accepted unchanged. [Tempo pool assembly](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/node/src/node.rs#L772), [network assembly](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/node/src/node.rs#L205), [maintenance](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/transaction-pool/src/maintain.rs#L475), [Reth bounds](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L114).

Neither example supplies an unchanged Multimmit pool lifecycle. Producer-lane inclusion is separate from global exact execution order, and several producers may include the same tx. Keep pool-local duplicate suppression, canonical replay semantics and cleanup separate. Static analysis still uses payload facts only; routing at admission versus filtering at packing remains undecided.

Names alone are not proof of reusable behavior. Alto constructs opaque test payloads without a pool. The separate `zmanian/commonware-mempool` demonstration has stub Relay/Verify paths and emits a message called FinalizedBlock from proposal construction; that event cannot drive canonical cleanup. These inspected sources are useful survey evidence, not selected Baton backends. [Alto builder](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/application.rs#L51), [demo proposal path](https://github.com/zmanian/commonware-mempool/blob/a80b86e22a74322cf4c29b07973f00711dbc4373/src/mempool.rs#L416).

## Tx P2P connection

Use existing Commonware authenticated P2P connections, with a logical tx channel separate from native consensus messages. Do not assume dedicated physical connections for transactions. Transaction floods compete with report, body, and native processing; concrete quotas, queues, and runtime placement remain open, as described in [P2P message planes](../overview/networking.md#p2p-connections-and-message-planes).

Use the selected chain backend's transaction transport when its complete workload/network is adopted. Constantinople's inspected ingress is HTTP with a separate HTTP relayer; it does not supply generic Commonware peer tx gossip. A generic Baton transport can reuse Commonware buffered broadcast and resolver on the existing authenticated channels. Their digest cache/fetch services replace generic propagation/cache/retry machinery, but do not choose unknown-tx inventory, admission identity or canonical cleanup. [Constantinople ingress](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L718), [HTTP relayer](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/bin/validator/src/relayer.rs#L455).

Buffered `get`/`subscribe` require a known digest; the adapter still needs an inventory/admission bridge if using announced hashes. A cached duplicate is not evidence of a canonically executed tx. In Constantinople, VerifiedTransaction aliases SignedTransaction and `new_unchecked` is public; `try_submit` also accepts caller-supplied digests separately from transactions. A P2P bridge bypassing HTTP must bounded-decode, verify the selected signature subject/domain, recompute chosen transaction IDs and align status IDs with actual validated transactions. Do not treat the type name or caller digests as validation. [Transaction alias](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/primitives/src/transaction.rs#L41), [submit arguments](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L112), [HTTP validation](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/http.rs#L246).

Canonical maintenance needs the backend's actual outcome contract. Reth `remove_transactions` treats entries as discarded, not mined; `BestTransactions::mark_invalid` only excludes iterator entries/dependencies and does not establish canonical retirement. For an Ethereum-compatible backend, use `prune_transaction(s)` when intentionally mapping a mined outcome; its contract preserves descendant eligibility. Full canonical refresh uses `TransactionPoolExt::on_canonical_state_change(CanonicalStateUpdate)` with the new tip, account/fee updates, mined transactions and update kind; prune alone is not the full refresh. Connect durable Executor outcomes through a verified backend outcome mapping. Constantinople's proposal pop and status ACK likewise do not establish durable canonical execution; outstanding digest records alone do not retain canceled proposal bytes. Retention, cancellation/reselection and aggregate pending-material limits remain adapter work. [Reth mined pruning](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L524), [canonical refresh](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L773), [discard removal](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L496), [iterator invalidation](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1117).

Wire protocol, producer targeting, retransmission and duplicate semantics remain undecided. Static validation hooks can supply a payload-only check, but a backend hook returning validation success/failure is not automatically TxPool's Features/Decision interface.

## Open decisions

| Item | Decision |
|---|---|
| Tx format / ID / signature domain | |
| Mempool implementation to reuse | |
| Static-analysis placement and result schema | |
| Router / packing policy and replacement interface | |
| Tx P2P wire protocol / logical channel ID | |
| Candidate selection order / byte and count limits | |
| Application semantics of duplicate transactions | |
| Durability of admission responses | |
| Proposal cancellation / reselection / retransmission | |
| Canonical cleanup / retention / GC | |

## Commonware primitives in the transaction layer

**TxPool owns admission and selection; Commonware supplies the networking, encoding and storage building blocks.** Keep static analysis inside `TxPool::analyze` / `classify`, whichever routing or block-filtering policy is eventually chosen.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_p2p::authenticated`, `Sender`, `Receiver`, `Recipients` | Tx propagation over logical channels on the existing authenticated network | Tx admission, duplicate identity, peer limits and routing/filtering policy |
| `commonware_codec::Codec` and `commonware_cryptography::{Signer, Verifier}` | Decode bounded tx messages and verify the chosen tx signature subject | Tx schema, domain, static features and application validity rules |
| `commonware_runtime` and `commonware_actor::Feedback` | Pool tasks, bounded mailboxes and local completion signals | Pool ownership, admission/selection coordination and feedback semantics |
| `commonware_broadcast::buffered` and `commonware_resolver::p2p` (generic transport composition) | Known-digest payload dissemination, local cache/subscription, keyed peer fetch/retry | Inventory/admission bridge and transaction identity; these do not implement semantic pool dedup or canonical cleanup |
| `commonware_storage::queue` (candidate) | Persistent pending-work storage if durable pool admission is selected | Deduplication, indexing, eviction and transaction selection; a queue is not a complete mempool |

The inspected MCP release inventory does not expose a standalone mempool or block-builder crate. Stateful's application provider may be backed by a mempool, but that provider is not a complete pool. Actual chain implementations above provide stronger reuse evidence. Existing pool/iterator and codec size tools can supply the packing kernel; state-dependent execution in Tempo/Constantinople builders is not a default for Baton's DA body builder. The router-versus-filtering-layer choice remains open.

See [versioned primitive evidence and compatibility checks](../reference/integration.md#primitive-reuse-catalog).
