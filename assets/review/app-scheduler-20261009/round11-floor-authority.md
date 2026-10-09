# Round 11: floor authority, generation and recovery

Source pin `6233438985d8249d2b2bc1204191d5d405652288`, inspected 2026-10-09. This is an independent source audit of the corrected reader wording. No native edits or runtime test claims.

## Verdict on the correction

The current execution/state-sync and consensus/ordered-input paragraphs are correct. `Start::Floor { floor_generation, floor }` has an existing caller-supplied generation; `Floor` and `Update` do not. Removing that startup field based on Floor's narrower shape was incorrect. The current corrected text restores the source contract without inventing a new public generation field.

There are three distinct local values to keep separate:

| Value | Ownership and source |
|---|---|
| Start::Floor.floor_generation | Positive monotone value authenticated/bound by the state-sync owner for a fresh namespace; `marshal/config.rs:163–186`. It is not signed as part of the Floor's L-QC. |
| Installed Marshal floor/delivery generation | Persisted native checkpoint/cursor generation. Live install derives current+1 locally (`actors/synchronizer/floor.rs:49–62`), and internal cursor/checkpoint transitions enforce generation consistency. |
| App worker/transition generation | App-owned fencing concept for its jobs/import/intake lifecycle. It is not an upstream Update field and does not replace the Marshal generation. |

`Floor` contains anchor L-QC, history opening and emitted frontier (`marshal/types.rs:329–334`). `Update` contains index, complete block and Exact acknowledgement (`:130–138`). Neither carries floor_generation. A peer's Floor therefore does not select the receiving running service's generation.

## Fresh namespace and recovered namespace

`Config::validate`/actor bounds call validate_start. For Start::Floor, it rejects zero generation, validates the anchor's native structure, constructs canonical frontiers and requires emitted to dominate ordered (`config.rs:597–621`). It has no verifier and does not cryptographically authenticate the anchor. In particular, positivity is checked locally; monotonicity relative to a previous imported App snapshot in some other/fresh namespace cannot be discovered from that empty namespace. The caller owns that authentication and binding, as the Start documentation states.

CatalogStore::open reads the durable record and selects it when present; only an absent record creates a start checkpoint and triggers seed (`storage/catalog/mod.rs:359–375,423–427`). Recovered checkpoint precedence does not mean arbitrary invalid configuration is ignored: configuration validation, epoch codec context and archive-layout compatibility still apply. It means changing Start is not a runtime floor-update mechanism and cannot overwrite the recovered checkpoint.

Fresh floor startup creates a hidden predecessor checkpoint using floor_generation−1, the anchor's parent certificate, the history's parent commitment and ordered tips (`storage/catalog/mod.rs:448–467`). Seed checks exact anchor-to-history commitment and constructs the target using the caller's positive generation and emitted frontier, then runs the existing durable installation protocol (`:472–514`). It does not invoke LqcVerifier or independently authenticate the imported application state. Service::start receiving a verifier later cannot retroactively authenticate that choice.

The source-recommended route for an untrusted peer-served floor is Start::Genesis then live install_floor, with App import coordination. It is not permission to allow delivery to run beyond an application state that has not been durably installed. No second App native-order interpreter is required.

## Live install_floor checks and completion

1. Public Mailbox::install_floor routes the Floor to synchronizer through the existing router (`marshal/mailbox.rs:458–469`; `service/router.rs:411–429`). The caller supplies no generation argument.
2. Synchronizer derives checked current+1; overflow fails GenerationExhausted. It rejects an epoch mismatch or an anchor view not strictly newer than the selected floor (`actors/synchronizer/floor.rs:57–84`).
3. Native floor validation checks anchor/history commitment, no regression of ordered/emitted frontiers and that emitted is the native final-sweep endpoint. It then verifies the L-QC using the configured verifier and resolves/checks ancestry between emitted and final targets (`protocol/floor.rs:42–102`; `actors/synchronizer/floor.rs:85–112`). This establishes native floor authority, not a VM state root or result certificate.
4. Started native commits finish before installing the checkpoint (`actors/synchronizer/floor.rs:145–157`). The store writes a durable install intent, archives the L-QC/floor/history, applies pending floors and publishes the new checkpoint (`storage/catalog/install.rs:49–164`). Internal checkpoint replacement requires a greater generation and compatible monotone frontier (`storage/catalog_state.rs:699–730`). The live caller uses exactly +1 even though this lower-level guard permits any strictly greater generation.
5. Catalog tells delivery to reset to installed generation and committed index. Catalog mailbox install waits for the reset token (`actors/catalog/actor.rs:741–777`; `actors/catalog/mailbox.rs:905–916`). Delivery clears old native waiters/cache, durably resets its cursor, updates the catalog mirror and checks the resulting generation/index before releasing reset waiters (`actors/delivery/actor.rs:423–455`). Router then retires obsolete backfill certificate markers before replying.

