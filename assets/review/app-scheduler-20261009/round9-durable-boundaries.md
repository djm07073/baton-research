# Round 9: durable completion and failure ownership

Reviewer: `/root/simplification`. Source/contract audit at native `6233438985d8249d2b2bc1204191d5d405652288`. Concentrated on what method completion proves, crash recovery and owner lifetime. No protocol tests, fault injection, runtime trace or crash-consistency proof was run.

## Findings and edits

1. Current `apply` creates an independently recoverable checkpoint but does not establish durability. Data whose durability was not observed may nevertheless survive restart. QMDB documentation already distinguishes apply and barrier completion, but did not explicitly explain the consequence for choosing a recovery checkpoint. Added a short paragraph using existing `ManagedDb::init(expected)` / `DatabaseSet::init(..., Some(targets))`: choose matching App database targets, outputs and provenance, rather than blindly selecting each DB's latest state or Marshal's cursor. Multi-store selection/linkage remains App implementation work.
2. The QMDB recipe's barrier row now explicitly says to require `true` from `Barrier::durable().await`, plus the App's recovery linkage, before ACK. This clarifies the existing failure rule; it adds no new barrier or service.

No root callback/core correction is required. Existing root code correctly keeps native agreement independent of delivery ACK and requires exact local durable application before acknowledging an Update.

## Method completion matrix

| Current method / event | What success establishes | What it does not establish | Source |
|---|---|---|---|
| Concrete draft `merkleize(self)` | Sealed batch and computed storage commitment | Canonical application, disk durability, App result certificate | `glue/src/stateful/db/mod.rs:296-324` |
| `ManagedDb::apply(self, batch) -> Ok(db)` | Returned DB exposes an independently recoverable applied checkpoint | Durability or coherent external outputs/applied metadata | `db/mod.rs:383-390`; Any `apply` at `db/any.rs:538-545` |
| `DatabaseSet::apply(...).await` | Every member's apply finished successfully | Crash-atomic transaction across members or external stores | `db/mod.rs:559-563,1041-1051,1835-1858` |
| `ManagedDb::finalize(self) -> Ok((db, handle))` | Persistence has been started for checkpoints applied before this call | Completion of the returned handle; coverage of later applies | `db/mod.rs:392-397`; Current wrapper `db/current.rs:543-550` |
| `DatabaseSet::finalize().await -> Barrier` | All per-DB finalize calls returned their completion handles | Successful durability merely from obtaining the barrier | `db/mod.rs:1054-1065` |
| `Barrier::durable().await == true` | Every covered DB sync handle completed successfully | App outputs/provenance/identity stored elsewhere; Marshal cursor persistence; result certification | `db/mod.rs:415-485` |
| Barrier returns `false` | Runtime Closed/Aborted prevented a successful durability observation | Zero disk writes, rollback, or permission to ACK | `db/mod.rs:456-479` |
| Other deferred sync error | Fatal panic boundary after DB advancement | Recoverable ordinary job failure on the same live instance | `db/mod.rs:480-483` |
| `DatabaseSet::prune(...).await` | Required pruning effects are durable | Permission to prune an undurable target or referenced App history | `db/mod.rs:572-576`; caller still checks reference/serving retention |
| `committed_targets().await` / readable query | Current applied checkpoint/values | Confirmed durability or exact App multi-store checkpoint | `db/mod.rs:578-579,1079-1082` |
| `Metadata::put` | Pending in-memory metadata update | Persistence | Metadata public API and `put_sync`/`sync` distinction |
| `Metadata::sync` / completed `start_sync` handle | Atomic persistence of that Metadata store's pending state | Atomic commit of QMDB plus another output journal | `storage/src/metadata/storage.rs:649-655,692-707` |
| QMDB sync reached-target notification | Sync has reached a target as progress | Rebuilt/root-checked/persisted returned DB | `storage/src/qmdb/sync/engine.rs:694-731` |
| QMDB sync returns the DB | Journal sync, reconstruction, target-root check and DB-specific persistence finished | Execution certificate authentication or App canonical handoff/linkage | `sync/engine.rs:745-769` |
| App signals Update Exact token | App claims its required local durable application is complete | An independent DB flush or native vote; correctness if the App violated its obligation | `marshal/types.rs:128-136`, delivery actor `315-325` |
| Marshal cursor sync completes | Marshal's acknowledged output prefix is recoverably recorded | App DB/output correctness or result certification | Delivery actor `330-355,361+` |

