# Round 19 — Result validation, transaction outcomes and worker ownership

Reviewed current core/execution/PreCut and companion E2E acceptance text against actual Automaton, native local AppExecutor, runtime handle, Stateful reference and concrete QMDB ownership APIs. This is source/design analysis only. No native tests or App/runtime proof was required or claimed.

## Changes

1. Completed root's approved Round18 consolidation in `docs/execution/interfaces.md`: replaced only the duplicate first callback table/signature paragraph with links to canonical callback contracts and actual Rust references. Kept the `Interface overview` heading/anchor and all execution identity, attempt, readiness and result material. Round18 report disposition now records the applied change.
2. Clarified `docs/baselines/precut.md:96`: for completed AC versus canonical ABC, reuse A, execute B on A, then repair C on AB **or explicitly validate retained effects/outputs for AB and prepare C's checkpoint there**. Root approved this narrow clarification.

The second change preserves a real baseline condition. Baseline commit `08cfe68b8b565fff4a0f8119cb36ec9b22062a31` at `docs/baselines/precut.md:91,96` permitted reuse beyond the matching prefix only when the shared backend explicitly proves applicable dependency reuse. Removing that exception would lose adopted conditional behavior. The newer abbreviated “unless validated dependency reuse applies” could instead be read as permission to relabel C-on-A's checkpoint/batch. The clarified row requires a result valid for AB and a matching checkpoint, without adopting a dependency-validation algorithm or new interface.

## Lifecycle distinctions verified

| Event/result | What it establishes | Required App handling | Evidence/current wording |
|---|---|---|---|
| Payload permanently invalid for supplied producer context | A negative payload verdict is justified | Resolve native verify false; no speculative admission | `consensus/src/lib.rs:160-183`; `baton/interfaces.md:41-47,59,63` |
| Body/dependency temporarily missing, or speculative capacity unavailable | No permanent invalidity | Retain required custody request or defer/forgo optional speculation; do not map to false | Same trait contract and core `interfaces.md:59-67` |
| Valid transaction executes with an ordinary application revert/conflict outcome | Execution has completed for the exact input state, with the selected runtime's effects/output | Retain the valid outcome and exact identity; it can be reconciled, committed and included in the result statement under the application rules | Core `interfaces.md:63`; verification acceptance `reference/verification.md:34` |
| Worker ends without reusable output | No completed validated checkpoint/effect result | Settle current-attempt ownership once; reevaluate from last valid checkpoint, retaining required canonical input | Core `interfaces.md:87`; no retry or transaction semantics invented |
| Completion duplicates an already accepted current attempt | No second execution transition | Ignore duplicate for path advancement and accounting | `execution/interfaces.md:25-28`; core dispatch/owner contract |
| A completion belongs to canceled/retired/context-stale work | It cannot authorize current path advancement | Reject adoption; maintain access/retention until actual work is safely terminated | Execution/core completion text and `e2e/reschedule.md:51` |
| Selected result root prepared | The selected commitment exists | Bind exact input/base/runtime/outputs; root alone is neither canonical durability nor direct execution evidence | `execution/qmdb.md:9-11,83`; result signing contract |
| Candidate batch passes `validate_batch` | Storage ancestry is currently acceptable | Still validate App semantics/exact context and preserve that access authority through use | `storage/src/qmdb/current/db.rs:662-679`; `execution/qmdb.md:65-69` |
| By-value DB apply/finalize fails or is canceled | That mutable instance is lost; state may have partially advanced | Stop using it and recover matched authoritative state; no ordinary worker retry against the lost handle | `glue/src/stateful/db/mod.rs:327-336,1835-1882`; QMDB failure text |
| Apply returns, covering persistence still pending | Recoverable/applied checkpoint, not observed durability | Do not ACK based on readability alone | `ManagedDb::apply/finalize` at `383-397`; `Barrier::durable` at `456-483` |
| Full matching direct result plus irrevocable input, fewer than f+1 peer signatures | Valid direct work exists; result certification incomplete | Direct apply/durability/ACK may continue; no certificate barrier on direct canonical work | `baton/interfaces.md:135`; `execution/interfaces.md:58-66` |
| Verified import adopted | Matching result/state can become canonical with imported provenance | Do not issue own direct-execution signature for merely imported work | Existing result/state-sync text; later direct execution from that base may sign its own later range |

## Source ownership and cancellation details

Native Multimmit `AppExecutor` is not this transaction worker. Its `AppOutcome` consists of Built, Custodied and CustodyCancelled; `AppResult` separately carries runtime task failure (`consensus/src/multimmit/actors/voter/actor/app.rs:33-70`). It calls local Automaton propose and then verify for custody before signing (`108-158`). No transaction success/revert receipt or application state checkpoint is interpreted there.

The local native path treats an uncanceled custody verdict other than `Some(true)` as fatal (`actors/voter/actor/live.rs:578-607`). Remote verification maps true/false/closed to Valid/Invalid/Unavailable (`actors/voter/chain_plane.rs:522-547`), with the already documented current remote rescheduling exception. These verdicts are not a generic interface for reporting later transaction outcomes or App worker capacity. The current docs correctly keep those meanings separate.

