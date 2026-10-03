# Delivering finalized execution order

**Orderer converts authenticated consensus history into an exact sequence for Executor.** It retains the evidence needed to explain that sequence, pauses at unresolved gaps, and tracks durable delivery acknowledgements. Native sparse finality and continuous execution order are separate outputs.

## Consensus and Baton integration

Rust declaration: [Orderer](../overview/rust-interfaces.md#orderer). The Rust interfaces page owns the complete declaration.

`Evidence` binds exact authenticated source witnesses to policy/history interpretation. Storing a notice or normalized projection alone does not retain the witness. `next_range` returns only continuous irrevocable input; an unresolved gap requires backfill or pending work. Missing included bodies are not empty slots. `acknowledge` advances the application delivery cursor after verifying a durable CommitResult for that exact range. It is neither a native vote acknowledgement nor a body-release request.

The trait combines public history retention, ordering interpretation, and delivery boundaries. Source-witness export and native policy adoption remain separate integration work on the existing owner. Orderer cannot authenticate or adopt native proposals on its own authority.

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
