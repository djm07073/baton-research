# Wave 8 final reader review — body, workers and delivery ACK

Reviewer `/root/reuse_network_v3`; baseline `99dc2c456c4b318fefb368cb39a145298f7d86b7`. **Pass; no material issue remains.** Source/document readback, not native compilation/runtime tests, durable completion proof or publication verification.

| Final draft page | SHA-256 |
|---|---|
| docs/consensus/block-body.md | 1125bac9b144d897fd30970349b980a674a1a8f9de2d783d923b2a713a1f748e |
| docs/consensus/ordered-input.md | 76ef44424a04306c5e89d863ff02243c1f6f8e4990a7ddbeeeb660d2320c2720 |
| docs/execution/README.md | a295253e38e5bdc4134a3f1e68f842bf10385d1d4e82ac8da4b6d2ab01d2b863 |
| docs/execution/qmdb.md (scope coherence/hash only; specialist query review separate) | cd32194a2eb62a41ca33954dc8ca97d8a984727338dd8c95dcd08f86e8abeecf |

The incoming-body addition accurately follows existing configured decode → digest → subscribers/resident cache. Mailbox.subscribe performs cached delivery or later wait; the text does not confuse that with peer fetch, application context validity, authenticated header/parent binding or durable custody. Resolver response Bytes go to Consumer and can reach the same existing custody owner, without automatic broadcast-cache insertion or a new receiver/forwarding actor. Prior callback error, native-context, Simplex incompatibility, durability/retention and no-ACK contracts remain intact.

The Orderer ACK paragraph reuses optional existing local Exact/oneshot completion, tied to immutable range and already-required durable CommitResult. Its clone/drop rule matches source. Exact alone has no identity, result, cursor or durable replay. The private Simplex tracker and Tempo's own engine predicate are reference patterns, not native exports or Baton durability. No optional observer gets an ACK veto, no cursor advances solely on cancellation, and no new mandatory waiter/native progress barrier is selected.

The execution table now explicitly lists existing Spawner/Strategizer and Pool/AbortablePool/OptionFuture while retaining journal/metadata durability. Native OptionFuture requires explicit completed-slot clearing/replacement; Strategizer supplies runtime-owned Rayon construction. The prose correctly distinguishes aborting a completion waiter from stopping separately spawned CPU work and preserves canonical mutation ownership. It adds no Runtime/Planner/reschedule trait, worker actor, selected priorities/capacities, strict quiescence promise or authority transfer.

Across the four-page draft, all headings and unrelated baseline lines remain. The sole replaced baseline row is intentionally split into journal/metadata durability and concrete runtime/future reuse; its prior responsibilities are preserved explicitly. Five Rust traits remain byte-identical to baseline (TxPool, Orderer, Baton, Executor, Storage). Thirty-nine open decision cells are empty and eighteen Mermaid source diagrams remain. Certificate-plus-applicable-material switching, full-result root-before-signing, direct/imported provenance, exact input/base/runtime/order, shared writer/access fencing and Storage durable linkage are unchanged.

DOCS_BODY_WORKER_ACK_RECEIPT.json records exact page/base hashes, preservation checks and all ten newly added scoped citations mapped to this reviewer's fresh pinned/tree/blob-verified source. Independent DELIVERY_ACK_CROSS_REVIEW and EXECUTION_WORKERS_CROSS_REVIEW bind their final report/delta hashes and actual MCP content checks. QMDB query-source validation belongs to the separate specialist review; this scoped review does not substitute for it.

No canonical page or foreign report was edited. No implementation, native build/tests, budget/backend/schema/policy choice or additional gate was created.
