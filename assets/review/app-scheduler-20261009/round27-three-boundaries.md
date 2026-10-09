# Round 27: final focused callback, ACK and startup review

2026-10-09 09:35 UTC, native `6233438985d8249d2b2bc1204191d5d405652288`. Read-only review of the latest core callback/role/assembly text, followed by fresh tracing of the three requested native boundaries. Current reader snapshots are in [round27-three-boundaries-hashes.json](round27-three-boundaries-hashes.json). No reader edit, native implementation, compilation or runtime test was performed. No material contradiction was found.

## 1. Verify origin and paired response

The native call returns a future of a receiver, then awaits that receiver. The App retains the paired Sender; it does not send via the Receiver. Example mailbox.rs:148–175 creates the pair, enqueues the Sender and returns `ready(receiver)`. Example actor.rs:60–68 races a pending body operation against `response.closed()`, showing the existing cancellation signal. Commonware's channel module reexports oneshot; no new callback-channel abstraction is needed (`utils/src/channel/mod.rs:8`). The current core wording now matches this exact handoff.

The same Context/body-digest pair does not identify the request's origin. Local app.rs:125–158 performs custody verification for a prepared unsigned header; live.rs:578–606 ignores a canceled result and requires Some(true) for an uncanceled one. Remote chain_plane.rs:522–555 issues validation for an authenticated header, maps sender closure to Unavailable, and eligibility.rs:352–355 permits rescheduling. Generation/anchor changes cancel pending remote requests (chain_plane.rs:493–518). Recovery.rs:473–497 clones the App handle, verifies retained obligations with bounded concurrency, and requires Ok(true) before open returns.

Role/lane qualification is also correct. Scheme key material determines native Validator/Observer (`engine/mod.rs:611–622`); every validator gets per-chain planes while Observer gets none (`actor/chains.rs:114–130`). Protocol::producer_chain maps a participant to an optional lane; numeric participant index is not inherently its lane (`config/protocol.rs:202`). A native own-header shortcut requires exact retained header equality, not merely the same chain (`machine/producer.rs:606–610`, `chain.rs:230–239`, `eligibility.rs:224–242`). A parent can still be Pending when a child becomes dispatchable (`eligibility.rs:309–325`).

Therefore the documented App lifecycle, exact identity, applied-state and ancestry checks remain necessary. They filter optional speculation; they must not falsify a still-required native custody verdict. The minimal App can retain metadata and answer true without awaiting speculative execution. The synthetic example's enqueue/failure policy is a wiring illustration, not proof of the proposed App's bounded intake, retry/fatal handling or transaction validity.

## 2. Update Feedback, ACK and durable cursor

Delivery creates Exact, calls App report synchronously, fails immediately on Feedback::Closed, and otherwise inserts the waiter (`delivery/actor.rs:303–327`). Backoff supplies no redelivery loop. An App that loses the token while returning Ok/Backoff eventually cancels the waiter. Every clone must acknowledge; clone/drop behavior is explicit in `utils/src/acknowledgement.rs:37–106`. The current non-dropping retained handoff is an App obligation, not something Feedback automatically provides.

The precise ordinary progression is:

1. App durably applies the exact input and completes its retained token.
2. Delivery observes the oldest completed waiter, coalesces any immediately following ACKs and frees those pending slots (`acks.rs:105–145`).
3. Delivery starts cursor storage for that ready prefix. Its private DeliveryCursor value moves at sync start (`cursor.rs:95–114`).
4. On sync completion, delivery advances its durable progress and notifies the catalog mirror (`actor.rs:372–393`); public progress/pruning uses that durable mirror (`catalog/cursor.rs:1–35`).

A useful source limitation is explicit in `delivery/actor.rs:184–209`: while a cold body read is active, ACK-event polling waits. Token completion therefore need not instantly free the window or appear in public progress. This does not contradict current docs, which describe separate milestones and contiguous processing without promising immediate ACK observation. It also does not turn cursor I/O into a native voting prerequisite. Engine receives native Activity rather than Update/Exact and ignores Reporter feedback (`engine/mod.rs:430–433`, `actor/live.rs:412`); application ACK handling resides in Marshal delivery.

The current text correctly preserves apply-before-ACK recovery, ACK-before-cursor-sync redelivery, full-window capacity and old App-held Update overlap across floor reset. Absence of a direct ACK dependency is not unconditional node liveness under exhausted shared resources or failed body services. Those App progress and failure conditions remain Not run acceptance work.

## 3. Minimum Engine/Marshal startup

The revised recipe is a valid minimal source connection: create App ingress/recover App state; start network/buffered transport; call public marshal::open; start the resolver with BackfillBridge as producer/consumer; obtain service.relay; start Marshal with SchemeVerifier and the App Update reporter; start App custody/output processing with `marshal.clone()`; open Engine with App Automaton, supplied Relay and `reporter: marshal`; then start Engine planes and await readiness. The real example matches these construction dependencies (`examples/log-multimmit/src/marshal.rs:126–212`, `node.rs:242–335`). The example's optional Reporters fanout is not a prerequisite.

Two distinct early-work cases are already handled in the prose:

- Marshal open starts catalog and, in immutable mode, promoter after storage recovery (`marshal/open.rs:75–166`). Service.start starts delivery before returning its mailbox (`service/mod.rs:213–295`), so an already-committed Update can reach App ingress before App processing is started. The callback must retain it, not execute inline or drop it.
- Engine open awaits recovered-body verification before wiring native actors (`engine/mod.rs:472–494`); native actors start only in Engine.start. App custody handling must be available during that await. Waiting for Running.ready before answering it would prevent open from completing.

The current recipe also keeps sibling handles under existing node ownership. Native readiness caches a startup result (`engine/mod.rs:156–173`), not continuing health or App-state readiness; Engine's root task can complete when a child stops (`engine/mod.rs:550–590`). Existing service handles do not supervise App/network siblings. The prose's unexpected-completion handling and abort-is-not-flush limitation are correct.

## Disposition

No correction is recommended for the latest reader text. These are confirmed API/control-flow and ownership facts plus explicitly proposed App obligations. A compiled App, non-dropping intake under pressure, persistent applied-state linkage, cancellation-safe workers, full Baton native policy and end-to-end liveness/recovery remain unproven. This focused audit does not mark the timed goal complete or replace root's final standalone-site/content audit.
