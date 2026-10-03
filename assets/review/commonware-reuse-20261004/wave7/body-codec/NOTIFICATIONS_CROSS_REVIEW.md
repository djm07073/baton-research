# Independent review — callback and mailbox reuse

Reviewer: `/root/reuse_network_v3`. Reviewed `../notifications/REPORT.md`, SHA-256 `9c47cd3cb115981d9f0c2d94695ee3c25d2ef10e5b98e5e648eeb09dca0f11ed`. Source/API fit passes; no material correction remains. This is independent source readback, not compilation, an implementation, protocol validation or publication approval.

## Decisive checks

- Native `Reporters` is publicly reexported. Its public tuple constructors combine two reporters with the same Activity, and nested composition needs no new event bus. Clone/Send/'static bounds, optional None returning Ok, synchronous dispatch and Closed-before-Backoff combination match actual code. Slow/panicking callbacks have no isolation or durable delivery guarantee.
- Native Multimmit Activity explicitly carries contextually accepted artifacts as non-authoritative telemetry. The voter dispatch discards feedback. Optional fan-out cannot implement the authoritative dense order delivery, durable ACK, certificate/material validation or execution authority. The proposed reader delta keeps those boundaries and adds no cut/report/direction wait.
- Mailbox `new` returns cloneable Sender and owned Receiver; enqueue feedback represents local capacity/overflow handling. Ready capacity alone does not bound caller overflow. The report accurately leaves message retention/coalescing/rejection/context semantics to Policy and notes overflow-lock reentry/unwind restrictions. Backoff is not consumer completion.
- Tempo really constructs nested Reporters with Executor/DKG/peer/feed/optional gossip. Its inspected private ingress handles use unbounded futures mpsc and a different Simplex Activity. Their composition is a useful pattern without importing those private owners, adopting their queue policy or claiming native Activity equivalence.

## Independent evidence

`cross-review-source-manifest.json` includes eight fresh native/release/Tempo downloads specifically for this review, individually Git-blob checked against this reviewer's complete pinned wave-7 trees. Previously independently fresh own `sources/native/consensus/src/lib.rs` and `sources/tempo/crates/consensus/src/consensus/engine.rs` cover reexport and actual construction. `CROSS_REVIEW_VERIFICATION.json` maps all 14 report anchors to own fresh files and exact line ranges.

`NOTIFICATIONS_MCP_CHECK.json` independently compares the actual explicit v2026.9.0 MCP response with own fresh release Reporter source: all 43 numbered lines match; this file is byte-identical to native. Zero-based MCP numbering was translated to one-based GitHub anchors. No successful JSON wrapper was treated as source evidence.

No canonical file was edited. No ACK barrier, default quota/Policy, new public trait, native protocol claim, application-result subject change or Storage/Executor ownership change was introduced.
