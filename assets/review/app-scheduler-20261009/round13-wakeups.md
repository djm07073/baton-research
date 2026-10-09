# Round 13 — Waits, wakeups and authority

Reviewed current core/execution/PreCut and recovery/leader flows for a waiting condition with no owning continuation. This table specifies App design obligations around existing native/runtime mechanisms; it does not claim an implemented scheduler or execution test. Both modes use the same ordinary execution/Update continuations. Report/planning rows apply only to Baton.

## Wakeup and authority table

| Wait or deferred state | Existing event that re-enters the owner | Authority checked before continuing | Work that remains independent |
|---|---|---|---|
| Startup recovery → live scheduling | `Running::ready()` completion plus App recovered-base completion; owner transitions lifecycle and re-evaluates retained candidates | Current recovered applied identity, exact candidate/context and eligibility | Custody callbacks remain serviceable during `Engine::open`; no wait for a second verify invocation or nonexistent index-zero Update |
| Missing body / custody | Marshal subscription/fetch/staging future completion, or native response cancellation | Exact header/body/context and actual custody success; current lifecycle/applied position rechecked after await | App owner stays responsive; speculation/report work is not a validity prerequisite. Subscription alone is not a peer fetch |
| Unknown/unfinished execution parent | Retained parent candidate facts, exact parent worker completion, canonical apply/import/recovery completion | Required dependency validity plus exact execution/checkpoint/storage ancestry | Merely receiving the child's valid body does not start dependent execution from an unrelated state |
| Full worker budget | Actual resource release/worker termination updates App state; owner re-evaluates retained eligible candidates | Pending/current-attempt ownership, valid exact parent and available resources | Verify can finish after custody; discarded speculative opportunities remain executable on canonical Update. No false payload verdict to obtain a slot |
| Pending report crypto | Bounded App crypto job completes and re-enters report owner | Current window/context, full signature/subject, distinct eligible identity, admission limits and still-open snapshot | Native cut and canonical apply continue. CPU completion itself is not report admission |
| Report threshold/deadline | Owner processes either admitted-report threshold or existing Clock deadline future | Close once using first processed threshold/deadline event; freeze original admitted reports with `m ≤ 4f+1` | No deadline extension for new arrivals; no wait for all outstanding crypto completions |
| Planning completion | Existing worker result is received by App owner | Original frozen window/context/current planning attempt and completed bounded evaluation | Stale/incomplete work cannot overwrite prepared state. Native actual-proposal validation is a later, still-proposed integration boundary |
| Closed snapshot / cycle finish | Local evaluation/enqueue-or-skip finishes; a new eligible context/work event can start the next cycle | New cycle context; closed snapshot remains immutable | No direction ACK/Ready quorum and no wait for peers to finish executing. Exact restart settings remain open |
| Canonical mismatch / missing exact work | Authoritative retained Marshal Update starts reconciliation; required execution/repair or verified import completion wakes its continuation | Exact continuous index/block, canonical predecessor/runtime and writer authority | No previous verify/candidate entry required; reports and local speculative priority cannot reorder or approve the Update |
| Failed/aborted current worker | Actual termination/failure completion or node recovery; owner settles the current attempt once | Was this the current attempt; did work safely terminate; what valid checkpoint remains; what resources are really releasable | Required canonical input remains retained. Aborting a completion waiter alone is not an underlying-work termination event; mutable DB failures still require recovery |
| Durable writer completion | Apply/finalize/barrier and App recovery-linkage completion re-enter App owner | Barrier covers selected work, durability succeeded, exact applied identity/outputs/provenance match current ownership | Owner advances once and ACKs exact retained delivery; pool maintenance is scheduled independently. Marshal cursor persistence is subsequent native work |
| Result certificate arrives | Existing authenticated App peer receive and verification job completion | Full subject, eligible distinct f+1 identities, irrevocable input/base; otherwise retain pending under chosen policy | Local valid direct work continues; scheduler adds no approval hop |
| Material / matching input becomes available | Material fetch/sync completion or canonical input/base advancement re-evaluates pending target | Certificate-authorized result, complete outputs, current predecessor/applicability and safe writer handoff | Progress notification is not DB readiness. No direct-work preemption until certificate, usable material and safe adoption conditions hold |

