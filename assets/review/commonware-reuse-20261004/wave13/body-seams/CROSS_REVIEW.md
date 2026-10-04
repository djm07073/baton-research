# Wave13 independent pool/Orderer and execution seam review

**Pass. Adopt exactly the two proposed prose clarifications; neither changes authority, completion predicates or public interfaces.** Reviewer `/root/reuse_network_v3`. `CROSS_REVIEW_RECEIPT.json` binds actual final peer reports,19 current page checks and four decisive retained primary sources. No fresh download is claimed.

## Exact reviewed reports

| Report | SHA256 |
|---|---|
| pool-orderer-seams/REPORT.md | `73efe0965391d7b6cca264a5ca6a0aaa7ca55af5bf85a0d099eb588ebe20a3a4` |
| pool-orderer-seams/READER_DELTA.md | `d1722b1197762b14bcf609e1910a074fa95340969eb71c83f5771b4c916fd3c0` |
| execution-seams/REPORT.md | `c4280a6e683e4904dd32b4d04329c13415c7549436f8c9cf07c9a9ce6ce1ea3e` |
| execution-seams/READER_DELTA.md | `71977ab39e80ea8dadc87f9f7b733bd486f1c13605bf6ad889b6440385dfb044` |

The retained Nunchi actor/pool and native DatabaseSet/sync sources were independently rehashed against this reviewer's complete-tree receipts and reread for the decisive ownership/completion boundaries. Existing source receipts are not presented as a fresh catalogue or compiled assembly.

## Nunchi lead

The exact replacement is:

> **Nunchi supplies the queue/selection actor; TxPool adds payload hooks and connects durable Executor outcomes to that actor.**

This improves the old project/module-ambiguous “canonical lifecycle to Baton” phrase. The existing actor owns pending/finalized messages and the private kernel; its current finalized notification remains lossy/fire-and-forget, not processed completion. Current Tx interfaces already require chosen processing/recoverable-handoff and selection/replay readiness; the new lead cannot replace those detailed conditions. It accurately names the existing direct durable Executor→TxPool→chosen backend path without placing Baton scheduling on the result path. No second pool, selected workload, new message or ACK is implied.

Pool/Orderer report's other seams agree with the actual current body/glossary/interface/E2E routes: stable selected material, producer versus execution ancestry, exact authenticated header/body correspondence, proposal versus canonical cleanup, and sparse native witness versus dense delivery remain explicit. It does not promote local dedup into cross-producer exactly-once execution, or native inspect/serve/Exact into durable source history. No additional reader delta is justified.

## CommitResult ownership paragraph

The exact insertion after the associated-type table is:

> `CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.

Actual central Rust declares TxPool::on_commit, Orderer::acknowledge and optional Baton::on_commit with owned CommitResult, while only requiring Send; Executor/Storage produce the same associated type. Equality connects types and Send permits transfer, neither supplies another owned receipt. A concrete type can provide shared/cloneable immutable handles or reconstruction from the already required recoverable exact durable evidence. Naming that concrete binding does not add a Clone trait bound or require another receipt actor/store.

The same immutable receipt must retain exact range/state/output/cursor/provenance identity and per-receiver checks. Copying it does not atomically process consumers, acknowledge the pool's private state, establish durability anew or allow Baton observation to gate the Orderer ACK. These conditions remain in the associated table, completion comments, Tx interfaces and canonical/recovery text. This is a documentation assembly clarification, not a diagnosed compiled generic bug.

The execution report's remaining custody/branch/preparation/certificate/material/writer/recovery seams match the previously independently reviewed source limits. DatabaseSet and QMDB sync do not supply the application CommitResult or multi-consumer transaction. Exact source/private extraction, rootless branching, import switch and cross-store receipt linkage remain explicit additional engineering; no new generic engine or default is inferred.

## Candidate and scope

All19 checked page bytes currently equal baseline78d5f2e; this review approves literal proposed changes before root mutation. Final reader hashes should be bound separately after adoption. No canonical edit was performed here.

Original concrete Commonware/actual-chain assembly research, repeated independent review through01:29:14UTC and verified publication/synchronization remain the full objective. Engineering implementation/proofs are outside the documentation completion gate. No native ACK/default/module/trait, compile/build/test, protocol implementation, dependency change, remote publication or early six-hour completion is claimed.
