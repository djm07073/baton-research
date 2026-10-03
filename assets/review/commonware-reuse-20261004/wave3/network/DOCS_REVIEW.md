# Independent reader-page review — network, body and Orderer reuse

Reviewed current uncommitted changes after canonical baseline `3c5ec96c91883dae892ee99832dee315c789eaee` / published GitBook `NY491pkJQdX6ny2Lyndj`. Review time: 2026-10-03T20:56:25.884365+00:00. This report is source/English/interface review only. No canonical page edits, upstream build, protocol test, dependency change or publication performed by this agent.

**Verdict: pass; no unresolved finding.** The four pages correctly name existing implementations, preserve application context/provenance/retention obligations, and make no additional cut/ACK gate or policy default. A small initial wording note, `cached overflow` → `queued overflow`, has already been corrected in the reviewed final snapshot.

| Reviewed page | SHA-256 |
|---|---|
| docs/overview/networking.md | `f4f289d67fc93f5a905f10fda482e908096846cbb65073452c51ff26c194356d` |
| docs/consensus/block-body.md | `c9141ddd44e2b21b084417e34a407b51561dd690de71ab42e9106508bd5d99ff` |
| docs/consensus/ordered-input.md | `fd68183770be07817f76cca676e0d5db5d31ecbd0412472949ca29967724655e` |
| docs/reference/integration.md | `6d912ad6a6d7a95e5378903c9f1d89b387d010745083b8863d8f1eca7b7a2b5c` |

## Verified network/body claims

- **Native registration signature:** `discovery::Network::register(channel, quota)` has two arguments and returns the exact native channels Sender/Receiver pair. The stale three-argument `256` calls in log-multimmit are established by the same pinned tree's source, direct Network reexport, workspace dependency and path resolution. Reader text explicitly limits this to source mismatch and does not claim a compiler result or pin upgrade. Integration step 1 now correctly registers before network start.
- **Whole-wire size:** generic resolver response `8 + 1 + body_bytes.encode_size()` includes fixed u64 request ID, tag and Bytes length prefix. Requests add `8+1` to key encoding. The private wire type is not advertised as a public construction API. The Sender maximum/assertion and bounded application Consumer decode are accurately distinguished from transport's own framing and opaque Bytes network bound. No maximum value or fragmentation policy is selected.
- **Existing start connections:** buffered and generic resolver take raw Sender/Receiver pairs and wrap their own wire types. Public `codec::wrap` remains the direct typed application-message option. Optional WrappedBackgroundReceiver does not satisfy their raw Receiver interface and is correctly described as lossy/conditional, with codec failure blocking distinguished from stale-context or local-storage failure.
- **Identity sets:** authenticated transport identity, connected recipients, body authors and eligible epoch result signers are kept distinct. A retained body may be served by a relay other than its author. Oracle supplies Provider/Blocker transport services, not trusted DKG/epoch signing provenance. No certificate count is inferred from connected peers.
- **Resource/lifecycle:** corrected `queued overflow` refers to buffered ingress's pending deque, while per-peer body cache remains its separate bounded mechanism. Configured mailbox capacity is not a total bound on subscribers or serve futures. The existing no-wait rule is still logical, without claiming physical quota isolation. All added IDs/quotas/placement choices remain open.

The source evidence is the already independently Git-blob-verified network wave's 50 fresh files, particularly p2p discovery/network.rs L169/L192, authenticated/channels.rs L51, utils/codec.rs L16/L169, utils/limited.rs L105, buffered engine/ingress, and generic resolver wire/config/engine. No higher-level Simplex Marshal gate is imported into native Multimmit.

## Verified Orderer table and limits

I independently recomputed all **38** retained Orderer source Git blob SHA-1s and matched them against the network review's complete pinned native Git tree. The new table matches real public APIs rather than hypothetical generic infrastructure:

| Added reader claim | Source check |
|---|---|
| Scheme certificate-only verifier and direct complete certificate methods | bls12381_threshold.rs L293, verify_vqc L770, verify_lqc L850, verify_da_certificate L587, verify_nullification L651 |
| Raw share verification requires full sharing material | certificate verifier retains da/nullification=None; individual raw verifiers and artifact_claims require their sharing; verify_artifacts correctly linked to **L889** |
| Tally/ConflictingVote return reconstructed unsigned bodies | tally.rs L235/L476; no individual signed artifact is manufactured by these returns |
| TipRecord commitment + Codec are existing | history.rs stores exact parent/tips and supplies Write/EncodeSize/Read; those codecs alone do not certify a history derivation |
| ViewProof Codec is public | emission.rs L17/L37/L56/L66, publicly reexported in multimmit/mod.rs L242; its private module location does not prevent using the reexport |
| Artifact does not itself implement Codec | admission.rs defines public Artifact and its id/unverified helpers, but no Artifact Read/Write/EncodeSize implementation |
| Archive gaps and MultiArchive | archive/mod.rs has next_gap/missing_items; MultiArchive supports additional items at an occupied index, while ordinary put does not |
| Journal replay / Metadata cursor storage | contiguous Journal APIs provide application record replay; Metadata atomically syncs its own pending updates, not a transaction spanning QMDB/other stores |

Contextual limits remain explicit: trusted epoch/committee/threshold provenance is not obtained merely from proofs of possession; raw share verification is not supplied by certificate-only Scheme; the original source certificate must remain available for reconstructed rows; exact policy/parent/history/source interpretation remains application/native owner work. Archive holes do not authenticate empty protocol slots. Native private tip extraction and exact source-selection export remain unresolved integration, and verification/replay storage does not magically produce dense input.

The integration page correctly keeps concrete Archive/MultiArchive identity layouts and journal/cursor linkage open. It preserves source witnesses through recovery and requires the application's durable state/output/cursor/provenance linkage before ACK, without adding a native vote or cut wait. There is no transfer of state finalization/sync authority to Baton.

## Cross-page clarity and scope

Headings lead with module responsibility and then explain public calls and remaining adapter work. New content remains English and links detailed page subjects rather than redefining the five application traits. Body size details stay in block-body, channel composition in networking, witness/order semantics in ordered-input, and assembly references in integration.

The Nunchi integration mention stays a **candidate** for compatible SHA-256/nonce lanes, qualifies its fire-and-forget finalization/restart/ingress/count-selection boundaries, and does not force its chain builder or Stateful/Application lifecycle onto Baton. QMDB's branch-access/one-shot/tuple/preflight refinements are consistent with the separately passed storage cross-review.

No reviewer change to the native pin, protocol selection, direction algorithm, root-before-sign, exact-context execution result signature requirement, direct/imported provenance, single canonical authority or undecided numeric/policy cells is requested. Document syntax/build/interface export and publication verification remain root's separate checks; this review does not claim them executed.
