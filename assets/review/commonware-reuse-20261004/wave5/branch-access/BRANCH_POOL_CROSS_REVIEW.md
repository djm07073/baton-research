# Independent Nunchi pool-source cross-review

Reviewer `/root/reuse_storage_types_v3`, wave5 branch-access role. Reviewed pool-source REPORT SHA-256 `89dda1e5f2bf5ff628d33be1c1f490b38573a352a0afd583309c0c23d19594ac`, matching the assigned snapshot. No canonical edits, backend selection, dependencies, actor implementation, protocol/native compilation or tests.

## Outcome

**Scoped source/API fit passes; no blocking source overclaim found.** The report correctly identifies a conditional maintained source adaptation of the existing one actor/kernel and its SDK tx boundary. It does not present that adaptation as an upstream ready-made generic pool, a compiled port, a chosen backend or an existing canonical-readiness guarantee. The proposed reader checklist can remain short and conditional.

## Decisive independent source checks

| Boundary | Directly inspected evidence | Conclusion |
|---|---|---|
| Minimum maintained actor source | SDK actor/pool/config/status/error/metrics imports; tx.rs L1–4 is the only SDK common/crypto import site in these core files. lib.rs L10–27 exports handles/config/status/tx contract while pool is private. | Whole actor/kernel reuse can avoid the SDK chain and Stateful Application. Keep tx adapter imports, public SDK NonceKey export and manifest dependency changes together. No private Pool external access is supplied. |
| Generic payload limits | PoolTransaction L32–47 requires Clone+Send+Sync, concrete native-graph SHA256 Digest, u64 nonce, encoded_size and verify. Blanket Transaction adapter begins L49. | Custom tx does not erase unchanged SDK adapter dependencies. Extract/gate that unit if chosen; arbitrary hash/nonce semantics are not a small localized extraction. |
| Transitive package/features | mempool/Cargo.toml L10–20 uses inherited nunchi-common/crypto plus Commonware/futures/etc. common/Cargo.toml defaults state; common lib gates state/runtime exports. crypto manifest uses codec/crypto/macros. Workspace declares edition2021 and enabled defaults. | State-disabled pool-only SDK types are a source-supported candidate, not a resolved build. Disabling one member import is insufficient; resolve all used packages/features and cross-boundary identities. |
| Existing actor task infrastructure | Native runtime root reexports utils, utils mod L24 exports Cell as ContextCell, cell macro L13–21 uses existing Spawner and synchronous restore; native metrics and macros exports correspond to actor uses. | No replacement task framework is justified. Source correspondence does not prove actor compilation after retargeting. |
| Source-aware admission | submit L63 checks stateless before mailbox; gossip handlers L435–470 clone/admit/gossip local tx; peer L473–501 uses read_cfg(unit), check_stateless and admit_verified without rebroadcast. Metrics enum distinguishes source privately. | Packing-only hooks can wrap selection; admission hooks must reach both actual ingress sites if selected. No public source hook exists unchanged. Existing InvalidSignature mapping cannot silently encode policy refusal. |
| Peer decoding/work boundary | Actor read_cfg consumes from IoBuf but does not enforce full-frame exhaustion here; validation/size runs after decode. P2P startup T:Encode+Read<Cfg=()> at L292–301. | Report correctly calls for explicit full-frame/nested/work/aggregate bounds and treats nonunit config as adaptation. Frame transport limit alone does not imply bounded nested decoding. |
| Canonical processed completion | Finalized message L33–37 has no responder, finalized L195–220 uses try_send, handler L414–427 invokes private pool.finalize. pending/status query tx data, not processed nonce/watermark. | Same-mailbox reliable submission/oneshot completion is proposed work. Current method cannot satisfy processed or seed-ready success; no second actor is needed solely to add it. |
| Canonical context/replay | Pool finalize L211–280 updates digest status, advances each lane nonce monotonically and refreshes ready index; status cache L35–45 overwrites existing status directly. | Older replay can overwrite per-digest height. An unrelated later update does not hydrate missing lanes. Context-bound dedup/readiness/recovery is additional integration, not native cut/direction gating. |
| Restart hydration | Pool new L50 begins empty committed_nonces; committed_nonce L304–305 defaults unknown to0. finalize can seed provided lane nonces and refresh touched lanes. | Candidate initialization through existing finalize kernel is plausible only with authoritative relevant-lane coverage and processed ordering. Unknown lane is not evidence of nonce0. No public seed/ready API exists unchanged. |
| Selected payload ownership | Pool pending L160–205 clones nonce-contiguous candidates, advances only selection cursor; admission L97–150 caches digest/tx Entry and same-nonce replacement updates queue. | Clone-based cancellation requires no automatic reinsertion. Clone bound cannot guarantee interior payload immutability: retain stable verified identity/encoding/features and exact selected bytes. Byte/dependency packing remains attachment/actor adaptation, not a new generic pool. |

