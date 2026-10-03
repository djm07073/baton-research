# Current execution/Baton reader-page review

Reviewer `/root/reuse_storage_types_v3`. Baseline `b5747f6a28527a4507901f2e46b426b5ff2a4b7c`; four current uncommitted pages reviewed below against the wave5 [branch report](REPORT.md), [noncompiled sketch](assembly-sketch.rs.txt) and baton-tasks report. Native source pin stays `534af0ede48affd35b2111522527547b4cc9bf72`. No canonical edits, policy/variant/backend selection, compilation, implementation or native protocol tests.

## Outcome

**Scoped source/API fit passes; no blocking corrections needed.** The new text accurately labels rootless replay as a conditional application materialization candidate, uses actual plain/staged batch visibility, preserves internal Executor→Storage ownership, and explains why a future-returning Strategy does not establish responsive scheduling or CPU cancellation. It does not claim native prefix adoption, bounded runnable scheduling or safe storage/signing handoff has been implemented/proved.

| Area | Independent source check and assessment |
|---|---|
| Plain drafts observe writes | Native Any Unmerkleized write at batch.rs L1306 records last-writer-wins mutations; get/get_many L1766–1816 resolves mutations before sealed ancestors/applied DB. Current batch L362–403 delegates equivalent behavior. Reader prose correctly uses concrete methods rather than inventing generic keyed methods on Unmerkleized trait. |
| Staged read visibility | Native Any/Current wrappers expand docs and implementation at any.rs L238–280/current.rs L241–283 preserve appended indices and do not observe caller-held computed updates before sealing. The new plain-versus-staged explanation does not treat staged as a mutable rootless overlay. |
| Rootless siblings | Native unsealed map and Base/into_parts are private; sealed new_batch at Any batch L2603 and applied new_batch L2704 supply actual anchors. Reader replay retains Storage-ready exact-prefix mutations, independent existing drafts, valid anchor access, normalization and fencing; it does not call unsealed fork or assume clone/extraction. |
| Root, base and history limits | Replay is explicitly base-bound; new applied batch cannot rewind sibling-advanced storage. Flattened mutations need not preserve separately sealed operations roots. Exact outputs/direct work remain separate. No backend, checkpoint frequency, root type or equality guarantee is selected. |
| Internal batch handoff | Existing concrete unsealed handle or AnyStaged plus indexed updates can be carried internally by ExecutionResult; Storage consumes/merkleizes selected work. Constantinople compute L160–189 returns actual staged handle plus Option<StateUpdates>; db helper L116–144 seals later. Kora keyed conversion L266 reads current generation. Pages correctly distinguish source examples/version graphs from a ready native adapter or crash transaction. |
| Generic/public bounds | Reader links retain the existing concrete-wrapper constraints and tuple sealing limits. ExecutionResult is Send and one-shot; PreparedResult can retain cloneable sealed material plus binding. Storage::read remains canonical query, not pending-parent access. No new public trait/method or dependency on glue Application appears. |
| Deadline/completion owner | Native Clock supplies sleep_until; futures Pool/AbortablePool has unordered FuturesUnordered storage with no capacity setting. Verification completion becomes snapshot admission only after owner context/identity checks before closure. README/direction preserve fixed once-only deadline and exclusion after closure. |
| Synchronous strategy cases | Independently fresh parallel source: Sequential L795–807 invokes f before returning; Rayon L1020–1059 invokes f immediately for <=1 thread and can run pool work inline while polling. Reader says chosen background placement is needed; it does not claim async-returning spawn alone moves compute away from cut. |
| Dropped future/abort limits | Rayon submits closure separately, discarding tx.send failure if receiver is gone. Native Handle abort only signals its task/completion AbortHandle. Dropping polling future does not preempt already submitted CPU work. Pages correctly retain correlated stale-result rejection and storage/signing quiescence caveat. |
| Event ordering/feedback | Newly fetched macros impl L510–541 emits biased tokio select; select_loop L735–755 uses that macro with shutdown first. Actor Feedback L13–29 describes submission/overflow status. Reader does not turn branch ordering into network arrival ordering or accepted feedback into verified admission/result/direction approval. |
| No-wait/adoption | Current direction page still publishes Some only after bounded admissible full-set evaluation is complete; cut never awaits window/timer/optimizer. f+1 honest intentions do not prove work or native inclusion. Pre-adoption actual-parent fallback stays distinct from preserving authenticated protected prefix; adoption/continuation remain open. |

