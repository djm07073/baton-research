# Round 14 — Progress under bounded resource pressure

Reviewed resource/queue ownership in core, execution, architecture and the planned verification table. Actual source was inspected for future pools, runtime placement, actor mailbox feedback and native strategy separation. This is an analytical design review; no scheduler/runtime test or performance claim is made.

## Confirmed missing invariant, now restored

Bounded queues and short callbacks did not alone prohibit allocation starvation:

```text
one App worker slot; canonical repair/root work C is ready and retained
optional speculative/report job S1 completes
owner grants the freed slot to fresh optional S2, then S3, ...
each job is finite; every queue/count remains bounded
report(Update) returns promptly, but C never runs and its ACK never progresses
```

This counterexample does not require a hung worker, failed disk or unknown parent. It exposes a missing resource-progress condition beyond “reports do not approve canonical work.” Reported the smallest core change to root.

Root added and this review read back `docs/baton/interfaces.md:120`: the App capacity policy must let required custody and canonical execution, root preparation and durability progress under sustained optional load; speculation/report verification/planning cannot indefinitely monopolize the resources needed for it. This is an implementation invariant, not a choice of quota, priority algorithm, thread count or extra service. Existing native critical-work separation should remain intact when wiring App CPU work.

The assertion is about runnable required work under otherwise healthy dependencies. It does not authorize early ACK when required storage is stalled, bypass ancestry/access fences, or promise a fixed wall-clock latency under arbitrary system failure.

## Pressure cases

| Pressure | Required behavior and current status |
|---|---|
| Speculative queue/worker capacity full | Verify's valid-custody reply cannot depend on obtaining a speculative slot. Retain/coalesce bounded candidate facts or forgo speculation; canonical input remains authoritative. Existing `baton/interfaces.md:59-67` already makes this explicit. |
| App report/intention traffic fills ingress | Synchronous Update handoff must still retain the complete block/token under its ordinary native window and explicitly bounded floor-reset overlap. A best-effort overflow policy cannot silently discard accepted Updates. Short callbacks alone do not make an arbitrary shared-mailbox policy safe. Existing intake contract supplies this obligation without prescribing another actor. |
| Report crypto/planning saturates CPU | Admission remains short and context-checked; create and poll potentially inline strategy work in the correctly placed worker. The fixed deadline closes the App window without waiting for pending crypto. Optional work cannot now starve required App continuations under the restored progress condition. |
| Optional root work competes with selected canonical roots | Roots needed for canonical durable application are required work; abandoned/speculative preparation cannot continuously take their capacity. Effects/root separation does not eliminate the selected root/durability work required before ACK. |
| Native cut is ready while App planning is busy | Current cut behavior remains independent of App reports/timers; future Baton policy integration may use already prepared/rechecked state but cannot wait for it. CPU placement and existing critical-strategy separation matter as well as the absence of an explicit await. No claim of zero scheduling latency is made. |
| Canonical writer is awaiting genuine durability | Retain exact Update/token and preserve the one-writer/storage contract. Optional work may continue only under valid access/resource rules. Do not free canonical progress by ACKing admission, ignoring a failed barrier, or canceling a by-value DB mutation. |
| Marshal delivery window fills | Later App deliveries wait for contiguous ACK capacity while native consensus remains logically independent. Already-retained required work must receive App resources; choosing a durability boundary needing more Updates than the window remains prohibited by `execution/interfaces.md:73`. |

## One-worker cleanup and transaction outcomes

The round-13 ownership correction remains correct at `baton/interfaces.md:87`:

1. An attempt actually ends without reusable output. The owner settles that attempt once, re-evaluates from a valid checkpoint, and keeps canonical input for repair/recovery.
2. Claims/resources become reusable only after work never began or safely terminated. Dropping an aborted completion waiter does not show that a submitted CPU job stopped.
3. A duplicate completion cannot release capacity twice or disturb a later attempt. An invalid live-DB branch still needs access fencing, independently of adoption rejection.

An ordinary transaction rejection/revert that the App semantics defines as a completed outcome is not automatically worker failure. Its effects/outputs can remain valid for the exact parent. Repeatedly retrying it merely because the transaction was unsuccessful would be incorrect. Core `baton/interfaces.md:63` already puts state-dependent outcomes in execution and says speculative reverts/conflicts do not retroactively invalidate an otherwise valid payload; no duplicate core paragraph was needed.

Mutable-storage failure is separate: that DB instance is lost/fatal and requires recovery, not ordinary worker retry. These statements do not select VM transaction semantics or a retry/backoff default.

## Existing primitives and their actual limits

| Current source | Supplied mechanism | App obligation not supplied automatically |
|---|---|---|
| `utils/src/futures.rs:15-58,91-142` | Pool/AbortablePool tracks submitted futures and yields completion | No submission capacity argument, workload isolation or App priority rule; count/account admission before submitting CPU work |
| `runtime/src/lib.rs:332-352,430-439` | Shared/blocking-friendly or dedicated placement and explicit strategy parallelism | Choose suitable placement/resource ownership; a shared future pool alone cannot guarantee canonical progress |
| `parallel/src/lib.rs:184-197,960-970` | Strategy may run work inline on submission or polling | Both creation and polling must stay off short App/native handlers when computation is substantial |
| `actor/src/mailbox.rs:92-132,274-286`; `actor/src/lib.rs:13-28` | Existing bounded endpoint plus application-defined overflow policy and Feedback | Overflow policy must preserve retained canonical input; Backoff is not a downstream resend protocol or worker fairness guarantee |
| `examples/log-multimmit/src/node.rs:299-320` | Native critical cryptography gets its own strategy, separate from bulk data verification | Do not defeat that assembly separation by putting App optional CPU work in the critical resource path; App budget details remain open |
| `consensus/src/multimmit/marshal/config.rs:545-593` | Native derived router/subscription/backfill bounds | These bounds do not allocate App speculative/canonical CPU or bound every App retention store |
| `runtime/src/utils/handle.rs:27-31`; QMDB mutation/barrier contracts | Distinguishes stopping a waiter from stopping submitted work; storage preserves its own completion rules | Safe resource release and failure handling must follow actual work/storage state |

No separate scheduler/executor service, generic capacity broker or arbitrary quota was recommended. Ordinary App ownership and existing runtime/queue handles can implement the required progress policy.

## Acceptance criteria review and root changes

`docs/reference/verification.md` is an acceptance-needs table, not executed evidence. Its previous “Scheduling independence” row covered valid custody with blocked speculation and healthy native progress, but did not explicitly cover retained canonical work under sustained optional CPU backlog.

Root expanded line 23 to require ready canonical work to reach durable ACK under sustained optional backlog. Root also added the “Worker termination” row at line 34: one worker, ownership settled once, required work resumes after safe release, dropped waiter does not release live work, ordinary valid transaction revert remains a completed outcome. These final lines were read back here. All statuses remain **Not run**.

Those cases should eventually be exercised in both scheduler modes with matching resource assumptions; Baton additionally supplies report/planning pressure. Checks must observe actual completion/ACK boundaries and avoid claiming progress while a required dependency is deliberately prevented from finishing. No runtime test or new production code was added in this review.

## Result

One material progress invariant and its planned acceptance checks were restored by root. No further contradiction was found between prompt callback returns, custody validity waits, native cut independence, root preparation, writer safety and ACK. Concrete queue/admission/placement/fairness budgets remain explicit implementation choices within the preserved progress and safety requirements. This agent made no production documentation edits in round 14.
