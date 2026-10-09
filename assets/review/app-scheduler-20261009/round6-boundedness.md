# Round 6: boundedness and progress boundaries

Reviewer: `/root/simplification`. Read-only analytical audit against Commonware `6233438985d8249d2b2bc1204191d5d405652288`. These are source observations and future App integration obligations, not executed protocol tests or a liveness proof. No signing range, codec, timeout, quota, worker policy or new public layer is selected.

## Findings

1. **Small source-accuracy correction:** `baton/direction.md` warns that a planning future may execute synchronously when polled. Current `parallel::Strategy::spawn` can execute the entire closure before returning the future. `Sequential::spawn` always does this; Rayon can do it under its inline strategy. Say that creating or polling the future can execute work synchronously. The existing requirement to keep planning work outside admission/cut handling is correct.
2. **Future batching must preserve delivery progress:** the open signing/commitment-boundary choice must be compatible with Marshal's finite outstanding-ACK window. This is a missing explicit acceptance condition, not a current implementation defect. A result range can be larger than the window if independently progressing durable application and exact retained result material support it; the design must not silently equate signing range with the minimum unacknowledged intake batch. No per-block signing requirement follows.

The other requested boundaries are already stated correctly. Current docs do not claim `max_pending_acks` bounds all App memory, do not make speculative capacity a condition of a valid custody verdict, and do not require certificate availability before valid direct work proceeds.

## Future result ranges versus current ACK window

Actual source behavior:

- `marshal/actors/delivery/actor.rs:237-247` reports further canonical blocks only while the pending window has capacity.
- `marshal/actors/delivery/acks.rs:74-84,107-124` bounds the pending queue and releases its acknowledged contiguous prefix. A later ACK cannot skip the oldest outstanding position.
- `marshal/config.rs:226-230` explicitly separates pending application ACKs from cursor persistence. Contiguous acknowledged progress coalesces while the cursor syncs.
- `marshal/actors/delivery/actor.rs:315-325` retains an ACK waiter after reporting. `Feedback::Backoff` does not arrange retry of an unretained Update.

Analytical counterexample, conditional on a future App choice:

```text
W = 2 outstanding Marshal Updates
R = 3 canonical inputs required by the App's chosen all-at-once durable batch
Canonical input is consumed only through Update; no alternate authenticated intake exists.

Marshal reports U1 and U2.
App retains both but will neither durably apply nor ACK until U3 arrives.
Marshal cannot report U3 until an earlier ACK releases capacity.
App waits for U3; delivery waits for App. Native agreement may continue.
```

Waiting for an f+1 certificate over that same range before the first ACK can create the same cycle, in addition to unnecessarily requiring peers. Current docs expressly permit direct canonical application before f+1 certification (`baton/interfaces.md`, `execution/interfaces.md:56-62`) and therefore do not prescribe either bad path.

Smallest suggested addition to the open-boundary prose: "Choose durability/batching boundaries that can release Marshal's ACK window without waiting for undelivered inputs; a larger signing range must not prevent independently valid durable application and ACK progress." The exact batching and retention solution remains open. It is not necessary to add a second order stream, change `Update`, require per-block signatures, or ACK before durability.

Result-range liveness also needs common exact subjects and retained material. Nodes signing different ranges do not combine merely because roots match; a certificate cannot be sliced. The current explicit open decisions and result-serving obligations preserve that limitation rather than promise liveness from the f+1 threshold alone.

## Speculative budgets versus custody and canonical work

