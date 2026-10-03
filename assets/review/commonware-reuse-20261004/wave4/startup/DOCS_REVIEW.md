# Wave-four reader-page review

2026-10-04; reviewer `/root/reuse_network_v3`. Reviewed the current root-authored startup/network/integration edits and the related pool/Tx prose against fresh pinned startup/pool receipts and the compatibility/certification source reports. Only this report was changed; source retrieval additionally extended the review-owned pool manifest with Nunchi status.rs.

## Result

**Pass. No remaining material reader-documentation issue was found in this snapshot.** Source/API scope, completion meanings and unchanged diagrams agree. No new ACK/public trait/backend/configuration choice is introduced, and no observed bug or verified authority-handoff guarantee is asserted.

| Reviewed page | SHA-256 |
|---|---|
| docs/e2e/recovery.md | `6977d87f2b6e49e46f8bef81e36d7edfe3ef6bd25a94923fac19e09ebecf0ceb` |
| docs/overview/networking.md | `fb6abeef514bd9bcaf99383a92d47ee218124c5d79a2b7794d6a655e13bcb2d0` |
| docs/reference/integration.md | `33db4673933e1a34bb02f1fa28a10f21edf4f1cc47fbeefdd95c59330abc9b27` |
| docs/tx/README.md | `d9ccd7b04fecc5a1a61d7a709e0ef6a05539000113a9f057cd71532ffc4fbe92` |
| docs/tx/interfaces.md | `5de73fea82efdeb9c68396a246a5219fce727f0d541070a8dac77dabac7f31d2` |
| docs/consensus/block-body.md | `099084ff74c6910b4147febf3bcca5435bc9d8e80fe8140ab1d8d7555b64e6a3` |
| docs/e2e/block-body.md | `e2ab8a122245fff340403dc0a3157945b1036986aad43ac05d328d6141ebd04b` |

## Startup and service lifetime readback

- **The early diagram start is explicitly preparation/idle intake.** The prose requires network binding before the first actual publication/fetch, rather than categorically forbidding actor construction/start beforehand. Native Network::start binds synchronously before spawning; pre-binding send feedback can accept and discard. The networking addition and recovery explanation state the same contract.
- **Body recovery has an independent usable resolver.** The body buffer/resolver can be started before Native Running exists. Native Engine::start may await Automaton recovered-body verification before constructing its own actors/returning Running, so the text correctly excludes a body fetch dependency on that handle. No remote Ready/ACK round or application QMDB prerequisite is added to native startup.
- **Readiness remains a remembered milestone.** Running::ready caches Ready/Failed; true cannot be reused as ongoing service health. Execution-state readiness and exact ordered input remain separate from body custody/native readiness. Existing pending recovered verification versus false/closed failure semantics are preserved.
- **Owned task selection is not durable shutdown.** Supervisor/Spawner descendants and Handle::select reuse are accurately scoped. First completion or dropping the owned selection aborts its group; cooperative stop waits for held-signal release. These do not flush a separate archive/QMDB owner, restart actors or prove state/output/cursor/provenance linkage. The canonical writer is kept outside short-lived advisory ownership.
- **Join is qualified without claiming a demonstrated race.** The table identifies the upstream documented lifecycle API; prose distinguishes its documented child-stop promise from root-only await and descendant abort requests visible in implementation. It retains the lifecycle recipe while refusing to promote root completion to proven signing-authority transfer or storage durability. This agrees with the completed [limited independent lifecycle receipt](LIFECYCLE_CROSS_REVIEW.md).
- **Storage reuse and identity are precise.** Archive initialization reopens its own committed local checkpoint; new body custody still requires exact covering sync. Cache reconstruction and partition/epoch-key provenance are separate application/deployment obligations. Native fresh start's never-active-key/new-partition restriction is not turned into a generic storage-deletion recipe.
- **Actual chain examples keep their differences.** Tempo's network-before-service and mandatory Handle::select composition is supported; Alto body-before-consensus prevents restart queue dependence, while try_join_all is correctly described as all-success/early-error rather than first-clean-exit. Neither Simplex wrapper is promoted to a public unchanged Multimmit attachment.

