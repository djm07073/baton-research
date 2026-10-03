# Wave 2: independent execution, Storage and state-sync source review

Review scope: current execution pages, canonical Rust interfaces, integration page and state-sync/result E2E pages. Canonical checkout: `/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research`. This reviewer read AGENTS.md, README.md, BATON_HANDOFF.md, baton-paper.md, docs/README.md and docs/SUMMARY.md before reviewing. The latest Executor/Storage split is authoritative. First-wave review was used only to identify leads; fresh upstream raw files were fetched and read independently.

## Verdict and correction requirements

The reviewed documentation implements the latest responsibility split correctly: Executor emits completed changes without compulsory hashing; Storage prepares selected commitments and performs canonical application/durability; Executor retains execution paths, certification and peer switching. No dependency on `stateful::Application` or the complete Stateful actor is required. I found no current safety-contract regression in the split, signing provenance, clone-wide access fence, native/release lifecycle distinction or durable ACK boundary.

The reuse investigation is incomplete in three concrete places. These are documentation/source-mapping corrections, not reasons to select a database variant, adopt a new codec or implement the protocol.

1. **Document the verified native-pin sync APIs directly.** The reviewed `docs/execution/state-sync.md` frames `qmdb::sync::Source` and DB P2P as indexed-release candidates needing existence/compatibility checking at the pin. That check is now complete for the actual files below. Source, Target, Engine, the sync entrypoint, collector traits and P2P mailbox already exist at the native pin; several files are byte-identical to v2026.9.0. Add native-pin citations and a concrete handle recipe. Retain the distinct database lifecycle recipes, since their apply/finalize interfaces materially differ. Do not infer whole-release compatibility from these equal files.
2. **Use the existing Current root witness if Current is selected.** The docs correctly distinguish `ops_root` from canonical `root`, but omit native `current::proof::OpsRootWitness` and `Db::ops_root_witness`. These already supply the commitment-link check; avoid presenting that hash/proof algorithm as new Storage work. Storage still must bind its authorized certificate subject, root kind, range, base and reconstructed result; the witness does not verify execution or native order. Root/variant policy stays blank.
3. **Make caller-owned same-history validation explicit for target updates.** `Target::advances` tests numeric range advance only: valid increasing end, nondecreasing start. It assumes both targets belong to the same append-only database. Engine rejects an advancing target with unchanged root, but does not itself authenticate a cross-target history-extension proof. Executor/Storage must establish the same history before submitting target updates. The current sentence “requires strictly advancing targets on the same history” is correct as a requirement; add that the history condition is caller-established, not checked by `advances`.

A normal-path recipe should also state explicitly that `qmdb::sync::sync` and `StateSyncDb::sync_db` produce/open an initialized database from configuration, rather than accepting the active DB and applying an arbitrary execution delta in place. The current pages already leave the active fence/swap contract open, so this is precision for the new assembly section, not an observed contradictory claim.

## Fresh source receipts and review identity

[Source manifest](source-manifest.json) records URL, HTTP status, content type, byte count and SHA-256 for each fetch. [Source comparison](source-comparison.json) records exact pin/release byte comparisons; nonidentical files have full diffs under `diffs/`. Raw Rust is saved under `sources/pin/` and `sources/release/`. This review fetched 56 valid files, with 27 pin/release comparisons. Six failed guesses are retained as HTTP 404 entries and are not source evidence: `glue/src/stateful/actor/initializing.rs`, `storage/src/qmdb/any/sync.rs`, and `storage/src/qmdb/current/sync.rs` at each revision. The verified variant sync paths use `sync/mod.rs`. [Native tree receipt](native-tree.json) confirms those paths.

The [document manifest](doc-manifest.json) identifies the exact reviewed document snapshots and hashes, captured at 2026-10-03T20:09:41Z under `reviewed-docs/`. Concurrent canonical edits may supersede those hashes; this report does not claim to approve files that were subsequently changed. Key reviewed files:

