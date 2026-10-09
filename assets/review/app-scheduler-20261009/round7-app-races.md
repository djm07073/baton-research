# Round 7: App ownership and concurrent event races

Reviewer: `/root/simplification`. Analytical audit of the rewritten App design against Commonware `6233438985d8249d2b2bc1204191d5d405652288`. No executable App exists in this documentation change; the traces below are design review, not executed concurrency tests.

## Confirmed pseudocode improvements

- **Admission is not dispatch.** Repeated successful verification may refresh the same candidate facts, but must not re-enqueue an already claimed attempt. Before launching computation, the serialized App owner claims the pending job, reserves its resources and records the current attempt. Root added this to `baton/interfaces.md:73-81`; owned execution/PreCut examples now agree.
- **The identities have different scope.** `execution/interfaces.md:16-18` now explicitly distinguishes exact block metadata from a path/parent-bound execution attempt. Deduplicating by block must not suppress legitimate repair on another exact parent, and a body digest alone must not combine different producer contexts.
- **Replay must exit.** The prior owned execution pseudocode put “recover/check an already applied identical update, or” above unconditional preparation/apply steps. It now explicitly ACKs and returns on exact durable redelivery (`execution/interfaces.md:39-40`); PreCut shows the same branch. This removes an ambiguous path to duplicate application rather than changing the established recovery contract.
- **Preparation does not reserve current writer state.** Direct/import preparation may await work while another transition advances the canonical DB. Recheck current predecessor and writer authority immediately before mutation; root's main callback and owned execution/state-sync/PreCut examples now say so.
- **Durability publication uses the same owner.** After durable application, reconcile the completion with the owner's current exact applied identity, advance once or recognize already-covered input, and ACK the matching durable Update. This avoids an old completion regressing scheduler metadata after a larger import. It does not require a new actor/queue or wait for pool maintenance.
- **Remove residual component aliases.** The result heading is now “Result certification inside App”; QMDB says “Give App execution concrete branch access.” Explicit old anchors preserve existing links. Neither section needs a named Executor component.

## Concurrent verification and metadata traces

| Event ordering | Required result | Assessment |
|---|---|---|
| Two remote callbacks for the same exact block finish custody together | Owner admits one candidate record; each still-live callback receives its honest verdict; one claimed local attempt per selected context | Pass with explicit claim-before-launch. The `true` response remains outside the admission condition |
| Local pre-sign custody and a later authenticated observation describe the same block | Refresh facts on the same identity; do not treat local custody as a unique other-lane packet or authenticated report admission | Pass: main entry/body pages qualify lane, role, lifecycle and report eligibility |
| Recovery records a usable body while dispatch is gated; live mode begins later | Reevaluate retained facts on owner state; do not wait for another successful verify event | Pass; startup owner transition remains distinct from payload validity |
| Verify awaits body/custody; canonical Update applies that block first | Complete any still-required custody verdict; owner sees exact applied identity and skips speculative admission | Pass; already applied is not invalid payload |
| Verify refresh arrives after the selected attempt is running | Update facts only; do not reinsert that attempt into pending or append it to F twice | Clarified by this pass |
| Two contexts reuse the same body bytes | Keep separate exact block identities; body-digest equality does not erase producer context | Pass: source header identity binds context and body digest |
| Same exact block must be repaired after a different canonical prefix | Use a distinct exact execution context; block-level metadata dedup does not authorize old-parent result reuse or forbid repair | Explicitly clarified |
| One of several custody request waiters is canceled | Do not erase independently useful candidate facts or another request's verdict obligation merely because one receiver disappeared | Pass: callback obligations and shared candidate state are separate; concrete coalescing remains optional |

Native source anchors: `consensus/src/lib.rs:155-183` returns a separate oneshot receiver per callback and carries no caller-origin parameter; `multimmit/types/block.rs:180-187,229-235` derives header identity from encoded epoch/chain/height/parent/body commitment. The source-specific remote closure retry and local/recovery failure distinctions are retained; they are not re-litigated in this pass.

The design needs retained facts only for candidates it elects to keep. A budgeted choice to forgo speculation is permitted; it does not justify dropping required canonical intake or lying in a custody verdict. A callback's metadata-only admission cannot be turned into a mandatory wait for a worker slot.

