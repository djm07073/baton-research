# Pre-cut and Baton scheduling inside App

**Both schedulers consume usable blocks and the same canonical Marshal Updates. Pre-cut starts local work early. Baton additionally exchanges intended orders and chooses advisory direction.** Execution workers, checkpoints, storage, result certification and state sync belong to the same application in both modes.

## Shared application state and different scheduling policy

| Input / state | Pre-cut | Baton |
|---|---|---|
| Valid usable candidate, commonly after `verify` | Deduplicate and sort eligible pending work | Same local admission rule |
| Valid predecessor checkpoint and free worker | Dispatch next eligible block | Dispatch under the applicable local/advisory policy |
| Worker completion | Retain exact-parent effects/checkpoint; reject stale completion | Same, also available when forming future intentions |
| Marshal `Update(index, block, ACK)` | Reconcile exact canonical order; reuse/repair; durably apply; ACK | Identical canonical authority; reports never gate it |
| Intended-order reports / direction | Absent; no Baton instance | Authenticate, admit, choose and disseminate inside App |
| Change to native cut policy | None | Required for full protected-prefix research objective; still open |

A scheduler chooses **what to start next**. It does not duplicate Marshal's history verifier, body resolver, dense order or delivery cursor. It also does not own a second canonical writer. App's execution state supplies the exact checkpoints used by the scheduler; private functions are enough for this connection.

## Global rule for local execution and reports

Keep completed/current execution order `F` on a valid local path. Sort only eligible, authenticated, not-yet-started candidates `S_pending` after the immutable frontier and within the selected horizon:

```text
intended_order = F ++ sort_G(S_pending)
```

`F`, `G` and `S_pending` are explanatory notation. They do not require public Rust types or a `GlobalRule` trait. Required producer ancestry/dependencies still hold. Comparator, deterministic tie-break and rule identity remain open; arrival time is not the tie-break.

| Arrival with G = A → B → C | Scheduler action |
|---|---|
| A is executing; C becomes eligible | Keep F = A, pending = C |
| B becomes eligible before C starts | Sort pending to B → C; leave A running |
| A completes on a valid parent | Start B on A, then C on AB: ABC |
| C already started on A when B becomes eligible | Keep F = AC; place eligible B pending: ACB |

Before dispatch, recheck pending eligibility and the exact execution parent. While that parent is running, enqueue/sort only; do not execute a dependent block from an unrelated state. Starting a block fixes its position on this local path. Ordinary arrival does not cancel or reexecute it just to make the complete known set match G. If only A and C are known, valid AC work need not wait for a hypothetical future B.

The local started prefix is not canonical. A later continuous Marshal Update can require exact-parent repair. Newly confirmed continuous input is the working repair trigger; unfinalized-proposal-triggered repair remains undecided. Equal rule/context/F/pending yields equal intended order. Equal total known blocks alone does not: two nodes can legitimately have ABC and ACB because their work started at different times.

## Canonical reconciliation is shared