The term “recoverable checkpoint” is deliberately weaker than “durably observed App commit.” `ManagedDb` states that non-durable state may or may not survive restart (`db/mod.rs:329-336`). Current concrete wrappers use `apply_batch` for apply and `start_sync` for finalize. Current `apply_batch` itself documents that publishing in-memory state/appending the journal precedes required durability (`storage/src/qmdb/current/db.rs:674-697`).

## Ownership and failure traces

| Analytical interruption point | Required outcome | Current docs |
|---|---|---|
| Awaiting a read or before acquiring the by-value write slot | No completed mutation may be assumed; canceling this wait does not establish any durable state | Correct |
| After Shared removes DB and before WriteSlot puts it back | Cancellation/error loses this live instance; reopen through recovery, not ordinary retry | Correct |
| One member of a tuple applies; another fails | The set may be partially advanced; DatabaseSet panics. Do not continue using the set as a coherent canonical App state | Correct under existing fatal-instance/recovery rule |
| `finalize` starts some DB syncs, then another member fails | Earlier I/O may continue; no successful barrier/App completion; recover authoritative linked state | Correct |
| Barrier waiter is dropped or a completion handle aborted | Observing failure/cancellation does not cancel all underlying I/O or prove it did not reach disk | Correct |
| Apply B runs while a barrier covering A remains pending | A's barrier does not cover B; await the prior barrier before another finalize; mutation method bodies do not overlap | Correct |
| Metadata start_sync handle is dropped | Sync continues and stored failure is re-surfaced on a later sync before another write | Consistent with existing per-store rule; docs do not claim dropping handles discards I/O |
| App state DB is durable but outputs/applied identity are not | No ACK/readiness claiming the full App contract; recover/finish the selected linkage | Correct; concrete cross-store protocol remains open |
| App state and exact applied record are durable; crash occurs before ACK or Marshal cursor persistence | Marshal may redeliver; verify exact index/block/linked state and ACK without duplicate effects | Correct |
| Direct preparation is superseded by import before writer admission | Recheck current predecessor/authority; select already-covered or still-applicable work, not the stale delta | Correct after round 7 |
| Import storage mutation fails after old direct work was fenced | No ACK and no reuse of the failed mutable DB; recover before continuing | Correct |

`Shared::write` empties the cell until `WriteSlot::put`, and later readers panic if the instance was lost (`db/mod.rs:120-176,238-245`). Tuple apply/finalize uses each member's own lock lifecycle. Helper apply explicitly treats failure as fatal because other members may already have advanced (`1041-1051,1835-1845`). These are supplied failure semantics, not an App rollback protocol.

Task ownership differs from completion ownership: `runtime/src/utils/handle.rs:27-31` says a completion handle stops waiting when aborted but does not cancel underlying work. Metadata separately records pending completion and refuses a subsequent write after deferred failure (`metadata/storage.rs:344-367,698-707`). These mechanisms do not eliminate App-level checkpoint selection after interrupted cross-store work.

## Recovery selection and safe redelivery

Two distinct sources of restart lag must remain separate:

- App may be ahead of Marshal's durable ACK cursor. This is ordinary exact redelivery after an honest ACK or before the ACK was sent; App must not repeat effects.
- One QMDB member may expose later applied state than the App's last recoverable multi-store record, including state whose covering barrier was never observed. Opening every member at its independent latest state does not establish a coherent App input/output/provenance boundary.

