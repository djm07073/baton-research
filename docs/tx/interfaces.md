# Tx interfaces

**TxPool exposes two actions: admit and select.** Admission validates RPC/peer input and classifies retained candidates using internal static payload policy. Selection builds a batch from selected candidates only.

## Interface overview

Rust declaration: [TxPool](../overview/rust-interfaces.md#txpool). The Rust interfaces page is the single source for declarations. Both methods return a Future whose output is `Result<SuccessType, Self::Error>`.

| Proposed interface | Caller → receiver | Input | Output / next action |
|---|---|---|---|
| `TxPool::admit` | Tx API / peer → tx layer | `Self::Tx`, `Self::Source` | `Self::Admission`; selected, unselected or invalid/drop outcome |
| `TxPool::select` | Producer adapter → pool | `Self::Selection`: producer context and limits | `Self::Batch`; bounded transactions from selected candidates only |

Inside `admit`, validate encoding, signature/domain and other chosen stateless admission rules, then apply payload-based policy. Selected candidates are eligible for this node's block batches. Unselected candidates are valid retained transactions used only by the chosen P2P retention/propagation policy, and cannot enter local batches. Invalid input is dropped rather than retained as unselected. Both RPC and peer ingress use this same admission contract.

Selected and unselected are logical classes within the reused pool. They do not require two physical pools, two actors or separate P2P connections. Whether implemented as metadata, indexes or an overlay remains open. Static policy reads immutable payload facts; live balances, current nonces and node load are not static-analysis results. Backend dependency/readiness checks remain separate from that classification.

`Selection` supplies producer context and bounded work/count/body-size constraints. `Batch` is an ordered candidate sequence where backend dependencies matter, not evidence of block inclusion or execution. Selection retains candidates, so canceling a proposal does not require a public proposal callback or generic reinsertion step.

Canonical cleanup remains internal pool/backend maintenance driven by applicable durable execution outcomes. It does not expose `on_commit`, require a TxPool `CommitResult` type or gate native cut/direction. Internal analysis/classification also exposes no `Features` or `Decision` types. Exact admission representation, policy configuration, retention and cleanup mechanics remain open.

A tx ID identifies a transaction; an external body commitment identifies body content; the native header ID identifies the complete producer header, including epoch, chain, height, parent, and commitment. Adapters maintain the correspondence between selected bytes, body, authenticated header, and canonical outcomes. Attachment-local request correlation does not imply that a native private build ID is exposed in Context. Codec, identity, and duplicate semantics remain undecided. [Producer header identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L113).

## Connect the trait to one existing backend

**Wrap one fitting pool backend and keep classification inside its admission/selection integration.** Reuse its candidate store, deduplication and dependency controls.

| Public action / internal responsibility | Existing API candidate | Connection still needed |
|---|---|---|
| `admit` | Nunchi `submit`; Reth `add_transaction(origin, tx)` | Apply the same validation and static classification to RPC and peer ingress; retain selected/unselected status and source handling |
| `select` | Nunchi `pending(count)`; Reth dependency-aware best iterator | Exclude unselected candidates before batch creation; preserve dependency rules and bounded full-body packing |
| Internal canonical maintenance | Nunchi `finalized`; Reth canonical update/maintenance | Map actual durable outcomes and next canonical nonces; reconcile missed updates and restart readiness |

Nunchi's built-in peer ingress does not automatically call a wrapper's policy, so connect classification to the existing actor admission path or a bounded ingress attachment. Its pool kernel is private; adapt the existing Message/handle/handler rather than adding another pool actor. Its lossy `finalized` notification does not prove processing, so the internal maintenance contract must cover missed updates and startup nonce hydration. These backend details do not add public TxPool actions or native waits. [Public handle](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L61), [Export boundary](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/lib.rs#L15), [Peer admission](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L473).

Nunchi's bounded pending walk truncates before an external filter. Filter inside the existing candidate walk when needed; otherwise an overlay can intentionally underfill a batch. A selected successor cannot bypass a required unselected predecessor. Reth's public predicate wraps its dependency-aware iterator and excludes rejected entries/dependents locally while retaining shared candidates. Returned-count limits alone do not bound all visited candidates or analysis work. [Pending walk](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L160), [Public predicate](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1175), [Filter loop](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L337), [Local iterator exclusion](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L124).

Constantinople's inspected selection pops candidates. It needs retention/cancellation integration to satisfy the non-destructive selection contract, and its `try_submit` receiver represents eventual batch status rather than the chosen immediate admission outcome. These are source-adaptation candidates, not unchanged compatible backends. [Selection](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L402), [Completion](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L112), [Reth admission](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L126).

For a Nunchi adaptation, initialize canonical nonce readiness before eligible selection. Its existing `finalize` also advances height and TTL; unknown nonce zero is not authoritative state. The internal maintenance implementation must account for those effects during startup. [Finalize and TTL](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L211).
