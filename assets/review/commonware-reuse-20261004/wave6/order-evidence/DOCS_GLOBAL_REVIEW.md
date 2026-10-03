# Wave 6 final global reader review

**Passed for the exact eight current page hashes below; no required correction remains.** Review baseline is `8b61492bbebdbf34dbc10e5d43c3117e19618377`. This is source/API and documentation review, not implemented/compiled integration, protocol or recovery testing, publication verification, or six-hour goal completion. I made no canonical edits.

| Canonical page | Reviewed SHA-256 |
|---|---|
| docs/consensus/block-body.md | `58e684e650355918c1e601ef9ee43a2ffe14600a50f8559d54ced5dfa8956491` |
| docs/consensus/ordered-input.md | `f760f5b05aae5f3000babdcf1e63a0d988bc72b454169b4434aec315544942d9` |
| docs/e2e/recovery.md | `b721fa48c1dfde23c18b8c2724b8bd238ad0af6391e510dd3ba9b0439d89f2a4` |
| docs/execution/interfaces.md | `68cddffcad9cb36b285ceb550245356bf3072a8d5aeb270c4e042be3623f41b4` |
| docs/execution/qmdb.md | `54e5c420980de25a2304a6208e8fd8302f251000e8d8972ce16edfc2b9e71435` |
| docs/execution/state-sync.md | `43d98720e4abfda32c1310fb22cbd191d813e1ca826ac6a054191ac3383205e8` |
| docs/overview/architecture.md | `1e9a61fc4830cef9ff5e70710416bfd9cc7c5411411e8548d443ba0bbbee41db` |
| docs/reference/integration.md | `0cfcc294617e815554166765ec92615a1ad69cdcbaee87c8e4eb4941048bf7ad` |

`global-cross-review/page-receipt.json` binds final page hashes, native-source receipts, preservation checks and the read-only checker output. The state-sync hash includes the final operation Codec/Send/Clone/'static and additional Source Sync amendment.

## Preserved structure and authority

Compared all 32 tracked docs Markdown pages against the baseline: every old heading remains in its original order, every old external URL occurrence remains, and every Rust/rust-ignore/Mermaid block is byte-identical. Canonical `rust-interfaces.md` is byte-identical and still declares exactly five traits: TxPool, Orderer, Baton, Executor, Storage. The generated Rust export is unchanged. All 56 tracked non-Markdown docs assets are byte-identical, including the 18 primary SVGs and Rust file forming the 19 published referenced assets. No diagram/schema/signature silently changes through the prose.

Read-only `python3 -B assets/tooling/check_docs.py --migration` passes: 31 content pages, 257 local links, 18 rendered diagrams, 39 preserved blank policy cells, zero failures. This validates documentation structure and linkage, not Baton/native runtime behavior.

The overview distinguishes reused primitives from new semantics without prescribing another actor for each green box. Tx/backend/static placement stays conditional. BlockService uses existing callbacks; Orderer owns exact input/delivery; Baton owns report/direction selection; Executor owns effects/tree/certification/sync control; Storage owns selected roots/canonical writer/durability/physical recovery. Exact order is delivered directly to Executor, result signatures/material travel Executor-to-Executor, and Baton does not gate certification/sync/apply. Native remains the adopted Multimmit pin `534af0ede48affd35b2111522527547b4cc9bf72`; Simplex/Stateful/Tempo remain assembly references.

The changes preserve fixed report closure, completed bounded candidate evaluation, original-report prefix support, cut no-wait, authenticated protected-prefix interpretation, and unresolved native adoption/continuation proofs. They add no direction/reports/Executor-readiness approval quorum. Local native startup, storage sync and proof-validation waits remain distinct from native cut/report waits.

## Fresh checks of introduced claims

Fetched 27 primary source files and three fresh complete, non-truncated Git trees. All raw source bytes match their tree Git blob identities. The unauthenticated tree API rate limit was handled using the existing authenticated `gh api`; no credential/configuration changes were made. Checked all 28 newly introduced source anchors against these exact files. Sources/trees/hash receipts are under `global-cross-review/`.

### Tempo block propagation paragraph

Confirmed the complete connection, not merely available crate names:

- Tempo's concrete Marshaled enum selects Commonware Deferred/Inline, and its Relay impl forwards to that selected wrapper. Its engine constructs an independent buffered broadcast Engine/mailbox, passes the mailbox into Marshal, and starts broadcast on its body channel while Executor starts separately.
- Shared standard Relay consumes the staged proposed block and calls Marshal `proposed`; absent staged data or a forward plan uses Marshal's forwarding path.
- Marshal's Proposed/Forward handlers invoke `buffer.send`. Standard's buffer implementation delegates to public `buffered::Mailbox::broadcast_shared`, after which the existing broadcast Engine sends on its channel.
- Tempo's fresh Cargo.lock resolves commonware-consensus/commonware-broadcast to registry `2026.9.0`; the cited Commonware `d476a236...` workspace version is `2026.9.0`. This substantiates the version-labeled reference path, without declaring registry/native package identities interchangeable or compiling an assembly.

