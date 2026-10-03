# Independent review of the emerging canonical Rust interfaces

Reviewed `docs/overview/rust-interfaces.md` while central edits are ongoing. Snapshot SHA-256: `a3986900997d622d7c22a62e3d66614f2815963dbee4821a960a6b66c2c48f24`. This review writes only this file; no canonical page, export, other report or protocol source was edited. It is an interface/source review, not protocol validation or a final whole-document coherence audit.

## Verdict

The revised page correctly removes the redundant BlockService trait and uses the existing Commonware callback signatures. Its five proposed application traits are TxPool, Orderer, Baton, Executor and Storage; BlockService is a logical attachment rather than a sixth mandatory trait/actor. Executor emits completed effects; Storage prepares roots and applies/persists state; Baton owns direction planning. The key storage cross-review corrections requested for this page are present.

No incorrect upstream callback signature was found. There is one preparation-access clarification to carry into the final canonical storage text, plus cross-page/export checks to finish after root's ongoing edits settle.

## Exact upstream signatures

Compared all four excerpts, ignoring only whitespace, against the exact native source at `534af0ede48affd35b2111522527547b4cc9bf72`:

| Method | Result |
|---|---|
| `Automaton::propose(&mut self, context: Self::Context) -> impl Future<Output = oneshot::Receiver<Self::Digest>> + Send` | Exact normalized match |
| `Automaton::verify(&mut self, context: Self::Context, payload: Self::Digest) -> impl Future<Output = oneshot::Receiver<bool>> + Send` | Exact normalized match |
| `Relay::broadcast(&mut self, payload: Self::Digest, plan: Self::Plan) -> Feedback` | Exact normalized match |
| `Reporter::report(&mut self, activity: Self::Activity) -> Feedback` | Exact normalized match |

Primary sources: [Automaton](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L116), [Relay](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L224), [Reporter](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L246).

The page labels them method excerpts with omitted trait bounds/imports, rather than standalone trait declarations. Application comments are distinguished from upstream signature provenance. Native Multimmit's example uses `Context<H::Digest>` and Relay `Plan = ()`; the page reflects this. [Native attachment](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/application/actor.rs#L36).

The excerpt's pending-versus-permanently-invalid description matches native Automaton. The detailed body page should continue to explain producer decline, live verify receiver closure, storage failure and recovery behavior; these are not all visible in the short excerpt. Reporter receives a whole Activity enum, so implementations must match the relevant accepted producer-artifact variant before the header/body join. It is not itself a durable evidence-export channel.

## Checked responsibility and safety boundaries

| Boundary | Current page evidence | Assessment |
|---|---|---|
| Direct body primitive assembly | BlockService prose and callback block route to buffered mailbox, generic resolver Producer/Consumer and archive handles | Correct: no custom broadcast/cache/retry engines are introduced. `get`/`subscribe` are local availability, resolver fetch is active peer lookup. |
| No native retire method invented | Paragraph after callback excerpts states Relay has no `on_retire` | Correct: a native retention/lifecycle bridge remains application integration. |
| Application versus existing source | Five `rust` declaration blocks; one `rust,ignore` callback block | Correct separation. The export tool's exact regex matches only `rust` followed immediately by newline, so `rust,ignore` is excluded. Do not imply exclusion means the excerpt was compiled. |
| Executor/Storage split | Execute returns completed changes/outputs; Storage prepare computes result commitment; apply proves durability/linkage | Correct: no mandatory root for every speculative attempt, no transaction execution moved into Storage. |
| Shared subject excludes local fields | Executor sign_result comment excludes local worker generations; Storage postscript excludes local generation, writer permit and retention coordinate | Confirmed requested correction. Physical metadata must not implicitly prevent f+1 matching among honest validators. |
| Selected storage rule and full result | Storage prepare comments bind selected rule, exact base/input, outputs and material to PreparedResult | Confirmed requested correction. Associated concrete fields and hashing choices remain open. |
| Honest custom rootless overlay | Execute and Storage prose distinguish upstream unmerkleized work from an application draft/read adapter; postscript says fork_batches accepts Merkleized parent | Confirmed: no upstream unsealed-parent fork or arbitrary snapshot is claimed. [Native fork API](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L548). |
| Direct/imported provenance | Sign requires retained own direct evidence and forbids imported material as own execution; ending text requires certificate plus applicable material before stopping work | Correct high-level boundary. Detailed import/preparation methods remain open rather than being falsely declared complete. |
| Full f+1 agreement | collect_result checks matching full subjects from distinct eligible epoch validators; verify_result checks exact order and canonical input chain | Correct: transport/raw collector counts are not certificates. No ordering-QC membership gate is added. |
| Durable canonical completion | Storage apply requires state, outputs, cursor and provenance recover together; failed flush is not success; Executor commit returns afterward | Correct application obligation. It is explicitly more than upstream readable state or a Barrier in isolation. |
| Actor independence | BlockService and Storage prose both make additional actors deployment choices | Correct: primitive reuse does not force Stateful or an additional actor per role. |
| Planning/no wait | Baton plan remains direction selection and cut never waits for its future; no direction vote/ACK/Ready quorum | Preserved. |

## Clarification to carry into the final canonical text

`Storage::prepare` must preserve valid base access throughout lazy reads, staged expansion, rootless materialization and Merkleization. The current preparation comments require correct binding but do not explicitly mention this access lifetime. Add a brief sentence on this page or an unambiguous linked detailed contract: preparation validates/holds admissible branch access, and canonical apply/imported swap fences or rebases incompatible work before further live-state use.

This matters even though eventual apply performs ancestry checks. Any batch reads fall back to the supplied/current database, and glue wrappers take a fresh Shared read guard for each call. A start-time binding check or final worker-generation check cannot repair intermediate reads against an incompatible canonical base. [Native read-through](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L1760), [release wrapper reads](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/any.rs#L110).

Likewise the detailed canonical writer contract must cover every cloned DatabaseSet alias, recovery, pruning and imported swap route. `&mut self` on the Storage facade expresses local sequencing but does not itself revoke independently held upstream mutation handles. This is already an open integration contract rather than an upstream guarantee; keep it explicit in QMDB/recovery pages. [Native DatabaseSet cloning/mutation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L508).

## Checks deferred until central edits settle

- Refresh `docs/assets/interfaces/baton.rs` through `npm run docs:interfaces`; verify it has precisely five application trait declarations and no standalone callback excerpts or BlockService duplicate.
- Remove stale `Executor::read` and `BlockService::build/fetch/publish/on_retire` references from layer/E2E interface mappings; use Storage read and direct callback/handle paths. Current old layer pages are known in-progress targets, not final coherence findings.
- Verify links to `#existing-apis-at-the-native-pin-and-indexed-release` and `#copy-the-assembly-from-real-chains` once those sections are written.
- Keep native `finalize(sealed)` and release `apply(sealed); finalize()` recipes separately labelled; avoid calling the latter native while using a native URL.
- Ensure diagrams show Executor → Storage for preparation/durable mutation and show unsealed/rootless application work distinctly from upstream sealed-parent batches.
- Preserve body archive occupied-index/below-floor no-op cautions and Marshal resolver receiver visibility in the detailed assembly sections.
- Check `Executor::ExecutionResult`, `Storage::ExecutionResult`, `Storage::PreparedResult`, `Executor::PreparedResult` and CommitResult type equalities in the interface-reading page. These are application attachment equalities, not automatically enforced merely by identically named associated types in separate traits.

No numeric policies, root variant, signature interval, overlay persistence schema, custom actor requirement or native consensus default was adopted by this review.
