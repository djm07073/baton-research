# Choosing direction and executing branches

**Baton chooses and shares a promising order; Executor manages its execution tree.** The leader evaluates original reports, chooses a valid candidate, and shares advisory direction. Each receiving Baton adjusts its speculative schedule without introducing a direction-approval quorum.

## Leader: choose direction from reports

Rust declaration: [Baton::plan](../overview/rust-interfaces.md#baton). The Rust interfaces page owns the complete declaration.

`ReportSnapshot` is a once-closed set of distinct, same-context original reports. `Candidates` is a bounded set of admissible full candidates. Return `Some` only when evaluation of that set has completed and the selection is valid. Incomplete evaluation or absence of valid candidates cannot be published as prepared policy. Never await this background future on the native cut path. Tail selection, budgets, adoption, and continuation remain open.

The snapshot owner admits verified reports; packet observation or worker completion alone is not admission. A verification result processed after closure stays outside that snapshot. Fix the deadline once with the existing Clock and run evaluation through [Commonware task/completion mechanisms](README.md#commonware-primitives-in-the-baton-layer). Synchronous strategy cases must also stay off the admission/cut owner; no new scheduler or direction collector is required.

| Stage | Input | Responsibility | Output |
|---|---|---|---|
| Start window | New work and actual planning context | Fix context and set the deadline | Window context |
| Admit reports | Signed reports | Verify shared context and distinct identity | Original report snapshot |
| Close snapshot | First `4f+1` admissions or fixed deadline | Close once; arrivals do not extend the deadline | `m≤4f+1` frozen reports |
| Evaluate candidates | Bounded admissible full candidates | Validate ancestry, predecessor closure, and actual context; compute LCP | Completed evaluation or incomplete work |
| Primary selection | Same-context original reports | Maximize the length of a valid nonempty entire prefix shared by `2f+1` reports | Full candidate containing the selected prefix |
| Fallback | No such prefix | Maximize raw sum-LCP among valid candidates | Valid direction candidate |
| NativeBase | No reports / no prepared valid candidate | Use an actual-parent-valid base policy | Native cut continues |
| Disseminate | Prepared direction | Send to producer and executor-validator Baton endpoints | Parent-linked speculative execution |

Let `ℓᵢ(P)=|LCP(P,Rᵢ)|`. The fallback score is `Σᵢℓᵢ(P)`. Filtering or completing reports must not manufacture support. An unfinished candidate search cannot establish a completed longest-prefix selection. Support from `2f+1` reports leaves at least `f+1` honest **intentions** under the fault assumption; it does not establish finished work, reuse, or native inclusion.

A prefix of length k has `2f+1` support when at least that many original reports match **all of the candidate's first k inputs in the same order**. This is neither a sum of separate supporters per block nor a requirement that the complete full candidate match every report.

For an illustrative calculation, take `f=1,n=6` and five distinct identities in the same context: `R1=[A,B,C,D]`, `R2=R3=[A,B,D,C]`, and `R4=R5=[A,C,B,D]`. Assume evaluation has completed over the two bounded admissible candidates below and that both candidates and their tested prefixes are valid. This is an analytical example, not an executed native trace.

| Full candidate | LCP lengths against original reports | Longest entire prefix supported by at least 3 reports | Raw sum-LCP |
|---|---|---|---|
| `P1=[A,B,C,D]` | `(4,2,2,1,1)` | `[A,B]`, length 2 | 10 |
| `P2=[A,C,B,D]` | `(1,1,1,4,4)` | `[A]`, length 1 | 11 |

The primary rule selects **P1**: supported prefix length takes priority even though P2 has a larger sum. If a different deadline snapshot contains only `R1=[A,B,C,D]` and `R2=[A,C,D,B]`, three-report support is impossible, so use the fallback. The raw sums are `4+1=5` for P1 and `1+2=3` for P2, selecting P1. Do not subtract the largest f LCP values. This calculation does not establish a global optimum outside the candidate set, native inclusion, or completed execution work.

How to choose the tail after an equally long supported prefix, including any secondary score, remains undecided. A cut does not wait for reports, timers, or Baton planning. Distinguish using a valid base before a candidate is prepared from preserving an already authenticated protected prefix. Native prefix adoption and exact continuation remain unimplemented and unproved.

Suppose a valid prefix `p=[A1,B1]` is selected after the same immutable frontier. The following comparison assumes the same canonical input state and runtime and valid predecessor closure. It illustrates the requirement, without claiming an executed trace or completed preservation proof.

| Emitted order O | Contains every input of p | Preserves p as the exact leading prefix |
|---|---|---|
| `[A1,B1,A2]` | Yes | Yes |
| `[A1,X,B1]` | Yes | No |
| `[B1,A1]` | Yes | No |

If X is a required predecessor of B1, `[A1,B1]` is not a valid candidate in that context in the first place. Check both candidate validity and preservation of leading order after adoption.

## Leader: disseminate direction

Send to producer Baton endpoints and the validator Baton endpoints responsible for execution. Overlapping roles on one node may share handling, but the whole committee is not assumed to be producers. Direction cannot arbitrarily change an existing body or signed producer ancestry.

There is no direction-receipt vote, ACK, or Ready quorum. Once the leader-local collection, selection, and dissemination cycle closes, the next cycle may start for new work or context. It does not wait for every node to finish the previous direction.

<a id="non-leader-request-execution-and-rescheduling"></a>

## Non-leader: request parent-linked execution

Accept direction only from the current leader and for the matching context. Resolve the required bodies and submit the proposed path as parent-linked `Executor::Block` values through `Executor::execute(block)`. A→B→C changing to A→B→D submits D with the hash of the completed AB execution parent. Executor reuses AB only when its input state, runtime, exact prefix, and storage ancestry match. A fresh public reschedule command is unnecessary.

Executor owns parent lookup, child linking, task priority, duplicate-work reuse, and stale-result fencing. An unfinished or missing parent leaves dependent work pending or triggers recovery; it never licenses execution from a different state. Old compatible branches may remain until commit or resource cleanup; a direction update does not itself make another branch canonical. Late completions cannot replace canonical state. Missing bodies or parent state add no native cut wait for direction replies.

## Open decisions

| Item | Decision |
|---|---|
| Window announcement / report / direction message codec | |
| Report / direction logical channels and quotas | |
| Intended-order construction rule | |
| Candidate set / horizon / finite work budget | |
| Conflicting reports within one window | |
| Tail selection / hysteresis for the same supported prefix | |
| Concrete deadline and cycle-restart settings | |
| Wire direction version / freshness / update ordering | |
| Producer / validator dissemination targets | |
| Native proposal adoption and policy-binding implementation | |
| Execution signing scope / common boundary | |
