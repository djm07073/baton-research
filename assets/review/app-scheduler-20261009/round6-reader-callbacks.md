# Round 6: source-to-reader callback trace

Reviewer: `/root/docs_alignment`. Source/doc/visual audit at 2026-10-09 07:45 UTC against parent checkout `6233438985d8249d2b2bc1204191d5d405652288`. This audit does not implement or execute a transaction App, protocol scenario or benchmark. Root-owned `docs/baton/README.md` and architecture edits were left untouched.

## Entry points traced from current source

| Entry point | Current source fact | Reader contract and result |
|---|---|---|
| Client/peer transaction ingress | Native Automaton accepts a producer Context, not individual transactions (`consensus/src/lib.rs:155`). The example builds `Body::junk` from a synthetic workload (`examples/log-multimmit/src/application/actor.rs:221–287`); it has no implemented transaction pool/RPC path. | `docs/tx/interfaces.md:7–29` and `docs/e2e/normal.md` correctly describe proposed App admission/selection and retained stable bytes. No existing native pool is claimed. Added a direct normal-flow link to the concise pool contract before the optional backend survey. |
| Producer propose | Native private `AppExecutor::build` awaits `automaton.propose(context)` and then its oneshot receiver (`actors/voter/actor/app.rs:83–118`). Example mailbox returns `ready(receiver)` and retains the response in a message (`application/mailbox.rs:148–159`); the actor stages before sending the body digest (`application/actor.rs:309–365`). | E2E normal/body diagrams label receiver resolution rather than a direct digest return. The pool-specific sketch is illustrative internal code. Body digest versus header identity and accepted staging versus durable custody remain explicit. Pass. |
| Local pre-sign verify | `AppExecutor::custody` constructs Context/body digest from the prepared header, calls verify and awaits its receiver with cancellation (`actor/app.rs:121–157`). `machine/producer.rs:471–489` only reserves signing after custody. | `e2e/block-body.md` and normal/native-consensus diagrams correctly place local validity/custody before signing. Local prepared bytes are not authenticated proposal evidence. Pass. |
| Live validation-plane verify | `chain_plane.rs:522–555` dispatches current native-eligible headers. `machine/eligibility.rs:309–323` permits a Pending producer parent; `:352–366` handles closed/true/false outcomes. `actor/chains.rs:114–179` creates every chain plane for validators, including nonproducers, and none for Observer. | Body E2E distinguishes callback eligibility from packet receipt, exact producer ancestry from execution checkpoint, nonproducing validator from Observer, and live candidates from recovery/local pre-sign work. Current canonical callback page documents remote closed-receiver redispatch without promoting closure to a portable retry API. Pass. |
| Recovery verify | `storage/recovery.rs:473–490` awaits both the callback future and Boolean receiver for retained requirements; only `true` succeeds. | `e2e/recovery.md` supplies App custody before Engine open, keeps speculation gated, separates native ready from App state readiness, and re-evaluates retained candidates on activation. Pass. |
| Relay/body exchange | `Relay::broadcast` is synchronous `Feedback` (`consensus/src/lib.rs:253`). Native publication calls it with header digest before transmission (`actor/publish.rs:124–145`). Marshal looks up the staged full block and calls buffered broadcast (`marshal/relay.rs:107–112`); missing lookup returns `Ok` without sending. `Service::relay` already sizes/owns this cache and remembers own-chain recovered subscriptions (`marshal/service/mod.rs:196–209`, `relay.rs:41–64`). | Body diagrams correctly keep native signed headers and complete body exchange on different paths with unconstrained receiver arrival order. Added a compact networking note that even local `Ok` is not proof bytes were sent. No new cache, relay service or retry layer. |
| Native Activity | Reporter is synchronous (`consensus/src/lib.rs:267`). `actor/live.rs:412` reports without waiting for downstream completion. Existing `Reporters` calls both typed native-activity consumers (`consensus/src/reporter.rs:31–46`); node config includes Marshal and the optional App handle (`node.rs:315–318`). Marshal's release cursor path differs from its ordinary hint queue (`marshal/mailbox.rs:500–518`). | Networking/native-consensus E2E correctly route native Activity to Marshal and optional App observation; they do not treat Activity as the full-block canonical stream. The native retention exception remains described in the consensus body contract. Pass. |
| Marshal Update | `marshal/types.rs:128–136` supplies complete block/index/Exact. Delivery's synchronous call (`actors/delivery/actor.rs:303–325`) treats only Closed as terminal, retaining the waiter for other feedback. It does not call App Automaton to execute transactions. | Canonical E2E requires retained intake, no execution in `report`, exact order, no Backoff-based lossy retry, and App worker application. Added the first-seen-block case so no earlier verify/candidate entry becomes a hidden requirement. |
| Canonical ACK | Update's comment requires durable App apply. `utils/acknowledgement.rs:39–101` makes Exact an in-memory signal requiring every clone; dropping one cancels the waiter. Marshal frees a contiguous ready prefix (`acks.rs:107–124`) and separately syncs its cursor (`actor.rs:330–378`). | Canonical E2E preserves durable state/output/applied identity before ACK, independent native progress, redelivery, Exact retention and per-window/floor-overlap bounds. Clarified that the example's immediate headless ACK is not a reusable durable transaction consumer. |