The full glue Stateful application is a separate reference lifecycle: its verify executes supplied ancestry/batches and returns merkleized state, returning None only for permanent invalidity (`glue/src/stateful/mod.rs:215-243`). Its apply reconstructs matching state and does not substitute for verify (`245-270`). These comments do not require Baton to import the full Stateful actor, and they do not classify a valid runtime-level revert as a worker/storage failure. The App transaction semantics remain open.

Runtime handles distinguish a spawned task from a completion waiter (`runtime/src/utils/handle.rs:27-52`). Aborting a completion handle stops waiting, not its underlying operation (`326-342`). `AbortOnDrop::abort` joins the handle, but even that is only a completion-waiter join for a completion handle (`365-378`); it is not a generic proof that detached CPU work or a sync operation stopped. Existing docs correctly require safe termination/resource release and a separate live-DB fence.

`ManagedDb` mutation takes ownership and returns it only on success (`db/mod.rs:334-336`). DatabaseSet's shared mutation helpers restore the Shared slot only after the owned call succeeds, and panic on mutable apply/finalize error (`1835-1882`). A generation number cannot restore a lost database instance or make this path an ordinary retry. Barrier false on closed/aborted handles is not proof that no storage writes occurred (`456-483`). No new failure-handling service is needed to express those existing ownership rules.

## Analytical traces

**Ordinary revert followed by the next transaction.** B is payload-valid, executes after A, and produces a valid runtime outcome representing a revert. Its exact effects may include runtime-defined accounting changes or none; the audit assumes no particular VM behavior. App records the outcome for AB and can start a dependent child from the actual valid AB checkpoint. It must not return native verify false after the fact, leave F pinned as an unfinished attempt, or omit B from the canonical input. Its outputs remain part of the chosen exact result statement even if selected state values happen not to change.

**Worker failure is not a revert.** With one worker slot, B starts on A but terminates without a valid effect/output result. Marking that as a completed B would manufacture a checkpoint; leaving its claim permanently active would block required canonical work. Settle that attempt once, safely release actual resources after termination, and reevaluate from A under the chosen repair/recovery policy. Current core text and the Not run worker-termination acceptance case already cover it; no duplicate failure table was added to production docs.

**Cancellation request races with completion.** An advisory branch retires attempt C0; its result arrives after the owner moved to C1 or another canonical path. Exact block identity or equal local generation alone does not permit C0 to advance that path. The current-attempt check rejects adoption once, while worker/access retention continues until safe. If a canonical DB mutation has already started, advisory retirement cannot cancel it and reuse the consumed handle.

**Dependency-proved effects are not the old checkpoint.** C previously ran on A, but B is now canonically inserted between them. Simple exact-parent reuse rejects C-on-A. The preserved optional optimization may validate retained effects/outputs for AB, then prepare C's result on that exact parent. It cannot merely label the old AC checkpoint ABC, reuse an incompatible sealed QMDB batch, or infer applicability from a repeated block digest. The clarified PreCut row now says this directly; the QMDB ancestry/access contract remains authoritative.

**Same root/digest, different execution identity.** An unchanged transaction digest or coincidentally equal state root does not bind canonical base, runtime/rule, ordered input prefix, outputs and attempt ownership. Parent-linked checkpoints retain those facts. Live `Reader` handles are not old-version snapshots, and an actual sibling apply invalidates branch use despite a later stale-result check. Current execution/QMDB text preserves this distinction without a new ResultValidator or read-view trait.

**Root preparation consumes the only draft.** A completed rootless AB attempt still needs its effects for a future exact-prefix operation. Consuming the draft during merkleization does not preserve those effects automatically. Existing docs retain needed effects before consumption and either prepare the exact selected prefix or reexecute from a valid checkpoint. This is concrete ownership work, not a justification for mandatory generic overlay infrastructure.

**Direct worker loses the race to imported durable state.** A verified applicable import reaches the single canonical writer and completes AB while a direct AB worker is still in flight. The owner recognizes canonical AB/imported provenance. A late direct result cannot mutate canonical state again or grant direct-signing authority merely from matching identity; it must independently meet the direct execution/validation evidence and current applicable statement contract. The docs' exact-owner completion/import rules prevent duplicate apply/ACK effects, while detailed import preference remains open.

**Applied checkpoint exists after unobserved persistence.** Process crashes after apply and before observing a covering durable barrier. On restart some of that checkpoint may exist. App selects matching QMDB targets, outputs/applied identity/provenance using its recovery rule, rather than treating latest readable state as completed durable application. Existing `init(expected)` supplies reopening/truncation machinery; multi-store checkpoint selection remains App work. Neither treating all recovered latest state as safe nor assuming all unobserved state disappeared is justified.

## Review result

The failure/result boundaries are already coherent across core, execution, E2E and verification pages. Beyond the approved callback-table consolidation and one PreCut checkpoint clarification, no meaningful cut or correction was found. Adding separate payload/result/worker/storage validator or failure actors would make the design larger without changing the ownership requirements.

No transaction failure semantics, dependency-reuse algorithm, retry policy, cancellation primitive, root scheme or import preference was selected. No diagrams or native source changed. Scoped `git diff --check` passed for the owned edits and reports. Runtime acceptance cases remain Not run.
