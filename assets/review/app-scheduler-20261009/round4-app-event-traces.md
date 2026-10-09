# Round 4: adversarial App event traces

Reviewer: `/root/docs_alignment`. Read-only source/design audit, recorded 2026-10-09 07:29 UTC. These are analytical event orderings, not executed protocol tests or proof of an implemented App. The application scheduler/backend remains proposed integration; current native code is the parent checkout at `6233438985d8249d2b2bc1204191d5d405652288`.

The current one-App design handles all five cases without another public trait, native event, or delivery layer. Three small clarifications would make the existing owner checks harder to omit: admit against current App state after asynchronous work, record permanent dependency invalidity, and consume each current execution attempt at most once. No diagram or API change is needed.

## Reading the traces

`B` identifies the exact producer header/context and its body, not just the body digest. `P` is a producer ancestor. `E` is an exact application execution context: canonical base, ordered prior inputs, runtime/rule and valid storage checkpoint. `J` is one local execution attempt. These are audit notation, not proposed public Rust types.

Each tuple lists events in processing order. App's existing owner retains canonical applied identity, candidate facts, current worker attempts and completed work; Marshal retains custody and ordinary delivery state; the native engine owns validation/signing eligibility. Async completion does not itself authorize changing any owner's state.

## 1. Verify success arrives after the same block is durably applied

**Tuple:** `(verify(B) starts, body/custody wait completes, Update(k,B) is reconciled and durably applied, ACK(k), App admits the queued verify completion for B)`.

This can also occur after a verified import or during a recovery custody recheck. It does not require local speculative verification to gate canonical input. A native cancellation can race the already-running App operation.

Expected owner state:

- App's applied record still covers exact `(k,B)`. The later completion must not reinsert B into speculative pending, append it to local F, dispatch another execution, or retire pool transactions again.
- A still-live verification request can receive `true` after validity and required custody are satisfied. Excluding B from speculation is not a reason to return `false`, skip custody, or assume native retention has ended.
- If the native requester has already canceled, completion delivery may fail harmlessly. A dropped requester does not authorize undoing accepted Marshal storage or deleting material still required elsewhere.

**Current contract:** `docs/baton/interfaces.md:57` requires exact deduplication and discarding already-applied work; `:69` rechecks dispatch eligibility; `:124` removes applied pending entries. `docs/execution/interfaces.md:23–30` excludes applied work and rejects stale completion. `docs/e2e/recovery.md:46` already rechecks current applied identity at live activation. **Pass at the invariant level; admission timing deserves one explicit sentence.**

**Minimal fix:** immediately after async validity/custody completion, admit candidate facts through the App owner against its **current** applied identity and lifecycle, then recheck at dispatch. Do not reuse an admission decision captured before the await. State separately that this speculation check does not bypass an active custody request.

Source support: `chain_plane.rs:504–516` cancels settled/reconfigured native validation; `:537–554` races callback completion against cancellation. `eligibility.rs:376–395` retires settled native jobs. The example App's `or_canceled` in `examples/log-multimmit/src/application/actor.rs:59–85` watches `response.closed()`. `marshal/mailbox.rs:327–350` explicitly lets accepted staging continue after its token is dropped. Native custody retention is audited separately in `round4-retention-source.md`.

## 2. Candidate facts arrive before live scheduling is activated

**Tuple:** `(App phase=recovering, recovery verify(B) establishes exact custody, App retains B metadata and replies true, canonical recovery/import advances the base, native ready succeeds, App activates scheduling)`.

Expected owner state:

- Custody callbacks remain answerable while speculative dispatch is gated; otherwise `Engine::open` can deadlock on an App waiting for native readiness.
- The activation transition scans/re-evaluates retained facts against the recovered applied prefix, current eligibility and exact execution parents. It excludes B if recovery already applied it.
- If B remains usable, it becomes pending without requiring a second successful native callback. Missing parent or worker capacity keeps it deferred. A candidate deliberately forgone under the speculation budget may wait for canonical Update instead.

