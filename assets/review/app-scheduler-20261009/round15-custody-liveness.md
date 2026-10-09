# Round 15: custody liveness, capacity and lifecycle boundaries

Audited source `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. This adds capacity/release/readiness findings to round12-callback-errors rather than repeating its verdict matrix. No native edits or tests.

## Result

Current docs correctly separate required payload custody from optional execution, preserve live requests during transient absence, and start App/Marshal handling before Engine open. No reader correction was necessary. The configured native bounds do not themselves bound all App-owned workers or guarantee App scheduling fairness. Existing bounded-job, cancellation and scheduling-independence requirements are essential rather than optional optimizations.

## Exact native capacity map

Let `p = pipeline_depth`, `c = producer-chain count`, and `w = min(p, max_verification_batch)` under the validated native profile.

| Path | Source bound and dispatch behavior | App consequence |
|---|---|---|
| Local propose | TaskReservations permits one LocalBuild independently of validation/crypto classes; producer.pending_build also prevents a second concurrent build. `actors/voter/tasks.rs:160–163`; `actor/dispatch.rs:260–268`; `machine/producer.rs:649–695`. | Slow remote validation does not consume the native build permit. A shared App queue/worker can still accidentally block that build. |
| Local custody verify | LocalCustody has at most p permits, separate from the single build and crypto pools. Prepared builds move through AwaitingCustody/Custodied/Reserved; pipeline and production credit additionally constrain admission. `tasks.rs:78–94,163–168`; `producer.rs:158–173,649–695`. | Several local prepared bodies may wait concurrently. Returning a body commitment creates a custody obligation; speculative capacity is not a reason to refuse its matching validity/custody check. |
| Live chain-plane verify | Each validator's producer-chain plane gets w validation items and `w × max_artifact_bytes` validation bytes. Observers have no planes. `config.rs:82–96`; `actor/chains.rs:117–126,153–172`. | Live per-chain accounting is separate from local custody and from App execution budgets. Do not use recovery's global capacity formula as a universal App-wide live bound. |
| Remote dispatch eligibility | Counts the signed header's encode_size; ascending-height candidates require their exact parent at the certified anchor or Pending/Valid locally. Parent Pending is allowed. `machine/eligibility.rs:266–324`. | Native validation bytes are header bytes, not full body or VM memory. Independent Marshal/body and App worker budgets remain necessary. Dispatch does not mean all ancestor App checks finished. |
| Engine-open recovery | Uses `min(c × w, max_cached_artifacts)` via engine inflight_application, then buffer_unordered at that bound. `engine/mod.rs:68–71,484`; `storage/recovery.rs:466–497`. | Multiple recovery requests must progress before any Running handle/readiness exists. A full speculation queue cannot be a prerequisite for answering them. |

Local custody jobs race the whole `automaton.verify(...).await` plus returned receiver against cancellation (`actor/app.rs:143–159`). Remote jobs do the same (`chain_plane.rs:535–556`). Prompt receiver return and asynchronous pending jobs therefore preserve the intended callback boundary; a long owner-blocking body wait is not required by the trait.

## Cancellation and bounds do not imply App work is gone

Remote anchor advance removes settled validations and returns their capacity immediately (`eligibility.rs:372–397`). Chain-plane handling removes cancel senders, then dispatches newly eligible jobs in the same event-loop branch (`chain_plane.rs:472–481,504–508`). An old response/callback cancellation can still be propagating while new work becomes eligible. The item limit bounds currently charged native validations, not detached App work that ignores response closure.

Local production has a stronger replacement fence: advance_produced records canceled AwaitingCustody requests, and drive refuses replacement production while cancelling_custody remains nonempty (`producer.rs:614–647,661–666`). Native cancellation completion returns that ownership. It still cannot prove arbitrary App-submitted CPU/storage work physically stopped. The example's or_canceled races response.closed() against a Marshal wait (`examples/log-multimmit/src/application/actor.rs:60–95`); accepted staging and begun durable subscription settlement have separate lifetimes.

A native generation change clears actor-owned App/crypto tasks, timers and task correlations, then reconfigures chain planes (`actor/live.rs:473–495`). The plane clears old validation futures on reconfiguration (`chain_plane.rs:513–519`), and stale native completions cannot release new capacity (`tasks.rs:217–245`). That private native generation is not carried in Automaton Context or Update. App attempt identity/lifecycle fencing and Marshal floor_generation remain distinct; an App checkpoint import is not an Engine generation transition.

## Marshal capacity is independently configured

Marshal derives router/subscription bounds from its own Config: router jobs and subscription callers use resolver_mailbox_size; effective backfill concurrency is additionally capped by the backfill-byte budget (`marshal/config.rs:550–594`). Engine profile validation does not check these values against its callback widths or App execution workload.

subscribe_block acquires a shared slot before routing; clones share the slot pool. A slot stays with a queued/registered caller until the router observes it answered or gone (`marshal/mailbox.rs:198–242,431–445`; `service/subscriptions.rs:132–170`). Same-reference callers share acquisition but each still consumes a caller slot. Futures waiting outside acquire are owned by their callers, so the Marshal slot bound is not permission for App to launch unlimited optional subscription tasks.

Consequently, optional jobs holding all available subscription/worker/memory capacity while required custody waits are not made safe merely by each internal queue having a finite limit. The App must let required custody and canonical work obtain needed resources under sustained optional load, within existing APIs and its chosen bounded policy. This is an integration obligation, not a demonstrated native bug or a proposal for another service. Current interfaces.md explicitly states the obligation.

There is also no automatic timeout-to-validity escape: a missing body may keep verify pending. Subscribe itself does not initiate peer fetch; the existing explicit fetch or independently accepted DA evidence provides active acquisition when needed. Response closure is not a portable retry mechanism, and Busy/Closed/Failed must retain their service meanings, as covered in round12.

## Release and recovery preserve a different boundary

Recovered payload requirements are the deduplicated union of retained local producer headers and local DA-vote header choices (`machine/chain.rs:287–318`), not every candidate App ever executed or every canonical block. They are reverified before recover returns, and a fresh machine has no such requirements (`storage/recovery.rs:225–235`). First failure ends the recovery future and drops its remaining in-flight waits; App reply cancellation/accepted-work lifetime rules still apply.

Remote validation cancellation at a newer certified anchor does not imply all those bodies are immediately prunable. CertificateRecorded.released trails the durable certificate by pipeline depth because recovery can still depend on older DA choices. Marshal caps ordinary, promoted and floor-install pruning at the lowest still-verifiable height; without a release it conservatively keeps every block (`marshal/storage/catalog/prune.rs:27–78,89–119`; `catalog/install.rs:190–223`). Release state starts unknown after reopen (`catalog/mod.rs:420`), while Engine recovery finishes its required checks before startup re-reports releases.

Thus zero live App verification jobs, an applied canonical block or a retired speculative candidate is not a substitute for Marshal's native custody-retention boundary. Conversely, App worker/query/result retention may need data beyond native release. Existing docs correctly keep those App obligations separate.

## Readiness checked against the actual signal

Starting::run drives the startup/recovery durability work to completion, seeds the resolver and submits an initial ProducerWake (`actor/startup.rs:198–232`). The voter then sends ready before entering its live loop (`actor/mod.rs:399–420`). The signal does not wait for that newly requested producer to finish a body, for all future live verifications, for Marshal to catch up, or for App execution/state durability.

Current consensus README, integration.md, baton/interfaces.md and e2e/recovery.md describe readiness as a startup milestone and require App's recovered base separately. They do not incorrectly gate required custody behind Running::ready. In particular, scheduling activation re-evaluates retained candidate facts because another successful verify is not promised. No material false readiness claim was found.

Only this report was added. Root received the independent capacity, header-byte accounting and cancellation-overlap findings; current reader requirements already cover them without further expansion.

Round17 precision note: "clears actor-owned App/crypto tasks" means clearing completion futures/correlations and signaling custody cancellation, not proof every submitted computation has physically stopped. Pool::cancel_all alone is not a join. Ordinary Handle drop and AbortOnDrop differ; full native subtree shutdown follows runtime supervision. The normal native generation advance is a startup/recovery transition, not an App floor-import control. This preserves the report's central distinction between native accounting and App work ownership.
