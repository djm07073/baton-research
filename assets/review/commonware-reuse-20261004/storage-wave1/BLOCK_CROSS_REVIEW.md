# Independent storage review of BlockService wave 1

Reviewed `block-wave1/REPORT.md`, its exact native/chain source snapshots, and current `docs/consensus/block-body.md` / `ordered-input.md`. Additional pinned raw reads verified native voter dispatch and the generic Archive trait. This is source review only; no service build, protocol execution, central-document change or policy adoption occurred.

**Verdict:** the proposed minimal logical BlockService and direct generic buffer/resolver/archive assembly are supported. The report correctly distinguishes generic Commonware reuse from a custom Multimmit attachment. The corrections below concern precision and preservation when moving these proposals into canonical documentation; they do not overturn the core recommendation.

## Confirmed API findings

| Claim | Independent source check | Result |
|---|---|---|
| Direct application callbacks can avoid a new propagation engine | Native `Automaton::propose` / `verify` return futures producing oneshot receivers; `Relay::broadcast` and `Reporter::report` are synchronous methods. The native Multimmit example sets producer Context and `Plan=()`. | Confirmed. The example is body-free and returns verify=true, so it proves callback shape, not durable body custody. |
| Generic buffered broadcast can disseminate bodies | `Engine::new` returns engine/mailbox; `Mailbox::broadcast_shared` enqueues an `Arc<M>`; `get` is an async local cache lookup; `subscribe` returns a local oneshot waiter. | Confirmed. Neither lookup nor subscription actively fetches missing bytes or persists them. |
| Generic resolver is the correct external body-fetch primitive | Its public Producer serves `Bytes`; Consumer receives a peer-visible key and subscribers; Engine is constructed with application Producer/Consumer. | Confirmed. It supplies fetch/retry/correlation without requiring a Simplex Block. |
| Marshal resolver is not an externally consumable replacement | Public `marshal::resolver::p2p::init` returns a handler Receiver and mailbox, but Receiver's `recv` / `try_recv` and underlying Message are crate-private. | Confirmed. An external attachment cannot simply consume that bridge. Use generic resolver::p2p, or treat a new facade as explicit integration work. |
| Native standard Marshal wrappers are not drop-in Multimmit adapters | Marshal documents Simplex-only operation and one-notarization-per-view assumption; Deferred's Automaton implementation requires Simplex Context and CertifiableBlock ancestry. | Confirmed. Native Multimmit Context and Plan=() differ. |
| Archive indices can silently defeat custody claims | Immutable Archive treats occupied indices as no-op; prunable Archive also satisfies puts below floor without storing. Keys may repeat and key lookup may return any associated value. | Confirmed. Sync success cannot prove an item that was never inserted. |
| Native restart requires body attachment readiness | `verify_recovered_payloads` runs application verification and requires `Ok(true)` before dependent consensus authority is live. | Confirmed. Archive/fetch/serving readiness must precede the native startup gate. |
| Relay acceptance is not remote custody | Broadcaster documents local processing admission only. Native `relay_ready` defers only on `Feedback::Closed`. | Confirmed. No application receipt quorum or durable-peer ACK follows. |

