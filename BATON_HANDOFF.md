# Baton — current research handoff

Updated 2026-09-30. This supersedes the current-state claims in [SESSION_HANDOFF.md](SESSION_HANDOFF.md), while preserving that earlier handoff as history. Research/specification work only; no native adapter, completed integration proof or E2E results.

## Source priority and synchronized documents

1. Latest explicit user decisions and current Google Docs.
2. [Baton paper](baton-paper.md) and [implementation specification](baton-implementation-spec.md), manually synchronized from the revisions below.
3. Historical Overpass outline/design/reviews, earlier handoffs, draft PR1, toy and archive material as cited context.

| Document | Native Google Doc | Verified revision |
|---|---|---|
| Paper: problem, mechanism, indispensable assumptions and conditional arguments, evaluation and limitations; eight sections | [Baton: Execution-Aware Ordering for Autobahn](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) | `ANLCKQkG0bHiwlyzmrsvy0ssYwUXBdYIZvrpOvfxOLFeGvcK8xGB0DbgU98dIpGftngtMnZ54s8SIFlx7ZtTGE39xSerkGJGnQ1AkrW1qK4` |
| Specification: identity/context, admission, frontier, bounds/completion, proposal/slot/recovery, signing, retention and alternatives | [Baton — 구현 스펙](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) | `ANLCKQldFScCUBScmgJIyaYLPQlgBG0-jI0rlb5_U3v2gX0Xu8MAXhBxHcyjHNY82H-xP142eGYXdLIhDp3KqCjj-Q226UsQGutIAR_eHK0` |

The repository name remains `overpass-research`. Historical citation titles and source URLs remain intact. These are manual counterparts, not automatic two-way synchronization. A later native revision or user decision requires deliberate reconciliation rather than overwriting either side.

## What changed from the earlier repository snapshot

- Renamed the conceptual project to Baton and use direction instead of plan in current narrative.
- Replaced sum-only selection by 2f+1-supported entire-prefix first, with sum-LCP fallback and valid actual-parent base fallback. Longest selection is relative to the completed bounded admissible candidate set.
- Precisely closed the local snapshot at 4f+1 admissions or fixed deadline, excluding excess/later reports. Local prefix uniqueness uses m<=4f+1; it does not extend to larger native recovery pools or different snapshots.
- Made immutable ordering frontier, raw-report support, bounded candidate validation and selected/emitted/signed prefix distinctions explicit.
- Strengthened the goal to leader/validator cut construction that preserves selected prefix membership AND exact leading sequence for the same canonical context. Pure advisory ordering over arbitrary independent native membership is insufficient for this requirement.
- Separated implementation contracts from the eight-section paper, retaining essential native sufficiency/recovery/no-wait uncertainty and conditional reuse in the paper.
- Kept authenticated proposal freeze, progressive native finality and the exact-order + f+1 execution-signature endpoint. Retention and common signing boundaries are required for eventual completion, not implied by cryptographic result safety.

## Core preservation obligation and unresolved bridge

For a selected valid prefix p protected by the adopted proposal, final executable order O after the immutable frontier must satisfy p ⪯ O in the same canonical input state/runtime. A1 and B1 membership with A1→X→B1 fails preservation of p=A1→B1. Extra native blocks cannot simply be discarded. A candidate missing a mandatory predecessor is invalid from the start.

The precise boundary between advisory selection and protected authenticated adoption is not yet specified. Cut no-wait allows a prepared valid actual-parent fallback before adoption; it does not license dropping an already protected prefix. Requiring an unavailable/unadopted prefix in every ready cut conflicts with that fallback. The user adopted preservation as a high-level requirement, not a finished availability/vote-validity/continuation/recovery construction.

Already-ready certified anchors are a possible native inclusion bridge; adding positive-adoption conditions to proposal/vote validity is another unadopted route. Neither has a completed cross-lane leading-prefix, no-wait or recovery proof. Do not silently force invalid/unavailable blocks, remove native extensions or restore the historical direction approval lock.

## Pinned source findings and caveats

Commonware commit: [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72).