All29 source links in the assigned report have this role's independently fetched receipts and valid line anchors: [citation checks](pool-report-citation-checks.json). These anchors were supplemented by reading the implementation, not used as proof from an inventory alone.

## Useful nonblocking refinements

1. **Hydration uses more than nonce maintenance.** Existing finalize also establishes monotone last_height and performs TTL expiry (pool.rs L260–280). If admissions occur before seed processing, their admitted_at may be0 (L126–130), and a high canonical hydration height can expire them. State the selected ordering of hydration/admission or chosen reconciliation semantics; do not imply finalize(empty digests, nonces,height) is a side-effect-free nonce setter. The report already leaves startup readiness and retention policies open, so this detail does not invalidate its candidate.
2. **Do not promise a publicly exposed source extractor.** Maintained tx adapter isolation must adjust imports, documentation links, lib.rs NonceKey export and inherited manifests together. The report already calls this source maintenance, not a feature available in the unchanged crate.
3. **Keep the reader checklist narrower than the report.** Retain one conditional paragraph/table: graph and payload fit → existing ingress hooks → same-owner canonical processed/readiness connection → stable dependency-aware body selection. Link source receipts for the detailed file list. Keep policies/defaults and schemas open; no new dispatcher, nonce engine, pool queue or public application trait is warranted by this review.

## Cargo documentation scope

Primary Cargo workspace documentation was read independently: edition2021 inherited member default-features=false may be ignored/rejected unless the workspace declaration disables defaults; feature enabling remains additive. The edition guide explains the older2024 rejection behavior, while current Cargo docs also describe a newer2024 override condition requiring Rust1.99+. The report's edition2021/applicable-rules caveat is accurate and does not select a toolchain or claim a compiled feature graph. [Workspace inheritance](https://doc.rust-lang.org/cargo/reference/workspaces.html#the-dependencies-table), [edition guide](https://doc.rust-lang.org/edition-guide/rust-2024/cargo-inherited-default-features.html).

## Independent fresh receipts

21 decisive native/SDK files were independently fetched for this review and matched freshly retrieved complete repository trees. Native pin `534af0ede48affd35b2111522527547b4cc9bf72`; SDK `eea35ced709f68c15d6fbc8bcc754696a7e44374`. This role's [source manifest](source-manifest.json) records URLs, lengths, SHA-256 and Git blob receipts; each suffix below is under `sources/`.