## Dispatch, completion and cancellation traces

| Event ordering | Required result | Assessment |
|---|---|---|
| Two wakeups both observe a pending B and free capacity | Owner claims B/resources/current attempt before launch; second wakeup sees it claimed | Explicitly fixed |
| Launch fails before computation begins | Undo only that still-owned attempt when resources are actually releasable; reevaluate pending eligibility in current context | Root's failed-launch qualification added; no retry/default policy selected |
| Future is dropped after strategy submits CPU work | Keep stale-result/access fences and resource accounting until work can no longer use the resources; do not equate waiter cancellation with task stop | Pass; root launch prose and execution/QMDB retention rules agree |
| Completion is delivered twice for the same generation and attempt | Accept once; the second completion cannot advance F, apply effects or release another job's resource reservation | Pass; exact attempt identity is checked in addition to generation |
| Old attempt completes after retry under the same block and parent | Match current attempt, not merely block/parent; reject the old result without removing the new attempt's state | Pass with current-attempt correlation |
| Candidate C becomes ineligible after a required producer parent fails | Dispatch rechecks required ancestry; running C may not become valid reusable work merely because its body passed validation | Pass; invalid ancestry/candidate dependencies remain fences |
| Worker reads lazily while an import is ready to mutate live DB | Writer transition fences incompatible live access before mutation; rejecting only the eventual worker result is insufficient | Existing contract preserved; no extra read-view service added |
| Root preparation consumes the only draft while another branch still needs the prefix | Retain effects/valid ancestors first, or reconstruct/reexecute from a valid anchor | Existing ownership rule preserved |

Claiming work is local scheduling state, not native finality or a new shared signature field. A dispatch claim which never begins work must not permanently manufacture a started execution prefix. Conversely, uncertain task cancellation cannot be used to pretend started work and held resources vanished. Current source strategies can execute synchronously at creation or leave offloaded work alive after a waiter is dropped; their mere future type supplies neither isolation nor cancellation proof.

## Canonical application and import races

Consider direct preparation for AB and a certified import for ABC, both based initially on A:

1. The direct path validates its input and prepares material asynchronously.
2. The import verifies exact certificate/material and safely advances the shared writer to ABC.
3. The old direct path reaches writer admission. Its earlier parent check is stale. It must recognize exact already-covered input or reject/reconcile the now-inapplicable attempt; it cannot apply the old delta on ABC.
4. If a durable AB completion was already produced but reaches App owner after durable ABC publication, the owner recognizes coverage and does not move its base backward. The retained matching Update can be ACKed from the correct durable identity evidence.

Single-writer DB mutation alone does not resolve steps 3–4 unless the writer/owner also serializes the identity checks and state publication. The explicit recheck/owner annotations now communicate that condition without requiring an extra coordinator actor.

Other outcomes remain unchanged:

- A speculative worker does not own or ACK a delivery token merely because it computed the same block. Canonical intake retains each original Update/Exact token and checks exact ordered coverage.
- Cloning Update also clones Exact; an extra clone adds an acknowledgement obligation. A second queue full of cloned Updates is not needed to notify the scheduler.
- A late direct worker cannot relabel imported state as its own execution evidence. An independently valid exact direct result remains distinguishable from merely imported material under the open worker/signing policy.
- A failed by-value storage mutation or failed durability barrier yields no successful ACK or reusable mutable DB. This is recovery, not ordinary speculative cancellation.
- Floor transitions reconcile old retained Updates with exact imported coverage. A new window is not permission to discard unknown tokens or infer an absent generation field.

Source anchors: `marshal/types.rs:128-136` supplies only canonical index, complete Arc block and Exact token; `marshal/actors/delivery/actor.rs:315-325` retains the waiter; QMDB's existing apply/finalize and live-access contracts still govern actual storage calls.

## Pool retention and pruning races

