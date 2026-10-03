from pathlib import Path
import hashlib,json,re,datetime,subprocess
b=Path(__file__).parent;root=b.parents[4];m=json.loads((b/'source-manifest.json').read_text());pins=m['pins'];baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
def link(tag,p,l,label):
 r,pin=pins[tag];return f'[{label}](https://github.com/{r}/blob/{pin}/{p}#L{l})'
n=lambda p,l,s:link('native',p,l,s);t=lambda p,l,s:link('tempo',p,l,s);c=lambda p,l,s:link('constantinople',p,l,s);v=lambda p,l,s:link('release',p,l,s)
report=f'''# Wave 8 — reuse worker ownership and completion helpers

## Outcome and scope

**Executor can use existing Commonware task/future helpers without a public Runtime, Planner, reschedule API or new worker actor.** Earlier lifecycle and Baton-task reviews already establish supervision, CPU placement, future pools and cancellation limits. This audit adds only two concrete connections not yet named in the execution layer: public `OptionFuture` for a sometimes-empty work slot and `Strategizer::strategy` for runtime-owned Rayon construction. Existing `ContextCell`/`spawn_cell` also avoid context take/restore boilerplate. These mechanisms do not choose execution priority, capacity, branch policy, stopping authority or worker quiescence.

Native stays `{pins['native'][1]}`; reader baseline `{baseline}` after CR10. Read current Executor/Storage and Rust contracts, canonical/results/state-sync/recovery E2E, wave5 baton-tasks and wave4 startup/lifecycle reports before source audit. Twenty-five freshly retrieved primary files match four newly authenticated complete, non-truncated native/release/Tempo/Constantinople trees. `source-manifest.json` records raw URLs, SHA-256, lengths and matching Git blob SHA-1. No canonical edits, dependencies, compilation, native tests or runtime trace.

Fresh explicit Commonware MCP calls used the user-provided public endpoint directly: server `commonware-library` v0.0.5, get_file version `v2026.9.0` for Handle185–275 and futures150–199 (zero-indexed). All 91+50 numbered lines match independently fetched pinned release bytes. Handle source is native-identical; the futures file differs in its pool lifetime surface. Release corroboration is version-labeled, not a dependency upgrade or native interoperability claim.

## Public mechanisms and their actual fit

| Existing public API at native pin | Avoided local plumbing | Boundary still owned by Executor/Storage |
|---|---|---|
| Supervisor::child / Spawner::spawn; shared(true)/dedicated | Task hierarchy and supported placement instead of another spawn/thread supervisor | Choose long-lived owner and finite work admission; task construction can still execute inline. Canonical mutation must not become an advisory worker's descendant |
| Strategizer::strategy(NonZeroUsize) → Rayon | Manually constructing a Rayon pool/thread spawn handler | Select compatible runtime, lifetime and parallelism; no prioritization/fairness/cancellation guarantee |
| ContextCell / spawn_cell! | Taking/restoring a moved runtime context for an actor's owned future | Macro restores context synchronously and uses default shared(false); choose CPU placement explicitly when needed |
| utils::futures::Pool / AbortablePool | Completion multiplexing and abort registration for polled futures | Pools do not supply work bounds, original execution identity or physical quiescence; completion must still be checked against actual input/base/runtime/generation |
| utils::futures::OptionFuture | Hand-written None → pending branch for an optional active future | Native wrapper does not clear itself on Ready and implements no FusedFuture; owner must remove/replace the completed slot before polling it again |
| Handle::from_receiver / from_future / select | Normalizing completions and first-exit group teardown | Completion handles abort waiting only; select aborts a chosen group, not generic successful branch jobs. No certificate/material verification, rollback or durable flush |

Sources: {n('runtime/src/lib.rs',261,'Spawner')}, {n('runtime/src/lib.rs',357,'Strategizer')}, {n('runtime/src/tokio/runtime.rs',657,'runtime-owned Rayon factory')}, {n('runtime/src/utils/cell.rs',6,'ContextCell/spawn_cell')}, {n('utils/src/futures.rs',16,'Pool')}, {n('utils/src/futures.rs',77,'AbortablePool')}, {n('utils/src/futures.rs',150,'OptionFuture')}, {n('runtime/src/utils/handle.rs',28,'task versus completion Handle')}, {n('runtime/src/utils/handle.rs',156,'completion constructors')}, {n('runtime/src/utils/handle.rs',189,'first-exit selection')}.

### Optional slot: an actual public helper, with a non-drop-in Tempo difference

Native OptionFuture implements Default/From<Option<F>>, Deref/DerefMut and Future. None remains Pending, whereas futures::future::OptionFuture resolves None immediately. A sometimes-empty execution slot can use it without another optional-future wrapper. Its {n('utils/src/futures.rs',185,'poll')} delegates the installed future and leaves Some installed even after Ready. Repeatedly polling a completed non-fused future is not guaranteed valid; the owner must clear/replace the slot or use an appropriate selected fusion pattern.

Tempo's actual Executor uses {t('crates/consensus/src/executor/actor.rs',219,'one execution slot')} and abortable parent-fetch subscriptions, but its OptionFuture is {t('crates/consensus/src/utils.rs',26,'a crate-private vendored wrapper')}. That wrapper explicitly clears the slot when ready and implements FusedFuture. It is neither an importable public executor primitive nor unchanged native OptionFuture. Reuse the public pending-when-empty mechanism with explicit completion handling; do not copy Tempo's whole actor or assume identical methods/semantics. The release public OptionFuture corroborated by MCP has the same no-auto-clear behavior; release Pool/AbortablePool permit `'a` futures while native public pools require `'static`. Source adaptation stays explicit.

### Cancellation must name what it cancels

Native Spawner returns a running-task Handle; a plain handle drop has no abort-on-drop implementation. `Handle::abort` requests future cancellation. `Handle::from_receiver/from_future` wraps completion waiting, so aborting it does not cancel underlying work. A {n('runtime/src/utils/handle.rs',54,'Handle::select group')} deliberately aborts all its handles when selection ends/drops. Independent branch workers that should remain alive after another completes do not share that first-exit teardown by default. An AbortablePool Aborter aborts its polled future; if that future is only awaiting a separately spawned Handle, the cancellation can drop the waiter while its worker continues. Existing context ownership or retained worker Handle must carry actual cancellation authority. No additional cancellation broker is required.

Sequential Strategy::spawn computes synchronously; Rayon with at most one thread also computes synchronously, and pool-member polling may execute pending CPU work inline. More importantly, a submitted Rayon closure keeps running when the result receiver is dropped. Spawner's Tokio implementation calls its closure to construct the task before it schedules the future. Place CPU computation **inside** the correctly placed task body; wrapping already computed work in an async result does not move it. {n('parallel/src/lib.rs',800,'Sequential')}, {n('parallel/src/lib.rs',1019,'Rayon')}, {n('runtime/src/tokio/runtime.rs',574,'task construction and placement')}.

Awaiting the spawned root's result is not a universal descendant/signing/storage quiescence barrier: Handle init sends the result before requesting descendant abort. Non-yielding CPU closures and independently submitted backend work remain distinct. The prior native join source-proof limitation is preserved. Result/adoption fencing still checks exact identity and local authority; no observed race/bug or completed worker transfer proof is claimed. {n('runtime/src/utils/handle.rs',125,'completion ordering')}, {n('runtime/src/utils/supervision.rs',144,'descendant abort walk')}.

## Actual chain and native-owner references

Tempo uses a {t('crates/consensus/src/executor/actor.rs',541,'private one-task slot invariant')}, polls completion before later scheduling in its {t('crates/consensus/src/executor/actor.rs',464,'biased owner loop')}, and uses {t('crates/consensus/src/executor/actor.rs',1533,'application scheduling priorities')} for forkchoice/finalized delivery/build/verify/convergence. These are workload/Simplex/EL-specific application policies, not a public Commonware scheduler or a chosen Baton priority. Its {t('crates/consensus/src/executor/actor.rs',2079,'parent subscription')} retains an Aborter; its {t('crates/consensus/src/executor/actor.rs',2550,'payload resolution')} races a backend resolve future against requester cancellation. Dropping the resolve future is that selected payload backend's seam; it is not proof that every CPU closure or canonical storage mutation is preempted. Parent/subscriber correlation and exact completed-result acceptance still belong to the current Executor owner.

Constantinople's {c('crates/application/src/consensus/execution.rs',159,'compute')} invokes existing Strategy for pure plan/update work and returns a staged batch plus optional updates; final sealing is separate. This supports using the same lower-level strategies/material split. Its transfer semantics, plan, Stateful/Application graph and scheduling are not adopted. Native Multimmit's {n('consensus/src/multimmit/actors/voter/executor.rs',37,'generation/permit completion')} is private owner/correlation code; Core's reserves are not a public Executor capacity API.

Native Stateful's {n('glue/src/stateful/actor/core/verifications.rs',158,'quiesce/drive machinery')} waits for invalidated pooled requests and retains controls, but it is pub(super), relies on Application/Marshal and does not offer a public generic CPU-worker quiescence primitive. Do not import the full actor for it. The existing application access/worker fence and canonical authority remain additional integration work.

## Other helpers considered without introducing new infrastructure

`utils::channel::reservation::ReservationExt::send_or_reserve` already handles bounded queue send capacity and returns an owned pending reservation; it avoids a hand-written retry waiter if that endpoint is chosen. It bounds queue slots, not all retained reservation objects, executing jobs or CPU. No queue choice/work budget/native cut wait follows. {n('utils/src/channel/reservation.rs',74,'ReservationExt')}.

`utils::futures::rebind/rebind_entry` thread owned consuming mutation results back into an Option/map and return extra outputs via Threaded. Errors leave the entry absent; canceling the future after removal cannot restore its moved handle automatically. They are small existing conveniences, not a second canonical writer, cancellation-safe mutation, transaction/rollback or durable recovery contract. The current Shared/WriteSlot connection is already documented; no additional reader change is needed for these optional conveniences. {n('utils/src/futures.rs',224,'rebind')}, {n('utils/src/futures.rs',252,'rebind_entry')}.

## Minimum connection and reader delta

Keep one existing Executor owner with application context/tree/result/canonical-authority checks. Reuse public tasks/future controls below it; retain explicit authority over running workers separately from completion waiters. Optional slot and runtime-owned strategy construction are the only small new reader additions recommended in READER_DELTA.md. Current Baton/recovery lifecycle explanations need no repeated new section. No public Runtime, Planner, reschedule method, actor, policy/schema, scheduler, dispatcher, queue or new quiescence service is selected.

For certified state-sync switching, continue direct execution until the **matching f+1 certificate and applicable material** are both verified. A response, reached-target notification, completed waiter, stale worker or abort request supplies neither. Before canonical apply, fence conflicting access/work across clones under the same Storage writer; do not cancel an in-progress canonical mutation through advisory task replacement. DirectExecuted versus ImportedVerified signing provenance, exact input/base/runtime/order, root preparation before own full-result signature and durable state/output/cursor/provenance linkage remain unchanged. Obsolete advisory work may be canceled under its own fence; that is distinct from stopping canonical direct work to import a peer result.

## Limits

Only source/API fit. No build/runtime job trace, fairness, preemption, bounded execution, strict quiescence, storage replacement or native integration proof. Whole chain/native package identities remain separate; release evidence does not force an upgrade. Worker placement/parallelism/priority/cancellation/retention and result policy cells stay empty; the six-hour goal remains active.
'''
(b/'REPORT.md').write_text(report)
delta=f'''# Small proposed reader delta — not adopted

Baseline `{baseline}` after CR10. Keep existing sections, five traits/signatures, diagrams and empty choices. No repeated lifecycle/Baton-task section is needed.

## docs/execution/README.md existing primitive table

One runtime/future row can replace the vague runtime part of the current journal/metadata row (keep journal/metadata as durability):

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `runtime::{{Spawner, Strategizer}}`; `utils::futures::{{Pool, AbortablePool, OptionFuture}}` | Existing worker ownership, compatible Rayon construction and completion polling | Selected placement/work bounds, exact completion context and safe worker/access fencing; cancellation is not quiescence |

Add one short paragraph if needed:

> The public `OptionFuture` keeps an empty active-work slot pending; its native implementation does not remove a completed future, so its owner must clear or replace that slot. `Strategizer::strategy` constructs the runtime-owned Rayon strategy without another thread-pool factory. Aborting a completion waiter does not stop separately spawned work; keep worker authority and canonical mutation ownership through their actual completion. Placement, parallelism and cancellation policy stay open. {n('utils/src/futures.rs',150,'Optional future')}, {n('runtime/src/lib.rs',357,'Strategy factory')}, {n('runtime/src/utils/handle.rs',28,'Task/completion distinction')}.

## Other pages

No Rust/E2E/Storage trait or diagram change. Existing state-sync stop-only-after verified matching certificate plus applicable material, shared writer, direct/imported provenance and durability rules already apply. Do not add generic worker priority or quiescence APIs. The report's Tempo private OptionFuture auto-clear/FusedFuture difference is source-port guidance; if a reader comparison is added, label it as a pattern rather than unchanged native reuse. Other public conveniences (ContextCell, reservations, rebind) need no new reader inventory.
'''
(b/'READER_DELTA.md').write_text(delta)
entries={(x['repo'],x['pin'],x['path']):x for x in m['sources']};anchors=[]
for name in ['REPORT.md','READER_DELTA.md']:
 for repo,pin,p,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^\s)#]+)#L(\d+)',(b/name).read_text()):
  x=entries[(repo,pin,p)];ls=Path(x['local']).read_text().splitlines();assert 1<=int(line)<=len(ls);anchors.append({'document':name,'repo':repo,'pin':pin,'path':p,'line':int(line),'line_text':ls[int(line)-1]})
receipt={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':baseline,'sources':len(m['sources']),'complete_trees':4,'anchors':anchors,'files':{p:hashlib.sha256((b/p).read_bytes()).hexdigest() for p in ['REPORT.md','READER_DELTA.md','source-manifest.json','mcp-content-check.json','mcp-futures-content-check.json']},'reader_hashes':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['docs/execution/README.md','docs/execution/interfaces.md','docs/execution/state-sync.md','docs/e2e/canonical.md','docs/e2e/recovery.md','docs/overview/rust-interfaces.md']},'canonical_edits':False,'implementation_build_native_test':False};(b/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['files'],indent=2));print(len(anchors),'anchors checked')
