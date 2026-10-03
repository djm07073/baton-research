# Baton task infrastructure: use the native runtime, not another scheduler

Baseline `b5747f6a28527a4507901f2e46b426b5ff2a4b7c`; published GitBook `VZgSSM1vxObvtUhGUVFR`. Previous goal turn independently re-read the Tempo body path and confirmed the next reuse boundary; it yielded source evidence, not a new publication. This wave adds a concrete Baton task/API audit. No protocol implementation, native build, dependency change, policy selection or new application trait.

**Existing runtime Clock/Spawner, future pools and parallel strategies cover the mechanisms for a report owner and background evaluation. Baton still supplies exact-context admission and direction scoring.** Another generic scheduler, timer engine, completion dispatcher or direction request/response collector is unnecessary. Source shape alone does not prove an implementation meets no-wait or a finite budget.

## Fresh evidence

[Source manifest](source-manifest.json) contains 11 fresh pinned raw files, independently matched by Git blob hash to their paths in a fresh complete recursive native tree. Native pin remains `534af0ede48affd35b2111522527547b4cc9bf72`. The source spans production runtime, native voter executor, parallel strategy, future pools, actor Feedback and macro surfaces. Release `v2026.9.0` MCP lookups are corroboration only, not a replacement for the native graph or its line numbers. Noncompiled integration descriptions below do not modify native consensus authority.

## Existing calls and their exact limits

| Local work | Existing native mechanism | Baton responsibility |
|---|---|---|
| Fixed once-only window deadline | `Clock::current`, `sleep_until(SystemTime)` | Freeze one deadline at window creation; never extend it on arrival. Close on the first processed threshold/deadline event. |
| Owned async services or evaluation task | `Supervisor::child` + `Spawner::spawn` | Preserve one report/window owner, exact context and bounded work admission; keep evaluation out of the cut path. |
| Short blocking or long-lived blocking work | `Spawner::shared(true)` / `dedicated()` | Select a supported placement explicitly. Do CPU work inside the spawned task body, not while constructing that task on the owner. No strategy/placement is selected here. |
| Independent completion polling | `utils::futures::Pool::{push,next_completed}` | Correlate completion to context/window/job before acceptance; pool itself is unordered, unbounded and not thread-safe. |
| Cancellation of a polled future | `AbortablePool::push -> Aborter`; dropping Aborter aborts its future | Drop obsolete future handles where safe; this does not preempt an already-running CPU closure or undo writes/signatures. Preserve fencing and storage ownership. |
| Collection evaluation | `parallel::Strategy::{map_collect_vec,fold,sort_by,spawn}` | Implement admissibility, original-report entire-prefix support, raw sum-LCP and any selected deterministic tie rule. These mechanisms are not the direction algorithm. |
| Owner event loop | `commonware_macros::select!` / `select_loop!` | Specify event-processing priority without claiming global/network arrival order. Both are biased by branch order; select_loop checks shutdown first. |
| Local mailbox feedback | `actor::Feedback` | Feedback is submission/overflow outcome, not report verification, snapshot admission, completed planning, remote receipt or direction approval. |

Sources: [Clock](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/lib.rs#L428), [Spawner placement and spawn](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/lib.rs#L261), [Tokio placement implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/tokio/runtime.rs#L563), [future Pool](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/futures.rs#L16), [AbortablePool](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/futures.rs#L77), [Strategy](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/parallel/src/lib.rs#L122), [biased select](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/macros/src/lib.rs#L45), [Feedback](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/actor/src/lib.rs#L13).

### A future-returning call can still do work inline

`Strategy::spawn` is not a general proof that the caller remains nonblocking. **Sequential executes `f(self.clone())` synchronously before returning its ready future.** Rayon also executes immediately when its pool has at most one thread; when polling inside the Rayon pool, its receiver loop may run pending pool work inline. Collection operations are synchronous as well. A description such as “put strategy.spawn into a future pool, therefore cut/report admission is independent” is unsupported.

Use existing runtime task ownership/placement to keep candidate computation off the cut/report owner, including inline strategy cases. A spawned async task body can invoke a chosen strategy internally; merely wrapping an already computed result in async does not move work. Shared(false) alone does not guarantee CPU-heavy work cannot starve co-located async tasks. No pool size, placement, worker priority or performance benefit is adopted by this source audit. [Sequential implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/parallel/src/lib.rs#L795), [Rayon implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/parallel/src/lib.rs#L1007).

The Rayon closure is submitted independently and its send result is discarded if the receiver is gone. Aborting/dropping that returned future therefore does not cancel the already submitted closure. Runtime Handle abort wraps a future in Abortable; it also cannot force a non-yielding synchronous closure to stop mid-instruction. Evaluation should remain pure with correlated result acceptance; worker/storage/signing authority needs the existing explicit lifecycle/fencing contract, not an abort-as-quiescence assumption. [Handle abort](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/utils/handle.rs#L252).

### Verification completion is not snapshot admission

Independent workers may return in another order than network observations. The leader-owned window accepts one valid eligible identity once, checks the exact context, and closes once at its first processed `4f+1` admission or fixed-deadline event. A pre-closure packet observation does not entitle a post-closure verification completion to enter the snapshot. Branch priority when several events are ready is an implementation choice under that processed-event rule, not an additional receipt vote or global-time guarantee.

Admission/job bounds are separate: Pool and AbortablePool impose no maximum by themselves. A bounded endpoint's Feedback::Backoff counts as handled under an overflow policy and cannot be treated as a reliable verified-report ACK. Do not introduce a new collector to count f+1 direction replies, and do not await window closure, a worker, pool capacity or an optimizer on the native cut path.

## Native implementation pattern to borrow, not new authority to import

Native Multimmit's voter executor already reserves task capacity before retaining work, carries task permits and originating contexts, and rejects stale-generation completions. `shutdown_tasks` clears its future pools and correlations. This is an actual local owner/completion pattern, not a public Baton policy hook: execute_capability/finish_task and the Core permits are internal native code. Reuse the public runtime/future mechanisms and mirror the application correlation principle; do not expose native Core permits as a new Baton dependency or alter consensus capacity/signing authority. [Permit completion and shutdown](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L37), [reservation before crypto work](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L479).

## Proposed reader delta

Replace Baton README's vague “Clock and runtime tasks” row by a few concrete owner/deadline/completion/strategy rows and one short no-inline/no-cancellation guarantee paragraph. In direction.md, clarify verification completion versus owner admission and that its background computation must remain outside the owner/cut despite synchronous strategy cases. Keep existing report thresholds, scoring, window rules, five traits and 39 blank choices unchanged. No new page, scheduling framework, runtime trait or worker algorithm is required.

## Limits

This source audit identifies mechanisms and concrete hazards. It does not verify a runnable Baton actor, bounded memory/CPU, event fairness, native prefix adoption, protected-prefix recovery, result liveness, crash durability or performance. Source compatibility is not compilation. The report does not select parallelism, implementation queueing policy, report priority, cycle restart or another open choice.