| Event ordering | Required result | Assessment |
|---|---|---|
| Pool selects bytes; another lane canonically applies the same transaction and cleanup runs | The constructed/staged body remains immutable; pool cleanup cannot mutate its commitment. Canonical replay semantics are separate from pool dedup | Pass in the alignment-owned tx pages; no edit made |
| Proposal is canceled after accepted stage | Marshal's accepted custody work and native retention are not revoked by deleting a pool entry or speculative candidate | Pass |
| App prunes an applied candidate record, then native recovery needs its body | Answer through required retained Marshal custody; App retirement is not native release authority | Pass in current body/recovery/native retention guidance |
| A conflicting branch loses adoption authority while old workers/queries still hold handles | Logical rejection precedes physical reclamation; required ancestors, outputs and serving material remain retained until obligations end | Pass in QMDB and recovery pages |
| Pool maintenance notification is lost or arrives late | Recover durable outcomes and reconcile backend readiness before relying on it; no extra pool ACK gates native or canonical delivery | Pass |

No automatic cancellation, tx eviction, speculative generation change or scheduler pruning step is allowed to revoke a body's separate native retention requirement. Conversely, native custody does not automatically retain all App execution effects and historical result-serving material.

## State and queue necessity review

| Needed fact / ownership | Smallest existing home | Extra machinery rejected |
|---|---|---|
| Exact validated candidate facts and pending eligibility | One App candidate/tree record using native header identity | Duplicate “received blocks” and “verified blocks” delivery services |
| Which work is claimed/running/completed on a path | Existing tree/job record plus runtime handle/resources | Public Executor trait or separate dispatch ledger framework |
| Wakeups when eligibility/capacity changes | Existing App mailbox/event loop or coalesced notification | A second authoritative copy of every candidate |
| Every accepted canonical block and live ACK obligation | Existing App retained Update inbox/current work | Cloned scheduler Update queue or App finality reconstructor |
| Applied identity, outputs and provenance that survive crashes | Existing selected QMDB/journal/metadata integration | Second Marshal cursor engine or public Storage service |
| Pool candidates and readiness | Chosen pool's own kernel/maintenance | A parallel transaction store just to rename selected/unselected |
| Body custody, history, backfill and native retention | Existing Marshal services and APIs | New BlockService or app-native release protocol |

These facts cannot all be replaced by one boolean “verified”: candidate validity, active execution attempt, canonical input, durable state and retained token ownership have different lifetimes. They can be fields in existing concrete state; separate public traits, actors or physical queues are unnecessary.

## Validation and remaining scope

Owned edits are limited to execution interfaces, the state-sync handoff condition, QMDB heading/anchor and PreCut pseudocode. Root made corresponding callback changes. `git diff --check` passed. No protocol implementation, concurrency tests, benchmark, diagram or wire/default selection was added. Actual worker policy, storage recovery linkage and resource scheduling still need implementation and meaningful tests.

## Reviewed fingerprints

Captured 2026-10-09T07:45:09+00:00. Both renamed-heading compatibility anchors were checked.

- `docs/baton/interfaces.md`: `fb47b4b3daf93ee2dfd9ec6c95557691ef5fb674f744e7a4d7acf1340be8ff08`
- `docs/execution/interfaces.md`: `4b21791898e0950f08a431a7f8ccbd5c84dd8e602b8581d955b822329334e18f`
- `docs/execution/README.md`: `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273`
- `docs/execution/qmdb.md`: `1103d67fd16fb6d13c39a24824af24368b45bc444b7f2614e71fbf1c24d8110f`
- `docs/execution/state-sync.md`: `31e7baa3a69922f5f9378fe4565a73284fa724fd36c315d725e9c4daef80ca54`
- `docs/baselines/precut.md`: `1fca0eb4ce69ecec77f966cb0dac0aa0615d0c65ff0af510137830b7d6a0a290`
- `docs/tx/interfaces.md`: `cb438bbf8740d98bf07ac4fe5da00dfd45dd603e831d594137e4bd803089ec32`
- `docs/e2e/canonical.md`: `c33c0ac0df8858f85d2fc8406a70a9c755f473d3c4c7c0b53d3540f410810fcc`
- `docs/e2e/block-body.md`: `88a7179b56d64cb1870d07c303448389af7bc5d8a0f80345579a172683395ee7`
- `docs/e2e/recovery.md`: `f24529f4ce34dab7dd848ca5724926363b10d7033b7ba1cf6f023ad0ea6fe99a`
