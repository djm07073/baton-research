# Reader-facing documentation cross-review

Reviewer `/root/reuse_storage_types_v3`. Review scope is current uncommitted certificate additions, native dependency/import identity and constructor checklist, plus startup/lifecycle additions. No canonical edits, implementation, compile or policy selection. Source evidence is independently fetched and tree/blob verified in [source-manifest.json](source-manifest.json).

## Outcome

**Scoped source/API fit passes.** No blocking source correction found in these additions. They preserve five public application traits/signatures, separate native pin from the indexed release, retain the execution f+1 threshold and root-before-signing/direct-versus-imported evidence, and qualify startup/cancellation versus storage durability. This is documentation review; it does not establish a compiled integration or protocol proof.

| Reviewed addition | Evidence and conclusion |
|---|---|
| Result-certificate recipe and execution primitive row | Native certificate Subject/Attestation/Scheme/Signers and concrete Ed25519/BLS Generic implementations support conditional reuse. Full application subject/epoch roster remains outside codecs; assembly cannot verify signatures. Consistent result-quorum adaptation remains open because N5f1 default is n-f. [Independent review](CERTIFICATION_CROSS_REVIEW.md). |
| Native graph/version paragraph | Exact native workspace declares 2026.7.0; fresh Tempo/Alto/Nunchi locks resolve registry Commonware2026.9.0. Package identities differ; byte-identical source is insufficient. The text recommends source adaptation without claiming an upgrade was selected or an actor already ported. |
| Native constructor checklist | Network/context/signing identity, buffer Body Digestible+Codec/config, resolver archive-backed Producer and validating Consumer, same transport PublicKey, peer Provider/Blocker are actual inputs. Native resolver `initial` and release-only Blocker `blocked()` are precise API deltas. Table is expressly noncompiled and chooses no numeric configs. |
| Rust-interface introduction | Adds only dependency identity guidance and a source-checklist link. No new application trait, method or associated type. Existing generated Rust export is outside this edit. |
| Recovery/network startup prose | Distinguishes construction/idle intake from first active outbound use; pre-bind acceptance drops bytes. Separate body resolver can serve native recovered-body verification before Running exists; no peer Ready/ACK round. Existing native recovery wait remains correctly stated. |
| Service-lifetime table and join caveat | Uses existing Spawner/Supervisor/Handle machinery; ready is remembered startup, abort/selection/stop are not flush. Strict native child/signing-material quiescence remains unproved by inspected implementation and no observed race is asserted. Archive sync and selected Storage barriers remain specific to their own contracts. [Independent source review](STARTUP_CROSS_REVIEW.md). |
| Canonical durability/provenance | These additions do not claim Archive metadata checkpoint is atomic with QMDB, AppliedCursor, output records or signing evidence. Executor/Storage integration/recovery remains open. |

All 28 GitHub source links introduced by this six-page diff are covered by this role's independent fresh receipts and have valid source line anchors. [Exact citation check](docs-citation-checks.json). Official Cargo patch requirements were separately read from primary Cargo documentation for the package-version constraint. Earlier unchanged citations and other agents' pool-specific additions are outside this review.

## Exact reviewed snapshot

| Page | SHA-256 |
|---|---|
| `docs/execution/interfaces.md` | `eae0d3a439353ed7d463ae0850e99d0ca3b234b0d92c7a827b64576c6c93b088` |
| `docs/execution/README.md` | `0827e8c86b8b04788cced1062efea579eb46298aeb2792cdb67ae30294c7c5f2` |
| `docs/reference/integration.md` | `33db4673933e1a34bb02f1fa28a10f21edf4f1cc47fbeefdd95c59330abc9b27` |
| `docs/overview/rust-interfaces.md` | `b93993c06103578bc129bc8b259c462b986a3ad645cbd03e6cbeb55875ecb49a` |
| `docs/e2e/recovery.md` | `6977d87f2b6e49e46f8bef81e36d7edfe3ef6bd25a94923fac19e09ebecf0ceb` |
| `docs/overview/networking.md` | `fb6abeef514bd9bcaf99383a92d47ee218124c5d79a2b7794d6a655e13bcb2d0` |

Native pin `534af0ede48affd35b2111522527547b4cc9bf72`; release references remain `v2026.9.0`, not substituted as the adopted engine. The optional detail about generated protocol-specific certificate Scheme wrappers in CERTIFICATION_CROSS_REVIEW does not require another public application trait or change these pages' current conditional language.
