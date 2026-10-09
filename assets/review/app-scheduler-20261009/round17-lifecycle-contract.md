# Round 17: public lifecycle contract recheck

Native source `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. Read current integration, consensus/ordered-input, baton startup and E2E recovery prose against source. No reader contradiction found, no native edits and no runtime tests. This round supplements round6-lifecycle and corrects one shorthand in the audit evidence.

## Public results and concrete entry points

| Boundary | Exact public result / source | Interpretation confirmed in current docs |
|---|---|---|
| Engine::open | `Result<Engine<...>, multimmit::OpenError>`; `engine/mod.rs:446–497` | Validates before storage, recovers and performs required App verification, then constructs native actors without spawning them. Failure is not a Running::ready failure, and does not shut down already-started sibling App/Marshal/network. |
| marshal::open | `Result<(Service<...>, BackfillBridge<...>), marshal::OpenError>`; public reexport `marshal/mod.rs:91`, implementation `service/mod.rs:96–187` | It is not actor-free. `marshal/open.rs:149–172` starts catalog and optional promoter before returning Service. The node owns this entire partial assembly, not only the later ServiceHandle. |
| Service::start | `(Mailbox<...>, ServiceHandle)` with no Result or ready handle; `service/mod.rs:213–311` | Starts delivery and other actors, then supervisor. Existing committed outputs can reach App immediately; precreated Update ingress must retain them even before App state/scheduling is live. |
| Running::ready | `Result<(), Stopped>`; `engine/mod.rs:159–172,187–195` | Cached milestone. Once the sender sent success, even a first late poll after later Engine failure can return Ok. It is not a health probe, App readiness, body-sync completion or proof the first proposal finished. |
| Running::join | `Result<(), commonware_runtime::Error>`; `engine/mod.rs:201–209` | Internal voter Fatal is logged then the voter returns; Engine's root can select that child exit and return normally. Unexpected Ok completion is a stop signal. Join does not return the typed voter Fatal. |
| ServiceHandle::abort / join | abort takes `&mut self`; join returns `Result<(), marshal::Error>`; `service/supervisor.rs:87–116` | Explicit abort sets shutdown_requested; subsequent runtime Closed/Aborted becomes Ok. An unrequested clean actor exit can also end the service with Ok. Neither means application flush or continued service health. |

The current integration lifecycle anchor correctly covers unexpected completion, sibling supervision and stop order. Concrete sources for readers remain Engine open/start at engine/mod.rs:446/517, Marshal Service::start at service/mod.rs:213, and ServiceHandle at service/supervisor.rs:87. No new readiness service or task driver is needed.

## Ownership precision newly checked

`Pool::cancel_all` clears the stored futures (`utils/src/futures.rs:61–67`); it does not independently join arbitrary work those futures spawned. Local AppExecutor spawns a child task and stores a future awaiting its ordinary Handle (`actor/app.rs:171–178`). Ordinary Handle is distinct from AbortOnDrop (`runtime/src/utils/handle.rs:358–374,439–461`). Therefore an audit sentence saying generation clearing "cancels every job" must not be interpreted as proof all underlying submitted work has physically stopped.

Local custody has an explicit cancellation channel, which AppExecutor clears/signals; remote chain-plane verification is polled directly and has its own cancellation race. Stale native completions are fenced separately. Full Engine exit invokes runtime supervision of descendants, and the public Running contract names join as the shutdown-completion boundary. None of that is App state durability or termination of arbitrary work outside the owned subtree.

The normal production GenerationAdvanced transition is issued at Start/RecoveryComplete (`machine/reducer/step.rs:679–718`), not a public App-import/reset command. This review identifies an ownership distinction, not a demonstrated native defect or an assertion of repeated live generation leaks. Current reader pages already distinguish response cancellation, worker fencing, accepted storage and durable completion. Earlier audit shorthand is annotated below rather than adding another reader paragraph.

The same distinction explains partial assembly ownership: dropping an ordinary handle or an open future is not a universal sibling-service abort guard. Marshal Service owns the early catalog/promoter handles before start; the existing node/runtime lifetime must manage abandoned assembly. Current reference/integration.md states precisely that obligation.

## Status and recovery checks

- Engine root selects runtime stop or any mandatory ingress/verifier/resolver/voter exit (`engine/mod.rs:547–587`). Voter records internal fatal errors then returns (`actor/mod.rs:409–415`; `actor/live.rs:124–150`). Reporter feedback is not an alternative cross-service supervisor.
- Marshal supervisor returns the first finished actor's result and aborts siblings. Clean completion is Ok; component/task failure is an Error (`service/supervisor.rs:15–26,64–84`). Requested abort's normalized Ok cannot be used as a flush receipt.
- Delivery starts independently of App/native ready, and Update report remains synchronous (`service/mod.rs:235–250`; `delivery/actor.rs:303–326`). Existing docs require retained ingress and replay deduplication accordingly.
- A recovered catalog state wins over Start initialization (`storage/catalog/mod.rs:359–375`). Configuration is still validated and epoch/archive layout remain checked; "recovered checkpoint wins" does not mean arbitrary invalid Config is ignored. Current prose does not claim that.
- The example aborts/joins Engine and App before stopping Marshal/resolver/broadcast and network (`examples/log-multimmit/src/node.rs:343–353`). It supplies a concrete teardown order, not a transaction-state drain implementation. App must separately establish its honest durable boundary or recover/replay after restart.

No changes to reader docs were needed. Only this concise report and precision notes in prior audit reports were written; source and diff checks support the wording, not a runtime liveness proof.
