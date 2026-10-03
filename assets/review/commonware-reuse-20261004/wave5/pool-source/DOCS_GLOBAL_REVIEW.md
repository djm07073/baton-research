# Final wave 5 global reader/API review

**Pass for the current eight-page documentation delta. No blocking reader or source corrections were found.** The changes make existing primitive reuse more concrete without adding another public module, generic scheduler, pool, database, broadcast or fetch engine. This is a documentation/source audit, not a compiled integration, custody/adoption proof, benchmark, production assessment or completion of the six-hour research goal.

Reviewer: `/root/reuse_orderer_v3`. Baseline: `b5747f6a28527a4507901f2e46b426b5ff2a4b7c`. Canonical pages were read without modification. Current page hashes, source-citation receipts and exact preservation checks are bound in [global-page-receipt.json](global-page-receipt.json).

## Evidence and independent inspection

Read the wave5 pool-source, body-storage, branch-access and baton-tasks reports plus the independent body/branch, Baton task, pool and execution/Baton page cross-reviews. The current pool report includes the final hydration/admission/TTL amendment; its earlier cross-review's final amendment check binds the updated report.

The current body report had already been independently checked by this reviewer against 28 newly fetched pinned files/four fresh trees and all 46 report anchors. For this global review, **13 additional decisive files** were freshly retrieved against fresh native, Kora and Constantinople trees: concrete Any access/raw batches/ancestry, runtime placement, future pools, native parallel strategies, both exported macro documentation and implementation, Kora keyed conversion, Constantinople compute/finalizer. All Git blobs match their own fresh tree. The previously independently verified SDK files remain the decisive evidence for localized payload imports, private kernel, existing ingress/mailbox and TTL behavior. No previous report inventory was used as a substitute for reading these source implementations.

All 18 source citations added by the canonical diff were matched to this reviewer's source snapshots and checked at their anchored line. Additional implementation reads checked the actual behavior behind the anchors. Receipts: [global-review-source-receipts.json](global-review-source-receipts.json), [body-review-receipts.json](body-review-receipts.json), [source-manifest.json](source-manifest.json), and global-page-receipt.json.

## Reader/API assessment

| Area | Result and preserved boundary |
|---|---|
| Body storage/fetch | The new table correctly separates ordinary Archive lookup, prunable-only MultiArchive and covering sync. get_all is unbounded by its signature; same-key ambiguity and full-key collision checks are accurate. One application attachment owner coordinates borrowed get with consuming mutations. Producer clones its request handle, not Archive. Existing text still disclaims copying private Simplex Marshal unchanged; no ready native Multimmit body actor is invented. |
| Body custody/lifecycle | Exact authenticated header→context/commitment→retained bytes and required parent-header lookup remain necessary. has_at, digest hit, put success, local Relay feedback and fetch completion do not become custody. Error/cancellation and retention remain distinct. Producer admission is required because generic serving futures are unbounded; no budget/drop policy is chosen. No new full-body/report/direction ACK barrier appears. |
| Whole selected pool | Nunchi remains a conditional SHA-256/u64 nonce-lane source candidate, with two unselected payload/dependency routes. SDK tx imports are localized, but export/manifests/features and native package identities still need maintained adaptation. Existing actor/kernel/Message/handles carry any selected source-aware ingress and processed canonical readiness. No second dispatcher/reconciler/pool or SDK chain builder is introduced. |
| Static hooks and packing | Features/Decision remain payload-only. Maintained pool nonce state is separate from static analysis. Both local/peer ingress need any selected admission hooks; packing-only filtering may use current pending candidates. Stable selected encoding/digest matters despite Clone/Send/Sync. Existing dependency-aware byte packing and canonical duplicate-execution semantics remain open and preserved. |
| Canonical pool completion/restart | Existing lossy finalized notification is still not processed-success evidence. Proposed reliable same-owner responder has exact context/range/replay readiness and does not become a native cut/direction gate. Unknown-zero is not authoritative. The new hydration caveat is correct: finalize can advance height/run TTL and expire pre-hydration entries; admission/hydration ordering and lifetime semantics remain unselected. |
| Deferred-root batch access | Native public plain Any reads resolve own write map before sealed ancestors/applied DB. Replay into independent existing drafts at one actually valid anchor is correctly conditional and does not claim unsealed-parent fork, Clone/private mutation extraction or historical rewind. Base-bound keyed conversion, normalization, writer/read fencing and retained outputs/direct evidence remain required. |
| Executor/Storage boundary | Executor owns execution tree/input choice and certification/sync control; Storage supplies branch access, selected hashing and canonical apply/durability/retention. ExecutionResult may internally own a one-shot existing draft or staged handle plus completed updates. Neither source handoff forces full glue Application nor removes root-before-signing. Replay/overlay stay alternatives, not selected schema/root/checkpoint policy. |
| Actual-chain handoff | Constantinople compute returns staged handle plus Option<StateUpdates>; separate helper seals state/history. Kora conversion reads account generation, so exact base matters. Current prose keeps their dependency graphs/source shapes separate from native-compatible types and refuses crash-atomic state/output/cursor or rootless-fork claims. |
| Baton deadline/admission | A verified completion enters only after the matching owner admits it before once-only closure. Fixed deadline does not slide; first processed `4f+1` distinct valid admissions or deadline closes the snapshot, excess/late completions remain excluded. Packet observation, worker completion and Feedback are not verified admission. |
| Evaluation/cut independence | Existing Clock, task placement, unordered future pools and Strategy provide mechanisms, not policy or capacity bounds. Sequential/one-thread Rayon may execute before returning; pool-member polling may run CPU inline. Task-body placement remains required. Dropping future/abort is not CPU/signing/storage quiescence. Cut continues from an already prepared valid candidate or actual-parent base and does not wait for report window/evaluation/capacity/direction replies. |
| Direction/proof scope | Current entire-prefix `2f+1` original-report support and raw sum-LCP fallback are intact. Fixed bounded candidate-set evaluation must finish before prepared selection. Honest intentions remain distinct from executed work/reuse. Authenticated adopted-prefix preservation, native sufficiency/continuation and recovery remain unimplemented/unproved; no policy lock or fallback after adoption is introduced. |
| Result finalization/provenance | Irrevocable exact order plus f+1 matching distinct eligible direct-execution/validation signatures remains required; material availability/durable readiness are separate. Storage computes result commitment before signing. ImportedVerified does not become own DirectExecuted; Executors exchange result/sync data directly and retain common writer/fencing/recovery obligations. Baton has no certification/sync/apply gate. |
| Native dependency graph | Native pin stays `534af0ede48affd35b2111522527547b4cc9bf72`. Existing package-identity/version constructor checklist is preserved. New source adaptation prose does not upgrade dependencies, claim a successful build or treat same names/hash bytes as equal Rust package types. |