| File | SHA-256 |
|---|---|
| docs/execution/README.md | `3afb5cefa76bce0348e2b00ae71609cfe863bc69277391cd9f979b00c1834ae9` |
| docs/execution/interfaces.md | `fe1f8acd4293054c1a9db93d33ce223a794c53579db2249dc7cdbb37daec217c` |
| docs/execution/qmdb.md | `080a4cae4248d42e33dd81125b249fa72fd82b840c48871d313b84a9f2e6a14e` |
| docs/execution/state-sync.md | `80effd5de813f5db4c77caed4f2f5116881edee59c7fc0d27d4a030ddb88d530` |
| docs/e2e/state-sync.md | `9b5dee130a7b6fe17734c4f56fde070fe408e7cd969615507333195921b6b799` |
| docs/overview/rust-interfaces.md | `8013382ce85dc94b6d85805751cbcbd3dc4304cd8cf2ac8774a5e4698b8990e8` |
| docs/reference/integration.md | `a6e5ae6fe29cece60e5324c44e5cf4a5ba73f7238fac52c0ee414e99433a2fd3` |

Selected fresh upstream hashes demonstrate the important version boundaries; the manifest contains every file's hash.

| Source path | Native pin SHA-256 | Release relation |
|---|---|---|
| glue/src/stateful/db/mod.rs | `36036c705fc5e2b78cf3bae2bed816d25481f612f624ef93abfac1b3c4a39201` | Different: release `96b0964a2bea28fc0ec9fd6edfd98d25b8c6fd58d1dda3b87950113bcf2315ba` |
| storage/src/qmdb/any/batch.rs | `35b1c70f82cf9f0de607f13908b272b15c6f5aed6b1e06491c6b7ac51ff0d582` | Different: release `11e318f5051c85a3ef54a28268a79b960fca64d4c4e5f2da83ac63422fa10d66` |
| storage/src/qmdb/batch_chain.rs | `9bdef186ced67babc192061569e35a52df9c41e994a5f3a173aa31b8926f95ee` | Identical |
| storage/src/qmdb/sync/source.rs | `fe614d2a6b2e5d5a707a3fcc2c957a622ee8ed1dfb881190e509ce91a292864a` | Identical |
| storage/src/qmdb/sync/target.rs | `b21baf4decdb8a0a9f348ff67c4460f70ea858c02122223449929e505997ac11` | Identical |
| storage/src/qmdb/sync/engine.rs | `73f439f8a10f7bc5915367487066dd86804918ae354887de225f456f981bae36` | Identical |
| glue/src/stateful/db/p2p/mailbox.rs | `da939538c1c575178b5596ba10e657fe1cb993f921dffc39bf19ad841b5bb0dc` | Identical |
| collector/src/lib.rs | `762fd749f69e34f26acecd39db354fbd292faaa66cc6e0710e28fa5c9936fd81` | Identical |

Native source pin remains `534af0ede48affd35b2111522527547b4cc9bf72`; indexed comparison is `v2026.9.0`. No branch head or homepage HTML substitutes for either.

## Execution changes and root-deferred preparation

Native [DatabaseSet::fork_batches](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L552) accepts `&Self::Merkleized`. Native Any [Base::Child](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L202) retains `Arc<MerkleizedBatch>`. No reviewed generic rootless-parent fork exists.

Direct supported path: create an applied-base unmerkleized batch, perform concrete keyed reads/writes, continue computing in that one attempt, and merkleize only when the selected boundary needs a commitment. Native Any [write/get/get_many/stage](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L1306) supports this. It does not supply a retained rootless tree with independently extractable AB and ABC checkpoints. That optional effect/read adapter stays application integration.

Native [stage/expand](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L1351) retains resolution/index information, does not deduplicate earlier staged keys, and cannot read values the caller merely computed for earlier staged slots. An execution overlay supplies such read-your-writes. Updates and upserts have ordering semantics; upserts applied last may overwrite staged updates. The docs correctly preserve these conditions and distinguish deferral from operation-history coalescing.

