# Round 4: scheduler invariants and execution diagrams

Reviewer: `/root/simplification`. Fresh read of `docs/baton/direction.md` and actual PNG render inspection of diagrams 17–19. This is design/source/visual verification, not executed scheduler/protocol tests or proof completion.

## Visual findings and smallest changes

| Diagram actually viewed | Finding | Resolution |
|---|---|---|
| 17 — QMDB/app flow | Labels visible with no clipping. Marshal Update entered the App subgraph boundary immediately above the scheduler, which could imply canonical processing depends on scheduler dispatch. | Root authorized targeting the existing execution/reconciliation node E directly. Inline Mermaid and diagram-17.mmd updated; no extra node/interface. Root owns targeted rerender. |
| 18 — execution tree | Canonical S0, reusable A/AB, alternative C/D descendants and different X→A context are visually distinct. All labels/arrowheads fit; no wrong-parent edge or clipping observed. | No change. |
| 19 — PreCut assembly | The long Application group title wrapped; its second line was obscured by the callback box. Canonical input correctly bypasses scheduler preference, and peer result traffic connects execution directly. | Root authorized the shorter “PreCut application” title. Inline Mermaid and diagram-19.mmd updated; root owns targeted rerender. |

Diagram 17 remains one App subgraph with reused QMDB handles outside it. Optional rootless effects/overlay is visibly optional; it does not claim QMDB supplies an unsealed-parent fork. The canonical writer and covering-durability/ACK return are distinct. Diagram 19 keeps native consensus/Marshal outside the App and pool/scheduler/shared execution/state inside, without creating mandatory services or public traits.

## Fresh scheduler invariant audit

| Requirement / adversarial analytical case | Current direction page | Result |
|---|---|---|
| A executes; C then B are admitted before C starts | Preserve F=A; pending becomes B,C; exact-parent dispatch gives ABC. | Pass |
| B arrives after C starts on A | Preserve F=AC and append eligible B. Ordinary arrival does not cancel/reexecute C to force ABC. | Pass |
| Only A/C are known | Eligible AC need not wait for hypothetical B. Required ancestry and parent checks remain. | Pass |
| Nodes know the same total set but have different F | Page permits ABC versus ACB; equality requires the same context/rule/F/pending. | Pass |
| Canonical input differs from speculation | Shared reconciliation compares exact prefix/base/runtime, repairs missing work and fences incompatible workers plus live DB access. F is not canonical. | Pass |
| Different identities support each separate position | Rejected as whole-prefix support: the same original distinct reports must match every position from the common origin. | Pass |
| Five reports at f=1; ABCD sum=10 and ACBD sum=11 | ABCD wins because AB has three whole-prefix supporters versus only A for ACBD. Longest supported prefix outranks raw score. | Pass; arithmetic consistent |
| Candidate evaluation unfinished | Cannot declare longest-prefix selection over the full admissible candidate set. Work is bounded/background; native cut does not await it. | Pass |
| No supported nonempty 2f+1 prefix | Use raw sum-LCP among valid full candidates; no subtraction of f largest values or manufactured support. | Pass |
| Reports continue past threshold or deadline | Close once at first processed 4f+1-valid-admission/deadline event; m≤4f+1. New arrivals do not extend deadline or alter closed originals. | Pass |
| Signature verification finishes after closure | Completion alone is not admission; late processing stays outside the frozen snapshot. | Pass |
| Re-sort F or fill missing candidate inputs before scoring reports | Original signed sequences remain intact; completion does not create support. | Pass |
| Previous direction execution is slow | The leader-local evaluation/dissemination-or-skip cycle may finish and allow the next eligible cycle; no all-node execution wait or direction ACK/Ready quorum. | Pass |
| Cut arrives before valid preparation | Actual-parent valid native base may be used before protected adoption; no report/timer/planning approval barrier. | Pass |
| Policy/body is missing after authenticated adoption | Recover authenticated interpretation; cannot silently drop protected prefix or reinterpret proposal as base order. | Pass |
| Final order contains prefix members with an inserted X | [A1,X,B1] does not preserve selected [A1,B1] as exact leading order. Mandatory predecessor X would invalidate that candidate beforehand. | Pass |
| Preferred prefix excludes extra native inputs | Preserve native tips/extensions and do not delete extra inputs to force the preferred order. | Pass |
| App tries to implement full Baton by sorting Updates | Forbidden. Automaton context is producer context; actual leader-policy adoption/validation/Marshal interpretation remains missing native work. | Pass |