**Current contract:** `docs/baton/interfaces.md:7–9` requires custody before open, gated dispatch and retained-candidate reevaluation; `docs/e2e/recovery.md:44–46` separates native ready from App readiness and explicitly covers the same transition and capacity wakeup. **Pass; no edit needed.**

Do not add `on_ready` or another public Automaton method. App already owns its startup phase and retained state. A coalesced wakeup is enough; the state is the durable logical source of pending work, not a one-time notification.

## 3. Child verify succeeds while its producer parent later fails

**Tuple:** `(native dispatches verify(P), P is Pending, native dispatches verify(B child of P), B body/custody succeeds and replies true, P's exact payload is found permanently invalid and replies false)`.

Expected owner state:

- B's local body-validity/custody fact may be true while its required producer ancestry is unresolved. It is not yet an eligible execution/report candidate merely because its own callback succeeded.
- App retains the distinction between payload-valid and ancestry-eligible. It does not dispatch B on an arbitrary ready application state, include it in an authenticated intended-order candidate, or treat P as an empty slot.
- Permanent invalidity of required P makes the dependent candidate ineligible; future eligibility and completion checks must observe that fact. App can remove affected speculative metadata under its resource policy. A malformed ancestor is different from an ordinary transaction revert/conflict against a chosen execution state.
- Native need not send a second `verify(B,false)` or a new App invalidation event. App observed its own P validation result, and optional activities are not a lossless invalidation stream.

**Current contract:** `docs/baton/interfaces.md:53–55` separates payload validity from execution outcomes and explicitly warns that native parent validation can still be pending; `docs/baton/direction.md:20–35` requires eligible authenticated ancestry and rechecks before dispatch; `docs/e2e/block-body.md:82` covers the same child/parent distinction. **Pass for safety; the false branch leaves the retained dependency-state update implicit.**

**Minimal fix:** when permanently invalid payload/ancestry is established, record that fact in existing App candidate state and exclude its dependent candidates; do not merely send `false` and leave earlier child eligibility unchanged. This is a private owner-state update, not a public invalidation callback or protocol extension.

Source support: `machine/eligibility.rs:309–323` explicitly allows a parent in `Pending` or `Valid` to enable child dispatch. `:352–366` keeps valid child records but removes the particular invalid record. `:445–524` still requires a contiguous validated/native-chosen prefix for the offered eligible run. Thus a true child callback is not proof that native already accepted the complete ancestor path.

## 4. Local pre-sign candidate is prepared but never published

**Tuple:** `(propose stages B, native invokes local verify(B), App confirms valid durable custody, native stops or the prepared production context is superseded before signing/publication, no TransactionProposed hint or canonical Update for B arrives)`.

Expected owner state:

- Durable body storage does not prove that a signed proposal exists or that B will ever appear in the canonical stream.
- App may retain local candidate facts within its bounded policy. It must satisfy the appropriate authenticated admission condition before including B in a report candidate. Any permitted local speculative work remains dispensable and cannot become canonical without exact native input.
- Selected transactions remain retained; no retirement is triggered by staging, `verify(true)`, or speculative completion.
- No mandatory “proposal abandoned” callback is necessary. State-based lifecycle/eligibility checks and bounded retention prevent indefinite speculative obligations. Optional native hints may improve speculation but cannot gate canonical intake.

**Current contract:** `docs/baton/interfaces.md:17–23` distinguishes accepted staging from durable completion and signing; `:57` explicitly says local pre-sign verification does not prove a signed proposal exists; `docs/e2e/block-body.md:82–84` requires proper authenticated admission and canonical-outcome pool retirement. `docs/baton/interfaces.md:55` bounds speculative retention independently. **Pass; no new event or method needed.**

Source support: `machine/producer.rs:403–421` prepares an unsigned header and requests App custody; `:425–445` marks custody; only `:471–489` exposes and reserves a custodied header for signing. `:613–642` can discard a prepared prefix and request cancellation for outstanding custody. `actors/voter/actor/app.rs:121–157` calls verify before header signing. `marshal/mailbox.rs:327` stages without broadcasting.