The selected result commitment must exist before signing. Hashing each abandoned speculative attempt is unnecessary. Storage's exact-prefix preparation cannot apply a longer sealed ABC batch and hide C to commit AB; retaining AB effects or reexecuting AB is required. An introduced AB storage commitment does not automatically preserve old sealed ABC ancestry. Native [batch-chain applicability](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/batch_chain.rs#L188) requires the current operation size/root to match recorded DB state or an actual ancestor, plus valid commit floors. Equal logical values are insufficient. These limits are correctly reflected in qmdb.md.

## Canonical access and durability

| Boundary | Verified native behavior | Reviewed documentation |
|---|---|---|
| Native application | `DatabaseSet::finalize(batches)` applies and returns Barrier; concrete `ManagedDb::finalize(self,batch)` applies and starts sync | Correct |
| Release application | `apply(batch)` then parameterless `finalize()`; later apply while returned Barrier waits is allowed, but dirty suffix needs later finalize | Correct separate recipe |
| Release sequencing | Observe previous barrier before next finalize; no overlap of apply/finalize/prune/rewind call bodies | Correct |
| Native prune | Barriers through target resolve; later-state barriers may remain pending, and prune coordinates with their writes | Correct distinction from release |
| Durable completion | Barrier true observes all captured flushes; Closed/Aborted yields false; other errors panic after DB already advanced | Correct failure/ACK caveat |
| Interrupted canonical mutation | Shared DB is taken by value; cancellation/error before put can leave its cell permanently empty | Correct; recovery rather than automatic retry/rollback |