| Analytical condition | Required behavior | Current assessment |
|---|---|---|
| Valid body has durable custody; speculative queue is full | Complete an honest `true` verdict; defer/coalesce within the chosen bound or forgo speculation | Pass: `baton/interfaces.md` verify contract explicitly separates capacity from validity |
| No speculative metadata slot remains | Do not silently create an unbounded deferred set; canonical Update still causes execution/reconciliation | Pass: bounded policy or forgone opportunity is explicit |
| Body is missing or custody has not completed | Keep validity unresolved under the request lifecycle; native local/recovery paths still need `true` | Pass: storage/custody can be a real gate; speculation cannot replace it |
| Every optional worker is busy when canonical repair is needed | A concrete resource policy must keep required canonical/custody work serviceable; best-effort speculation cannot permanently consume its only route to progress | Future integration obligation; no worker allocation policy or implemented guarantee is claimed |
| A speculative waiter is canceled, but submitted CPU work retains handles | Do not treat the resource as physically released or permit invalid live DB access solely because the waiter disappeared | Pass: execution/QMDB pages preserve worker, access-fence and retention obligations |
| App recovery waits for Engine ready, while Engine open needs custody verify | Keep custody processing available before open and gate speculative dispatch separately | Pass: startup cycle is explicitly excluded |
| App uses one global owner lock across long execution/storage awaits | This can block otherwise independent custody/intake; one App is not a requirement for one blocking handler | Pass at design level: short admission handlers and separate Commonware tasks are explicit; implementation still needs validation |

The native callback is not a promise of unlimited body-storage capacity. Current source supplies storage/resolver/custody bounds and can experience legitimate I/O backpressure. The distinction is that transaction computation, reports, directions and optional speculation slots are not additional prerequisites for a valid custody verdict.

## Planning CPU versus cut no-wait

`baton/direction.md` and `e2e/leader.md` already require bounded background candidate evaluation, a closed original report snapshot, no timer/optimizer/report-count wait at cut, and a valid actual-parent base path when no policy has been prepared before adoption. They do not claim unfinished evaluation proves the longest prefix. After authenticated adoption, a protected policy cannot be silently dropped as fallback; that separate native availability/liveness obligation remains open.

Fresh source evidence for finding 1:

- `parallel/src/lib.rs:184-197`: `Strategy::spawn` documents inline execution before return and possible work on the polling thread.
- `parallel/src/lib.rs:960-970`: `Sequential::spawn` evaluates `f(self.clone())` before constructing its returned async result.
- `parallel/src/lib.rs:1199-1220`: Rayon's single-worker or chosen inline path also evaluates immediately and returns a ready future.
- `runtime/src/lib.rs:332-348`: runtime spawn placement distinguishes shared, blocking-friendly and dedicated work. A particular deployment strategy still needs selecting; a future's return type is not a CPU isolation guarantee.

The report count `m <= 4f+1` alone is not a total resource bound: report sequence bytes, candidate horizon/count, admissibility checks, retained windows and queued verification jobs also need bounds. Current direction/networking pages explicitly leave finite work budgets, bounded codecs, channel quotas and runtime placement open. An implementation cannot discharge those obligations by counting admitted reports alone.

## Optional certified import versus valid direct execution

| Analytical condition | Required behavior | Current assessment |
|---|---|---|
| No certificate or fewer than f+1 valid matching signatures | Continue valid direct work and permit direct durable apply/ACK | Pass |
| Certificate exists; matching material is missing or invalid | Continue direct work; a certificate alone cannot cancel the only local execution path | Pass: `execution/state-sync.md:7` and E2E state-sync alternatives |
| Certificate/material arrives for unresolved native input or wrong predecessor | Retain pending/recover exact order, or reject; no result-message shortcut through unresolved order | Pass |
| Import candidate preparation runs concurrently with direct execution | Separate candidate storage ownership; never open the same live partitions as an isolated candidate | Pass |
| Fully verified applicable import is chosen | Fence conflicting work/access and serialize one canonical writer; preserve imported provenance | Pass |
| Import mutation or durability fails after direct work was fenced | No ACK; recover authoritative storage before reuse. "Continue direct work" does not authorize using a failed mutable DB | Pass |
| Every validator waits for peer results rather than producing direct evidence | This violates the stated fallback. f+1 is a validity threshold, not a progress mechanism by itself | Excluded by current direct-work requirement; no general liveness theorem claimed |

