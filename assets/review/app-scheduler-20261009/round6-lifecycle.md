# Round 6: startup, cancellation and failure ownership

Source audit at native `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. Native source and current docs were read directly. No runtime test, new task framework, native code change or shutdown proof was added.

## New conclusions and reader-page changes

- Engine open is actor-free; Marshal open is not. Marshal already starts catalog and optional promoter before returning Service. Its later start launches the remaining actors, including delivery, which can immediately replay to the precreated App handle.
- Engine and Marshal supervise their respective actor subtrees. Neither API automatically owns an independently started App, the other's lifetime, body broadcast, generic resolver or node network. The existing node/runtime owner must retain/observe those lifetimes and coordinate a failed startup or shutdown.
- Callback cancellation is reusable through oneshot response closure. It does not mean accepted body writes were rolled back, and service shutdown does not mean they were durably finished.

`docs/reference/integration.md` now states these three boundaries with existing source links. Existing E2E recovery already distinguishes native readiness from App readiness/health and abort from flush; no replacement lifecycle abstraction is necessary.

## Startup and recovery: actual owners

| Step | Existing method and source | Required App/node behavior |
|---|---|---|
| Construct App handles | `examples/log-multimmit/src/node.rs:260–280`; `application/mailbox.rs:147–173` | Create callback and Update ingress before Marshal delivery starts. Their creation does not mean transaction state is ready. |
| Open Marshal | Public `marshal::open`, implemented in `marshal/service/mod.rs:96`; `marshal/open.rs:82–165` | Opens/replays catalog and cursor, then starts catalog and optional immutable-body promoter. Own the whole startup attempt; do not assume nothing runs until Service::start. |
| Connect transport and relay | Example `marshal.rs:139–194`; `Service::relay` at `service/mod.rs:204` | Keep buffered broadcast and the generic resolver alive; attach the supplied bridge as consumer/producer; obtain Relay before start. These are existing components. |
| Start Marshal | `Service::start` at `service/mod.rs:213–312` | Starts serve/backfill/delivery/synchronizer/router and the service supervisor; returns Mailbox and ServiceHandle. Delivery can replay immediately. No separate public ready barrier is returned. |
| Start App | Example `application/actor.rs:188–206` | Run short custody/admission handlers and retained output intake. App recovery may delay applying Updates, but its ingress cannot drop them and its required custody callbacks must make progress. |
| Open Engine | `engine/mod.rs:446–497`; `storage/recovery.rs:227–235` | Validate config, recover stores/artifacts, finish every required recovered payload verification, compact recovery state, and build actors. No native actors, network ingress, timers or publications start yet. |
| Start Engine | `engine/mod.rs:517–599` | Spawn ingress/verifier, resolver and voter over the four planes. Internal actor/task driving is already supplied. |
| Await native ready | `engine/mod.rs:159–172,193`; `actors/voter/actor/startup.rs:188–228`; `actor/mod.rs:407–420` | Startup/recovery barrier becomes durable and initial ProducerWake is submitted. This is neither completed first proposal nor App transaction/durability readiness. |

`Running::ready` caches Ready/Failed. Once Ready, a later call can still return Ok even after the engine stopped. The current E2E page correctly says this is not a live health check. False or closed recovered verification returns RecoveredPayloadUnverified from `Engine::open`; the Running handle does not exist yet. A temporary unresolved custody request can keep open pending. App must not postpone that body service until native ready or turn temporary absence into false.

Recovery's verification jobs are bounded plain futures polled by `verify_recovered_payloads`, using cloned Automaton handles (`storage/recovery.rs:473–496`). One terminal failed verdict fails the aggregate; it is not hidden indefinitely by another pending request. Dropping/failing the open attempt drops its native awaits, but independently spawned application work still needs the response-closure/owner cancellation behavior supplied by the App implementation.

## Native and Marshal failure scopes

| Boundary | Actual failure behavior | What callers must not infer |
|---|---|---|
| Engine config/open | Invalid config fails before native storage access; recovery/storage/verdict failure returns OpenError. | An already-started Marshal/App/network is not rolled back by this returned error. |
| Mandatory Engine actor exit | Root selects ingress/verifier, resolver, voter or runtime stop; exiting the Engine root aborts its descendants through runtime supervision. `engine/mod.rs:547–587`. | This does not itself shut down sibling Marshal/App/transport tasks. |
| Voter Fatal | Logged/counted, then voter returns. `actor/mod.rs:412–415`; `actor/live.rs:124–149`. | `Running::join` is `Result<(), runtime::Error>`, not a typed Fatal result. A child fatal can make the root finish normally; Ok is not proof that no protocol/storage failure occurred. |
| Engine abort/join | `abort` requests shutdown; consuming `join` awaits the engine root, with runtime errors for aborted/panicked root. `engine/mod.rs:201–215`. | No App state flush, execution completion, result certification or separate-service shutdown follows from that API. |
| Marshal component exit | Supervisor waits for the first actor, preserves its result and aborts the others; dropping Children also aborts them. `marshal/service/supervisor.rs:15–84`. | A clean actor exit can end the service with Ok; service completion is not continuing health. |
| Marshal abort/join | ServiceHandle::abort records explicit shutdown and aborts the supervisor. join maps expected Closed/Aborted after that request to Ok; otherwise reports component/supervisor failure. `supervisor.rs:87–115`. | Ok after requested abort means the shutdown path was accepted, not that pending Custody or App writes became durable. |
| Catalog mutation failure | Owning actor stops, with in-flight requests resolving Closed; supervisor ends the service. `catalog/actor.rs:296–312`; `marshal/mod.rs:48–50`. | Closed is not invalid payload or proof no write occurred. Reopen/recover rather than reuse a failed mutable store. |
| App Update reporter Closed or dropped Exact | Delivery fails and Marshal supervisor stops its subtree. `delivery/actor.rs:303–327`; `delivery/acks.rs`. | Native activity feedback is ignored, so App/Marshal failure is not automatically an immediate Engine failure. The node owner coordinates the coupled graph. |

The example explicitly stops and joins Engine, then App, then Marshal and its resolver/broadcast, then network (`examples/log-multimmit/src/node.rs:343–353`; `marshal.rs:91–110`). It is a synthetic log example, not a graceful transaction-state drain implementation. The App still chooses an honest durable completion versus restart/replay outcome for outstanding canonical work.

Runtime supervision aborts descendants when their parent task exits (`runtime/src/lib.rs:355–386`). A plain future is not the same lifetime owner as a spawned task; ordinary Handle drop is not the abort-on-drop guard (`runtime/src/utils/handle.rs:358–374,439–461`). Thus a partially completed assembly should stay under the existing node task's managed lifetime and handle cleanup. No separate Driver service is required. This review uses the native public lifecycle contracts and does not claim a new proof about completion of arbitrary CPU jobs outside that subtree.

## Callback cancellation and accepted custody work

Local builds/custody are run by the native private AppExecutor, not transaction execution (`actors/voter/actor/app.rs:83–173`). A local custody job races its verdict against native cancellation (`:143–159`). The voter checks CancelRequested before treating a non-true verdict as Fatal::Automaton (`actor/live.rs:578–605`). Remote chain validation similarly races a native cancellation channel; anchor advancement removes settled jobs and cancels their awaits (`actors/voter/chain_plane.rs:505–554`). The App should not invent an origin/cancellation argument in Automaton.

The example App uses `response.closed()` as the caller cancellation signal for subscription waits and proposal preparation/staging (`examples/log-multimmit/src/application/actor.rs:60–85,248–276,329–336`). A real App can use the same signal while separately fencing speculative attempts and canonical writer ownership. Canceling a native verdict wait does not itself cancel an App-owned transaction job or make an already admitted candidate canonical.

Marshal's operations deliberately have different cancellation boundaries:

- `stage_block`: router owns accepted storage work, and dropping the returned Custody does not cancel it. The router sends the Custody result before downstream backfill bookkeeping (`marshal/service/router.rs:302–326`). A completed success is still a valid durable fence if later bookkeeping fails.
- `subscribe_block`: callers share acquisition; when all callers leave, the unresolved race can be aborted. Once a block is found, its durable settlement runs independently of remaining callers (`marshal/service/subscriptions.rs:1–9,135–190`). This is within the service lifetime, not a promise to complete after service abort.
- Explicit fetch: dropping its future cancels that fetch request (`marshal/mailbox.rs:376–417`). It does not undo bytes already admitted, nor establish a missing durability boundary.
- `install_floor`: accepted router work is not rolled back by dropping its reply (`marshal/service/router.rs:410–424`). App import coordination cannot equate caller cancellation with “floor unchanged.”

Custody::wait returns its configured Closed error when the accepting actor drops the unresolved sender (`actors/util/completion.rs:1–40`). That is not success. Only successful durable custody/put/subscription completion justifies the native custody promise; only linked App durability justifies Update ACK. Abort/join alone supplies neither.

## Retained Update and restart ownership

Marshal stopping drops its own pending ACK waiters, not Update values already moved to App. An App worker may still hold block/token/state references. Restarting Marshal alone can replay a new delivery window while old App work remains. Reconcile/fence those values through the existing App/node lifecycle, just as floor import coordinates old and new generations; do not infer global retention bounds from one Marshal window. A normal coordinated stop that also joins/fences App is the simple existing ownership path.

No unconditional drain is implemented by native ready, mailbox drop, service abort or ACK token drop. If App completed durable apply but Marshal did not persist its cursor, reopening can redeliver; exact identity replay remains the recovery rule. An incomplete App write must not receive a fabricated ACK to make shutdown appear clean.

## Root-owned documentation recommendations

1. Keep the E2E startup/teardown sequence and its readiness caveat. Optionally link to the newly explicit Marshal-open distinction in reference integration instead of duplicating another startup diagram.
2. If describing supervision in more detail, distinguish each native service subtree from the node's coupled Engine/App/Marshal/transport lifecycle. Describe Engine join as a runtime lifecycle result, not a returned voter Fatal or storage flush.
3. Preserve existing current-attempt/writer fencing language. Native request cancellation, worker result cancellation and state durability are separate facts; existing runtime/oneshot methods suffice.

No current reader page was found that requires a second native task driver. The confirmed minimal omission was the Marshal-open actor ownership and cross-service cleanup boundary, now clarified in the owned integration page. Further graceful App shutdown, checkpoint/writer handoff and protocol integration remain implementation work, not guarantees added by these docs.
