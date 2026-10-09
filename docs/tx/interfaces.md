# Transaction admission and selection

**Use concrete pool operations inside the app; implement the existing `Automaton` at the consensus boundary.** No public TxPool trait is required. The [callback interfaces](../overview/rust-interfaces.md) show the actual Commonware connection.

## Interface overview

| App operation | Called by | Completion means |
|---|---|---|
| Admit transaction | RPC or peer ingress | Bounded input validated and retained as selected/unselected, or rejected |
| Select batch | `Automaton::propose(context)` handler | Stable selected bytes fit dependency, count, work and full-body limits |
| Maintain canonical pool state | App's durable application path | Exact applied outcomes reconciled with the chosen pool backend |

Admission verifies encoding, signature/domain and chosen stateless rules, then applies payload-based policy. Both RPC and peer paths use the same classification. Selected candidates may enter local batches. Valid unselected candidates remain only for the chosen retention/propagation policy. Invalid input is dropped. These classes need no second pool, actor or physical connection. Static classification uses immutable payload facts; live balances, canonical nonces and node load belong to separate readiness checks.

Selection uses the supplied Multimmit producer context. Its `parent` is a producer-header parent, not the application execution checkpoint or current canonical state. Dependency-aware packing cannot bypass an excluded required predecessor. Bound visited work and encoded body bytes as well as returned transaction count. Retain the selected bytes so proposal cancellation, pool replacement or concurrent admission cannot change a constructed body's commitment. Selection alone does not retire a transaction canonically.

Local pool membership, selection and readiness govern this node's proposals; peer or canonical blocks are validated under the agreed payload rules without requiring their transactions to have been locally admitted or selected.

```text
app.handle_propose(context):
    txs = pool.select(context, configured limits)
    body = encode stable selected bytes
    block = TransactionBlock::from_context(context, body)
    custody = await marshal.stage_block(block)
    retain accepted body/custody association
    reply with body digest
```

This is App-internal proposal code. Follow the canonical [verify handler](../baton/interfaces.md#automatonverify-validity-custody-and-scheduling) and [Update handler](../baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack) for scheduling, reconciliation and ACK. Pool maintenance consumes recoverable durable outcomes; it adds no required pool-processing ACK to canonical delivery or native consensus. Reconcile missed maintenance before relying on the backend's readiness state.

Transaction ID, body digest and native header digest identify different objects. Maintain selected bytes → body → exact header/context → applied output correspondence.

<a id="connect-the-trait-to-one-existing-backend"></a>

## Connect one existing backend

Reuse one fitting candidate store and its deduplication/selection machinery. Keep app-specific classification in its existing admission paths.

| Candidate | Existing operations | App connection still required |
|---|---|---|
| Nunchi | `submit`, `pending(count)`, `finalized` | SHA-256/nonce-lane fit, classification in both local and peer ingress, byte packing, canonical nonce hydration and lost-update reconciliation |
| Reth | `add_transaction`, dependency-aware best iterator, canonical maintenance | Ethereum transaction/provider semantics and complete canonical outcome mapping |
| Constantinople | Admission, bounded foreground/background queues, batch selection | Fixed transaction/context types, destructive selection retention/cancellation, canonical lifecycle and source-version adaptation |

Nunchi's private pool kernel can be adapted through its existing Message/handle/handler. Its lossy `finalized` notification does not establish processing; startup and lost-update reconciliation remain necessary. Its limited pending walk can underfill after filtering, and a selected successor cannot bypass an excluded required predecessor. [Nunchi handle](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L61), [pending walk](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L160).

Constantinople pops selected candidates; retain bytes and reconcile canceled proposals if adapting it to the app's selection contract. Reth's local iterator exclusion is separate from mined canonical cleanup; use its full canonical maintenance when that backend is selected. These are source-adaptation candidates, with unverified compatibility to the current Multimmit graph. [Constantinople selection](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L402), [Reth maintenance API](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L773).

Backend choice, transaction codec/identity, duplicate semantics, static policy, quotas and physical retention remain open. The [pool survey](README.md#reuse-an-existing-pool-without-importing-the-wrong-lifecycle) retains the detailed source fit and limits.