No scheduler approval, report-window completion, direction ACK or result-service relay is inserted in these paths. Concrete handoff/retry/resource policies remain implementation work.

## What is and is not bounded

`max_pending_acks` is a count of one active delivery window. It is not a bound on all retained effects, result subjects/certificates, serving material, tx-pool entries, speculation, decoded allocations or in-flight worker handles. Current docs state the floor-reset overlap problem and require separate bounded accounting; `Update` has no generation field.

Current source also distinguishes:

- `max_block_bytes`: encoded per-block limit (`marshal/config.rs:266-270`).
- `max_delivery_bytes`: target bytes of one custody read; one larger valid block may be read alone to avoid stalling progress (`281-284`). It is not a strict cap on the App's entire inbox.
- Other configured caches, resolvers, storage segments and retained archives have their own limits/lifetimes. Encoded byte bounds are not automatically exact decoded resident-memory accounting.

`overview/architecture.md:75-77`, `overview/networking.md:19,39` and QMDB retention sections already require bounded queues/bytes and retain still-needed worker/query/recovery/result/sync material. No current global-memory claim needs removing.

Finally, "native consensus does not wait for an application ACK" describes the source control dependency. It does not promise native throughput under unlimited shared CPU, disk or network contention. Existing resource-placement and shared-backend comparison requirements preserve that distinction; this pass adds no warning or new service to the reader flow.

## Outcome

Root accepted both findings. `baton/direction.md` now requires creating and polling strategy work inside an appropriately placed worker. At root's request, `execution/interfaces.md` now states the durability-boundary/window progress condition without requiring per-block signing. Its completion pseudocode also accepts a still-current execution attempt only once and rejects canceled/retired/duplicate completions, aligning the parallel callback audit.

The native agent's fresh-start floor finding was source-checked in `marshal/config.rs:163-185` and reflected briefly in `execution/state-sync.md`: `Start::Floor` is caller-authenticated fresh-namespace import authority; later `Service::start` verification cannot retroactively authenticate it. A peer-served floor follows `Start::Genesis` plus verifying `install_floor`, or explicit existing epoch L-QC verification before a trusted floor start. No second proof engine is added.

Everything else is a preserved implementation obligation or an already-correct documented boundary. No protocol code, test, diagram or selected default was changed by this audit.

## Reviewed fingerprints after accepted fixes

Captured 2026-10-09T07:35:05+00:00. `git diff --check` passed.

- `docs/baton/interfaces.md`: `c9ffb733120a683cd2cbe5cd10134e9eec85509e9775c0c7f480ddf06061f8ea`
- `docs/baton/direction.md`: `05034ddefa566581528e7b1114cfa9a7391b03f704e147b8bae3308f8ab99519`
- `docs/execution/interfaces.md`: `6c0fcf11d1d97ee50f3be5e4d52b3c4550613ee2e894ed7cbc2eeda66549de13`
- `docs/execution/qmdb.md`: `d9de7f53bbcec34dfa86466e42c54dc6bd46ef28897e344067665bae05f81381`
- `docs/execution/state-sync.md`: `09c3a0a4f1bca56dd53040e40b45e6719d302068a0c7fc4949ecde1a390b727b`
- `docs/overview/architecture.md`: `ec3ddc229be0ef4fcae436ccef4f9fa162934a4bb7f85e744b7ca5a30f44524f`
- `docs/overview/networking.md`: `301efa5ca25405c2112de729d9664d9e5ad105519c0be34ce1d413e967031951`
- `docs/e2e/results.md`: `fe48138a0ef55784eed6a27a724755f27fed0f1a1ea4a18ca17b9e45e1990edb`
- `docs/e2e/state-sync.md`: `9b46bee7d882ac3f2a2783ab4ddb7d0e965e955448235653592d820d9f47134b`
- `docs/reference/verification.md`: `e80600277c7198c40fdd5774ff52b2c28481f8d566299f96ea647b238a390a44`