These claims were checked against [startup source/anchor receipts](source-manifest.json) and [REPORT.md](REPORT.md); lifecycle postconditions retain their stated proof boundary.

## Integration constructor/graph and certificate pointers

The new table names existing public constructors and supplies the actual body/peer/channel responsibilities without inventing an importable body service or new supervisor. Native Config's `initial` and release Blocker's added `blocked()` match the pinned compatibility source excerpts. One native dependency graph, native workspace version versus registry identity, and ecosystem direct/transitive adaptation are presented as compatibility constraints, not a dependency upgrade or a compiled assembly. The Nunchi non-P2P versus unit-config P2P distinction agrees with its actual start bounds. This readback relies on the separately source-verified [compatibility report](../compatibility/REPORT.md); it does not claim registry bytes equal the inspected release tag or consumer lockfiles automatically inherit upstream lockfiles.

The execution pointer correctly directs readers to existing Subject/Attestation/Scheme/Signers while retaining full Executor input/base/provenance checking. Built-in consensus quorum is explicitly adapted to f+1; no native quorum, key/scheme, public trait or result-signing boundary is selected. This matches the [certification source report](../certification/REPORT.md) and the current linked section; independent full certification review remains its separate scope.

## Pool report delta and root Tx prose

The final [pool-builder report](../pool-builder/REPORT.md) now hashes to `4ff1ed704c94a444fba690154ccf6a2d1399a15bf83540745e1d3babf5525712`. The earlier [independent pool cross-review](POOL_BUILDER_CROSS_REVIEW.md) covered report `9666f067e239a33755adeb6fa6158f18c13da23a5fff6f55321a8970cba8fbbe`. The new completion/status statements are supported:

1. Actor height drives TTL admission/expiration and Finalized status, so native producer-lane height cannot silently be the durable canonical execution-range coordinate. In inspected Pool, admitted_at comes from last_height, finalize advances last_height monotonically and performs height-driven TTL scans. Mapping the application durable range to that scalar remains selected adapter work.
2. Monotone lane nonces do not supply ordered status replay. Pool::finalize records each supplied digest as Finalized at the supplied height even when the digest is no longer pooled; StatusCache::insert overwrites an existing entry without a height comparison. Replayed older finalization **can** replace a status height while nonce advancement remains monotone. No executed trace or default replay policy is claimed.

The second delta was checked through a further fresh retrieval of pinned [mempool/src/status.rs](pool-review-sources/nunchi/mempool/src/status.rs), matched to the independently fetched Nunchi Git tree. The [pool-review manifest](pool-review-source-manifest.json) now contains **15** verified files: the original 14 decisive review files plus this scoped status receipt. Pool.rs L211–272 and status.rs L34–40 directly support the two additions.

The root Tx/pool/body edits preserve that final report's semantics: one chosen backend; ordered candidate sequence; payload-only feature hooks; direct peer admission bypass exposed; explicit selected on_commit completion/reconciliation; non-destructive count/refill selection and retained exact bytes; dependency-preserving packing; local cancellation separate from canonical retirement; durable Executor outcomes, including applicable imports, separate from body/native finality. The Reth no_updates/provider-backed maintenance/graceful backup and separate Tempo AA two-dimensional maintenance remain conditional reuse references. No pool completion gates native cut, direction or Orderer's durable delivery receipt.

## Preservation and static checks

Both recovery diagrams and both E2E body diagrams are byte-identical to HEAD. The prose explicitly resolves the early-start interpretation without modifying those existing sequences. Exported public declaration/type/signature tokens are unchanged ignoring comments/whitespace: **TxPool, Orderer, Baton, Executor, Storage**, with no additional trait or method.

Ran the document-only `python3 assets/tooling/check_docs.py --migration`: **31 content pages, 249 local links, 18 rendered diagrams, 39 blank policy cells, zero failures**. This checks document navigation/exports/assets, not native protocol execution or Rust package compatibility.

The hashes cover this readback only. This report does not claim compilation, benchmarks, protocol proof, publication or completion of the six-hour work goal; subsequent reader edits require their own readback.
