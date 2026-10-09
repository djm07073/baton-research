# Round 4: custody release and application retention

Inspected parent checkout `6233438985d8249d2b2bc1204191d5d405652288` on 2026-10-09. This records source evidence and application counterexamples, not newly executed tests or a finding that native pruning is broken.

## Three independent retention boundaries

| Boundary | Authoritative fact | Consequence |
|---|---|---|
| Native producer custody | `Activity::CertificateRecorded { certified, released }` per producer chain | Engine will no longer depend on App verdicts at or below released, including after restart. Already-dispatched requests can still arrive; their settled verdicts are ignored. |
| Marshal canonical history/body retention | Retained verified floor, durable ACK cursor, native releases, materialization pins and configured storage mode | Ordinary prune retains unacknowledged outputs and native-required bodies. A floor jump changes the cursor lifecycle and requires matching App import coordination. |
| Application execution/state/result retention | Exact applied identity, live workers/branches, recovery/query/result-serving and sync obligations | Speculative retirement, pool cleanup and physical state removal need App decisions. Neither a DA certificate nor delivery ACK authorizes removing every App artifact. |

No additional BlockService or retention protocol is required for native body custody. Use the existing Marshal reporter, mailbox and stores; keep App execution bookkeeping concrete and separate.

## Native release is deliberately behind certification

`machine/da.rs:34–40` computes `released = certified_height.saturating_sub(pipeline_depth)`. DA retirement preserves local votes above that bound (`:251–278`) because native voting/recovery can still use them below a newer certified tip. Durable persistence completion reports CertificateRecorded only after the safety record is acknowledged (`machine/reducer/persistence.rs:550–627`); startup reports the newest record for each chain (`machine/reducer/step.rs:707`; `types/activity.rs:104–117`).

Recovery reverifies the deduplicated union of retained local producer headers and local DA-vote headers (`machine/chain.rs:288–318`). It is not a replay of speculative pending entries or only unapplied canonical blocks. `storage/recovery.rs:473–496` requires every recovered verdict to be true; false or closed completion fails `Engine::open` with RecoveredPayloadUnverified. A genuinely live local pre-sign failure is Fatal::Automaton (`actors/voter/actor/live.rs:578–605`).

Counterexample: App applies a block, drops its speculative candidate, then restarts while a local DA vote for that body remains in the native pipeline. Returning false because the candidate was retired fails native recovery even though the transaction block remains valid. App must still validate/custody live native requirements, while avoiding duplicate scheduling or transaction application.

## Marshal already preserves the required bodies

- Mailbox Reporter routes CertificateRecorded to the catalog's dedicated coalescing release lane (`marshal/mailbox.rs:503–510`). Releases only rise and queued updates coalesce by chain (`marshal/actors/catalog/mailbox.rs:351–407`). Dropping this connection prevents reclamation; it does not grant permission to prune.
- Catalog storage initializes release knowledge to None on reopen (`marshal/storage/catalog/mod.rs:420`). No release means keep every block. The Engine reports its durable releases again at startup; Marshal does not guess them from finality or App ACKs.
- `verifiable` caps a chain's proposed body-prune floor at `released + 1`; an unreleased chain keeps all bodies (`marshal/storage/catalog/prune.rs:66–89`). Immutable-mode promotion also applies that cap (`:28–62`).
- Ordinary `prune` clamps the requested index to the acknowledged cursor (`marshal/actors/catalog/actor.rs:783–788`). Retained floors determine which finalized history can be removed, and each producer keeps the newest block at/below the floor plus any older still-verifiable bodies (`marshal/storage/catalog/prune.rs:91–150`). Pinned materialization segments also remain protected.
- Source fixture `pruning_keeps_every_block_the_engine_may_still_verify` (`marshal/tests.rs:3211–3286`) covers no-release retention, per-chain release bounds, stale release monotonicity, floor-parent retention and conservative reopen behavior. It was inspected, not run in this documentation task.

Counterexample: treating certified height 100 as release when pipeline depth is 10 can remove bodies 91–100 that restart still verifies. The current Marshal code avoids this by consuming the supplied released field. App must not implement a competing prune calculation or use its canonical output index as a producer height.

Floor installation does not override this producer release bound. It does reset delivery generation/cursor independently of old App-held Updates; the Round 2 cross-store/import handoff remains necessary. App query/results/worker references can require additional retention beyond what Marshal promises.

## Late callbacks after release

Native explicitly allows an already-dispatched verification to reach App after release (`types/activity.rs:107–112`). Advancing a remote anchor removes settled validation jobs and cancels their awaits (`machine/eligibility.rs:371–400`; `actors/voter/chain_plane.rs:505–506,538–554`). A raced completion with no current job is Stale (`eligibility.rs:326–350`). Thus a missing body after correctly authorized pruning need not imply broken custody: the only remaining callback may already be obsolete.

This does not make false a generic response to App retirement. Retirement of an App branch, eviction under a speculative budget, prior application, or an App generation change is not proof that native has released the block. App should distinguish live callback work from canceled/settled work, stop waits when the native response closes, and prevent stale candidate resurrection. The compiling example races subscription against `response.closed()` (`examples/log-multimmit/src/application/actor.rs:60–85`). That is reuse of existing oneshot cancellation, not a new origin flag or public protocol.

Two adversarial cases to preserve in later App tests:

1. Native still needs an already-applied valid body: serve the custody/validity verdict without reexecuting or reinserting it into pending work.
2. Native has released/canceled the request and Marshal legitimately prunes its body: stop stale work and do not wait forever for a speculative candidate or recreate an applied branch. Do not infer payload invalidity from absence alone.

## Documentation resolution

The owned block-body page now qualifies “skip already applied” as a scheduling decision, explains the per-chain released height and the allowed late callback, and keeps App material retention independent. The verification matrix includes these future scenarios. An ambiguous “recovery closure fails open” phrase was corrected to “makes Engine::open fail.” Root and the E2E/callback owner were informed to align their retired-candidate wording. No new native API, body archive, ACK gate or retention framework was added.
