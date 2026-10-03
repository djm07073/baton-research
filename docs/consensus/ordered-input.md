# Delivering finalized execution order

**Orderer converts authenticated consensus history into an exact sequence for Executor.** It retains the evidence needed to explain that sequence, pauses at unresolved gaps, and tracks durable delivery acknowledgements. Native sparse finality and continuous execution order are separate outputs.

## Consensus and Baton integration

Rust declaration: [Orderer](../overview/rust-interfaces.md#orderer). The Rust interfaces page owns the complete declaration.

`Evidence` binds exact authenticated source witnesses to policy/history interpretation. Storing a notice or normalized projection alone does not retain the witness. `next_range` returns only continuous irrevocable input; an unresolved gap requires backfill or pending work. Missing included bodies are not empty slots. `acknowledge` advances the application delivery cursor after verifying a durable CommitResult for that exact range. It is neither a native vote acknowledgement nor a body-release request.

The trait combines public history retention, ordering interpretation, and delivery boundaries. Source-witness export and native policy adoption remain separate integration work on the existing owner. Orderer cannot authenticate or adopt native proposals on its own authority.

## Reuse proof verification and storage

**Orderer interprets exact order; Commonware supplies proof verification, encoding, archives and replay.** Keep original source witnesses and application bindings around those existing handles. No new general proof verifier, fetch engine or cursor database is needed.

| Needed operation | Existing Commonware API | Remaining application connection |
|---|---|---|
| Verify complete native certificates | `Scheme::certificate_verifier`, `verify_vqc`, `verify_lqc`, `verify_da_certificate`, `verify_nullification` | Trusted epoch/config/committee provenance and exact parent/history/policy/source checks |
| Reconstruct an aggregate transcript's vote body | `Tally::vote`, `ConflictingVote::vote_body` | Retain the original certificate; reconstruction does not recover a standalone vote signature |
| Encode proofs and safe-tip history | `ViewProof` Codec, `TipRecord` Codec/commitment | Bounded envelope, exact keys and proof-backed history linkage |
| Store and locate missing evidence | Archive gap APIs; MultiArchive for multiple same-view versions; generic resolver | Choose identity/index schema and serving/retention context |
| Replay emitted ranges and retain a cursor | Contiguous variable Journal and Metadata | Exact predecessor/range/ACK records and recoverable linkage to Executor's durable result |

The certificate-only constructor does not establish trusted epoch/DKG provenance or validate sharing thresholds. Verifying raw DA/nullification shares requires the full verifier with sharing material, including when using `verify_artifacts`; a certificate-only instance is insufficient. Ordinary-key proofs of possession also do not establish committee assignment. [Certificate verifier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/scheme/bls12381_threshold.rs#L293), [batch verification](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/scheme/bls12381_threshold.rs#L889).

Use public aggregate-body reconstruction rather than exporting or reimplementing compact tally decoding. Original certificate provenance remains necessary. ViewProof and TipRecord have existing codecs; the native Artifact enum does not itself implement Codec, so `Archive<Artifact>` is not an unchanged storage recipe. Store supported typed records or a bounded application envelope for exact artifact variants. [Tally opening](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/tally.rs#L235), [history record](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/history.rs#L20).

Archive gaps describe missing stored objects, not empty or unresolved protocol slots. An ordinary view-indexed Archive retains one value at an occupied index; use MultiArchive or unique export ordinals when retaining several same-view source revisions. Concrete layout remains open. [Archive/MultiArchive](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/mod.rs#L116).

Journal replay and Metadata atomic updates are local storage guarantees. They do not automatically form a transaction with QMDB, another journal or retained witnesses. Preserve crash ordering and state/output/cursor/provenance linkage before delivery ACK. Native-selected witness export and private tip extraction still need the narrow owner bridge; public proof verification alone does not derive dense order. [Journal](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/journal/contiguous/mod.rs#L161), [Metadata](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/metadata/storage.rs#L689).

See the [normal native sequence](../e2e/native-consensus.md#normal-native-consensus-producer-da--leader-proposal--finality) for message flow.

The existing native Core owns votes and finality. Producers disseminate signed headers containing application commitments on independent lanes; a separate leader chain gathers evidence about their order. Each view leader places an earlier V-QC parent and anchored per-lane paths into a transaction-free LeaderBlock. It need not await a DA certificate for every descendant: a locally DA-voted continuous suffix satisfying native conditions may be proposed. [Producer / leader chains](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L9), [Proposal / direct vote](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md#L309).

The canonical digest of the owner-built LeaderBlock identifies the leader proposal. VoteBody references it together with round, position, and extension. [LeaderBlock digest](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L643), [VoteBody](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/vote.rs#L119).

Each producer anchor is the block reference from which that lane's proposed path starts. It is represented by an inherited safe-tip reference from the parent V-QC or a higher DA certificate carried with the proposal. This differs from the parent V-QC coordinate referenced by the leader proposal. [Anchor representation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L399).

For each producer, a validator records how many consecutive proposed blocks after the anchor match its DA-voted path. From the end of that prefix, or the anchor when position is zero, extension carries bounded body commitments from the continuing DA-voted path. The validator signs one complete vote containing every producer's position and extension. [Position / extension construction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978).

| Native evidence | Bound material | Establishes |
|---|---|---|
| DA certificate | `n−2f` distinct valid DA shares for the same producer header | Availability / uniqueness at that producer position and a certified anchor |
| V-QC | `n−f..n` attributed votes / novotes from distinct identities, including at least `2f+1` votes for the designated proposal | Safe tips for the next leader and view exit |
| L-QC | `n−f` complete votes for one leader proposal | Portable finality evidence for leader and per-producer tips |

DA uses a threshold certificate. V-QC and L-QC combine ordinary signatures in a complete attributed transcript. A local sticky vote pool reaches finality at n−f independently of L-QC creation. Exact merged execution order may be shorter than individually fixed producer prefixes, so connect sparse finality to [ordered delivery](../e2e/canonical.md#cut-commit--ordered-range--execution-commit). [DA / certificates](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L147), [View / local finality](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md#L350), [Chain-local finality and exact placement](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L210).

These native DA/view votes differ from [Baton intended-order reports](../baton/direction.md#leader-choose-direction-from-reports) and [direct-execution result signatures](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification). Direction adds no separate approval quorum. Binding selected prefix and policy to actual parent, history, and frontier at proposal authentication still needs development and validation. Preserve the exact leading sequence, not merely membership of its blocks.

Orderer verifies and retains the exact witness selected by the native owner and the original policy/history, then computes continuous input. A resumable owner export supplying this material is new integration. Sparse tip certificates do not provide a body stream, past policy, or dense cursor. Simplex marshal compatibility with Multimmit also needs separate review. [Native application boundary](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md).

| Existing attachment / query | Supplies | New adapter responsibility |
|---|---|---|
| Native `Reporter::report(Activity)` | Activity notices, including accepted artifacts | Durable witness handoff, cursor, retention; a separate domain from Baton reports |
| `Running::inspect` / `Inspection::finality` | Current normalized finality projection | Retain source material needed for same-tip evidence and settledness revisions |
| `Running::serve(view)` | Retained useful native ViewProof | Preserve exact historical interpretation; a higher covering L-QC may be returned and old proofs pruned |
| Proposed exact owner export | New handoff of selected source and immutable context | Verify / retain original witnesses → interpret terminal slots → emit continuous OrderedRange |

These responsibilities can live in one consensus application attachment. No separate Orderer server or mandatory multi-actor deployment has been chosen. [Reporter trait](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L246), [Inspection / serving](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L530), [Retained proof selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/resolver/actor.rs#L245).

FinalityFact is a normalized projection of leader, tips, positions, settledness, and evidence identity. It is not the witness archive.

An evidence hash identifies a witness commitment; it is not signature-verification material. A selected row reconstructed from an aggregate V-QC may lack a standalone raw vote artifact. Retain the signed vote or source certificate authenticating that row and material needed to reproduce extraction/opening. Do not replace the native-selected exact body for an identity with a conflicting body or an arbitrary quorum subset.

Identical tips can have different sources, evidence, or settledness. Immutable export must therefore track the owner's exact source-selection transition. [Evidence commitment](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L2082), [Aggregate row provenance](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L1681), [Pool revision](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L1865).

Ordered delivery jointly verifies epoch/committee, actual parent, history, frozen policy, selected pool source, producer header/ancestry, native tips, positions, extensions, and settledness. It distinguishes included, irrevocably-empty, and unresolved slots and stops at the first unresolved slot. Missing included content is not evidence of emptiness. Private `pub(crate)` extraction APIs are not already callable by the application. A limited facade or verified equivalent bridge remains a development choice. [Native extraction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L336), [History opening](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/history.rs#L10).