Successful installation is therefore a native durable floor/delivery boundary. It does not mean App database import, worker cancellation or old App-held Update reconciliation happened automatically. A failed/canceled caller also must not assume accepted native storage work rolled back; the existing router owns that work.

## Recovery and ACK boundaries

The installation protocol records its artifacts in the durable intent. Recovery decodes/checks their identities and finishes the archived installation before ordinary reads (`storage/catalog/install.rs:71–81,165–189`). This recovery trusts the previously authorized durable intent; it does not newly verify its signatures or App snapshot against a new caller.

Open chooses a pending installation's target as the delivery recovery cut. Missing cursor metadata may be initialized only for that install or when the committed index equals the floor index; otherwise open rejects it (`marshal/open.rs:167–204`). Cursor open rejects a cursor generation ahead of catalog or a same-generation ACK beyond committed. When catalog generation is newer, it durably resets the cursor to that authorized cut (`actors/delivery/cursor.rs:40–76`). This is why imported App state must already be bound to the floor: native recovery is allowed to skip the installed prefix's ordinary delivery.

Normal acknowledgement requires the current generation and a strictly advancing index; reset requires a newer generation (`actors/delivery/cursor.rs:94–131`). Catalog ignores old-generation cursor notices, rejects newer-than-catalog or past-commit notices, and advances only monotonically (`actors/catalog/cursor.rs:25–48`). These internal checks do not add a generation tag to Update or an application import transaction.

During ordinary delivery, max_pending_acks bounds reported outputs still waiting for App ACK. The queue completes an oldest contiguous ready prefix and separately coalesces cursor synchronization (`actors/delivery/acks.rs:45–114`). ACK permits another delivery before its cursor sync is durable; this is consistent with App durability preceding ACK and idempotent replay after a crash. The current docs do not confuse an in-memory acknowledgement with completed cursor I/O.

A floor reset clears native pending waiters/cache, including ready/syncing tracking, and supersedes old cold reads (`actors/delivery/actor.rs:210–221,423–455`). It cannot clear values or acknowledgement clones already retained by App. Another generation can create a new window while old App work remains, so max_pending_acks is not a global bound across repeated resets. Update's absent generation field means the existing App owner must coordinate intake, exact old identities, workers and durable state during handoff. Current docs correctly leave exact cross-store sequencing unresolved rather than assuming an atomic import supplied by Marshal.

## Callback/custody dependency

Marshal floor installation does not invoke Automaton, reset Engine's consensus state or release Engine's payload needs: the service is parameterized by a body type, native verifier and Update reporter, not Automaton (`marshal/service/mod.rs:214–225`). Its installation pruning still clamps body removal to what Engine has released and preserves required custody (`storage/catalog/install.rs:188–231`). Thus an App import/applied position is not permission to answer a still-live verify without durable custody or to mark that payload invalid. Existing block-body lifecycle/retention text already states this boundary; no new callback is necessary.

## Counterexamples excluded by current wording

- Treating Floor's L-QC signature as a signature over a newly added generation or application state root.
- Supplying Start::Floor on reopen to overwrite an existing durable namespace.
- Passing a zero startup generation or expecting an empty namespace to prove monotonicity against unrelated prior imports.
- Reading a peer Floor and assuming it dictates the receiver's live floor generation.
- Treating successful install_floor as proof that App state was imported, or ACKing unapplied ordinary Updates merely because a native floor was observed.
- Dropping/fencing only native waiters while allowing stale App workers to mutate the new imported database.
- Assuming repeated floor resets leave at most one old-plus-new App queue of max_pending_acks items.

## Documentation disposition

Re-read root's corrected state-sync and ordered-input text. Both assign startup generation binding to the caller, distinguish Floor/Update shape and retain the App coordination gap. Reference/integration's shorter statement is consistent and links the detailed source boundary. No further reader edit is necessary; additional paragraphs would repeat established constraints.

Existing source tests include missing cursor initialization cuts, catalog-generation recovery, monotone cursor mutations, incompatible/stale floor handling, frontier rewind rejection and floor preemption of peer waits. Their source presence is evidence of intended native behavior, not an executed App/native integration proof in this round.
