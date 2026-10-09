# Round 5: local ordering authority and peer result authority

Initial read-only review of current reader pages against parent source `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. The root then authorized the minimal startup-authority clarification in owned consensus/ordered-input and reference/integration pages; those changes are applied. No protocol edits, new codecs or tests were made in this round.

## Finding and smallest correction

The docs consistently assign ordinary order reconstruction to existing Marshal and do not require an App-side Orderer. They also correctly leave result codecs, target binding and full Baton native policy unresolved. Two short clarifications would prevent readers from reconstructing the old extra layer:

1. In result-certification/state-sync prose, state that a node binds its execution range to its own authoritative Marshal stream plus recovered App checkpoint; it does not independently reverify native evidence for every local Update. A peer-supplied Update-shaped object is not the same trusted local callback and is not a portable finality proof.
2. In startup/recovery and floor-import prose, distinguish `Start::Floor` from runtime `install_floor`. **Fresh `Start::Floor` is caller-authenticated; `marshal::open` and Config validation do not verify its anchor signature.** Providing SchemeVerifier at the later service start does not retroactively authenticate it. The existing source recommends starting from Genesis and calling `install_floor` for a floor served by a peer. No new verifier framework is needed.

The second point is a concrete omitted source boundary. Existing “authenticate the floor-to-state relation” wording is necessary but does not explicitly tell an implementer which startup API already performs native proof verification.

## What the local stream establishes

`marshal::Update` contains exactly OutputIndex, Arc<complete block>, and Exact acknowledgement (`consensus/src/multimmit/marshal/types.rs:128–136`). The full block supplies producer epoch/chain/height/header-parent/body binding. It does not supply an L-QC, native finality proof bundle, execution base/root, application runtime/rule, Baton report window, adopted policy, execution certificate, or floor generation.

Marshal's owner graph verifies/reconstructs native history, commits dense output rows and reports them in order (`marshal/mod.rs:1–46`). Delivery reads only through committed progress; cold reads check each output index and block reference before reporting (`marshal/actors/delivery/actor.rs:237–302`). OutputIndex is canonical **within one stream**, with index zero reserved for genesis (`marshal/types.rs:54–63`). An index alone does not identify a deployment, epoch transition, execution state or result.

The App therefore uses the exact local Update sequence and its recoverable applied-state identity to establish the input/base relation for execution. Its remaining checks concern range identity, exact canonical predecessor, runtime/result interpretation, replay and imported-material applicability. This does not require rerunning Marshal's history walker or placing an additional native finality gate in the canonical apply path.

Reading an Update is also not transaction validation by Marshal: its body is opaque application data. The App still enforces its transaction/effect/state contract. Conversely, a completed speculative result does not turn an unresolved candidate sequence into irrevocable input.

The following current pages already support this split: `docs/consensus/ordered-input.md`, `docs/baselines/precut.md`, `docs/baton/interfaces.md`, and `docs/e2e/canonical.md`. Wording in `docs/execution/interfaces.md` requiring “verified irrevocable order” is sound as a condition, but could be read as a second proof-verification component without the short local-stream clarification above.

## What native floors establish, and what they assume

Floor carries anchor L-QC, committed tip-history opening and emitted producer frontier (`marshal/types.rs:320–362`). It assumes the imported application snapshot contains all input through that frontier. It does not contain or authenticate an App state root, output contents, runtime/rule, result certificate, or direct-execution provenance. Its output index derives from the emitted heights; MarshalProgress similarly contains native generation/floor/committed/acknowledged values, not an execution state (`:445–456`).

For a running service, `Mailbox::install_floor` reaches the supplied LqcVerifier, checks epoch/view freshness, history commitment, nonregressing frontiers, final-sweep bounds and ancestry, then installs the native checkpoint (`marshal/actors/synchronizer/floor.rs:52–159`; `marshal/protocol/floor.rs:37–96`). App snapshot authentication and cross-store handoff still remain App responsibilities. Installing a valid floor cannot prove that a random QMDB root is the result of its prefix.

For fresh storage, `Start::Floor` is explicitly an import authority authenticated by its caller. The caller must authenticate the epoch L-QC anchor and bind emitted frontier and positive floor generation to the imported application snapshot (`marshal/config.rs:164–185`). `Config::validate` is structural (`:535–540`). The storage seed checks shape/history linkage and writes the imported checkpoint before the later service receives its verifier (`marshal/storage/catalog/mod.rs:448–502`). A recovered durable checkpoint wins over Start; replacing configuration is not a runtime floor update.

Minimal supported route for a peer-served floor is the source-documented `Start::Genesis` plus `Mailbox::install_floor`, coordinated with App snapshot authentication/durability. A deliberately trusted fresh Floor bootstrap can instead reuse the existing epoch verifier before opening, but this review does not specify a new bootstrap protocol or claim that signature verification alone establishes application-state correctness.

## Peer certificates and material stay separate

The docs' proposed result endpoint binds exact input/range, canonical base, runtime/rule and result to `f+1` distinct eligible epoch signatures. Those fields are not automatically copied from an Update. The App chooses and validates the complete stable subject under its still-open result codec/domain and boundary contract; its local stream or authenticated checkpoint establishes the relevant input authority.

For normal local progress, match a peer statement to locally established exact input/base before importing its verified material. A certificate arriving before that local ordering relation is available stays pending; it does not establish order by itself. A floor-based catch-up additionally needs the native floor and authenticated floor-to-App-state relation. For an external result consumer without the local stream, the exportable native input/checkpoint evidence and verification contract remain open. Do not serialize an Update or attach an arbitrary index and call that contract implemented.

QMDB target/proof verification authenticates retrieved material against a caller-trusted target; it does not choose or authenticate the execution target (`storage/src/qmdb/sync/mod.rs`). A valid operations proof or reached-target notification does not replace execution certificate verification, exact predecessor checks, imported provenance, or durability. The current `docs/execution/state-sync.md` and E2E state-sync page already preserve these distinctions.

There is no existing Baton rule/window/adopted-prefix field in current native Update/Floor that can satisfy full Baton automatically. The proposed native protected-policy change remains separate protocol work; neither local App reordering nor stronger peer result signatures can supply it.

## Reporter Feedback is not one universal delivery contract

| Caller/adapter | Current source behavior | App implication |
|---|---|---|
| Generic Feedback | Ok means accepted within capacity; Backoff means overflow policy handled the submission; Closed means endpoint closed. `accepted()` includes Ok and Backoff. | Feedback alone does not specify processing, persistence, retry or quorum semantics. `actor/src/lib.rs:13–28`. |
| Native activity dispatch | Engine discards the return from `reporter.report(activity)`. | Optional App Activity Backoff/Closed neither gates native progress nor promises replay. `multimmit/actors/voter/actor/live.rs:412`. |
| `Reporters::from((marshal, app_activity))` | Calls both present reporters; combines their statuses with Closed > Backoff > Ok. Does not remove a branch or install a retry queue. | Optional App observer failure does not suppress the same call to Marshal. The combined status is still ignored by native activity dispatch. `consensus/src/reporter.rs:31–55`. |
| Marshal activity mailbox | CertificateRecorded uses its dedicated release lane; other native activities use hint routing, with rejection mapped to Backoff. | Pass actual native observations to existing Marshal. Optional observers must not become an alternative canonical stream. `multimmit/marshal/mailbox.rs:503–522`. |
| Marshal Update delivery | Constructs one Exact, invokes reporter, fails on Closed; every other return keeps the waiter in the pending window. It does not resend because of Backoff. | App must retain the original Update/token. Lossy observer adapters cannot be reused for this boundary. `multimmit/marshal/actors/delivery/actor.rs:303–327`. |

`Option<Reporter>::None` returns Ok while dropping its input (`consensus/src/reporter.rs:11–18`). That is harmless for optional native observations but cancels an Update's unacknowledged Exact. Similarly, fanning out Update through generic Reporters clones Exact: every clone must acknowledge. The current docs appropriately use two typed App handles and describe reporter composition for native Activity, not as a shortcut for optional canonical-delivery sinks.

The Update handoff is guaranteed only by the implementation's retained inbox/ACK contract, not by the shared Reporter trait. A custom reporter returning Ok after dropping an Update still breaks delivery. No second delivery service or extra App approval stage is warranted; retain the existing Update in the canonical worker path.

## Review disposition

No contradictory implemented result proof or App Orderer was found. The fresh Floor authentication clarification is now applied to the owned ordered-input and integration pages; root/other owners are aligning their startup/state-sync entries. The local-stream clarification remains a recommendation for result-certification prose. Keep future remote result/evidence representation and cross-store import sequencing explicitly open. All statements here are source-inspected; no protocol integration, imported checkpoint or result certificate was executed or proved.
