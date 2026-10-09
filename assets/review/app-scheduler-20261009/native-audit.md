# Current Multimmit / Marshal source audit

Inspected local native commit `6233438985d8249d2b2bc1204191d5d405652288` and research baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31` on 2026-10-09. This is source inspection, not a compiled Baton integration or runtime test. Paths below are relative to the parent Commonware checkout. Historical `534af0...` findings about an absent Multimmit Marshal no longer describe this checkout.

## Existing call boundaries

| Boundary | Current source | Consequence for the application |
|---|---|---|
| Shared Automaton | `consensus/src/lib.rs:125–183` | `propose` and `verify` return futures yielding oneshot receivers. Missing bytes/dependencies keep verification pending; false means permanent invalidity. The shared trait describes single-shot requests, but current remote Multimmit reschedules a closed-receiver Unavailable result; deduplicate live repeats and recovery (see Round 2). |
| Local production | `consensus/src/multimmit/actors/voter/actor/app.rs:83–158` | `propose(context)` yields a body digest. Native builds its header, then calls `verify` for custody before signing. This private `AppExecutor` runs callbacks, not application transaction execution. |
| Local custody failure | `consensus/src/multimmit/actors/voter/actor/live.rs:578–609` | An uncanceled local verdict other than true is `Fatal::Automaton`; an application must not turn queue pressure into false/closed completion. |
| Remote validation | `consensus/src/multimmit/actors/voter/chain_plane.rs:522–555` | Native eligibility chooses authenticated ready jobs, derives Context and body digest from a signed header, and awaits `verify`. Packet arrival is neither necessary nor sufficient as a one-to-one callback event. |
| Recovery validation | `consensus/src/multimmit/storage/recovery.rs:466–496` | `Engine::open` verifies recovered required payloads before native actors run; the app/body services must already answer. This is not a new other-lane receive event. |
| Custody promise | `consensus/src/multimmit/mod.rs:50–65` | True means valid, locally available, crash-reconstructible payload. Neither speculative transaction completion nor a result certificate is part of this promise. |

`Context::parent` is the producer header parent, not the application execution-state parent. Local own-lane `verify` precedes header signing; a scheduler that requires authenticated candidates cannot treat that call as proof the header has been signed. `Activity::TransactionProposed` identifies the later signed local block, but activity is best-effort, so a missed observation may lose speculative opportunity; it must not lose canonical delivery.

## Reuse supplied machinery

- Public `marshal::open` (implemented in the private service module) opens custody/order/delivery state and returns the public resolver bridge; `Service::relay` supplies the existing Relay; `Service::start` connects a resolver, `LqcVerifier`, and `Reporter<Activity = Update<TransactionBlock<...>>>` (`marshal/service/mod.rs:93–100,195–248`).
- `Mailbox::stage_block` admits complete header/body storage and returns a `Custody` token. Success at this call alone is not disk completion. Dropping an accepted token does not cancel storage. `put_block` waits for the token (`marshal/mailbox.rs:327–358`).
- `subscribe_block` obtains durable custody through local storage/buffer ingress; it does not initiate peer fetch. `fetch_block` does. Get/fetch success can expose buffered material before storage sync and is not itself a custody fence. Separate accepted DA evidence may cause backfill that fulfills a subscription (`marshal/mailbox.rs:390–446`).
- Existing Relay maps the **complete header digest** to the staged complete block and calls buffered broadcast. Native wire separately disseminates signed header + attestation. A receiver can see the header before its body; enqueue order at the sender is not a remote-arrival guarantee.
- Marshal already owns authenticated certificate/history resolution, base-order reconstruction, gap handling, body retention, dense output indices, delivery windows and restart cursor. A second BlockService, Orderer, fetch engine, proof archive, or ACK database is unnecessary for the base pipeline.

## Update and acknowledgement

`Update` contains exactly `index`, `Arc<complete block>`, and `Exact acknowledgement` (`marshal/types.rs:128–136`). The token's documented condition is **durably applied by the application**. It is not an inbox receipt, transaction-validity verdict, or quorum vote.

`Reporter::report` is synchronous (`consensus/src/lib.rs:258–268`). Delivery reports several updates up to `max_pending_acks`, retains their waiters, and resumes as the oldest contiguous acknowledged prefix advances (`marshal/actors/delivery/actor.rs:237–247,303–327`; `acks.rs:74–124`). Native consensus has no application-ACK wait in this path. A completed valid speculative result can make final processing selection/application I/O; unavailable or mismatching work still requires app execution/repair before ACK.

**Backpressure trap:** delivery checks only `Feedback::Closed`; `Backoff` does not retry the Update. The application must retain the original Update and ACK in a non-dropping bounded ingress/owner queue. The supplied Marshal window bounds one ordinary delivery generation; floor resets can overlap new deliveries with old App-retained Updates. Do not mix them into a lossy notification queue. If an ACK is dropped, delivery errors with `AcknowledgementCanceled`. Every cloned `Exact` must acknowledge (`utils/src/acknowledgement.rs:38–102`).

App durable apply and Marshal durable acknowledgement cursor are separate I/O boundaries. Application ACK retires a contiguous window prefix; Marshal then asynchronously syncs its cursor (`delivery/actor.rs:330–399`). A crash between them can redeliver an already applied block, so durable app position + exact block/state identity must support idempotent completion. A cursor sync does not itself apply app state. Floor installation resets generation/window and requires coordinated application state-sync fencing.

## Assembly and native policy gap

`examples/log-multimmit/src/node.rs:242–335` registers four engine planes plus Marshal resolver/body-broadcast channels, constructs app handles, starts Marshal and app, calls Engine::open with `automaton`, existing relay, and `Reporters::from((marshal, app_activity))`, then starts and waits for readiness. `application/reporter.rs:33–48` immediately ACKs synthetic headless output; this is not a transaction-state durability recipe. One Rust type cannot implement Reporter twice with different associated `Activity` types: use two typed handles to one app owner.

Native leader proposals do not pass through Automaton. Current `LeaderBlock` contains round, parent, history and lane proposals, with no Baton prefix/policy. Current Marshal's `protocol/order.rs` reconstructs the native base stream (history then positional and extension passes, with final-sweep halt conditions). Sorting finalized Updates in Baton would change the authenticated output order and is invalid.

PreCut and the app callback/execution pipeline can use current APIs. Full Baton still needs a narrow actual-leader-context/prepared-policy integration, authenticated policy binding, pre-vote validation, and matching policy interpretation/retention through native recovery and Marshal delivery. Reports alone cannot implement these changes; `Reporter<Activity>` is a best-effort post-admission observation.

## Required application scenarios for later implementation

1. Body before header, header before body, missing body, malformed peer response; keep temporary verification pending.
2. Duplicate/recovery/local/remote verify calls, canceled jobs and superseded anchors; no duplicate execution admission or false new-receive interpretation.
3. Full speculative queue while valid custody completes; consensus verdict remains independent of speculative completion.
4. Full Update queue with ACK retained; no Backoff/drop assumption; shutdown cancels without inventing durable completion.
5. App apply durable but ACK lost, ACK accepted but cursor sync incomplete, later ACK before earliest ACK; exact replay and no duplicate effects.
6. Confirmed order differs from local `F ++ sort_G(pending)`; exact-parent reuse/repair precedes canonical apply.
7. State-sync floor installation with old workers/updates in flight; fence writer authority and coordinate matching app/native state.

These are design/verification obligations, not executed test results.

## Later review corrections

[Round 2](round2-native-correctness.md) corrects the initial single-shot shorthand and records parent-Pending dispatch plus floor-reset/window overlap. [Round 3](round3-source-binding.md) records exact API excerpt checks, public path verification and the buffered get/fetch versus durable subscription distinction. The above initial findings incorporate the public-path and retry corrections; source audits remain separate from runtime test results.
