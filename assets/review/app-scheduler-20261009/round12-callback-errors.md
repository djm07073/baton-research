# Round 12: callback cancellation, errors and shared App ownership

Audited source `6233438985d8249d2b2bc1204191d5d405652288` and current baton/interfaces, baton/README, overview/rust-interfaces and reference integration pages, 2026-10-09. No native changes or runtime claims.

## Verdict

Current payload/error/custody and Update/ACK claims are consistent with source. The only recommended reader clarification is how the pseudocode's waits run: cloneable callback handles must reach the same App state, and long body/custody waits must not monopolize that owner's event loop. Root received a two-sentence clarification request; no new runtime abstraction or public API is needed.

## Automaton outcome matrix

| Path/outcome | Actual behavior | Required interpretation |
|---|---|---|
| propose returns digest | Local AppExecutor awaits the returned oneshot, then native producer prepares its exact Context/header and issues local custody verification. `actor/app.rs:83–116`; `machine/producer.rs:362–423`. | The body digest commits the proposer to successful local verification. It is not a full header digest or completed-execution result. |
| propose response closes | Recorded as None; a matching producer build clears pending work and schedules its configured production timer. `machine/producer.rs:380–399`. | Declines this build. Current Multimmit may later build again; the shared trait does not promise that behavior portably. Temporary dependency absence should stay pending when the same request must survive. |
| local verify true | Produces BlockCustodied, with task/generation/header correlation. Only a custodied prepared header becomes eligible for signing. `actor/live.rs:578–613`; `machine/producer.rs:426–480`. | Valid contextual payload with required durable custody. No execution/report wait. |
| local verify false or response closes | Uncanceled verdict other than Some(true) is internally Fatal::Automaton. `actor/live.rs:578–604`. | False and closure are not pressure/retry signals. Running::join does not publicly return this typed native fatal error. |
| local native cancellation | AppExecutor races the verdict against its cancellation channel; even if a verdict wins that race, a recorded CancelRequested takes the cancellation-completion path. `actor/app.rs:143–163,183–201`; `actor/live.rs:585–603`. | An obsolete request must not become a fatal invalidity merely because cancellation closed its receiver. Accepted Marshal storage is a separate lifetime. |
| remote verify true / false | Mapped to Valid / Invalid. Valid retains the native eligibility record; Invalid removes it and returns the invalid artifact result. `chain_plane.rs:522–553`; `machine/eligibility.rs:326–368`. | True still does not prove all ancestors' App checks or an execution parent are complete; false is permanent expected-payload invalidity. |
| remote response closes | None maps to Unavailable; eligibility returns the record to Ready. | Current native exception to the shared single-shot/terminal-close documentation. Do not use it as an App retry API; tolerate repeated calls. |
| remote native cancellation/reconfiguration | Cancellation returns Verified::Cancelled without a verdict; reconfiguration clears cancel senders and outstanding validation futures. Late generation/job results are stale. `chain_plane.rs:502–555`; `eligibility.rs:326–350,372–390`. | Drop obsolete waits when the App reply's receiver closes and fence late App state mutations independently. |
| recovery verify false/close | Recovery accepts only Ok(true); otherwise Engine::open fails RecoveredPayloadUnverified. Work is concurrently bounded and uses cloned Automaton handles. `storage/recovery.rs:466–495`. | Recovery must have live custody handlers before Engine open finishes. A retired speculative candidate is not permission to fail needed custody. |
| callback task failure | Current task failure is fatal; stale task permits/generations are ignored. Generation clearing cancels actor-owned App/crypto jobs. `actor/live.rs:487–495,539–546`. | Service/worker failure is lifecycle failure, not bool payload invalidity. |

The shared contract explicitly reserves false for permanent invalidity and response closure for terminal inability, and allows future contexts with unresolved dependencies (`consensus/src/lib.rs:125–184`). Current docs correctly explain the remote implementation exception without generalizing it to local/recovery paths.

## Marshal requests and lifetime

