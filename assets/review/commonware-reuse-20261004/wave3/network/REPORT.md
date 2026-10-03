# Network/body assembly — third wave

Source investigation and documentation recommendations only, 2026-10-04. No protocol implementation, dependency change, external checkout mutation, build, benchmark, canonical documentation edit, commit or publication performed by this agent. The prior two-wave catalog remains applicable; this report adds exact network wiring, encoded-envelope limits, peer-provider behavior and one concrete stale native example call.

## Main result

Baton can use one existing Commonware authenticated network and give each body service its existing channel `(Sender, Receiver)` pair. Pass one pair directly to `buffered::Engine::start` and another to generic `resolver::p2p::Engine::start`. Clone the existing network oracle for `Provider` and `Blocker`; no new transport, peer-discovery engine or generic request correlator is implied. The unavoidable custom seam is body/header/key/context checking and archive custody/retention ownership.

The current published architecture is sound at this component boundary. It needs two small precision additions: the pinned log-multimmit example contains an outdated three-argument channel registration call, and the maximum permitted body must fit the **resolver response envelope**, not merely the raw broadcast body. Remaining notes below clarify reuse rather than introduce new modules or policy defaults.

## Sources and receipts

Every downloaded Rust/TOML source was freshly fetched from its immutable GitHub revision, checked against its Git tree blob SHA-1, and recorded with SHA-256 in [source-manifest.json](source-manifest.json). The four recursive trees are complete (`truncated=false`). The Commonware release tag resolves to `d476a2361ce6840d2b9d0aa6fb30a924429046d4`; release links below use that immutable hash. One guessed Alto `chain/src/main.rs` path was absent and was not used; its actual entry point is `validator/src/main.rs`.

| Source | Revision | Purpose |
|---|---|---|
| Native Commonware | `534af0ede48affd35b2111522527547b4cc9bf72` | Adopted network/buffer/generic resolver API baseline |
| Commonware release | `d476a2361ce6840d2b9d0aa6fb30a924429046d4` (`v2026.9.0`) | Exact standard wrapper → Marshal → buffer path used by chain references |
| Tempo | `61c979a524f9af5de9c540a0088c429a44741e4c` | Actual body broadcaster, backfill channel, peer manager and outbound size adapter |
| Alto | `1d87569348b5560699465a72d691d90f18affb9c` | Actual channel registration and size-budget calculation |

These snapshots are not one compiled dependency graph. No protocol compatibility or production maturity claim follows from source inspection.

## Exact outgoing body path in Tempo and Alto

Tempo's `Marshaled` wrapper implements upstream Automaton/Relay and selects release standard Inline or Deferred around its application. The documented wrapper responsibility includes persistence, broadcasting and the Simplex certify durability gate. [Tempo attachment](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/application/mod.rs#L1).

The release source closes the propagation call graph, rather than merely showing a buffer was constructed:

1. Standard Relay processes `Plan::Propose` by taking the staged body and calling `marshal.proposed(round, body, Recipients::All, ack)`; `Plan::Forward` calls `marshal.forward` with recipients. [standard relay](https://github.com/commonwarexyz/monorepo/blob/d476a2361ce6840d2b9d0aa6fb30a924429046d4/consensus/src/marshal/standard/relay.rs#L21).
2. Marshal handles `Message::Proposed` by calling `buffer.send(round, Arc::clone(body), recipients)` before `persist_verified`; forwarding first finds the body by commitment then calls the same buffer send. This early broadcast is protected by the **Simplex wrapper's later certify gate**, not evidence that Multimmit's propose custody can be weakened. [Marshal dispatch](https://github.com/commonwarexyz/monorepo/blob/d476a2361ce6840d2b9d0aa6fb30a924429046d4/consensus/src/marshal/core/actor.rs#L649).
3. The Standard Buffer implementation for `buffered::Mailbox` calls `broadcast_shared(recipients, body)` directly. Its `retire` implementation is a no-op, so Standard buffer eviction is driven by the broadcaster's cache/peer policy rather than generic durable-reference reclamation. [direct delegation](https://github.com/commonwarexyz/monorepo/blob/d476a2361ce6840d2b9d0aa6fb30a924429046d4/consensus/src/marshal/standard/variant.rs#L90), [send and retire](https://github.com/commonwarexyz/monorepo/blob/d476a2361ce6840d2b9d0aa6fb30a924429046d4/consensus/src/marshal/standard/variant.rs#L113).
4. Tempo starts the existing broadcast Engine on the body channel and the Marshal resolver on its separate backfill channel. [startup](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L526). Alto registers independent broadcaster and Marshal channels on the same authenticated network, starts that network, then hands their pairs to the chain assembly. [Alto register/start](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/validator/src/main.rs#L316).

For Baton, reuse step 3's public buffered handle and generic resolver underlying the fetch service. Native Multimmit has `Relay::Plan=()` and producer Context, so implement its existing Relay callback directly; retain the documented body/parent custody boundary on Automaton success. Do not import a Simplex Plan, use the private standard relay helper, or move a Simplex certify gate into native Multimmit.

## Finding N1 — log-multimmit example channel calls are stale at the adopted pin

**Observed:** [log-multimmit main](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L366) calls `network.register(0, quota, 256)` (and the other three native channels likewise). At exactly the same tree revision, [discovery Network](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L169) exposes only:

```rust,ignore
pub fn register(
    &mut self,
    channel: Channel,
    rate: Quota,
) -> (
    channels::Sender<C::PublicKey, E>,
    channels::Receiver<C::PublicKey>,
)
```

This is not an alternate type/reexport or different package version:

- main imports `commonware_p2p::authenticated::discovery` and calls `discovery::Network::new`; no local extension trait defines another registration method.
- [discovery/mod.rs L255](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/mod.rs#L255) directly reexports `network::Network`.
- [example Cargo L23](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/Cargo.toml#L23) uses `commonware-p2p.workspace=true`.
- [root Cargo L133](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/Cargo.toml#L133) resolves that workspace dependency to local `path="p2p"`.

**Exact replacement recipe:** call `network.register(channel_id, quota)` for both native and additional application planes. Register all channels before `network.start()`; registration is impossible after start. Select channel IDs and quotas under the existing open policies, without copying `256` as an adopted mailbox choice. The returned Sender and Receiver are directly suitable for the existing Engine start bounds.

This is a source-level incompatibility in the pinned example, not a recorded compiler failure and not a reason to change the adopted Multimmit pin. The docs should call the example a wiring reference and explicitly use the selected pin's primitive signature when adapting it. No external checkout repair is authorized by this report.

## Finding N2 — the resolver envelope must fit the shared transport payload limit

The body channel broadcasts encoded `Body`; generic fetch responses broadcast an encoded resolver `Message<Key>` containing request ID, discriminator and encoded `Bytes`. At the native pin the payload-size assertions occur in `channels::UnlimitedSender::send`; an oversized locally produced response can panic rather than become a peer invalidity verdict. [sender assertion](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/channels.rs#L51), [typed sender encoding](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L60).

For canonical body bytes of length `b`, the native generic resolver format is:

| Message | Native encoded application payload size |
|---|---|
| Raw body broadcast | `Body::encode_size()` |
| Fetch request | `8 + 1 + Key::encode_size()` |
| Fetch response | `8 + 1 + body_bytes.encode_size()` |
| Fetch error | `8 + 1` |

Here `Bytes::encode_size()` includes the length prefix plus `b`; it is not merely `b`. The fixed `u64` ID is 8 bytes and the payload tag is one byte. [resolver wire](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/wire.rs#L16), [response sizing](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/wire.rs#L109), [Bytes codec](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/types/bytes.rs#L23), [fixed integer encoding](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/types/primitives.rs#L78).

The wire module is private. The adapter should not name or instantiate its private `Message` type; use these source-grounded sizing obligations and existing public Codec/EncodeSize APIs to validate its configured body budget and server-produced byte buffers. Perform checked arithmetic for configured limits. The network handles its own channel/encryption framing; do not count that overhead a second time against the configured **application** payload maximum.

A body that exactly consumes `Config::max_message_size` on raw broadcast cannot necessarily be served by generic resolver on the same network. Require the whole allowed response envelope to fit, and bounded-decode Body using its application `Read::Cfg` in the Consumer. Generic resolver decodes opaque response Bytes with unrestricted RangeCfg because network length already bounds the source buffer; this does not supply application transaction count, nested-object or validation-work bounds. [opaque decode](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/wire.rs#L139).

Real chains already consider this boundary. Alto computes a network maximum including block bytes, their codec length prefix and base message allowance, with a checked u32 conversion and authenticated maximum. [Alto size calculation](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/validator/src/main.rs#L60). Tempo wraps each outgoing channel in a small `SizeLimited` sender to reject oversized encoded payloads and count the drop; that wrapper is Tempo `pub(crate)` adapter code, not a directly public Commonware primitive. [Tempo limit_channel](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/network.rs#L50), [Tempo channel wrapping](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L488). Whole-message limit validation can keep Baton's adapter small without creating a new transport engine. No numerical maximum or wrapper choice is adopted here.

## Existing handles and identity relationships

| Connection | Exact reusable API/bound | Application work |
|---|---|---|
| Physical transport / discovery | `discovery::Network<E,C>::new` returns Network and `Oracle<C::PublicKey>` | Choose deployment namespace/authorized peers using current epoch rules; register logical channels before start |
| Body dissemination pair | `buffered::Engine<E,P,Body,D>::start((Sender<PublicKey=P>, Receiver<PublicKey=P>))` | `Body: Digestible+Codec`; pass its decode config and current peer Provider |
| Body publication | `Mailbox<P,Body>::broadcast_shared(Recipients<P>, Arc<Body>) -> Feedback` | Resolve retained digest/body mapping and choose allowed recipients; queued success is not actual send/remote custody |
| Missing-body pair | `resolver::p2p::Engine<E,P,D,B,Key,Con,Pro,NetS,NetR>::start((NetS,NetR))` | `Key: Span`, `Con: Consumer<Key=Key,Value=Bytes>`, `Pro: Producer<Key=Key>`, both channel identities `P`, subscriber `Clone+Ord+Send` |
| Archive serving | `Producer::produce(Key) -> oneshot::Receiver<Bytes>` | Return exact canonical body bytes from retained archive; bound concurrent serve work, preserve cancellation-safe store owner |
| Response validation | `Consumer::deliver(Delivery<Key,Subscriber>, Bytes) -> oneshot::Receiver<Outcome>` | Check exact peer-visible key, bounded body decode and digest; correlate local header/context subscribers separately; persist/readiness ownership remains local |
| Other application planes | Public `p2p::utils::codec::wrap` / `WrappedSender` / `WrappedReceiver` | Implement tx/report/direction/result schemas and cryptographic/context checks, using existing channels |

Sources: [buffer bounds/start](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L40), [generic resolver bounds](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/engine.rs#L36), [Producer](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L100), [Consumer](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L149), [typed channel wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L16).

Use cloned native oracle for Provider/Blocker when its current tracked set expresses the serving policy. Tempo has a custom peer-manager mailbox because its validator-set changes derive from its execution/backend model; its mailbox implements existing Provider/AddressableManager. Baton's fixed/native configuration does not automatically need a second peer-manager actor just to call buffer or resolver. [Tempo Provider implementation](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/peer_manager/ingress.rs#L65).

Transport identity `P` is the authenticated relay peer, not necessarily the native producer that authored the body. Honest relays may serve someone else's retained body. Validate body/header/statement authorship in its exact cryptographic subject rather than requiring the serving transport key to equal the producer. Network BLS identity, transport Ed25519 identity and native/result signing keys are distinct concepts in the chain reference; its use of multiple types is not a Baton's key-binding policy. [Tempo transport Provider key](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/peer_manager/ingress.rs#L13), [Tempo chain network identity](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/network_identity.rs#L6).

## Buffer recipients and peer updates are distinct

`broadcast_shared` accepts explicit `Recipients`, enqueues work, and returns only mailbox Feedback. The buffer handles it by attempting a **local cache insertion** then calling the typed Sender; the Sender's returned recipient list is ignored. No propagation result receiver or automatic retransmit loop is supplied by this call. [buffer publication](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L237).

At the native pin, `Recipients::All` is expanded by the actual rate-limited channel's connected-peer snapshot. It is not automatically a validator committee/custody quorum and is not the buffer Provider's `latest.primary`. [connected snapshot expansion](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/limited.rs#L105). Recipient selection, peer membership and transport admission remain distinct.

The Provider's `latest.primary` controls the buffer's **residency**, not all delivery. Nonprimary senders may still satisfy current `subscribe` waiters, but their bytes are not retained as cache entries. Primary removal evicts their references unless another primary peer still references the same digest. Broadcast still attempts sending even if local insertion is ineligible. [notify before cache eligibility](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L301), [eligibility](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L327). Thus a publication accepted before the first peer update need not make a later `get` succeed; retain the existing archive-backed lookup contract. This is not a reason to add a native consensus readiness gate.

Generic resolver outbound fetches are restricted to its Provider's `latest.primary`, including explicit targets; inbound requests can be served for every connected peer. Already documented serving continuity across peer-set changes therefore applies independently from broadcast recipient expansion. [resolver selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L66).

## Existing network backpressure replaces a generic queue implementation

Native channel registration derives inbound capacity as configured retained-peer count × quota burst. Inbound connections share that bounded mailbox and drop arriving messages when it is full. Channel sender clones share a per-recipient quota; all channels share a pooled outbound router mailbox, so separate logical IDs do not imply physically reserved bandwidth or capacity. [network register contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L136), [capacity implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/channels.rs#L199).

Network start binds registered senders before spawning the network actor. Sends submitted before router binding are accepted and dropped; current Baton's startup already starts the network before body/native actor traffic and should preserve that order. [start and bind](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L192), [unbound messenger behavior](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/router/ingress.rs#L204). Network authentication authenticates/decrypts received frames, not application-context admissibility or retained custody. [received message contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/lib.rs#L34).

The buffer ingress Policy retains pending messages in an overflow deque, and its subscriptions/waiters can outlive fixed mailbox capacity. Generic resolver's serving-futures pool is unbounded and deliberately delegates concurrency limits to Producer. Do not claim a chosen `mailbox_size` is a whole application memory bound. These limits belong to existing open budgets and owner admission, without adding a cut/ACK wait. [buffer overflow](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/ingress.rs#L73), [resolver serve pool](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/engine.rs#L77).

For application result/report/tx receive loops that actually need parallel decode, existing public `WrappedBackgroundReceiver` supplies strategy-limited decode jobs, a bounded lossy decoded mailbox, automatic blocking on codec-invalid frames, and a Handle whose lifetime owns the task. It is a conditional reuse opportunity, not a required new module. It does **not** implement the raw Receiver required by buffered/resolver Engine, and these engines already perform their own typed wrapping. Do not insert it blindly ahead of them or use its codec failure policy to punish local storage/stale-context failures. [API and bounds](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L169), [Handle lifetime](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L220), [decode result policy](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L271).

## Proposed small documentation changes

1. **integration.md / source assembly:** name the native `Network::register(channel, quota)` signature and the stale three-argument example; make clear this example is a source wiring reference, not a verified build. This is an API correction, not a pin upgrade.
2. **block-body.md / final body size:** extend the existing encoded body budget to cover opaque resolver request/response envelope sizes and shared transport max; no numeric quotas, sizes or fragmentation choices.
3. **networking.md / reuse table:** record Network/Oracle/registered Sender+Receiver, Provider/Blocker clones, existing typed codec wrappers, and exact body/fetch start connections. Keep channel IDs and quotas blank where undecided.
4. **block-body.md / buffer details:** note explicit recipient selection/connected expansion vs latest-primary cache residency, local Feedback vs downstream attempted send, and retained archive fallback across initial/update events. No new acknowledgements or native startup gate.

The body format, key schema, routing/filtering choice, archive layout, transport/signature key binding, resource quota values and any retry/fragmentation policy remain undecided. No changes to Baton direction selection, no-wait cut, result certification, Executor/Storage ownership or native retention authority are proposed.