There are no required reader corrections within this snapshot. “Appropriately placed background task” remains a requirement, not a verified runtime deployment or finite-latency guarantee: supported placement, fairness/budgets and application correlation must still be implemented. Similarly, replay describes a possible access/materialization route, not a selected rootless tree algorithm.

## Exact preservation checks

A source-only comparison confirms all canonical `rust` declaration blocks are byte-identical to baseline; exactly five public traits remain TxPool, Orderer, Baton, Executor, Storage. The current documentation still has39 blank policy cells and zero filled cells under the repository's policy-table counting rule. No interface export/diagram edit was performed by this reviewer. [Page/check receipt](execution-baton-page-receipt.json).

All9 source links introduced in this four-page diff have this role's independently fetched source receipts and valid line anchors. [Citation check](execution-baton-citation-checks.json). This validates citation locations/source correspondence, not compiled integration or protocol correctness.

## Current page snapshot

| Canonical page | SHA-256 |
|---|---|
| `docs/execution/qmdb.md` | `e6aa69292bf74d459d856a0c485a165f2333b7a327489445e169d2520d6b306e` |
| `docs/overview/rust-interfaces.md` | `20fee85bb12a433ca4a42f66084b6a0a6fdfef0f4faf6f7c7f3a74c1073c5d36` |
| `docs/baton/README.md` | `c768b51940aa34448747592ec120dc2da4be226243acc708c7c04ea3b89b92bd` |
| `docs/baton/direction.md` | `d723b6bcd87cc960e02dd88109eaee50aeafbb8b54b9f0e1814a2ebc13afed97` |

## New independent native receipts

Seven additional runtime/parallel/owner/macro files were freshly fetched for this review and tree/blob verified. Earlier wave5 batch and application receipts were already inspected directly; all receipts remain in [source-manifest.json](source-manifest.json). Paths below are under sources/native/.

| Native source path | SHA-256 | Git blob |
|---|---|---|
| `parallel/src/lib.rs` | `52a45191faa76acaf0cf724eb04804390fd57b9743435c7de6e82898447c213b` | `9780db47130f3814e28e632cbb00d7d530e6a91d` |
| `utils/src/futures.rs` | `782f2ff116c7e25b4472ba4b7fa5145c08d6bc4711426a47d55900c9e3fed973` | `69dc2efc6541d8242911c54be0509b0a7116e0de` |
| `actor/src/lib.rs` | `e05f4194eeee88127882ec1c239a339c3265fe8506c48feccd61a20a2551b137` | `3195779ab3c1888f2464e860f3155ea68a961211` |
| `runtime/src/utils/handle.rs` | `cbe48ac3f8ae7a9bb9b297c226431d36191f4c6b03a563e35bb624d672a2171e` | `efd0782b46d254a82f94edc11d6ed2d4ce137ddf` |
| `runtime/src/tokio/runtime.rs` | `855b836b353b553a0bc24389abe850a985ebcd76cb960b6fedbf5e3d2508c192` | `2defd7d93966c22ea4b6c9c22661c11210da7f80` |
| `consensus/src/multimmit/actors/voter/executor.rs` | `780e2723d917711ef7800a20de1aadd79048d32904ce38bcf2463994115aacea` | `4e38fbb0b91c9368906ff40a01b39734630720ec` |
| `macros/impl/src/lib.rs` | `ae1d77b4575d18b96b382fe31ed9c9e0eeadd231f82a944f955c0044d7e7dcbf` | `30e1333e0a2e6748f1a8bb00d66f209ed910cdd0` |

The native macro implementation, not only exported API documentation, was inspected for biased branch ordering. Other pages still being drafted are outside this snapshot review.