The paragraph accurately locates body propagation in the consensus attachment and proposes native Multimmit's distinct `Relay::broadcast(digest, ())` retained-body connection. Existing custody paragraphs still require exact context and real covering durability; the new paragraph does not treat broadcast feedback or the staged proposal path as native durable custody, nor copy Simplex Relay/Marshal unchanged.

### Metadata and canonical completion

Confirmed Metadata's public put/sync/put_sync/start_sync signatures and underlying completion ownership. It atomically updates that metadata store's pending map; put_sync includes all pending changes. Versioned two-copy/CRC recovery is existing code. Start_sync retains a shared pending completion; the next sync waits and propagates its failure before writing, so dropping the observer does not cancel persistence or erase a failure. Current prose scopes this guarantee to Metadata and explicitly excludes a transaction spanning QMDB plus output journal.

QMDB DatabaseSet finalize/Barrier is selected-state apply/flush coordination, not tuple-wide state/output/cursor atomicity. Append alone is not commit. Storage continues to own exact recovered record identity, outputs/provenance/cursor linkage and physical retention; no separate WAL/cursor transaction engine, record encoding, recovery ordering or GC policy is silently selected.

### Repeated sync and result transport

Confirmed public qmdb::sync::sync(Config) returns a reconstructed DB and StateSyncDb::sync_db delegates publicly without requiring Application. StateSyncSet remains one-time bootstrap coordination. Config uses DB configuration/Source rather than a live DB handle, supports optional update/finish/reached channels, and continuing sessions do not yield a usable DB per progress event.

Reached-target notification precedes journal sync, reconstruction, root checking and persistence. The prose correctly forbids stop/usable-state/delivery ACK on that notification. Reopening configured partitions can mutate/prune/rewind them; concurrent candidate ownership and exclusive writer fencing remain application work, not assumed Rust-handle isolation. Current's retained lower range must respect sync_boundary and operation-versus-canonical root binding remains explicit.

Final adapter amendment is source-correct: P2P Actor requires `Op<DB>: Codec<Cfg=()> + Send + Clone + 'static`; Source mailbox additionally requires Sync. Actor DB/Shared/Family bounds remain the linked recipe's conditions. Numeric operation requests omit trusted root/execution identity, attach_database only enqueues, and local proof feedback cannot be delayed through result collection or canonical apply.

My independent result-transport review separately fresh-checked 41 files/2 trees and confirms typed decode is not signature validation, buffered cache stores one object per artifact digest, and Collector counts requested transport peers before Monitor's application validation. All three caveats are retained beside the new interface table. Executor still enforces exact statement, irrevocable order/canonical base/runtime, f+1 eligible distinct original signers, applicable material and direct/imported provenance before abandoning direct work. Imported material does not produce an own DirectExecuted signature for the same range. No new ResultService actor or crypto quorum choice appears.

### Native witness and recovery connection

Fresh native checks confirm the new ordered-input/recovery statements: durable safety state contains selected artifacts/floors/outbox, not every remote vote/direct-pool source revision; ordering payload is empty; replay clears newly-ready admissions. Native serve is useful retained view evidence, possibly covering L-QC, not exact archival source identity. Checkpoint/view compaction does not consult Executor's applied receipt. Native reads alone cannot recover external dense delivery history. Existing Journal/Archive/Metadata/resolver can host the narrow handoff; placement, retention and private extraction access remain development work. Included/empty/unresolved slot semantics and authenticated policy interpretation remain unchanged.

## Remaining risks and limits

No blocked editorial correction remains. The following integration obligations remain explicitly open in the reviewed text:

- Native direction-preserving proposal/adoption/continuation proof and recoverable exact selected-source export, including retirement/export lag and lossless bounded handoff.
- Selected root/DB variant, operation-versus-result/output identity, codec/key/domain/budget choices and compatible authenticated sync-target/session identity.
- Candidate storage isolation or fenced exclusive handoff, exact verified import switching, direct/imported recovery provenance and canonical writer authority.
- State/output/cursor/metadata crash linkage across selected stores and physical material retention; primitive local atomicity/transport acceptance is insufficient.

Root publication must verify the generated site/GitBook/GitHub independently. This report approves only the eight bound source-page hashes and unchanged assets; it does not infer publication success or six-hour completion.