Both schedulers use the same [canonical Update worker](interfaces.md#marshal-reportupdate-canonical-input-and-ack). Compare retained work with the exact canonical predecessor, ordered prefix, input state and runtime. A matching block digest alone is insufficient, and a producer-header parent is not the merged execution parent. Missing required bodies or state keep work pending; they do not create empty inputs.

The shared worker reuses valid work or finishes/repairs the canonical path, fences incompatible workers and live database access, and durably applies before ACK. After application, advance App's canonical base once, remove applied pending entries and rebase/fence conflicting work. Retain compatible descendants only within the resource and retention budget. Reports and direction add no approval step.

## Leader: choose direction from reports

Baton uses the same fixed-prefix-plus-sorted-pending sequence to form a report. A report is an authenticated **intention**, even though part of it has already started locally. It is not a progress proof, result certificate or direction vote. Bind exact epoch, view, history, canonical parent, rule, window and immutable frontier. Count each eligible identity once in the same window.

| Step | Rule |
|---|---|
| Open window | Fix context and deadline once |
| Admit verified reports | Owner checks matching context, identity and limits; worker completion alone is not admission |
| Close snapshot | Once, at the first processed event of `4f+1` valid distinct admissions or the fixed deadline; `m ≤ 4f+1` |
| Evaluate | Finish the bounded admissible full-candidate set; preserve ancestry, actual parent and original signed sequences |
| First choice | Maximize the length of a valid nonempty **entire prefix** supported by at least `2f+1` original reports |
| Fallback | With a nonempty report snapshot but no such prefix, choose by raw sum-LCP among valid candidates |
| No reports or no prepared valid candidate | Native cut uses a valid actual-parent base before protected adoption; it never awaits planning |
| Disseminate | Send an authenticated advisory direction; no direction ACK or Ready quorum |

New arrivals do not extend the deadline or rewrite a closed snapshot. Reports arriving or finishing verification after closure stay outside it. Completing a candidate with missing inputs does not add support to the original reports. Evaluation runs in bounded background work using existing Clock/runtime/P2P/crypto primitives. On completion, the App owner checks the original window/context and current planning attempt before publishing prepared state; a stale result cannot overwrite a newer context. The native actual-proposal recheck remains a separate later boundary.

Create and poll strategy work inside the appropriately placed worker: some strategies compute immediately when creating the future, and others can execute work while it is polled. A future return type alone does not keep admission or cut handling responsive.

For a candidate P, `score(P) = Σ_i |LCP(P, R_i)|`. Entire-prefix support means the same distinct reports match every position from the shared origin. It is not per-position votes collected from different identities. An unfinished search cannot claim longest selection over the full admissible set.

With `f=1`, these five synthetic reports illustrate the distinction: `R1=ABCD`, `R2=R3=ABDC`, `R4=R5=ACBD`. For this illustration, assume the complete admissible candidate set consists of the two valid rows below. This is arithmetic, not an executed native trace or a choice of candidate-generation policy.

| Candidate | LCP lengths | Longest prefix with 3 supporters | Sum-LCP |
|---|---|---|---|
| ABCD | 4, 2, 2, 1, 1 | AB, length 2 | 10 |
| ACBD | 1, 1, 1, 4, 4 | A, length 1 | 11 |

Choose ABCD because supported-prefix length takes priority. Ties after the same longest prefix, tail selection and hysteresis remain open. `2f+1` support leaves at least `f+1` honest intentions under the shared fault budget; it proves neither completed work nor native inclusion. Preserve the original signed snapshot when scoring; do not re-sort its fixed prefix or trim/inject inputs to manufacture support.

## Leader: disseminate direction

Use authenticated Commonware P2P channels between peer Apps. Producer and execution-validator roles may overlap on one node. Direction does not alter an existing body or signed lane ancestry. Finish the local collection/evaluation/enqueue-or-skip cycle and allow a new eligible context/work event to open another window; do not wait for every node to finish executing the preceding direction.

<a id="non-leader-request-execution-and-rescheduling"></a>

## Non-leader: request parent-linked execution

App validates the leader and complete direction context, then gives usable work to its Baton scheduler. A suggested A→B→D path needs the valid AB execution checkpoint before D can start. Reuse AB only for matching exact input, canonical base, runtime and storage ancestry. Missing or unfinished parents leave work pending or require recovery.

A direction can adjust eligible unstarted work within the adopted policy. The precedence of a conflicting advisory direction over a local started prefix remains undecided; do not silently adopt cancel-and-reexecute or automatic override. Retaining a compatible branch does not make it canonical. Reject stale worker results by local job/context fencing; local worker generations are not cross-validator signing fields.

## Existing callbacks versus the native policy gap

Existing `Automaton::Context` contains producer epoch/chain/height/parent. It is not a leader report-window context. `propose` builds a lane payload; `verify` checks that payload. Neither method selects the cross-lane leader cut, authenticates a Baton ordering policy or changes Marshal's deterministic native order.

The existing [`ProposalPolicy::Endorsed/Certified`](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/config/mod.rs#L32) chooses whether a lane proposal extends its certified anchor with locally DA-voted blocks. Both forms use the same native validation rules; this setting does not accept an App comparator or Baton prefix.

For full Baton, a native integration must expose the actual leader parent/frontier, recheck a prepared policy immediately, bind it to the authenticated proposal, and let validators verify its adoption/preservation conditions. Marshal must then recover and interpret the same frozen policy across extensions and view recovery. Current `LeaderBlock` and `Update` do not implement that contract. This is specific future protocol work, not a reason to replace existing custody and delivery machinery with a new public layer.

The required result is `p` as the exact leading prefix of final order `O` after the same immutable frontier and canonical input state/runtime. For selected `p=[A1,B1]`, `[A1,B1,A2]` preserves it; `[A1,X,B1]` merely includes its members. A missing mandatory predecessor makes the candidate invalid from the start. Preserve native tip extraction/extensions and do not delete extra native inputs to force the preferred sequence.

Report-window closure is not protected-prefix adoption. Before adoption, a ready cut can use a valid base when preparation is absent. After authenticated adoption, losing a policy/body or receiving late reports does not permit dropping the protected prefix or reinterpreting that proposal as base order. Recover the authenticated interpretation. Adoption/availability, native sufficiency, exact continuation and view-recovery proof remain open. A commitment field alone does not solve them.

## Open decisions

| Item | Decision |
|---|---|
| Window announcement / report / direction message codec | |
| Report / direction logical channels and quotas | |
| Concrete global comparator / deterministic tie-break / rule identity | |
| Candidate set / horizon / finite work budget | |
| Conflicting reports within one window | |
| Tail selection / hysteresis for the same supported prefix | |
| Concrete deadline and cycle-restart settings | |
| Wire direction version / freshness / update ordering | |
| Producer / validator dissemination targets | |
| Native proposal adoption and policy-binding implementation | |
| Execution signing scope / common boundary | |
