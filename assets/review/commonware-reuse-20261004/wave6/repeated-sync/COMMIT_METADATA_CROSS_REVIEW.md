# Independent wave 6 commit Metadata and overview cross-review

Reviewer: `/root/reuse_storage_types_v3`.

| Reviewed target | SHA-256 |
|---|---|
| `wave6/commit-metadata/REPORT.md` | `9ea6eb545de885145784a937b9d9d7c53d37d635a7f8b0bf0bc06249d5175740` |
| `docs/overview/architecture.md` | `1e9a61fc4830cef9ff5e70710416bfd9cc7c5411411e8548d443ba0bbbee41db` |

**Pass for scoped source/API fit and the overview's six-row responsibility table. No blocking correction required.** Source review does not confirm compiled integration, an implemented application commit protocol, atomic cross-store switching or execution safety. No canonical edit was made.

Fresh files and pinned complete-tree verification are recorded in `cross-review-source-manifest.json`; snapshots/hashes in `cross-review-target-receipt.json`. The additional tree fetches hit GitHub 403 rate limits, so complete trees previously independently fetched by this reviewer were used with explicit receipts; all 48 freshly retrieved raw-file Git blobs matched. No claim of fresh tree retrieval or runtime test is made.

## Existing storage mechanisms

1. **Metadata atomicity is local.** The actual two-blob version/checksum format and alternating durable copy are in native `metadata/mod.rs` L1–35. Public Metadata has `K: Span`, `V: Codec` and consuming mutation semantics (`metadata/storage.rs` L616 onward). `put` is pending; `put_sync` commits all pending metadata changes, and `sync` atomically commits this map (L683–698, L742–746). None spans QMDB state, an output journal, cursor store or imported provenance in another store. CRC32 detects corruption/partial writes; it is not authenticated consensus/execution evidence. The report states those limits correctly.
2. **`init_bounded` is startup allocation protection, not a future mutation budget.** Its exact bounded initialization signature is L647–659; malformed/oversized copies can be discarded. Recovering an empty metadata map does not prove no prior application commit existed. The report preserves external consistency/retention/budget choices and does not select reset semantics.
3. **Pipelined Metadata flush retains its completion.** `start_sync` L748–761 consumes/returns the store and observer handle. Actual `record_pending` L599–607 converts the blob sync to a shared completion, keeps one clone internally and returns a separate observer; `wait_for_pending` L382–405 must observe prior failure before a new write. Dropping the observer alone does not cancel or discard the internally retained completion. This is not rollback on cancellation of a consuming store mutation.
4. **DBSet has per-member writers, not one transaction.** Tuple finalize (`glue/stateful/db/mod.rs` L998–1016) joins individual `finalize_shared_or_panic` calls. That helper takes each Shared by-value slot, finalizes, then puts the DB back (L1802–1811). `finalize_or_panic` deliberately treats failure as fatal because other members may already have applied (L1783–1800). No tuple-wide rollback/state-output-cursor transaction is created by this join.
5. **Barrier covers its actual handles.** L425–495 records one member flush and waits; Closed/Aborted yield false, other deferred errors panic. An empty manually constructed barrier is immediately durable. Thus successful Barrier resolution establishes only its represented flushes; the report correctly calls these “retained” flushes and separately requires exact application linkage before ACK. It does not claim arbitrary Metadata/outputs are covered automatically.
6. **Journal replay reuses storage, not semantics.** The public variable Journal and Contiguous read/replay implementation provide owned append/read/replay/sync machinery with consuming error/cancellation behavior. Append alone is neither a durable application commit nor provenance validation. A selected record schema and recovery/retention remain application responsibilities; no new generic WAL/cursor engine is made mandatory.
7. **ACK example is correctly limited.** Native glue processing L307 onward drives finalization, places the barrier on the completion pool and acknowledges after durable completion; false leaves it unacknowledged for restart. It is a useful existing future-pool/flush/ACK composition, not a ready Multimmit external cursor or reason to depend on full Stateful Application.
8. **Chain references match source.** Constantinople's Shared Any state plus compact keyless transaction-history tuple is real, but transaction digests do not imply full Baton outputs/cursor/provenance. Kora `apply_batches` sequentially writes accounts/storage/code with commit sequence sentinels (`store.rs` L334 onward); `QmdbHandle::commit`'s “atomic” comment (L138) does not turn this into crash-atomic rollback. The report correctly rejects that stronger wording.

The report's reuse direction is sound: let one existing Storage owner connect QMDB roots/apply/flush and selected Metadata/journal/history records; use the upstream mechanisms instead of rebuilding checksums/two-copy persistence/replay. The required application encoding, linked identity, canonical writer generation, recovery consistency and retention cannot be omitted. No storage placement, ordering rule, schema, numeric budget or public trait is selected.

## Architecture six-row table

The reviewed Role/Reuse/Write table has exactly TxPool, logical BlockService, Orderer, Baton, Executor and Storage. It describes six logical responsibilities rather than six new public traits or mandatory actors. Existing public interfaces remain five, with body work through upstream callbacks.

- TxPool keeps backend choice and canonical outcome/payload hooks open.
- BlockService reuses buffer/resolver/archive while retaining exact body/header/context and custody integration.
- Orderer reuses native verification and fitting existing stores, with exact recoverable witness handoff/delivery in its application column.
- Baton reuses clock/tasks/future pools/optional Strategy; scoring/admission/context remain its semantics. No second scheduler or result-finalization gate is implied.
- Executor reuses runtime/crypto/P2P and keeps computation/tree/result verification/peer-sync control.
- Storage reuses native batches and glue Shared/DBSet/Barrier plus selected metadata/journal, with selected roots/authorized writer/recoverable linkage. `Shared/DatabaseSet/Barrier` are glue storage wrappers, not a requirement to use full Stateful Application.

The adjacent explanation correctly says colors mark responsibilities/integration boundaries and green roles still reuse infrastructure. Blue reuse does not promise ready Baton integration; orange does not prescribe editing primitive algorithms. Direct Orderer→Executor canonical delivery, Executor↔Executor result/sync path and Storage's root/apply/durability remain intact. No factual source-scope or role-ownership correction is needed for the table.

## Tree-fetch follow-up

After the initial unauthenticated GitHub tree API rate limit, fresh authenticated `gh api` GET requests succeeded for all five exact pinned repositories. `authenticated-tree-receipts.json` records complete nontruncated trees and zero fresh-file blob mismatches. Earlier failure/fallback receipts remain preserved; final source identity checks now also have fresh complete trees. No credentials were modified.