| Operation | Pressure/closure | Cancellation boundary |
|---|---|---|
| stage_block | Router rejection → Busy; closed endpoint/dropped reply → Closed. Accepted staging returns a Custody token before its durable result. | Router-owned staging and subsequent durability continue if the caller/token disappears. Successful token wait is still required to claim custody. `marshal/mailbox.rs:313–352`; `service/router.rs:301–330`. |
| put_block | stage followed by token.wait. | Dropping the future does not undo already accepted storage. It also does not prove the write completed. |
| subscribe_block | Waits for a shared caller slot and retains live requests under router pressure. Internal acquisition/custody may still fail. A failed backfill branch falls back to the buffered branch. | Same-reference callers share acquisition. Once all leave, the unresolved race is aborted; after a body is found, begun durable settlement continues even if all callers leave. `service/subscriptions.rs:135–218`; `service/router.rs:341–391`. |
| fetch_block / fetch_certificate | Pending registry pressure or eviction → Busy; backfill mailbox stop → Closed. NetworkClosed remains Failed with its cause. | Dropping the future closes its reply; tracked cancellation removes the still-registered waiter and releases resolver demand. It does not roll back admitted storage. `backfill/waiter.rs:271–287`; `backfill/actor.rs:600–608`; `marshal/types.rs:224–232`. |
| get/fetch block success | May expose buffered material before storage sync. | Not a replacement for successful subscription or completed stage/put custody. |
| Failed | Retains the component cause; not synonymous with permanent invalidity or universally retryable pressure. | Failed mutable storage requires recovery of that instance. Do not report true without custody, false for missing data/I/O, or close a live verification merely to retry. |

Public `SubscriptionCapacity` exists as a defensive router bound; normal public subscription slots prevent that bound from being exceeded (`service/subscriptions.rs:135–155`). Error names alone do not authorize inventing a body-invalid verdict. The existing example logs a subscription error and drops the reply; that small demo branch is not a general application recovery policy.

## Reporter and clone semantics

- Native Activity is synchronous and best-effort; Engine ignores Reporter feedback. Supplied Marshal ingress protects/coalesces releases and L-QC progress while optional hints may drop. Round9 contains that source matrix.
- Update report is also synchronous. Delivery treats Closed as ReporterClosed; Ok and Backoff both proceed with its Exact waiter. Backoff does not retry a dropped Update (`marshal/actors/delivery/actor.rs:303–326`). Retain the complete accepted value and return promptly.
- Update derives Clone, and cloning its Exact adds an independent acknowledgement obligation. Every clone must acknowledge; dropping any unacknowledged clone cancels the waiter (`marshal/types.rs:130`; `utils/src/acknowledgement.rs:38–106`). Fan-out is not free: an optional observer must not accidentally own an unacknowledged cloned Update. Current docs already state this requirement.
- Custody::wait consumes a non-cloneable completion token; it returns Result<(), Error>. Marshal Mailbox clones share the same actor endpoints, subscription-slot Arc and staged-cache Arc (`marshal/mailbox.rs:259–280`). Cloning the mailbox does not create another independent subscription capacity budget.
- Automaton is Clone + Send + 'static. Native code clones it for local build/custody, remote verification and recovery. A clone must therefore be an ingress handle into the same App candidate/pool/state owner, not a deep copy of an independent pool or scheduler. The example mailbox Clone shares its sender and clock (`examples/log-multimmit/src/application/mailbox.rs:112–125`).

## Pseudocode concurrency review

Current interfaces correctly describe oneshot receivers at the trait boundary, retain temporary requests, recheck current state on App ownership before candidate mutation, and separate synchronous Update report from canonical work. There is no required new driver or thread per callback.

The example makes the intended execution model concrete: mailbox propose/verify enqueue and return ready(receiver), while its App actor polls pending job completions alongside mailbox intake (`application/mailbox.rs:147–175`; `application/actor.rs:190–214,292–305`). Body/custody awaits are pending jobs; short state changes happen on the actor. The root recommendation is to make this interpretation explicit before the private pseudocode so a reader does not implement `await body` while blocking the sole owner from processing the message that would make that body usable. Same-owner completion checks also prevent clones or stale jobs from recreating applied candidates.

Root applied the clarification at the start of baton/interfaces.md: cloned handles share App state, propose/verify return receivers promptly, bounded asynchronous waits leave owner intake available, and completed jobs re-enter that owner before shared-state updates. Re-read the final wording; it matches the example handoff without adding a public actor/framework. Focused diff and report whitespace checks passed.

No existing error statement needed correction in consensus/reference pages. No tests were added or run; this is source verification of the documentation's proposed App behavior.

Round17 precision note: the table's "generation clearing cancels actor-owned jobs" describes clearing native completion ownership and custody cancellation, not joining every underlying submitted worker. Pool::cancel_all drops its futures; AppExecutor's spawned ordinary Handle awaits and explicit custody cancellation have different physical lifetimes. Full subtree shutdown relies on runtime supervision and Running::join. Current reader docs already avoid equating cancellation with safe worker termination or durability.