## Exact preservation checks

Compared all 32 baseline Markdown files (31 content pages plus SUMMARY) to the current tree, not only the changed pages:

- Eight Markdown pages changed; every prior heading and explicit existing-library excerpt remained identical.
- Every prior external citation occurrence remains present, including repeated occurrences; added source citations have valid source locations.
- All application `rust` blocks are byte-identical. Exactly five public traits remain **TxPool, Orderer, Baton, Executor, Storage**; no declared method/signature or comment inside those declarations changed.
- `docs/assets/interfaces/baton.rs` is byte-identical to baseline and matches canonical Rust extraction. No generated interface edit is needed.
- All Mermaid source fences and all 55 tracked diagram assets remain identical to baseline; the existing 18 rendered diagrams are preserved.
- Exactly 39 policy decision cells remain blank, zero filled. Their policy choices were not adopted through prose.

Read-only `python3 -B assets/tooling/check_docs.py --migration` passed: 31 content pages, 251 local links, 18 rendered diagrams, 39 blank policy cells, zero failures. This checks documentation/navigation/export/diagram/migration consistency; it does not run the Baton protocol. No compilation, dependency change, native tests, benchmark or canonical modification was performed by this reviewer.

## Current reviewed page snapshot

| Page | SHA-256 |
|---|---|
| `docs/baton/README.md` | `c768b51940aa34448747592ec120dc2da4be226243acc708c7c04ea3b89b92bd` |
| `docs/baton/direction.md` | `d723b6bcd87cc960e02dd88109eaee50aeafbb8b54b9f0e1814a2ebc13afed97` |
| `docs/consensus/block-body.md` | `240343de16701934f3210d861356cb8882c4c4b3ac8cacb9a6bbac2e9527d192` |
| `docs/execution/qmdb.md` | `e6aa69292bf74d459d856a0c485a165f2333b7a327489445e169d2520d6b306e` |
| `docs/overview/rust-interfaces.md` | `20fee85bb12a433ca4a42f66084b6a0a6fdfef0f4faf6f7c7f3a74c1073c5d36` |
| `docs/reference/integration.md` | `754d6c0b411de8549eefc6a8242eca843a9deb981cdd4fb9f5269734c0ad6295` |
| `docs/tx/README.md` | `7d1b4d26320b1c487b03437b8123923040b6c0f8713eee43f27f11f52cf555ff` |
| `docs/tx/interfaces.md` | `64c74f0663712717cb12947addd329949b2d3636a7e19f87c5a99016c1a79a52` |

These hashes define the reviewed snapshot. Publication verification and any subsequent reader edits remain root-owned; a later page change requires refreshing its review binding.