| Source suffix | SHA-256 | Git blob |
|---|---|---|
| `nunchi/Cargo.toml` | `8c8d35af791227dfb050982fd193eac886df0a9d5eb01b9690723ba16afce8ad` | `bc97e1da17e589679cc5b95a6f94ef6f44c46b28` |
| `nunchi/mempool/Cargo.toml` | `2eff13e932d0b752716fdd2e191de5ed1bf544dea7a7df65404ed48b2697cd5f` | `415d0178ff84d004972f8b21ce736e36a262ea3a` |
| `nunchi/mempool/src/actor.rs` | `16565587ca03737c35ecbc3469ff8e59e55bc90c5be31026a793f8713472690f` | `becd1fd372cf61a11a388d1528dd1be2d4243316` |
| `nunchi/mempool/src/pool.rs` | `6de4c1387e43ebf2624e640c5fe9840160dec61973e4e516847b47c330d92e24` | `90fab9253f40757e49ae39472683e187d821e25e` |
| `nunchi/mempool/src/tx.rs` | `1ca9f24f1906a58102cf87e53d5fc1b8e06ceac620c99782d86008af205a7833` | `a870a59297f4cbd448597471f3c921b735ada1e6` |
| `nunchi/mempool/src/lib.rs` | `92b0cd637a14289526ec3cf639c7f1146c1e0c456205d3d2d12813a51c3f7427` | `471e964a4bcd35b546e602961d600df5f5067037` |
| `nunchi/mempool/src/config.rs` | `1bd799cfb54747cf83c23f703c00fa0dbe95278de009b4d259b1f60f76227392` | `f6d123c747c8aeafbdeef440056dfe241d2a0267` |
| `nunchi/mempool/src/status.rs` | `546b02366607a08c8c55b982c2d04227e3e9843896be949771a271a8ddc6d81c` | `490ff2be0f5cb760eddac5c5d200443dae4d6877` |
| `nunchi/mempool/src/error.rs` | `b0df9f04e0c08ec71bbd85816353e1b4d24e6169367b8282281ac5158b4024b1` | `8d8a0e131c05bc81fa45b0372c4fa12820bac23b` |
| `nunchi/mempool/src/metrics.rs` | `1b33ef10ed75f765a1349d58f296b93f0cb078dea0e4bccba5c5510d9ffe02b1` | `ac66b8dd42a5f3e5468ae73a8edd691197beaeb1` |
| `nunchi/common/Cargo.toml` | `cd297d56f2e3f984fdad80f1f00051fdb2dcbcc859431cc1ede317eb03f50d0e` | `bd9186ccda732fbb08b28b9ef67e51bd6b279015` |
| `nunchi/common/src/lib.rs` | `95ada948c9ffcddb4aec60cc3931483d518daa612f5f25c4fde3608946f302f9` | `7f14091e9a2052bdc36dd069dc93408d1405ffe0` |
| `nunchi/common/src/transaction.rs` | `e0a7d57510dc35cb51e981cd3088c1940dcac6e3d63dec5939c771d8785c36b3` | `2c8b95ca6fbda2de0309e84530a9c65a994afad3` |
| `nunchi/crypto/Cargo.toml` | `ced9b94dc05859c43f866945015cc43fd05a865f321ded5f7f63bf8168ab6d8f` | `5c59e236d7a18a21cc8859c6cd56b762c1d1b5ba` |
| `nunchi/crypto/src/lib.rs` | `deed0b7b3f1e7e87d09a1488562835d7bd7e98ac4d7d2fd45c5326f260aee9c9` | `6292c4b35d14c11f7b103d230c02c1df75865dd0` |
| `native/runtime/src/utils/mod.rs` | `2f5e34408dee8d159cdc298bc3eb84b06cfe31af8261e6436e1a37d88707296a` | `7e1aed5cbcb6a339ce5022c3e8c80612f5e669e1` |
| `native/runtime/src/utils/cell.rs` | `1993e75c2d8fed26f221043aa1e5e9f17f75b9c398f61cfb8837e9bd293f8a61` | `bf7bfd65c41c9412060ad1e896f76270f53baedd` |
| `native/runtime/src/lib.rs` | `bacb6553a3186170effa6dabb46644c1c9e5310a9edef1cd5ad5a24e3204e0be` | `139a63a62b07caaadb799d3f4b1cfa4a8cd37fca` |
| `native/runtime/src/telemetry/metrics/mod.rs` | `e5bd1c6c09695a19d0ee7f43825bdcb98d8070e3186796c39a853c462896c963` | `5d2dec0dcb564d4f0d776927aab9f9114c58d45a` |
| `native/p2p/src/lib.rs` | `d1f2bfd100849dc730385b459dbf14cabb434909494d83677c7e6666ef163272` | `9931331ede2de93c9b16eaad3dc263b13fe952ec` |
| `native/macros/src/lib.rs` | `274c70751ff1bbd08da72574043582cc340faaffdafe2acf8077e7c9fd2562a2` | `94600ae1426fe8114de552aca9f791a3cbec3795` |

This review finds source-local separability and realistic missing hooks. It does not prove minimal compiled dependency closure, production maturity, bounded E2E processing or modified Multimmit behavior.

## Final narrow amendment check

The amended pool-source report SHA-256 `880481a271e4f4077d760d6e1378b68eae99d767ee89782eb5922d5346018ab6` adds the hydration/admission/TTL caveat identified above. Fresh retained exact SDK pool.rs shows Entry.admitted_at=self.last_height (L126–130); finalize advances last_height and performs expiry using height (L260–280). The report correctly uses conditional expiration and leaves hydration ordering/lifetime policy unselected. Its new L128 and L211 citations match the already independently fetched exact source; no broad refetch was needed. Scoped source fit remains passing, and refinement1 is addressed.

The matching new TTL/admission-ordering paragraph in docs/tx/interfaces.md was also checked narrowly; SHA-256 `64c74f0663712717cb12947addd329949b2d3636a7e19f87c5a99016c1a79a52`. It states initialization must complete before eligible selection, relation to admission remains a selected contract, and unknown zero is not authoritative. It adds no native cut/direction wait or new actor. Other ongoing Tx/interface changes are outside this narrow amendment check. [Final receipt](pool-final-amendment-receipt.json).
