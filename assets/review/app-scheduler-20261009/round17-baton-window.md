# Round 17 — Baton report-window and candidate-selection traces

Read current `docs/baton/direction.md`, core README/interfaces, `docs/e2e/leader.md`, consensus open decisions and verification acceptance cases. Checked existing Clock/strategy and native proposal source where relevant. This is an analytical design audit: the Baton report protocol, candidate policy and native adoption bridge are not implemented or runtime-proved by this review.

## Finding and minimal recommendation

No confirmed semantic contradiction was found in the current adopted rules. `direction.md:47-73` and `e2e/leader.md:39-41` consistently use owner-processed admission/deadline events, frozen original reports, bounded full-candidate evaluation and entire-prefix support. No core edit was made.

One optional reader clarification was sent to root for `direction.md:60`: “Admission and deadline events serialize at the App owner; packet arrival or worker completion timestamps do not backdate admission.” This restates the existing first-processed-event rule. It must not silently become a new timer-priority rule, receive-time cutoff, deadline extension or equivocation policy.

## Window closure: concrete event traces

Let `f=1`, so the admission threshold is five. `D` is the deadline fixed when window W opens. A “processed admission” below means the App owner has checked verified report/context/identity/limits and admitted it; packet receipt and worker completion alone are not that event.

| Event order | Required result from current design | Owner/mechanism |
|---|---|---|
| W has four admissions; the fifth valid distinct report is processed; deadline is processed later | Close immediately with exactly those five original reports. The later deadline cannot close again or change the snapshot. | App-owned W state; `direction.md:51-60`. |
| W has four admissions; deadline is processed; fifth report was received earlier but verification is still running | Close with four. Verification completion after closure is outside W, regardless of earlier network receipt. | Existing Clock deadline event plus owner admission check. |
| W has four admissions; fifth report's crypto work already completed, but deadline is processed before its completion message | Close with four. Worker completion time is not retroactive admission authority. | `direction.md:52,60` explicitly separates worker completion from admission. |
| W has four admissions; deadline and the fifth completion are both ready; owner processes the completion/admission first | Close with five by threshold. The first-processed-event rule does not prescribe how the event loop prioritizes simultaneously ready sources. | Serialized owner decision; no new timer-priority policy inferred. |
| Same readiness state; owner processes deadline first | Close with four; the fifth completion stays outside W. Both this trace and the preceding trace satisfy the stated event-order rule. | Same existing owner/Clock mechanisms. |
| W has four admissions; one worker batch returns two additional valid distinct reports | Admit serially against current W; the first reaches five and closes. The sixth must not be inserted merely because it arrived in the same batch. | Atomic per-admission state update; `m <= 4f+1` is an invariant, not an eventual cleanup target. |
| A stream of new arrivals appears before/after D | The fixed deadline is never rearmed to `now + timeout`. The owner still services the deadline without waiting for pending verification/planning. | One existing deadline future; bounded App handling. |
| An old deadline event remains queued after a new window opens | It belongs to the old window/context; it cannot close the new window or alter its own fixed deadline. | Existing exact window/context identity, not a new public event type. |

The docs choose processed-event order, not a universal packet-timestamp inclusion rule. If the owner is delayed and multiple events are ready, the implemented event ordering determines the winner. The timer still retains its originally fixed deadline, and no report gets backdated into a closed snapshot. Choosing a deterministic simultaneous-readiness priority or an explicit hard receive/verification-time cutoff would be additional policy; this audit adopts neither.

`Clock::sleep_until` already supplies the deadline future (`runtime/src/lib.rs:500-514`). It does not itself admit reports or choose among App events. CPU work must not delay the owner by accidental inline computation: `Strategy::spawn` may execute before returning or while polled (`parallel/src/lib.rs:184-197`), and `Sequential::spawn` actually calls the closure before returning (`960-970`). The current worker-placement sentence at `direction.md:62` correctly covers both creation and polling.

## Duplicate, equivocation and stale-context traces

**Duplicate verification completion.** W admits identity X's original signed report. A duplicate packet or two verification workers later report the same report. Owner deduplication leaves one X and one count. Duplicate completion does not move the threshold or rewrite the stored original sequence. No separate deduplication service is needed.

**Two conflicting reports from one identity before closure.** X signs `ABCD` and `ACBD` in W. Both signatures can be cryptographically valid, but X cannot contribute two admissions or two supporters. The choice to retain one, reject the identity or otherwise handle conflict remains explicitly open (`direction.md:107`). Whatever policy is chosen must leave at most one eligible counted original report per identity in the snapshot and must not synthesize a third sequence. This review does not choose first-wins or last-wins.

**Equivocation learned after closure.** The frozen snapshot already contains X's selected original. A late conflicting report cannot silently replace that sequence, remove it and refill the window, enlarge the snapshot or restart the deadline. Conflict/evidence handling remains open, but it cannot violate immutable-snapshot scoring. Counting one Byzantine identity once preserves the stated fault-budget accounting; an authenticated report remains intention, not execution progress.

**Same signer in another context.** A valid report for W0 or another epoch/view/history/canonical parent/rule/frontier arrives during W1. Signature validity alone is insufficient. Owner rejects it for W1; it cannot satisfy W1's threshold or support. Reports must bind every listed context dimension (`direction.md:47`).

**Stale planning completion.** Plan A0 starts from W0's snapshot. The owner moves to W1, or starts a newer current planning attempt A1 in the same relevant context. A0 completes later. `direction.md:60` requires original window/context and current-attempt validation before publishing prepared state, so A0 cannot overwrite A1/W1. This is ordinary App-owned request identity.

