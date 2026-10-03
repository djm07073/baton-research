# Independent source review — local acknowledgement handles

Reviewer `/root/reuse_network_v3`. Reviewed root delivery-ack REPORT SHA-256 `08ec5345f433483bb9aff0fe70c5dd3e12d18c2b89fdbd78bfdc93dd681f4d91` and READER_DELTA `6a2e0974eeebd77ac68a241c460c2642cbd5daf19a58f683e69e0f69f940e777`. **Pass; no material correction remains.** Scope is public API/document fit, not implementation, runtime ACK testing, durable completion proof, compilation or publication verification.

The public native Acknowledgement trait and reexport, consuming acknowledge, Exact handle/waiter pair and Future<Result<(),Canceled>> are source-correct. Exact Clone increments outstanding instances; dropping any unacknowledged instance irreversibly cancels the waiter; dropping the waiter has no handle cancellation hook. Exact counts local handles rather than validators/signatures and carries no OrderedRange, CommitResult, durable cursor, deadline, wire identity or restart state. The reader delta clearly makes the handle optional internal plumbing tied to the already-required immutable range/full durable result, not a new mandatory ACK mechanism or replacement for the adopted rich Orderer receipt.

Fresh Tempo sources show its private Executor Reporter enqueuing Marshal Update<Block>, FinalizedBlockRequest retaining Arc<Block> and Exact, and acknowledge_finalized draining requests covered by tracked finalized state before acknowledge consumes the token. The inspected restart/redelivery path checks canonical digest, and comments distinguish tracked state from an EL finalized marker that can lag after restart. The report appropriately does not import that height/engine predicate as Baton's durable-range invariant.

Native private PendingAck/PendingAcks bind height+commitment and run FIFO capacity/queue handling, but are pub(super). Fresh release Marshal dispatch waits for the archive dispatch durability gate before creating an acknowledgement pair. Its processed-height update explicitly buffers metadata and requires separate sync. Copying these patterns therefore does not establish atomic application state/output/cursor/provenance linkage, expose the private tracker, or make local ack completion durable by itself.

Optional Baton observations must not hold mandatory Exact clones: all-clone completion would otherwise grant optional telemetry a veto. The report and proposed paragraph preserve that boundary and leave cancellation pending/recoverable without cursor advancement. No report/direction/body ACK gate, native cut wait, quorum, default policy, trait/signature change or mandatory extra waiter was introduced.

## Independent receipts

Six new decisive primary files (native ACK/export/private tracker, release ACK, Tempo ingress/Executor) were freshly fetched and Git-blob matched against this reviewer's complete pinned wave-8 native/release/Tempo trees. Own already fresh release Marshal actor closes dispatch/durability evidence. `cross-review-source-manifest.json` records source hashes/blob IDs; `DELIVERY_ACK_CROSS_REVIEW_RECEIPT.json` maps all 11 report anchors to own files and exact lines.

The actual explicit v2026.9.0 MCP ACK response was independently compared with the fresh release source: all 82 numbered lines match, using zero-based MCP labels. Native/release ACK files are byte-identical for this helper; this does not unify their dependency graphs.

No canonical file or foreign report was edited.