Evidence: native [ManagedDb](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L344), [Barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L456), [DatabaseSet](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L508); release [ManagedDb](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L389) and [mutation safety](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L518). Native [Stateful delivery](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/actor/core/processing.rs#L307) waits for durability before Marshal ACK as a reference; it does not implement Baton's separate state/output/cursor/provenance crash linkage.

Native [Any wrappers](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/any.rs#L110) acquire Shared read access for get/stage/expand/merkleize. These accesses read the live applied DB, not an independent immutable historical state. The current docs correctly require an authority covering all clones and preparation/lazy reads, rather than checking worker generation only at final result admission. A sibling canonical advance can invalidate branch fallback reads before apply-time stale-batch validation catches it.

The source [writer-preferring Shared lock](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L139) can deadlock if an outer guard is retained while a wrapper reacquires it after a writer queues. Current docs correctly warn about this and multi-DB lock order. An application access permit need not be a recursively acquired upstream read guard; the actual protocol remains open. CPU work over [immutable Merkle snapshots](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/journal/authenticated.rs#L325) may outlive caller cancellation without authorizing stale result adoption.

## Result statements, collector and provenance

The Rust/interface/result pages correctly separate local worker generation, writer permit and retention coordinates from the stable cross-validator signature subject. The common subject binds exact input/range, canonical input state, runtime/rule and result/output/material interpretation. Storage computes this commitment; Executor checks its retained own direct execution/validation evidence before signing. Recovery must not turn imported work into direct provenance. An imported range may be served with original signatures; the receiver may sign a later range it directly executes. Current docs retain these rules.

Native [collector Handler/Monitor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/lib.rs#L43) supplies requested attestation plumbing. Native [Engine response admission](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/p2p/engine.rs#L207) only requires tracked response commitment, requested peer and first decoded response. It inserts the identity before Monitor validates. Its count includes any such decoded response; it does not establish eligibility, matching full execution statement or signature validity. Executor's own validated map must count f+1. This is already explicit in execution/README.md.

Native collector also ignores unsolicited responses for unknown commitments/unrequested peers. Push certificates/signatures need the shared authenticated P2P path or a tracked request. There is no need for a second generic request collector or ResultService actor. Request and response commitments must identify the full shared subject; including each signer's signature bytes in that grouping commitment would split collection. The reviewed design keeps these application checks open and does not claim the raw collector count is a certificate.

## Native sync assembly that can be reused

1. Open selected QMDB DBs and hold their native `Shared<DB>` handles under Storage authority.
2. Construct public [DB P2P Actor::new/start](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/p2p/actor.rs#L133) with peer provider, blocker, optional local Shared DB and an authenticated channel. No Application/Stateful bound is present: `Shared<DB>: Source` is the storage constraint.
3. Reuse its [Mailbox::serve/attach_database](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/p2p/mailbox.rs#L133). Mailbox is a `qmdb::sync::Source`; Actor owns the generic resolver, duplicate-subscriber fanout and serving/fetch feedback. Reuse this machinery rather than writing another generic material-fetch engine.
4. Executor verifies f+1 certificate and irrevocable exact range/input-state chain. Storage derives or verifies authorized ops target/range and any selected output/result commitments. QMDB does not authenticate that target.
5. Call public [qmdb::sync::sync(Config)](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/mod.rs#L50), or selected [StateSyncDb::sync_db](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L625). The lower-level engine verifies operation/boundary proofs, reconstructs DB state, checks rebuilt ops root and persists provisional material. The wrapper is not required to use the full Stateful actor. Current/Any concrete sync implementations must remain version-specific even where the generic engine is identical.
6. For Current, reuse [Db::ops_root_witness](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/db.rs#L292) and [OpsRootWitness::verify](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/proof/mod.rs#L85) to authenticate the ops root under the trusted canonical root when needed. Also verify the reconstructed selected canonical result; the sync engine's [Database::root implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/sync/mod.rs#L6) verifies ops root alone.
7. Before canonical adoption, perform the open active-validator fence/swap or applicable-delta protocol under the same writer as local execution. It must integrate output/cursor/provenance recovery and survive repeated switches. Material prep itself must not destroy/overwrite the active DB through shared storage partitions before its authorization/fencing boundary; configuration/opening and replacement ownership need an explicit adapter contract. Sync source operation proofs alone do not establish this.

Native [Target::advances](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/target.rs#L29) and [engine target update](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/engine.rs#L670) are forward-only within caller-established same history, not arbitrary branch selection. Native [StateSyncSet](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L699) coordinates one-time initialized-set sync and anchors. Native [Stateful lifecycle](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/mod.rs#L42) records completion and does not peer-sync again on later startups. It therefore does not satisfy Baton's repeated normal-path certified-result switching by itself. The current docs correctly leave that integration unresolved.

## Preserved scope and limits

[Blank-policy receipt](blank-policy-receipt.json) independently counted 39 empty decision cells. No cells, native pin, no-wait behavior, fault thresholds, prefix adoption or continuation policy were changed. This review does not select Any/Current, per-block signing, codecs, overlays, crash-atomic storage layout or switch policies.

This reviewer wrote only this report and its own receipts under wave2/storage. No canonical document, source checkout, generated GitBook/site, protocol, benchmark, test suite, commit, PR or review thread was changed. Source inspection supports API reuse and correction requirements; it is not compilation, integration execution, a protocol proof or a completed six-hour goal. The report's findings must be reconciled with subsequent canonical edits and publication readback.

## Root correction readback before closing this round

The root reviewer updated only state-sync.md among the snapshotted review files before this review closed. I independently reread it at SHA-256 `ae86d60930bfd5b84576236f891bbeaffcfde223efb63ea83cb6cbc360f5b840`. Correction requirements 1 and 3 are resolved in this readback: it now cites native-pin Source/P2P, limits the byte-identity claim to core sync files and the P2P module, and explicitly places authenticated same-history validation with Executor/Storage. P2P actor/handler implementations differ by version, so the limited module claim is appropriate. The conditional Current witness addition has been supplied to the root reviewer with exact verified API anchors; it was not yet present at this readback. The original snapshots/findings above remain provenance. [Final readback](final-readback-manifest.json) and [concurrent-change receipt](concurrent-doc-change-receipt.json) record this distinction.

All 56 valid upstream snapshots passed SHA-256 and non-HTML source checks. Every monorepo citation in this report maps to a fresh receipt with an in-range line anchor. No requested test, build or protocol validation was implied or run.