The current existing API helps with the second case: `ManagedDb::init(expected)` opens the selected target and durably discards later state before returning; target mismatch is an error (`db/mod.rs:358-366`). `DatabaseSet::init` delegates selected per-DB targets and treats failure/mismatch as fatal (`527-536`). App still has to choose the matching targets and linked output/provenance record, preserve required retention, and determine what recovery may safely complete or discard. This audit adopts no record layout, write ordering, WAL, transaction service or new recovery actor.

Marshal's pending ACK queue releases only its contiguous acknowledged prefix (`actors/delivery/acks.rs:107-124`). Cursor I/O starts separately and may lag (`actors/delivery/actor.rs:330-355`). A token clone adds an obligation; a canceled token does not mean successful completion. The existing non-dropping intake and exact identity checks remain necessary. Imported exact durable coverage may satisfy retained Updates, but neither a certificate alone nor a floor jump is an App durability result.

## Lock and access guard check

The restored warning is correct for the current source. `Shared::read` is write-preferring and explicitly warns about retaining a guard across an await that reacquires the same cell (`db/mod.rs:148-152`). `AnyUnmerkleized::get/get_many` acquire their own shared DB read guard (`db/any.rs:107-118`). An outer Shared read guard must therefore not be used as the App's broad access fence around those calls.

Multi-DB access also has an existing discipline: a mutation must not hold one member's writer while waiting on another, because readers can span members (`db/mod.rs:488-496`); tuple helpers complete member lock lifecycles independently (`1045-1051`). Current docs reuse those helpers and prohibit overlapping mutation method bodies. They do not prescribe a conflicting outer multi-DB lock scheme. No new lock service was added.

## Execution-doc source link audit

All **23 unique current GitHub source links** in `docs/execution/*.md` were checked against local source:

- Referenced revision is the intended native pin.
- File exists and the line anchor is inside that file.
- Local source bytes match the corresponding pinned Git blob.
- Relevant method/docs were read for the claim rather than treating existence as semantic proof.

The exact URL/reference/file-hash inventory is [`round9-source-links.json`](round9-source-links.json). It includes QMDB/apply/finalize/recovery/locks, certificate/P2P/collector recipes, sync target/witness/completion/ownership and Marshal floor/reset contracts. Anchors near an impl header still lead to the cited methods in that local section; no broken or materially mismatched source link was found. This is a local pinned-source audit, not a live HTTP availability check.

## Outcome

One recovery-selection clarification and an explicit true-barrier condition were added to the owned QMDB page. All other reviewed completion/failure statements are consistent with current source. Mechanisms supplied by QMDB/Marshal remain distinct from App's unimplemented cross-store recovery contract; direct and imported paths share that same requirement. `git diff --check` passed. No runtime correctness claim is made.

## Reviewed document fingerprints

Captured 2026-10-09T08:00:49+00:00.

- `docs/execution/README.md`: `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273`
- `docs/execution/interfaces.md`: `eb1c38b1a34f484d537ad0c46b534448cfc1bceedf9db3359e77bfb53d1b2128`
- `docs/execution/qmdb.md`: `4a0caa78c8dbfa2e1d7e171d2ef9f83f791c312cafadf41e33938300c93c8731`
- `docs/execution/state-sync.md`: `3b1eea59bff1dabf02aae08babf2e5661567a09423dca5ef090763b7d61f7466`
- `docs/baselines/precut.md`: `672cb053c048d7c99c567084c450c2d38e7c498af561a218f60e0d3e2360e74f`
- `docs/baton/interfaces.md`: `583dd99555e3feeaaa8d05e98b4c64c5e1bc939f39ba93f2848019c75eb25623`
- `docs/e2e/canonical.md`: `c33c0ac0df8858f85d2fc8406a70a9c755f473d3c4c7c0b53d3540f410810fcc`