**Parent changes after App publication.** A plan passed App owner checks, but native proposal construction now uses a different parent/history/frontier. Native must recheck the prepared policy against its actual proposal immediately before adoption (`direction.md:93`; `e2e/leader.md:55-66`). App freshness and native actual-parent validity are different checks; neither replaces the other.

## Candidate evaluation and scoring traces

### Whole-prefix support cannot be assembled position by position

Assume these five original reports and candidate `ABCDE` share one admissible context:

| Report | Original sequence |
|---|---|
| R1 | ABCDE |
| R2 | ABDCE |
| R3 | ACBDE |
| R4 | DBCAE |
| R5 | EBCAD |

Position 1 is A in R1/R2/R3. Position 2 is B in R1/R2/R4/R5. Position 3 is C in R1/R4/R5. Thus each of those positions separately has at least three matching reports. Nevertheless only R1 supports the entire ABC prefix, and only R1/R2 support AB. The longest threshold-supported prefix of this candidate is A, not ABC. The same distinct original supporters must match every position from the common origin (`direction.md:64`). All rows are synthetic analytical sequences; they do not select the real candidate universe or native ordering policy.

### Longest supported prefix outranks a larger raw score

The current page's example remains arithmetically correct: original `ABCD, ABDC, ABDC, ACBD, ACBD` gives ABCD a supported AB prefix and sum 10, while ACBD has only supported A and sum 11. Within the example's explicitly complete two-candidate universe, ABCD wins by longer supported prefix. A score-first implementation would violate the rule. Tail choice and ties at the same longest prefix remain open.

### No supported prefix means raw sum-LCP, not a new threshold

For original reports `ABC, ABC, BAC, BCA, CAB`, no first symbol has three supporters. Suppose the chosen complete admissible candidate set contains only ABC and BAC. Their raw sum-LCP scores are 6 and 4 respectively, so the fallback chooses ABC. It does not require three supporters, subtract Byzantine reports, trim originals or wait for more arrivals. This hypothetical finite set only illustrates scoring; it does not adopt a candidate-generation rule.

### Candidate completion cannot manufacture report support

Three originals end at A. A valid complete candidate includes ABC after adding required remaining input. Those originals support A only. Filling missing candidate inputs must not append BC to the signed originals or count them as AB/ABC supporters. Likewise, removing an intervening X from an original AXB cannot create support for AB. Store/scoring use the original signed sequences (`direction.md:60,73`).

### Incomplete search is not complete selection

The chosen bounded admissible universe includes P with threshold-supported prefix AB and Q with threshold-supported prefix ABCD. Work has evaluated only P when the native cut becomes ready. App cannot label P the maximum over the whole universe, nor invoke sum-LCP merely because Q was unfinished. The current design requires completion over the bounded full set; absent a prepared valid choice, the native pre-adoption path proceeds from its valid actual-parent base. Candidate count/horizon/budget remain open, so “full” means the selected admissible bounded universe, not all possible permutations.

### Admissibility precedes preference

A reported/selected `[A1,B1]` prefix requires mandatory predecessor X before B1, but X is absent or would have to occur between A1 and B1. That prefix is invalid for the requested exact leading order; support cannot legalize it. Native continuation must preserve tips/extensions and cannot delete extra mandatory input to make the preferred permutation fit (`direction.md:95`). Completing a candidate is not permission to rewrite protected leading order.

## Cut, freeze and adoption authority

| Trace | Required behavior | Status |
|---|---|---|
| Native cut ready while W is open | No wait for count, timer, report crypto, planning, execution or direction reply; use valid actual-parent base if no prepared valid policy exists before adoption. | Current required design, not implemented Baton hook. |
| Snapshot closed, evaluation incomplete | Closure freezes data; it does not create a valid prepared policy or protect a prefix. Native does not await completion. | Pass. |
| Plan ready, native recheck fails before adoption | Use actual-parent valid base; do not relabel stale policy as valid. | Pass. |
| Native proposal adopts/binds prefix and interpretation | That authenticated proposal stays fixed despite late reports, plan completion or a larger native pool. | Required future integration. |
| Policy/body unavailable after protected adoption | Recover authenticated interpretation; do not silently drop the prefix or reinterpret the proposal as native base. | Pass; availability/adoption/continuation liveness proof remains open. |
| Previous direction still executing on a peer | Finish local collection/evaluation/enqueue-or-skip cycle and permit a new eligible cycle; no all-node execution barrier, direction ACK or Ready quorum. | Pass. |

Current native `ProposalPolicy::{Endorsed,Certified}` only chooses construction above the certified anchor (`consensus/src/multimmit/config/mod.rs:32-41`); it is not an App prefix/comparator hook. Native regular proposal processing is its own bounded pass over native chain state (`machine/view/proposal.rs:78-131`). Existing leader block construction does not implement the App report window. These source facts support keeping the future bridge explicitly separate; they do not prove a hypothetical Baton extension preserves no-wait or protected order.

## Minimality and limits

The window needs ordinary App-owned context, admitted-identity/original-report state, one closure decision, a deadline future and current planning-attempt identity. Those are unavoidable facts of the adopted semantics, not a reason for separate actors, public Window/Planner traits or another consensus service. Existing bounded workers, crypto and authenticated transport supply mechanisms beneath them.

No candidate universe, horizon, timer priority, deadline duration, conflict policy, tie-break, hysteresis, tail rule, direction precedence or protected-adoption condition was chosen. No core/diagram/source edits or runtime tests were made. The optional owner-admission clarification is a recommendation only. Acceptance cases in `docs/reference/verification.md:31-33` remain marked Not run.
