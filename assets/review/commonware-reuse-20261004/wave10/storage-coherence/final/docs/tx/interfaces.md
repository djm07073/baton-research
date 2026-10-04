# Tx interfaces

**TxPool owns candidate lifecycle and payload-based classification.** Admission makes a transaction available for selection. A canonical result determines its eventual lifecycle update. The detailed contract keeps these events separate.

## Interface overview

Rust declaration: [TxPool](../overview/rust-interfaces.md#txpool). The Rust interfaces page is the single source for these declarations. Arguments use the associated types shown below. Async methods return a Future whose output is `Result<SuccessType, Self::Error>`; synchronous policy methods return Result directly. The output column names SuccessType.

`Selection` identifies the native producer context and bounded selection limits. `Batch` is an ordered candidate sequence where backend dependencies matter, not evidence of block inclusion or successful execution. `on_proposal` handles local build cancellation and reselection; `on_commit` handles lifecycle updates from durable canonical results. They do not share a deletion condition.

TxPool::classify consumes static features extracted from payloads. Where and how `Decision` controls producer routing or packing filters remains undecided. Balance, nonce, and load lookups do not belong in static analysis. CPU budgets and worker placement for the two pure computations are separate decisions.

| Proposed interface | Caller → receiver | Input | Output / next action |
|---|---|---|---|
| `TxPool::admit` | Tx API / peer → tx layer | `Self::Tx`, `Self::Source` | `Self::Admission`; retained candidate |
| `TxPool::analyze` | TxPool admission / packing integration | `&Self::Tx`; configured analysis version | `Self::Features` |
| `TxPool::classify` | TxPool / inclusion integration | `&Self::Features` | `Self::Decision`; placement and policy undecided |
| `TxPool::select` | Producer adapter → pool | `Self::Selection`: producer context and limits | `Self::Batch`; candidate transactions |
| `TxPool::on_proposal` | Producer adapter → pool | `Self::ProposalOutcome`: local correlation and outcome | `()`; local lifecycle update, separate from canonical deletion |
| `TxPool::on_commit` | Executor → pool | `Self::CommitResult`: durable range and tx outcomes | `()`; canonical lifecycle update |

A tx ID identifies a transaction; an external body commitment identifies body content; the native header ID identifies the complete producer header, including epoch, chain, height, parent, and commitment. Adapters maintain the correspondence between selected bytes, body, authenticated header, and canonical outcomes. Attachment-local request correlation does not imply that a native private build ID is exposed in Context. Codec, identity, and duplicate semantics remain undecided. [Producer header identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L113).

## Connect the trait to one existing backend

**The trait wraps the selected pool; it does not create a second queue.** The concrete mapping depends on the workload and compatible source adaptation. Static feature extraction and policy remain application hooks.

| TxPool call | Existing API candidate | Connection still needed |
|---|---|---|
| `admit` | Nunchi `submit`; Reth `add_transaction(origin, tx)` | Preserve admission completion and source handling; Constantinople's private `try_ingest` needs exposure/adaptation, while the receiver returned by `try_submit` resolves eventual batch status |
| `analyze` / `classify` | Application payload hooks around the selected actor/iterator | Backend stateless validation is not a Features/Decision result; connect peer admissions if admission-time policy is chosen |
| `select` | Nunchi `pending(count)`; Reth dependency-aware best iterator with `BestTransactions::filter_transactions` | Native producer context, selected work/count limits, dependency-preserving full-body byte packing |
| `on_proposal` | Existing candidate/iterator/build ownership | Cloned or iterator-selected candidates need no generic reinsertion solely on cancellation; destructive selection needs a reconciled ownership contract |
| `on_commit` | Nunchi `finalized`; Reth canonical update/maintenance | Actual durable outcomes and next canonical nonces; explicit completion and restart/reconciliation readiness |

Nunchi's exported notification returns no processed nonce/watermark acknowledgement. Its `Pool` module is private, so a wrapper cannot simply import its internal state to prove the update happened. `on_commit` success needs a defined completion condition; a lossy notification alone does not prove backend processing. Any selected recoverable handoff versus processed-completion contract must state how selection is reconciled. This does not add a pool ACK to native cut or direction. [Nunchi public handle](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L61), [export boundary](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/lib.rs#L15), [Constantinople completion](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L112), [Reth admission](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L126).

**For a packing overlay, reuse the selected backend's predicate and dependency controls.** Reth's public `filter_transactions` wraps its best iterator; rejected entries invoke `mark_invalid`. The base iterator excludes those entries/dependents locally while retaining candidates in the shared pool. An ordinary filter after yielding a predecessor does not preserve this dependency behavior. A returned-count limit after filtering bounds yields, not visited/rejected candidates or static-analysis work. Keep analysis on immutable payload facts and connect the chosen body-byte/work limits. This is conditional on a compatible pool backend; direct routing versus packing remains open. [Public predicate](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1175), [Filter loop](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L337), [Local iterator exclusion](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L124).

For a Nunchi source adaptation, add reliable canonical processing through the existing Message/handle/oneshot pattern, with context/range checks before replay. Startup nonce hydration must complete before eligible selection, and its relation to admission needs a selected contract: existing `finalize` also advances height and runs TTL, so seeding a high height may expire pre-seed entries. Unknown nonce zero is not authoritative state. Retain the private kernel and its existing owner; no new pool reconciliation actor is required. [Finalize and TTL](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L211).
