# Cases to verify

**Verify the App at its actual Multimmit/Marshal boundaries.** The cases below are acceptance criteria for future implementation, not executed Baton tests. Documentation source review, link checks and renders verify this design's presentation only.

Use the deterministic Commonware runtime and simulated network with the same public Sender/Receiver interfaces as deployment. Construct real App callbacks and current Multimmit Marshal; native mock callbacks alone do not establish transaction/body/scheduler behavior. Reuse the current [Marshal integration fixtures](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/tests.rs) for assembly patterns.

| Existing support | What it controls | App assertion still needed |
|---|---|---|
| `deterministic::Runner`, simulated Network/Oracle | Seeded scheduling, peer/channel links, delay/loss/bandwidth | Exact application outputs, custody, ordered indices and state |
| Native Engine and Marshal test fixtures | Native producer/DA/order, custody/backfill and delivery lifecycle | App-owned pool and scheduler integration through real callbacks |
| Runtime `DelayedSyncContext` / `PendingSyncs` | Started, entered, parked, completed or failed sync operations | Correct App state/output/applied-position linkage before ACK |
| `Runner::start_and_recover` | Recoverable runtime checkpoint for a subsequent runner | Reopen all matching stores/services; no surviving old writer authority |

Inspect the current sync controls rather than copying an older API name. Observe actual operation gates/completion counts; starting a sync does not prove durability. A lost application ACK is a separate boundary after application state is durable. Runtime mocks model their storage abstraction, not every possible physical device failure. [Current sync controls](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/runtime/src/mocks.rs#L1240), [runtime recovery](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/runtime/src/deterministic.rs#L578).

## Verification cases by component

| Component | Required scenarios and assertions | App execution status |
|---|---|---|
| Pool / propose | Valid/invalid/duplicate tx; selected/unselected retention; bounded batch; canceled proposal; selection does not imply canonical retirement; body digest and supplied producer context match | Not run |
| Custody / verify | Header-before-body and body-before-header; permanent invalidity vs temporary absence; wrong digest/context; accepted stage before durable completion; recovery reads matching retained body | Not run |
| Verify admission | Remote eligible block, local pre-sign check and startup recovery serviced before Engine::open returns; duplicate/canceled/stale completion, including remote rescheduling after closure; parent still pending its verdict; exact contextual deduplication; no false new-peer event; speculative queue pressure never becomes invalid verdict | Not run |
| Scheduling independence | Verify true after valid durable custody while execution is blocked; healthy native progress while App speculative worker is stalled; body I/O remains the promised custody fence; ready canonical work reaches durable ACK under sustained optional backlog | Not run |
| Retention / late verify | Native release uses per-chain released height, not certified height or App applied index; retained recovery requests still validate after speculative retirement; settled/canceled late requests do not recreate work; Marshal prune retains unreleased bodies and App retains independently needed state/results | Not run |
| Canonical Update | Exact next index and block identity; no App reordering; replay below applied cursor checks identity; gap/conflict stops apply; canonical-first input works without prior verify or speculative admission, including Observer | Not run |
| Delivery capacity | Non-dropping Update ingress under `max_pending_acks`; retains token; `Backoff` is not treated as retry; accidental Exact clone/drop detected; out-of-order ACK cannot skip earlier unacknowledged output; batching/signing ranges cannot require an extra Update beyond a full window before any ACK for durable application | Not run |
| Floor/import handoff | App checkpoint durable before authorized floor jump; old App-held Updates survive native waiter reset; new window overlap is bounded; no assumed Update generation field; stale worker/input fenced; crash between App adoption and Marshal reset recovers matching prefix | Not run |
| ACK / recovery | App apply durable before ACK; crash before ACK; ACK observed before Marshal cursor sync; already-applied redelivery is idempotent; ACK after valid speculation needs no repeated transaction execution | Not run |
| PreCut | No Baton instance/reports/direction/policy changes; shared pool/body/backend/resources; `F ++ sort_G(pending)`; exact-parent reuse/repair on new continuous confirmed input | Not run |
| Pending-only rule | A running, C then B admitted before C dispatch gives ABC; B after C starts preserves AC and gives ACB; arrival alone does not reexecute; differing native ABC still repairs from the correct parent | Not run |
| Baton reports | Exact context/identity verification; one report per signer; first `4f+1` or fixed deadline closes once; later arrivals do not extend deadline or mutate frozen originals | Not run |
| Baton selection | Completed bounded full-candidate evaluation; longest valid entire prefix with `2f+1` distinct original support; otherwise sum-LCP for a nonempty report snapshot; zero reports or no prepared policy uses the actual-parent valid base path before protected adoption | Not run |
| Native Baton policy | Authenticated actual-parent/rule/frontier binding; exact leading-order preservation; omission/substitution/reordering rejected; cut never waits for report/timer/optimizer/ACK; view recovery and Marshal interpretation agree | Not run |
| Worker termination | With one worker, an attempt ending without reusable output settles ownership once and allows required work to resume after safe resource release; dropped waiters alone do not release live work; an ordinary valid transaction revert remains a completed execution outcome | Not run |
| Execution / backend | Exact input-state/runtime ancestry; reuse only matching work; stale worker completion fenced; root preparation separate from effects; single canonical writer and crash-linked applied identity | Not run |
| Certification / state sync | `f+1` valid distinct same-statement signatures; direct/imported provenance; imported state never signed as local execution; state-sync floor/worker/Update coordination; scheduler cannot gate result/apply path | Not run |

Existing native tests include custody subscriptions, staged Relay, exact body/history backfill, restart redelivery and bounded ACK pipelining. Their presence is source evidence of native mechanisms, not proof that the proposed App has been tested. Useful starting points are `buffered_ingress_subscription_establishes_durable_custody`, `production_engine_reporter_survives_engine_and_marshal_restart`, `crash_redelivers_only_until_acknowledgement_is_durable`, and `delivery_pipelines_exact_acknowledgements_up_to_the_configured_bound` in the [current Marshal tests](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/tests.rs).

For each eventual test, compare canonical state/output with a sequential oracle over the same exact order, base state and runtime. Compare Original / PreCut / Baton under matching input, backend, resources and certification/readiness endpoint. Trace repeatability and historical toy tests do not establish these properties or performance gains.