Core locations: `baton/interfaces.md:7-15,35-87,95-135`; `baton/direction.md:18-43,47-85,87-97`. Execution details: `execution/interfaces.md:24-55,63-73`, `execution/qmdb.md:44-83,107-133`, `execution/state-sync.md:5-15,31-43`. Startup/capacity re-evaluation is explicit at `e2e/recovery.md:46`.

## Confirmed completeness correction

Before this pass, the dispatch paragraph covered failed launch, stale/canceled result rejection and successful completion, but did not explicitly settle an already-started **current attempt ending without reusable output**. A one-worker counterexample was: B is claimed and counted in current work; its computation terminates without a valid checkpoint; the App rejects the result but leaves the claim/capacity pinned, preventing further dispatch even though no work runs.

Reported the smallest correction to root. Root updated `docs/baton/interfaces.md:87`, and the final text was read back:

- Failed launch or a current attempt ending without reusable output settles ownership once and re-evaluates from the last valid checkpoint.
- Claims/resources are released only when work never started or safely terminated; losing a waiter is insufficient evidence.
- Required canonical input remains retained for the chosen repair/recovery path.

This adds no public callback, scheduler service, retry default or cancellation protocol. A deterministic transaction failure/revert can still be an ordinary completed execution outcome; it is not automatically a failed worker. Mutable-storage failure remains fatal for that DB instance under the existing QMDB contract. The concrete retry/resource/access policy is still open.

## Existing source mechanisms checked

| Source | Relevance |
|---|---|
| `examples/log-multimmit/src/application/mailbox.rs:148-173` | Existing Automaton handle creates response channels, enqueues messages and returns ready receivers; callback work need not occupy the native caller until custody finishes |
| `examples/log-multimmit/src/application/actor.rs:59-118,192-205,290-370` | Cancellation/body futures enter a pending pool and completion events return to the same App loop; this is an existing assembly pattern, not the proposed transaction scheduler implementation |
| `consensus/src/multimmit/engine/mod.rs:187-195,437-488` | Native readiness is a future; open first performs recovery with Automaton before running native actors |
| `runtime/src/lib.rs:500-514` | Existing Clock provides a deadline future; report closure needs no periodic polling or added consensus event |
| `parallel/src/lib.rs:184-197,960-970` | Strategies may execute while the work future is created or polled, so both creation and polling belong in properly placed bounded App worker work |
| `runtime/src/utils/handle.rs:27-31` | Completion-handle abort stops waiting, not necessarily submitted work; termination/resource release must be established separately |
| `glue/src/stateful/db/mod.rs:334-397,415-485,493-579` | By-value mutation ownership, distinct apply/finalize/barrier boundaries and mutation non-overlap underpin the writer continuation and failure handling |

The current native `AppExecutor` is specifically the local propose/verify job executor, not the universal owner of remote/recovery callback work. Root narrowed both core/execution introductory wording accordingly; those final introductions were read back in this round.

## Limits and result

No further missing wakeup or actual contradictory starvation/boundedness claim was found. Future pools, local clocks, runtime handles and existing App-owned state changes can deliver the listed continuations. They do not automatically implement App identity checks, retention, resource accounting or fairness; the documents leave the concrete policies open instead of claiming a universal liveness guarantee.

No proposed report/planning wait was moved into the native cut path or synchronous `report(Update)`. The full Baton leader-context/policy-adoption bridge remains future native protocol work; this table does not mislabel it an already existing callback. No production execution-page changes were made by this agent in round 13, and no native code or runtime tests changed.
