# Independent execution-certificate cross-review

Reviewer: `/root/reuse_storage_types_v3`, wave4 compatibility role. Native source is independently retrieved at `534af0ede48affd35b2111522527547b4cc9bf72`, with SHA-256 and Git blob matches in [source-manifest.json](source-manifest.json). No canonical edits, scheme choice, dependency change, compilation or protocol execution.

## Outcome

**Scoped source/API fit passes.** The certification report and proposed execution-page additions correctly reuse existing cryptographic machinery conditionally. They do not claim a ready-made execution-result service, an already-selected certificate scheme, or f+1 from native consensus defaults. This is source fit, not a compiled integration or an execution-finalization proof.

## Direct checks

| Boundary | Fresh source check | Assessment |
|---|---|---|
| Statement/crypto separation | `certificate.rs` L178–216: `Subject` supplies namespace/message; Verifier accepts its associated Subject. `Attestation` L86–91 stores only Participant and Lazy signature. | Full epoch/input/range/base/runtime/result envelope remains an application responsibility. The docs explicitly preserve it. |
| Distinct eligible counting | `certificate.rs` L320–386: Scheme roster, sign, verification, assembly; duplicate candidates unsupported. Signers L509–537 builds bitmap with duplicate/out-of-range panic boundary. | Verify roster indices and deduplicate before these APIs; raw response count is insufficient. Report/docs say so. |
| Quorum mismatch | `utils/faults.rs` L62–68 default quorum is n-max_faults; N5f1 L112–135 has max_faults=(n-1)/5 and separate f_plus_one. `ordered.rs` L274 delegates to Faults::quorum. | Full committee n=5f+1 gives 4f+1 for unchanged N5f1. A result-specific consistent quorum adapter remains unselected; f+1 requirement is retained. |
| Assembly is not authentication | Ed25519 Generic::assemble L181–212 and BLS multisig L233–260 have no Subject argument; they parse indices/signatures, count and encode/aggregate. | Feed only already-verified, distinct, same-full-subject attestations. Docs do not treat assemble as signature validation. |
| Received certificate | Ed25519 L217–275 checks exact roster bitmap length, count/threshold and cryptographic messages; BLS multisig L263–303 similarly checks roster/quorum and aggregate verification. | Consistent threshold and subject construction required on both sides. Neither establishes irrevocable order, canonical base or direct-execution provenance. |
| Roster-bounded decoding | `certificate.rs` L294–315 separates certificate_codec_config from unbounded trusted-storage-only decoding. | Reader recipe correctly requires roster-bounded peer decoding; decoding alone does not establish epoch eligibility or result binding. |
| Conditional scheme suitability | Ed25519 Generic L33–41 is lower-level; macro-generated Scheme L441–489 fixes Subject and Faults. BLS Generic L45–108 requires caller PoP verification and identity/signing roster. | Generic is not itself an arbitrary drop-in Scheme. A protocol-specific Subject/Faults wrapper is still required if this route is selected; report/docs already call the signing scheme and result-quorum adapter conditional. |
| Signing provenance | Existing certificate APIs have no execution-evidence field or canonical writer authority. | Current interfaces explicitly retain root preparation before signing and own-direct versus imported provenance; state sync cannot mint direct evidence. |

No blocking source overclaim was found. A useful implementation-facing detail is that the exported Ed25519/BLS certificate macros generate protocol-specific Scheme wrappers with a fixed Subject/Faults choice. Treat that as the already-open result-scheme adapter, not another public application trait. This clarification is optional; the current wording “when the selected signing scheme fits” and explicit result-quorum adapter is accurate.

## Exact review snapshot

| File | SHA-256 at review |
|---|---|
| `assets/review/commonware-reuse-20261004/wave4/certification/REPORT.md` | `35e9d5b2ba89bfd4ee8e5a51ac06544e18a6653eac9e709b2d60a10ead5559c7` |
| `docs/execution/interfaces.md` | `eae0d3a439353ed7d463ae0850e99d0ca3b234b0d92c7a827b64576c6c93b088` |
| `docs/execution/README.md` | `0827e8c86b8b04788cced1062efea579eb46298aeb2792cdb67ae30294c7c5f2` |
| `docs/reference/integration.md` | `3f1746aebc61b04e23a4db8c7dda93f951d3d01a9cb9eca6244074be5ec34a7b` |

## Independent fresh source receipts

The five files below were freshly retrieved separately for this review and matched complete native-tree Git blobs. Their local paths are `sources/native/<path>`. Native source line references above are to these exact bytes, not the indexed release.

| Native path | SHA-256 | Git blob |
|---|---|---|
| `cryptography/src/bls12381/certificate/multisig/mod.rs` | `14ee57f2842a35dbc966b6e0ff1dd3c9e66280b75fde82e4f320337b664c81ad` | `3789f180d3fac7f90967f3b8e5b15efa77aa2170` |
| `cryptography/src/certificate.rs` | `853ea79c2cae741860a7935f88c4a397f47ae9874b9155f183d3180f9f1e010c` | `ca1ac76dbf51be8e354a96b15da977aecd3d46fa` |
| `cryptography/src/ed25519/certificate/mod.rs` | `036f04b3eb0322e6c604bab485cc881c73139f1ef2006f7ab7071e595c9a9972` | `d5547aee30ed315e2afbf1f437ab0c837c4784bb` |
| `utils/src/faults.rs` | `46ad12c3f6fbc075a6642c9b8130446770615039d12279f1ac9413d494646897` | `ea0d4b71414cbd424a897da692c1f61b6fabd76b` |
| `utils/src/ordered.rs` | `3f95fddd7f8b3335802f88a80dbb3e4ee969179afbde36c42fade2819447c706` | `4e7624be019c1532843b8badac24a8bf571bcbd0` |

Review also reused independently fetched native runtime/engine receipts only for provenance separation, without treating lifecycle cancellation as flush or result authority quiescence. No new readiness ACK, wait for certificates before further work, backend choice or numeric policy was introduced.
