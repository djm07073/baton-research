# Reader documentation review: Nunchi pool comparison and assembly

Independent review date: 2026-10-04. Scope: the Nunchi edits in docs/tx/README.md and docs/reference/integration.md, compared with the current HEAD and pinned SDK source plus ecosystem REPORT.md. No canonical files were edited. Snapshot hashes:

- docs/tx/README.md: `b2601076f47c4dbab50f7faefbf17ef06ea6be78d4e4c3b337c3af7aa304f2af`
- docs/reference/integration.md: `6d912ad6a6d7a95e5378903c9f1d89b387d010745083b8863d8f1eca7b7a2b5c`

## Result

The substantive recommendation is supported: assess the public Nunchi whole actor first **when custom SHA-256, monotonic nonce-lane payloads are actually appropriate**. It does not select that workload, backend, package or a default replacement/TTL/fairness/routing policy. The ten Tx policy cells remain empty. The generic TxPool seam stays responsible for payload-only Features/Decision; pool nonce snapshots are explicitly maintained state, not static analysis.

Two small wording corrections would make scope/completion clearer before publication:

1. **docs/tx/README.md L29 — “Neither example” is stale after adding a third candidate.** Replace with “None of these references supplies an unchanged Multimmit pool lifecycle.” This covers Nunchi as well as Constantinople and Tempo/Reth, without changing the conditional recommendation.
2. **docs/tx/README.md L37 — attribute removal to processing, not merely calling the lossy handle method.** Suggested first sentence: “When processed, the actor's `finalized` notification removes included digests and advances nonce snapshots.” The following sentences already explain lossy try_send/no processing ACK correctly; this precision prevents the opening sentence being read as successful removal upon a `()` return. No new processing ACK or native gate is selected by this correction.

No other blocking issue found in the reviewed Nunchi content.

## Source and contract checks

- New `PoolTransaction` L32, `Mempool::new` L258, `finalized` L195, `start_p2p` L292, workspace Commonware declarations L61 and builder L264 anchors were spot-checked against the retained pinned files. The snapshot-maintenance link L213 lands inside the `Pool::finalize` signature; it supports the nearby method/body claim, although L211 is a more exact method entry point if touching that sentence.
- Public `pending(limit)` returns clones without destructive pop. It is count bounded and nonce contiguous relative to the supplied committed snapshot, not a byte packer or arbitrary runtime-validity guarantee. Docs keep byte framing and nonce-preserving filtering in the application adapter.
- `submit` is admission; lossy `finalized` has no processed ACK; in-memory state and nonce-zero startup require canonical hydration/reconciliation. Lost lane-A updates are not repaired by lane-B-only updates. These limitations are accurately stated without promoting the SDK self-healing comment.
- Canonical cleanup is driven by linked **durable Executor outcomes**, including locally applicable certified imports; it is separate from native cut/direction and cannot become Orderer's durable ACK. This agrees with current adopted Executor/Storage ownership.
- P2P requires `Encode + Read<Cfg=()>`, reads before size/signature checking and does not explicitly require whole-input exhaustion. Docs state codec/ingress bounds, one-shot local-origin sends, no rebroadcast/inventory/fetch/retry, count-only selection and aggregate request work.
- Replacement/TTL/status behavior is named as package policy requiring adapter compatibility, with no default adoption. Reusing pool actor does not imply importing SDK Stateful Application or builder execution/merkleization.
- Registry receipt contains HTTP 404 for exactly `https://crates.io/api/v1/crates/nunchi-mempool`. Docs appropriately say publication was **not confirmed** by that lookup; they do not claim permanent nonexistence, source inaccessibility or production immaturity. Native-pin compatibility remains explicitly uncompiled.
- Comparison/assembly rows distinguish Nunchi ecosystem reuse from Commonware core primitives and do not add a second custom pool.

## Preservation checks

Compared both current pages with git HEAD: no preexisting heading was removed and no external source URL **occurrence** was removed. The new Nunchi heading/link extends the existing reading paths. All existing Tx decision cells are blank. Other wave-three network/Orderer/Storage additions in integration.md are outside this focused Nunchi review.

This is source/documentation review. No pool simulation, protocol compilation, e2e trace, test result, compatible dependency graph, publication or six-hour completion is claimed.