## 5. Duplicate verify requests and a canceled execution finishing late

**Tuple:** `(verify1(B), verify2(B), both exact validity/custody checks complete, App admits B once, App starts J1(B,E), canonical reconciliation/import retires J1 and fences its live access, replacement work may start as J2, J1's CPU/I/O completion arrives late)`.

Expected owner state:

- Candidate admission and starting work are deduplicated against current owner state. Two successful verification replies need not produce two speculative candidates/jobs; replying to each live request is independent of admission count.
- A completion is adoptable only for the still-current execution attempt with its exact identity/parent/runtime and valid ancestry. The owner consumes that attempt once. A retired/canceled J1 cannot append to F, publish effects as J2, overwrite the canonical base, or sign a directly executed canonical result merely because its block digest matches.
- Ignoring the result is insufficient if J1 can still access a mutated live database. Existing database-access fencing and reference retention must protect the canonical writer before the transition; cancellation or dropping a future alone is not proof the work stopped.
- Dropping one verification waiter must not cancel shared retained candidate facts or custody still needed by another live requester. Requests and speculative execution attempts have distinct local lifetimes.

**Current contract:** `docs/baton/interfaces.md:51–57` requires repeated-live/recovery deduplication; `:63–70` rejects stale/context-mismatched completions and binds generation/exact inputs. `docs/baton/direction.md:49,96` fences workers/live DB access and names job/context checks. `docs/execution/README.md:35` explicitly warns that dropping a waiter need not stop CPU/I/O. **Pass for the intended design; at-most-once current-attempt consumption is not as explicit as candidate deduplication.**

**Minimal fix:** change the completion instruction to “accept only the still-current execution attempt, once; reject duplicate, retired/canceled, stale-context or invalid-ancestry completions.” Use existing private job state. A process generation alone cannot distinguish two attempts in the same generation.

Source comparison: native `eligibility.rs:331–350` checks generation, removes an issued job ID and verifies the matching `Pending(id)` state before adopting validation. `actors/voter/actor/live.rs:584–601` explicitly handles a local cancellation race before accepting a custody result. These are examples of the needed ownership discipline, not application APIs to expose or copy wholesale.

## Minimal design conclusion

The five cases all resolve inside already-required App ownership: current candidate facts, applied identity, exact worker attempts, canonical writer/access fences and bounded retained material. A public Executor trait, BlockService, callback-origin field, native cancellation event, or second finality stream would not remove those obligations.

Recommend only the three short clarifications above, with the late-verification/custody distinction in the E2E body/recovery explanation. Keep canonical reconciliation independent of optional speculation and preserve existing open backend/policy decisions. No protocol tests, rendering, or repeated documentation build was run for this analytical audit.

## Authorized clarification and readback

After the read-only findings, root authorized minimal E2E edits and applied the core callback changes. Readback confirms:

- Root's `docs/baton/interfaces.md:34–47` now records invalid dependent eligibility and rechecks current applied position/lifecycle on the App owner after custody. `:59` explicitly keeps already-applied exclusion separate from an honest required custody answer.
- Root's `docs/baton/interfaces.md:65–77` now accepts the still-current execution attempt once, rejects canceled/retired/duplicate completions, and states that a matching generation alone is insufficient.
- This reviewer changed `docs/e2e/block-body.md:82–84` to cover permanent required-ancestor invalidity and late completion against current App state while preserving live native custody/retention obligations.
- This reviewer changed `docs/e2e/reschedule.md:51` to cover current-attempt-at-most-once adoption and the separate live-access/reference fence. `docs/e2e/recovery.md` already covers the activation case and needed no change.

All five analytical traces now have explicit owner rules. The proposed App implementation still needs to realize those rules; this review does not supply runnable validation. Only the two named E2E pages and this report were edited by this reviewer in Round 4. Embedded Mermaid and diagram sources were unchanged, so no rerender was needed. Targeted `git diff --check` passed.
