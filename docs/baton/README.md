# Baton: roles and reports

**Baton coordinates execution order before and after native consensus.** It manages intended-order reports and advisory directions so Executors can begin useful work before order is final. Executor owns state finalization and state sync.

## Roles and responsibilities

Baton receives candidate blocks from the consensus attachment and schedules speculative execution. It preserves completed/current execution order and sorts only eligible not-yet-started blocks under the shared global rule. Reports contain that fixed prefix plus sorted pending work. Arrival while a predecessor runs updates only the queue, preserving started execution. The leader evaluates the report snapshot inside Baton, then disseminates the prepared direction. Non-leaders use a valid direction to adjust their execution plans. Baton also verifies/retains native finality/history and delivers confirmed exact ranges to Executor independently of its advisory planning. Executor and Storage handle result certification and canonical application. Executor controls peer state sync; Storage controls roots/apply/durability. These result/apply paths require no advisory Baton approval or acknowledgement.

**Baton** owns report admission, direction messages, and speculative block requests. **Baton** also selects direction, reconstructs confirmed exact input, and retains delivery history/cursors. Those functions do not move native finality authority or Executor state-finalization control into Baton. **Executor** owns parent-linked execution branches, transaction effects, result certification, canonical promotion, and pruning. Storage prepares selected roots and serializes canonical application through the shared single writer; Executor orchestrates it. Native signing, voting, and finality authority remain with consensus.

## Report connection

Use Commonware P2P to carry authenticated window context, intended-order reports, and advisory directions. Messages bind epoch, view, history, actual parent, rule, window, and immutable frontier. A leader-local timer does not establish that remote nodes know the window.

A report expresses **execution intent constructed with the global rule**. It is the fixed local execution prefix followed by the rule-sorted pending snapshot, not a fresh sort of all known blocks or a receipt-order list. Execution dispatch and report generation use the same context/frontier/horizon and ordering rule. See [global-rule scheduling and the A/C/B arrival case](direction.md#global-rule-for-local-execution-and-reports). It is not execution progress, a state root, a completion proof, or a direction vote. Count one valid original report per identity in the same window. Worker verification and admission into the leader-owned snapshot are separate events. Reports that arrive after closure cannot enter that snapshot.

## Commonware primitives in the Baton layer

**Baton selects direction; its infrastructure should reuse Commonware rather than add a second networking or task framework.** `Baton::plan` consumes the fixed report snapshot and candidate set. Executor owns the execution tree.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_p2p::authenticated`, `Sender`, `Receiver` | Report and direction logical channels on the existing network | Message admission, one report per eligible identity, context correlation and bounded retention |
| `commonware_cryptography::{Signer, Verifier}` and `commonware_codec::Codec` | Authenticate reports/direction and encode bounded policy subjects | Exact epoch/view/history/parent/rule/window/frontier binding and frozen proposal interpretation |
| `commonware_runtime::Clock::sleep_until` | One deadline fixed when a report window starts | Close once at first 4f+1 valid admissions or the processed deadline event; arrivals do not extend it |
| Runtime `Supervisor::child` / `Spawner::spawn` | Existing owner and background task lifetimes | Keep candidate evaluation outside report admission and cut; select supported CPU placement and finite work admission |
| `commonware_utils::futures::{Pool, AbortablePool}`; `commonware_actor::Feedback` | Independent completion polling and local submission feedback | Correlate context/window/job; bound retained work separately; feedback is not verified admission or completed planning |
| `commonware_parallel::Strategy` (candidate) | Existing collection evaluation and CPU work | Entire-prefix support checks, sum-LCP scoring and deterministic tie rules; the parallel framework does not implement the policy |

**Use the existing runtime to own evaluation, rather than another scheduler.** Future pools provide unordered completion, not a capacity limit. Verification completion enters the snapshot only when its owner admits the still-matching report before closure. `select!` / `select_loop!` are biased by branch order; that local processing order does not establish network arrival order. [Clock and tasks](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/lib.rs#L261), [future pools](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/futures.rs#L16), [event selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/macros/src/lib.rs#L45).

`Strategy::spawn` can compute immediately with Sequential or a one-thread Rayon pool, and polling from a pool member may run work inline. Call the chosen strategy inside an appropriately placed background task; returning a future alone does not keep cut or report admission responsive. Dropping a result future also does not preempt a submitted CPU closure. Reject stale completions by context; abort is not storage/signing quiescence. Placement and parallelism remain open. [Sequential](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/parallel/src/lib.rs#L795), [Rayon](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/parallel/src/lib.rs#L1007).

Do not use a request/response collector to introduce direction acknowledgements or a readiness quorum. Cut reads an already prepared valid result or uses the admissible base path; it never waits for reports, the timer or planning. Commonware supplies mechanisms, while the direction-preserving native integration remains an open proof obligation.

See [versioned primitive evidence and compatibility checks](../reference/integration.md#primitive-reuse-catalog).

## Confirmed-order delivery

`on_finality` is native evidence intake, distinct from advisory reports and direction. Baton independently verifies/retains the exact source and frozen history/policy, backfills gaps, delivers continuous irrevocable ranges through `Executor::commit`, and records matching durable completion for restart/redelivery. Use existing native verification, archives, resolver, Journal/Metadata and completion handles; the [native source-export bridge](../consensus/ordered-input.md#consensus-and-baton-integration) still needs implementation. These internal functions expose no separate Orderer trait or record/next_range/acknowledge/recover API.

Reports express intent; only verified native evidence establishes confirmed input. Slow report collection or planning cannot hold that delivery path. Native signing/voting/finality, Executor result certification/peer sync and Storage application remain under their existing owners.