The report context continues to bind epoch, view, history, canonical parent, rule, window and immutable frontier. Reports remain intentions, not execution progress or native inclusion certificates. `2f+1` yields an `f+1` honest-intention lower bound under the same fault budget, not completed execution or canonical uniqueness across windows.

## Four unadopted choices remain unadopted

| Previously proposed default | Current treatment |
|---|---|
| Per-block result signing | Execution signing scope/common boundary is blank/open. Per-block Marshal Update/ACK does not select the signature boundary. |
| Incumbent-first tail | Tail, tie and hysteresis remain open; the page does not force incumbent retention. |
| Inline policy bytes | Native proposal binding is required, but representation/availability remains open; consensus decisions still leave inline bytes versus retrievable commitment undecided. |
| Finite-prefix permutation followed by base sweep | No concrete continuation algorithm is adopted. Exact continuation, native sufficiency and view-recovery proof remain open. |

## Rootless execution and retained responsibility audit

Removing public Executor/Storage traits has not removed transaction semantics, exact execution ancestry, selected root preparation, writer authority, durability or result provenance. Concrete QMDB handles remain beneath these App responsibilities.

- Unsealed continuation and sealed-parent forks are different supported paths. Rootless branching needs retained exact effects/replay or a chosen overlay; no generic extra read-view service is mandated.
- Selected root computation precedes full-result signatures. Abandoned speculative work need not be hashed. Deterministic operation/batch boundaries and result-root scheme stay open.
- Same logical key values do not establish storage ancestry. A sealed ABC batch cannot be partially applied as AB; reconstruct the exact boundary or reexecute, and then recheck C applicability.
- App writer mutation and live-access fencing are separate from stale-completion rejection; current direction pseudocode now names both.
- Direct application/ACK remains independent from peer f+1 collection, while verified imports require their certificate/material and preserve imported provenance.

No new abstraction or protocol choice is recommended. Only the two visual/source clarifications above were necessary in this round. Final targeted render readback is pending the root renderer.

Review recorded 2026-10-09T07:21:52+00:00.

## Targeted render readback

Fresh actual PNG readback at 2026-10-09T07:24:24+00:00: diagram 17 now routes Marshal Update directly into execution/reconciliation, with no clipped labels or overlapping shapes. Diagram 19 no longer hides a wrapped title line and all boxes fit. One minor visual crossing remains: the native callback arrow passes through the word “application” in the group title; root was told that shortening it to “PreCut” can remove this without changing meaning.

- `docs/assets/diagrams/diagram-17.mmd`: `9ac290c7ec5ea996a6e1488dbb4554d03f54265d0344ad334c649f64b0fde824`
- `docs/assets/diagrams/diagram-17.svg`: `d1ab8c7d8132e54327e5c06687eb98544f812ccb43251cb9d6b3712f9463ecab`
- `docs/assets/diagrams/diagram-17.png`: `a87b01a7e02e28ebdcb17bed630ba495130aaa19b2521430f496fe9ff2df7f31`
- `docs/assets/diagrams/diagram-19.mmd`: `7d1b80fa68b7663856ea84adaeca61e2addf63260ede80ca3191f84a818dc058`
- `docs/assets/diagrams/diagram-19.svg`: `1ea8b129c156bd94c8f0a9feeec1aa033656da143e5fb7ece9cd717663068301`
- `docs/assets/diagrams/diagram-19.png`: `c3039d27c526af356b0a6e27af5ff930f112b09e7deed80247e2a50f867e7b63`

## Proposed next focused scenario

A remote verify begins, then canonical Update processing (or a verified import) applies that block before the original App verification completion is admitted. Native cancellation may drop the receiver while App body/custody work still finishes. Check the current applied identity again at candidate admission and dispatch so stale completion cannot resurrect already-applied speculative work. Verify validity/custody can still be satisfied independently of speculative cancellation and effect GC. This combines callback, canonical-worker and retention state without rerunning unchanged diagram/link tests. It requires no new trait or protocol event.
