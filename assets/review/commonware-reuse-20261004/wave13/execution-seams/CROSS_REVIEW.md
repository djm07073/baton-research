# Wave 13 independent body/pool seam review

**Pass for scoped documentation/source fit. Approve the exact Nunchi lead correction; body needs no reader delta.** The existing direct durable Executor→TxPool→selected backend path becomes clearer without a new service, backend/default choice or Baton gate.

Reviewer `/root/reuse_storage_types_v3`; baseline `78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4`.

| Reviewed artifact | Exact SHA-256 |
|---|---|
| `wave13/body-seams/REPORT.md` | `8f9183ac887c4b8ed66c112db7648d1c3a0b0e071535cabe73822cec2610a253` |
| `wave13/body-seams/READER_DELTA.md` | `725df7a178157005bbfba252c1a7c16b9fe7ddbc418edabad5dd63f708067491` |
| `wave13/pool-orderer-seams/REPORT.md` | `73efe0965391d7b6cca264a5ca6a0aaa7ca55af5bf85a0d099eb588ebe20a3a4` |
| `wave13/pool-orderer-seams/READER_DELTA.md` | `d1722b1197762b14bcf609e1910a074fa95340969eb71c83f5771b4c916fd3c0` |

`cross-review/CROSS_EVIDENCE.json` binds 11 current page hashes and 11 retained pinned primary source files independently rehashed against this reviewer's retained complete native/Nunchi tree blobs. Nine body sources are the report's decisive native subset; two Nunchi sources are this reviewer's prior independently fetched actor/kernel bytes. No source download or broad new API inventory was needed. Current pages include root's exact two adopted draft changes; the receipt distinguishes these literal changes from unchanged baseline pages. No canonical edit was made by this reviewer.

## Body report

The source boundaries fit the report. Native TransactionBlockHeader commits the complete producer coordinates, parent identity and opaque body commitment (`types/block.rs:113–125`); Artifact ID separately domain-separates exact encoded artifacts (`machine/admission.rs:145–160`). Neither is merged execution-parent identity. The report correctly keeps exact authenticated header/body/context join in the attachment, selected execution-parent binding in Executor, and dense canonical interpretation in Orderer.

Activity's primary source explicitly labels non-authoritative idempotent telemetry, with an exact admitted Arc artifact and no delivery/progress/retention authority. Voter ignores Reporter feedback (`voter/actor.rs:1655–1663`), and replay clears newly-ready notices. Thus a missed speculative candidate observation cannot mean empty canonical input, and native verification need not await Baton join/approval. A recoverable exact-native-source handoff remains additional integration rather than an observer ACK or ready-made journal replay guarantee.

Buffer waiters are notified before eligibility-based cache residency (`buffered/engine.rs:299–322`); generic resolver routes matched responses through Delivery/Consumer rather than automatically establishing body custody. Immutable archive occupied-index put is ignored (`immutable/storage.rs:237–241`), while sync persists Freezer/Ordinal before publishing its checkpoint (`:293–310`). The report preserves exact presence/expected-byte/parent checks and covering sync, rather than assigning durable custody to cache arrival or put success. Existing native/body/Orderer adapters remain necessary and open, with no duplicate transport/cache/fetch/store framework.

## Pool report and exact lead

Approve only:

> Nunchi supplies the queue/selection actor; TxPool adds payload hooks and connects durable Executor outcomes to that actor.

Nunchi really retains one public Mempool owner/private Pool and passes Pending/Finalized through its mailbox. `pending` clones nonce-run candidates; public `finalized` uses lossy `try_send`, while private kernel finalize advances nonce/height and TTL. Existing Tx prose already requires authoritative hydration, completion/replay/selection reconciliation and static local/peer payload hooks at that owner. The replacement lead accurately describes this **application connection**, not an unchanged upstream durable-result API or selected completion policy.

The old phrase “canonical lifecycle to Baton” could mean the project, but the adjacent module named Baton owns scheduling only. Naming durable Executor outcomes and the existing actor removes that concrete ambiguity. Actual imported outcomes still pass through Executor's authorized durable result; header/proposal success, root equality and local enqueue cannot substitute. Backend duplicate semantics, packing/dependencies, workload, schema and lifecycle choices remain open. Optional Baton observation remains outside certification, state sync, canonical apply and ACK; no new actor, barrier or default is introduced.

## Verdict and scope

Adopt the one lead correction and body no-delta conclusion. They preserve exact bytes/header/parent/context identity, retained selected material, direct/imported result provenance, shared Storage writer/durability, recoverable exact-range ACK and distinct backend processing readiness. Existing public callbacks/primitives do not silently provide application interpretation, atomic consumer processing or recoverable dense delivery.

This is documentation and actual retained source fit, not compiled integration, executed E2E, benchmark or protocol proof. Full original concrete assembly/actual-chain explanation, repeated independent review for the six-hour window and verified publication/synchronization remain the goal. Engineering implementation/proofs remain outside that documentation completion gate. The window ends **2026-10-04 01:29:14 UTC** and remains active; current draft changes are not treated as published. No canonical edit, new API/module, policy/backend choice, dependency mutation or build/test occurred here.