The native paths above are beneath `consensus/src/multimmit/` unless prefixed otherwise. `actor/` abbreviates `actors/voter/actor/`; `chain_plane.rs` is in `actors/voter/`; delivery `acks.rs` is in `marshal/actors/delivery/`. Example application/node paths are beneath `examples/log-multimmit/src/`.

## Confirmed reader hazards and applied minimal changes

### Example output reporting is wiring, not transaction durability

`examples/log-multimmit/src/application/reporter.rs:36–46` records an ordered observation, then either forwards to the terminal sink or immediately acknowledges in headless mode. The App mailbox's `ordered` observation filters to the local producer for latency (`mailbox.rs:135–144`); it does not preserve the Update/ACK for execution or apply storage.

`docs/e2e/canonical.md:51` now states this distinction and links the exact source. A new engineer following node assembly must supply the documented retained canonical-worker consumer instead of copying that immediate ACK. Root can link this paragraph from its source-reference/startup guidance; repeating a second implementation recipe is unnecessary.

### Canonical input cannot depend on prior speculative intake

The complete body is opaque to native transaction semantics (`types/block.rs:264–303`). A native Observer has no live validation plane; ordinary Marshal delivery still reaches the App. Speculation may also be skipped on any node under its bounded policy.

`docs/e2e/canonical.md:43` now explicitly allows Update to be the first App encounter. The canonical execution path performs its required application checks, reuses exact validated work, or uses verified applicable imported material. It does not require another Automaton callback or a scheduler candidate, and transaction outcomes do not rewrite native order. `docs/e2e/normal.md:51` reflects the same independence. Root added the concise core counterpart.

### Diagrams should not imply scheduler or pool-maintenance approval

- Diagram 02 now puts exact-index canonical reconciliation at the existing App owner before selecting matching work/repair. It no longer routes that decision through a participant labeled scheduler/workers as though policy selected canonical order.
- Diagrams 02 and 08 now say “Advance applied base, schedule pool maintenance.” The diagrams retain durable state/output/identity before ACK without implying completion of a backend maintenance notification is an additional ACK gate.
- Diagram 09 labels its existing coordinating participant “App execution owner.” It already owns exact-parent work and canonical branch reconciliation; this changes no actor count, trait or architecture.

Both embedded Mermaid and the three corresponding `.mmd` sources were edited. No broader algorithm, body format, scheduler precedence, result threshold or backend policy changed.

### Local Relay feedback is not delivery evidence

`docs/overview/networking.md:37` now names the source no-op behavior. The existing service already supplies retention sized from native outbox capacity; the note does not create a new App cache or a protocol defect claim. The native reviewer independently confirmed this fact from its earlier source-binding review.

## Undefined-name and async/sync checks

No undefined mandatory class/trait was found in the current reader path. App is explicitly the proposed owner; native `AppExecutor` is the callback driver, not a VM. Pool operations, candidate admission, dispatch and canonical reconciliation are local responsibilities. `Reporter<Update>` is reader shorthand; the Rust reference supplies the actual associated-type form and separate typed handles for native Activity versus Update.

Automaton's two completion stages are consistently represented as a future yielding a receiver and a later digest/verdict. Relay and Reporter return synchronous Feedback. ACK consumes an Exact handle after App durability, and neither its call nor callback return is described as I/O. The important remaining qualifications—temporary missing data, native cancellation, current-owner checks, invalid ancestry, once-only current attempts and access fences—remain in their canonical contracts.

## Targeted render readback and checks

Root rendered only the affected diagrams and refreshed their manifest records. This reviewer then inspected the actual final PNGs through `view_image`:

| PNG | Visual/semantic result | SHA-256 |
|---|---|---|
| `docs/assets/diagrams/diagram-02.png` | All labels/arrows fit. App owns canonical reconciliation; scheduled maintenance follows durable state and precedes the local ACK signal without a processing wait. Optional speculation remains visibly separate. | `31a99b021e99cc835893f1ced2e3c3136e555e3f67200d318eece06594e4bbe3` |
| `docs/assets/diagrams/diagram-08.png` | No clipping/overlap. Lossless handoff, exact predecessor/redelivery branch, existing-work/import/repair alternatives, durable apply and ACK remain clear. | `13da4387ecb069ac8dbd8d7c405da7ef3b7158c9d3f318f11549a717f11d1ebe` |
| `docs/assets/diagrams/diagram-09.png` | New owner title fits. Parent-bound effects, selected roots, canonical writer, durability and retained-reference guard remain legible, including failure branch. | `53469838ffc2ead22c450c9d76d3c78bb7c773f96472c8eb0301f5611b5fe113` |

Source mapping: normal.md first Mermaid → diagram-02; canonical.md first Mermaid → diagram-08; canonical.md second Mermaid → diagram-09. No diagram edits were made after this readback.

Targeted `git diff --check` passed. Fresh `npm run docs:check` passed with 32 pages, 240 local links, 19 rendered diagrams and 38 blank policy cells; no failures. Existing source files/line ranges were read for the claims above. These checks are documentation/source/visual evidence, not a runtime test of the proposed App.
