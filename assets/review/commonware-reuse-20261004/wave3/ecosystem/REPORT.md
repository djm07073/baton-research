# Additional ecosystem candidates

Source investigation during the active six-hour goal. Canonical baseline is GitBook `NY491pkJQdX6ny2Lyndj` / GitHub `3c5ec96c91883dae892ee99832dee315c789eaee`. No backend, transaction semantics, dependencies or protocol implementation are selected by this survey.

## Nunchi supplies a reusable generic mempool actor

The pinned [Nunchi SDK](https://github.com/nunchi-labs/sdk/tree/eea35ced709f68c15d6fbc8bcc754696a7e44374) contains a stronger conditional whole-actor candidate for a custom SHA-256, monotonic nonce-lane workload than Constantinople's fixed transaction/Header pool. This is an ecosystem package using Commonware, not a new core Commonware primitive.

| Existing public surface | Reuse value | Application connection |
|---|---|---|
| [PoolTransaction](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/tx.rs#L32) | Custom transaction type, associated nonce key/error, digest, nonce, encoded size and stateless verify | Match SHA-256 identity and nonce assumptions; keep payload-only Features/Decision analysis in TxPool |
| [Mempool::new/start/start_p2p](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L258) | Existing actor, mailbox ownership and Commonware Sender/Receiver integration | Use the chosen dependency revision; establish channel/decode/message limits |
| [submit/submit_many](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L64) | Stateless checking and actor admission response, not a canonical completion wait | Admission budgets and aggregate request bounds; no duplicate custom queue |
| [pending(limit)](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L177) | Count-bounded gap-free nonce runs; underlying [selection clones entries](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L164) | Add selected body-byte/framing budget and static filtering; no destructive proposal pop |
| [finalized](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L195) | Existing global digest cleanup, committed nonce refresh and TTL/status bookkeeping | Map durable Executor outcomes, recover dropped updates and hydrate canonical nonces at startup |

`finalized` uses `try_send` without acknowledgement. Its comment claiming the next report self-heals a dropped update is not unconditional: lose lane A's update, then finalize only lane B transactions, and A's committed nonce remains stale. The actor initializes nonce snapshots to zero and has no dedicated recovery constructor. Replaying/seeding complete required canonical nonce state, knowing refresh readiness, and reconciling dropped updates remain integration work. A pool notification must not become a native cut or direction approval gate.

`pending` does not provide byte packing, producer-context identity, reservations or deterministic canonical execution. Same-nonce replacement, nonce-gap handling, TTL and status retention are package policies, not adopted Baton defaults. Canonical outcomes, failed/replayed input and multi-producer duplication still need the chosen application mapping.

`start_p2p` requires `T: Encode + Read<Cfg=()>`. Incoming [raw read](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L473) occurs before stateless size/verify checks and has no explicit complete-frame exhaustion check. Local successful admissions send once to `Recipients::All`; received transactions are not rebroadcast. There is no inventory, missing-tx fetch or delivery retry machinery. Bound decoding and the full transport payload, and add only the selected delivery/admission integration needed by the workload.

The source workspace declares Commonware `2026.9.0` and SDK `2026.9.0-alpha.1`. The crates.io API returned HTTP 404 for `nunchi-mempool` during this survey; no published registry artifact was confirmed. Evaluate the pinned source workspace rather than assuming a registry dependency or compatibility with Baton's native pin. The chain builder's execution/merkleization lifecycle is not required merely to reuse the pool.

Independent reviews: [pool/canonical semantics](ORDERER_POOL_CROSS_REVIEW.md), [P2P/admission](../network/NUNCHI_CROSS_REVIEW.md).

## Other inspected candidates

[Kora](https://github.com/refcell/kora/tree/446b4c7aba80e8358486ddb43a276c5bfa183102) separates a BlockExecutor returning changes/receipts from storage conversion, and has its own EVM transaction pool. This supports the execution/effects/storage separation as a source example, but does not supply an unchanged generic Baton backend: its interfaces use Alloy headers, Ethereum transactions and EVM account/storage/code partitions. Its StoreBatches are application mutation lists, not Commonware unmerkleized batch handles. No production claim is inferred from its README.

[qmdb-revm](https://github.com/refcell/qmdb-revm/tree/2814bc541974087c75b51cfe5ce0625be871a6dc) is archived and points readers to Kora. It adapts REVM to a user-implemented QmdbBackend and Commonware storage `0.0.65`, composing partition roots in its application code. It is an older REVM-specific adapter reference, not a direct native-pin database, rootless branching primitive or selected dependency.

## Evidence scope

[source-manifest.json](source-manifest.json) records 29 fetched files with SHA-256 and verified Git blob hashes across three pinned repositories. Recursive trees and the registry response are retained. These are source/type/lifecycle findings, not compilation, integration tests, maturity assessment or six-hour completion.