Anchors: [Automaton](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L118), [Relay/Reporter](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L224), [body-free Multimmit example](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/application/actor.rs#L36), [buffer mailbox](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/ingress.rs#L89), [generic resolver Engine](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/engine.rs#L108), [Marshal receiver visibility](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/resolver/handler.rs#L118), [Marshal limitations](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/mod.rs#L61), [Deferred type/timing](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/standard/deferred.rs#L471), [recovered-payload gate](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L265).

## Corrections required in the adoption text

### 1. Archive custody recipe must retain the consumed handle

The report's shorthand `put + sync` is correct as a lifecycle, but a concrete recipe must bind returned ownership. Generic Archive's mutating methods consume `self`; dropping their future or returning an error destroys the handle. Use `archive = archive.put(...).await?; archive = archive.sync().await?`, or upstream `put_sync`, under a retained storage owner. `put_start_sync` also exists and returns `(archive, handle)`; await its covering durability before custody success. These helpers remain subject to occupied-index and below-floor no-ops.

A canceled resolver subscriber may discard its validation result. It must not cancel the storage owner's in-flight archive mutation. The same applies to the propose/verify requester being canceled after archive work starts. Keep storage mutation ownership distinct from cancelable readiness observation. Current `block-body.md` already discusses consumed `store::Blocks`; extend that precision to the direct generic Archive recipe instead of limiting it to the unadopted Marshal store wrapper.

[Archive ownership and helpers](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/mod.rs#L44).

### 2. Peer-visible resolver validity is distinct from subscriber context

Consumer checks bytes against the exact peer-visible key and then dispatches applicable readiness to subscribers. An invalid body/digest for that key can return `Invalid`. A canceled/stale-generation subscriber does not make correct returned bytes malicious. Where a key deliberately admits several valid responses, a valid response that leaves subscribers unresolved uses `Ambiguous`; if the entire key is no longer needed, use `Ignored`. Do not broadly turn every context mismatch into `Invalid` when that context exists only in local subscriber metadata.

If context is authenticated in the key/body schema, the adapter can enforce that peer-visible binding. Otherwise perform stable native `(Context, payload)` validation separately. The report mentions disposition differences, but its abbreviated “Consumer checks exact key/context” flow should make this distinction explicit to prevent blocking honest peers for local scheduling changes or storage failure.

[Consumer dispositions](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L118), [Consumer delivery contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L157).

### 3. Reporter/body-ready joins provide opportunistic intake, not reliable witness export

Native `dispatch_work` explicitly discards Reporter Feedback. The report's no-native-ACK intake is correct. Keep this fact adjacent to the proposed direct Reporter wiring: local queue acceptance is not a durable retained-witness transfer, and there is no native retry guaranteed by Reporter Feedback. Missed candidate notices may trigger bounded local reconciliation, while exact canonical witness export/cursor recovery remains Orderer integration work.

Likewise native Relay only gates transmission on `Closed`; a body-publication attachment should enqueue work synchronously and distinguish its own readiness/lifecycle from native encoded-effect retry. No claim that Relay exposes native Retire or authorizes archive release is supported. The report already labels that bridge unresolved; preserve that language when translating `BlockService::on_retire` into prose.

[Reporter feedback ignored](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L1655), [Relay gate](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L2285), [Broadcaster feedback](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/lib.rs#L26).

### 4. Exact archival presence must remain protected after the custody check

A put followed by sync and an exact-value lookup is useful evidence only under serialization/retention authority that prevents a conflicting prune or handoff from invalidating it. Stable custody must retain exact body bytes and durable header/context correspondence for all currently required native recovery, ordering, speculative branch, query and peer-serving obligations. A successful lookup at one instant cannot justify early archive release.

Ordinary global height indices collide across Multimmit lanes and competing producer bodies. `MultiArchive` permits duplicate indices, but it does not choose which logical object a plain Index lookup should return; use exact key/value verification and an appropriate collision-safe mapping. Do not fill an index policy by adopting Simplex height layout through an example.

[Archive uniqueness/durability](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/immutable/mod.rs#L6), [prunable duplicate-index/key semantics](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/prunable/mod.rs#L32), [prune-floor behavior](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/prunable/mod.rs#L97).

### 5. Cross-epoch retention must provide currently reachable serving coverage

Keeping old bytes on a former validator does not make them fetchable by the default resolver. Outbound requests use `latest.primary`, and explicit targets cannot bypass that filter. Inbound serving handles connected peers more broadly; the asymmetry is intentional and does not solve new-committee retrieval from old-only sources. Buffered content can also be evicted when its senders cease to be primary.

The adapter must establish custody transfer/serving coverage before an epoch peer change makes required content unreachable, or explicitly select a compatible provider/serving construction. Retention duration, committee overlap and release policy stay open. Tempo's backend watermark is a practical handoff pattern but does not prove Baton's independent recovery/query/serving obligations or indefinite fetchability of backend-pruned history.

[Resolver peer selection/targeting](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L64), [buffer eviction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/mod.rs#L19), [Tempo Hybrid backend lookup/prune](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/storage/hybrid/mod.rs#L393).

## Minimal recipe accepted for further integration

Implement an application attachment with upstream Automaton/Relay/Reporter, body codec/Digestible, generic resolver Producer/Consumer and handles for the buffered Engine, generic resolver Engine, and archive owner. Keep construction, exact header/body/context correlation, durable custody and retention authority in thin application glue. Reuse native source call shapes; chain release examples show assembly structure, not unchanged native signatures. No Stateful/Application dependency is necessary for these body primitives.

The current BlockService project trait can remain a compatibility facade over that attachment until the interface synchronization explicitly changes it. The source does not itself mandate either retaining or deleting a project-facing trait. Executor remains responsible for transaction execution/certification/sync orchestration and Storage for roots/material/apply/durability. Body archival custody is a separate concern from execution-root calculation; do not move result certification into BlockService merely because both use retained storage and authenticated transport.

No material contradiction was found in the report's exact source-version labels, Simplex restriction or generic resolver recommendation. These corrections preserve already-adopted no-wait native cut, immutable policy/terminal order, and f+1 execution-result boundaries; none closes the native prefix-adoption or exact-order delivery proof obligations.
