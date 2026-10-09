# Round 2: callback, recovery and delivery correctness

Read-only adversarial source review of the first App rewrite, followed by minimal corrections in this agent's assigned `docs/consensus/*` and `docs/reference/*` pages. Inspected current native `6233438985d8249d2b2bc1204191d5d405652288`. No protocol code or tests were executed/changed. Test names below are inspected source, not passing-run claims.

## Finding 1: a floor reset replaces the native delivery window, not App's retained Updates

**Counterexample:** App retains a full window of old-generation Updates. A state-sync owner installs a newer floor. Delivery drops the old waiters and reports another full window, while the old values still exist in App. A queue sized under the unconditional claim “all retained Updates are bounded by max_pending_acks” can now overflow. Returning Backoff and dropping the excess item would not trigger a retry.

Source:

- `marshal/actors/delivery/actor.rs:423–455`: Reset clears the pending window/cache, resets cursor storage, checks catalog progress and resolves reset waiters.
- `marshal/types.rs:128–136`: Update contains only index, block and Exact token; no delivery-generation field is exposed.
- `marshal/actors/catalog/actor.rs:741–777`: floor installation commits the new checkpoint and asks delivery to reset to its committed index, without waiting for App ACKs.
- `marshal/actors/synchronizer/floor.rs:54–63,135–159`: installation advances the internal generation and adopts the verified checkpoint.
- `marshal/protocol/floor.rs:37–65`: native floor verification prohibits frontier regression; it does not apply or authenticate the App's execution state.

**Minimal correction:** Qualify window sizing as ordinary delivery within one active generation. The App-owned floor/import lifecycle must serialize/fence the handoff, reconcile old retained Updates/tokens, and budget any overlap. It cannot read a nonexistent `Update.generation`. The native reset is not an application-state installation. Ordinary prune protects the current ACK prefix; an authorized floor reset replaces that boundary.

Resolved in this agent's `consensus/ordered-input.md`, `consensus/block-body.md`, `reference/integration.md`, and `reference/verification.md`. Root and companion-page agents were notified for their owned pages. Concrete cross-store sequencing remains explicitly unresolved; no new generic state-transfer/cursor service was added.

## Finding 2: shared Automaton documentation and current remote retry behavior differ

**Counterexample:** A remote verification request's receiver closes because an App drops the reply sender under pressure. The shared trait documentation says that request is terminal and not retried. Current Multimmit maps the closure to Unavailable, returns the block to Ready, and dispatches it again. A design that assumes no repeated call before restart can duplicate scheduler work or repeatedly spin on a closed/overfull ingress. Local-producer/recovery calls have different failure behavior.

Source:

- `consensus/src/lib.rs:162–175`: shared single-shot / terminal-closure contract; temporary conditions should remain pending.
- `multimmit/actors/voter/chain_plane.rs:537–547`: closed receiver becomes `BlockValidity::Unavailable`.
- `multimmit/machine/eligibility.rs:326–355`: Unavailable restores `ValidationState::Ready`.
- `multimmit/actors/voter/chain_plane.rs:480–481`: completion is followed by another dispatch.
- `multimmit/machine/eligibility.rs:796–810`: source test `an_unavailable_verdict_reschedules_the_block` explicitly expects another job for the same header.
- `multimmit/actors/voter/actor/live.rs:600–601`: uncanceled local verdict other than true is Fatal::Automaton.
- `multimmit/storage/recovery.rs:486–490`: recovered verification other than true returns RecoveredPayloadUnverified.

**Minimal correction:** Keep the recommended App contract: temporary absence remains pending; false is permanent invalidity; closure is not a portable retry API. State the current remote implementation exception and require deduplication of repeated verification without assuming restart. Do not promise exactly one callback per body or per run. Corrects the initial audit's overbroad “single-shot within one run” shorthand.

Resolved in this agent's body/custody and verification pages; root was notified for the canonical callback/interface pages. No native trait documentation or implementation was modified because this task is an application-design documentation rewrite.

## Finding 3: remote verify dispatch does not finish predecessor validation

`multimmit/machine/eligibility.rs:259–275,308–322` permits validation when the producer parent is certified at the anchor or is Pending/Valid. An App can receive child verify while the parent verdict/body is still pending.

**Minimal clarification:** Native producer authentication and ancestry eligibility are established, but App speculative dispatch must independently satisfy required producer dependencies and exact execution-parent availability. Child payload validity/custody can be determined independently where application rules allow; a call to verify does not itself establish dispatch eligibility. Added to the body page and verification scenarios; root notified. Existing admission/dispatch separation already supports this distinction.

## Checks that held

- Startup serves custody during Engine::open; speculative activation waits for the recovered App base rather than blocking native custody on readiness.
- Propose returns body digest after accepted staging; the later local custody fence remains required before header signing.
- Missing data remains pending and state-dependent speculative execution outcome is not substituted for payload-format validity.
- Canonical Reporters retain the whole Update/Exact, return synchronously and do not assume Backoff retransmission.
- Exact clone/drop behavior is accurately stated. Native delivery can pipeline; window retirement follows the contiguous acknowledged prefix, independently of cursor-sync completion.
- App-state durability and Marshal cursor durability remain distinct; exact applied identity supports crash redelivery without duplicate effects.
- Direct apply can proceed while result signatures are collected, while imported material requires its verified applicable certificate. Neither is approved by Baton report selection.
- Current native order remains authoritative; full Baton policy/adoption/continuation/recovery stays a separate unimplemented native integration obligation.

Further implementation verification must exercise these adversarial sequences with actual App code. Source review and doc checks do not establish those runtime outcomes.