- Final proposal position is the **3f+1-th greatest** position. Ordinary payload B at position j needs at least 3f+1 pool votes with position>=j for finalized position>=j. Extension carry additionally uses native n−f support when the finalized proposal position reaches proposed tip. [tips.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143)
- Vote position reflects local consecutive DA-voted valid path. A node may know a proposal without a local positive DA path; position 0 is then legal. [chain.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978), [proposal validity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L2601)
- In the stated f=1,n=6 ordinary-payload example, h1,h2,b report B; h2's view vote is delayed; b knows B but votes low. Pool h1,b,h3,h4,h5 has positions [1,0,0,0,0]; fourth greatest is 0. Only three honest nodes lack B. Final tip G is unsettled below B, so this does not prove permanent exclusion or arbitrary later emission. Requiring a complete DA certificate for candidate eligibility could make this example inadmissible. It is source-level analytical reasoning, not an executed protocol trace.
- At/below a valid DA-certified anchor, B is part of the position-0 base ancestry. Low positions cannot exclude it. This distinguishes the anchor case from ordinary payload support, without proving the cross-lane leading order. [anchor selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1880)
- Native certificates, tip history and consensus retention do not supply dense ordered delivery, policy content, emission evidence or durable marshal cursor. Recovery must preserve terminal decisions, previously emitted prefixes and protected direction prefixes. Source inspection does not close the modified native proof.

## Four proposed defaults remain unadopted

| Choice | Recommended proposal, not adoption | Tradeoff | Exactly what remains blocked |
|---|---|---|---|
| Signing boundaries | Per-block deterministic statement boundaries with canonical parent/result checkpoints | More signatures and retained intermediate state than chunks | Exact range/statement schema and common-boundary result liveness |
| Same-supported-prefix tail | Keep valid incumbent; canonical tie-break if none | Less churn, but may give up a higher tail sum-LCP score | Deterministic tail/update rule; first-tier longest-prefix rule is already fixed |
| Policy availability | Bounded canonical policy bytes inline in authenticated proposal | Larger proposal versus commitment-only retrieval obligations | Concrete encoding/availability/recovery interface |
| Continuation | Finite valid initial-prefix ancestry-preserving permutation followed by original base sweep | Restricted reorder scope; compatibility and eligibility still need proof | Exact completion rule and its common-prefix proof; cannot alone guarantee native inclusion |

These choices do not automatically solve or select the native prefix-adoption bridge. τ/W/budget tuning and benefit are empirical questions. No new choices were adopted during synchronization.

## Draft PR1 and next validation boundary

[Draft PR1](https://github.com/djm07073/overpass-research/pull/1), head `0a06faff9b859da16b31f285c28128e0768662e2`, remains unmerged and open. Its P/Q/P+ B2-extension fixture, legal-transcript checks, unresolved-slot-skip negative mutation, policy freeze/recovery/cursor checks, matching-f+1 endpoint and common-resource E2E gates remain useful. Its finite D=[B,B,A] encoding is a test candidate, not an adopted continuation or proof of selected-prefix preservation.

Before treating that plan as current implementation work, add the protected-prefix adoption/inclusion/leading-order gate and verify it through native extension and view recovery. Preserve its distinction among exact-five L-QC, larger sticky pools and safe V-QC facts. No fixtures or gates were executed by this documentation update.

## Checks performed for this synchronization

- Re-read native revision-protected content, preserved all paper heading roles/eight sections and References, and checked the removed technical paragraphs were retained in the specification.
- Confirmed both native cross-document Workspace chips target the right files and show Baton titles; owner-only access remained unchanged.
- Checked final native PDF exports page by page: paper 14 pages, specification 10 pages. This is exported-PDF layout QA, not a live browser-canvas check.
- Checked descending native rank, certified-anchor non-exclusion wording and the analytical-transcript caveats. Corrected the final-position comparison to j-or-greater and Korean naming grammar without changing decisions.
- Markdown paragraph/citation preservation, local links, references and Git diff/whitespace are checked separately before commit. Git publication/CI status belongs in the delivery report; it is not native protocol validation.

No protocol implementation, native/toy tests, protocol compilation, benchmarks, spending, credential reconfiguration or draft-PR management was performed. Future implementation requires explicit scope; do not ask again for decisions already adopted.
