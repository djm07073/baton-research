# Round 20 — Independent core and source cross-review

Freshly read current `docs/baton/README.md`, `interfaces.md`, `direction.md` and the PreCut shared-contract sections. Inspected actual current native/example/runtime sources for the callback handoff, role qualification, delivery/ACK behavior, work placement, callback composition and Stateful boundary. Prior reports were not treated as proof that the current prose was correct. No native implementation or tests changed; all counterexamples are analytical.

## Confirmed omission: the empty report snapshot

Baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31:docs/baton/direction.md:41` explicitly required NativeBase on **No reports / no prepared valid candidate**. Research AGENTS.md:38 preserves the same adopted condition. The current rewritten table had retained only “No prepared valid candidate,” while its fallback row applied raw sum-LCP whenever no threshold-supported prefix existed.

Counterexample: deadline closes W with `m=0`; the selected bounded candidate universe is nonempty and fully evaluated. Every candidate has score zero and no `2f+1` prefix. The prior rewritten rows allowed the fallback/tie policy to choose a reportless candidate. That differs from the adopted explicit no-reports base branch, even though the candidate itself might be valid. This is a missing condition, not a reason to invent a tie-break or expand the candidate universe. Earlier nonempty-snapshot traces did not expose it.

Root confirmed and restored the core table:

- Fallback applies to a **nonempty** report snapshot with no supported prefix.
- **No reports or no prepared valid candidate** uses actual-parent valid native base before protected adoption, without waiting.

Readback confirmed those changes at `docs/baton/direction.md:56-57`. Root assigned the matching E2E/diagram branch to alignment and acceptance-case/reference corrections to the native agent. The post-adoption protected-prefix rule is unchanged; an empty later report window cannot undo an already authenticated policy.

## Two source-boundary clarifications

### Separate ACK capacity release from persisted-cursor recovery

Core `interfaces.md:127` previously listed “Later delivery and permitted pruning” as what cursor sync permits. This could imply the next delivery slot waits for cursor I/O, while the preceding row already releases capacity on App ACK. Source retirement pops the acknowledged oldest entry and contiguous acknowledged successors (`marshal/actors/delivery/acks.rs:107-124`); the ready prefix is synced separately (`delivery/actor.rs:330-355`).

Recommended limiting the cursor-sync row to persisted-cursor recovery and pruning. Root applied it; readback now says “Recovery from the persisted cursor and permitted pruning.” This clarifies the endpoint without altering native behavior or removing required App durability before ACK.

### Stateful has a different callback surface

At root's request, source-checked and added one sentence to `docs/execution/README.md:27`. `glue::stateful::Application` requires `CertifiableBlock` (`glue/src/stateful/mod.rs:164-168`). Its mailbox imports **`commonware_consensus::Application as ConsensusApplication`**, plus **`simplex::marshal::Update` and ancestry** (`glue/src/stateful/actor/core/mailbox.rs:8-13`). It implements that block/ancestry Application (`245-303`) and handles Simplex Tip/Block Updates (`306-333`), whereas Multimmit's Update is the indexed full-block/Exact struct (`multimmit/marshal/types.rs:128-136`).

The added sentence names those exact contracts and links the source. It explains why the whole Stateful mailbox is not an unchanged Multimmit callback handle, while preserving direct reuse of fitting concrete `glue::stateful::db` utilities. No adapter framework or alternate public App interface was proposed.

## Fresh callback and ownership checks

| Core claim challenged | Actual source/analytical result | Disposition |
|---|---|---|
| Callback clones can route to one App owner | Example Mailbox clone shares sender/clock (`examples/log-multimmit/src/application/mailbox.rs:113-118`); propose/verify create one-shot response and return ready receiver (`148-173`). Actor handles pending completions and ingress (`actor.rs:192-205`). | Supported wiring pattern. The App's semantic state/attempt discipline remains implementation work, not a supplied transaction executor. |
| Body/custody work need not occupy the short owner | Example construction runs under a runtime task, returns a completion, then owner arranges stage work (`actor.rs:266-368`). Core explicitly places pending jobs outside short handlers and returns to owner for shared-state changes. | Pass. No mandatory second actor is needed. |
| Example mailbox proves bounded total App work | Its Overflow Backlog is a VecDeque; live messages are pushed without an intrinsic total length cap (`mailbox.rs:62-96`). The example demonstrates handoff, not a total memory/capacity proof. | Core already requires App bounds. Recommended reference catalog replace broad “bounded work pools” with actual future pools plus App budgets; root assigned correction to native owner. |
| Accepted staging equals durable custody | `stage_block` returns a token; accepted work continues if token is dropped (`marshal/mailbox.rs:327-350`). `put_block` waits that token (`352-358`). | Core separates both boundaries correctly. No redundant body service or second scheduling flush. |
| Subscription starts peer fetch | `subscribe_block` establishes durable custody but explicitly does not initiate peer fetch; it waits for subscription capacity (`mailbox.rs:419-445`). `fetch_block` is separate (`403-416`). | Core pseudocode explicitly starts needed fetch without awaiting subscription first and permits custody establishment from exact fetched material. Pass. |
| Every successful verify means a new other-lane receipt | Every validator gets chain planes; observers get none (`actors/voter/actor/chains.rs:114-128`). Callback context does not supply origin/recovery metadata. | Fresh README role table and lifecycle/dedup checks correctly qualify this. A local pre-sign report still needs its chosen authentication eligibility. |
| One Reporter type can serve both activities directly | Reporter has one associated Activity (`consensus/src/lib.rs:258-268`). `Reporters` composes reporters of the same Activity, cloning that activity (`consensus/src/reporter.rs:31-45`). | Distinct typed App handles are necessary ordinary Rust wiring, not a new service layer. |
| Native activity hints can gate canonical delivery | Current native voter ignores reporter Feedback (`actors/voter/actor/live.rs:412`); the optional observer can be composed as a sibling with Marshal. Actual canonical input comes from delivery Update. | Core direct Marshal routing and optional hints remain correct. Do not build another finality interpreter. |
| Reporter Backoff requests Update retry | Delivery only treats Closed specially, then retains the created waiter (`delivery/actor.rs:315-325`). | Core requires retained Update/token and correctly rejects lossy intake assumptions. |
| Cloning an Exact token is harmless | Clone increases required count; drop without acknowledgment cancels (`utils/src/acknowledgement.rs:54-101`). | Core explicitly requires every clone to ACK and retains tokens through durable completion. No extra ACK protocol needed. |
| One active ACK bound covers all App state | PendingAcks bounds only its queue (`acks.rs:74-84`). App may also retain speculative work, results and old-window Updates during floor handoff. | Core explicitly limits the bound's scope and requires serialized transition/bounded overlap. Pass. |

## Candidate versus attempt, capacity and canonical progress

Fresh pseudocode retains separate facts that should not be collapsed: a candidate's exact header/context identity, a selected execution parent/path, a current local attempt and its resource claim. Two successful verify completions can refresh one candidate; the owner claim before launch prevents duplicate dispatch. A canceled/retired attempt can finish late without authorizing the new path. Core requires completion acceptance once and correlates attempt as well as context; no public Job/Executor framework is mandated.

A failed launch or safely terminated no-result attempt must settle ownership and permit reevaluation from the last valid checkpoint. An ordinary valid transaction revert is a completed application outcome, not an excuse to keep the claim pinned or retroactively return false. In contrast, a dropped waiter does not prove underlying work stopped. Runtime handle semantics distinguish spawned tasks from completion waiters (`runtime/src/utils/handle.rs:27-52,326-378`), supporting core's separate access fence and safe resource release.

`Spawner::shared(true)` and dedicated task options are placement mechanisms (`runtime/src/lib.rs:332-352`); `Strategizer` supplies configured parallelism (`429-439`). Strategy work may run when created or polled (`parallel/src/lib.rs:184-197`). Core requires bounded work and progress for custody/canonical execution/root preparation/durability under sustained optional load. It does not prescribe arbitrary quotas or claim a future queue supplies that policy. This resolves the W=1 case where optional speculation would otherwise keep winning every released slot forever.

The canonical path has one writer for direct and imported results, with actual-predecessor checks and live-access fencing before mutation. Durable completion is reconciled on the App owner before one canonical advance and ACK. This does not duplicate the native delivery cursor. Pool maintenance is scheduled from recoverable outcomes and adds no approval gate. Missing early speculation or native activity hints cannot make canonical Update processing depend on a nonexistent earlier scheduler entry.

## Baton support and adoption cross-check

Recomputed the page's five-report example: ABCD receives LCP lengths `4,2,2,1,1`, sum 10 and three-report AB prefix; ACBD receives `1,1,1,4,4`, sum 11 but only threshold-supported A. The primary rule therefore selects ABCD within the stated complete two-candidate universe. The prose correctly requires the same original identities for every position of the entire supported prefix; candidate completion cannot fill the signed reports to manufacture support.

Owner-processed threshold/deadline closure, `m<=4f+1`, frozen originals, full bounded candidate evaluation, stale-planning rejection and the separate native actual-proposal recheck remain explicit. Neither an unfinished search nor missing reports is now an excuse to delay native cut. The restored empty-snapshot branch is the only adopted selection condition found missing in this fresh pass.

Native `LeaderBlock` still contains round, parent, history and lane proposals only (`types/block.rs:800-824`). It supplies no Baton policy field or report-window hook. The current docs consistently label authenticated prefix adoption, validator preservation, continuation and matching Marshal recovery as future native work. Before adoption a valid base is allowed; after authenticated adoption, unavailable policy/body or late planning cannot silently reset that interpretation. No new policy defaults were introduced.

## Disposition and validation

- Core zero-report omission: root fixed and read back; peer E2E/acceptance updates assigned by root.
- Core cursor milestone: root fixed and read back.
- Execution Stateful boundary: one source-linked sentence added by this agent.
- Reference “bounded work pools” precision: sent to root; native owner assigned.
- No further mandatory queue, generic overlay, result relay, proof archive, scheduler writer or importer writer was found to remove.

The exact candidate set, ties/conflicts/hysteresis, timer settings, adoption mechanism, VM, resource quotas, root normalization and cross-store recovery policy remain open. No diagrams were edited by this agent, and no native/runtime tests were run. Scoped whitespace validation passed; root owns final link/build/render verification.
