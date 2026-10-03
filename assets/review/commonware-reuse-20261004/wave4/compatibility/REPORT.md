# Wave 4: one native dependency graph, with ecosystem assembly references

Reviewed canonical Baton baseline `cd9a0864cfa2171769bbe7f6d64fa3396ca878c6`, following GitBook revision `GltIqzIYvnV8QtVLNNNH`. This is a source/API compatibility audit. No dependency, protocol, external checkout, canonical document, public trait or numeric/backend policy was changed. No native protocol compilation was run.

**Use the adopted native Commonware graph for network, buffer, resolver, cryptography and QMDB. Copy ecosystem wiring or adapt selected actor source into that graph; an unchanged release-dependent pool cannot simply consume native handles.** The fresh lockfiles establish a concrete compatibility obstacle beyond the already-documented database lifecycle difference.

## Concrete findings

1. Native pin `534af0ede48affd35b2111522527547b4cc9bf72` declares Commonware workspace packages at `2026.7.0`. Its implemented Multimmit is absent from the inspected `v2026.9.0` release tree. This is a source revision containing Multimmit, not permission to replace it with a registry package named `2026.7.0` or with the indexed release.
2. Nunchi, Tempo and Alto's pinned Cargo.lock files resolve their Commonware dependencies at **registry 2026.9.0**. Earlier “declares 2026.9.0” evidence can now be strengthened to actual lockfile resolution. It still proves neither registry payload equality with the inspected Git tag nor Baton's assembled build.
3. Native git/commonware and registry/Commonware types have different package identities. A native Sender, Runtime Context, codec trait implementation or SHA-256 digest does not become the release type by using the same import spelling or identical bytes. Identical buffer/network source is useful porting evidence, not a type bridge.
4. Resolver has an exact constructor difference: native `Config` requires `initial: Duration`; the indexed release removes it. Release `Blocker` also adds `blocked()`, absent from native. Reusing a release resolver configuration or a custom release Blocker implementation unchanged is unjustified.
5. Nunchi `Mempool::start_p2p` requires the actor's resolved Commonware Sender/Receiver and `T: Encode + Read<Cfg = ()>`. This fixes digest and decoder constraints more tightly than “generic actor” alone suggests. Its pool without P2P only requires PoolTransaction; use that distinction when assessing source adaptation.

## Revision and package identity receipts

| Component source | Declared/locked dependency identity | Meaning for Baton |
|---|---|---|
| Native monorepo pin | Workspace version `2026.7.0`; internal workspace path packages | Preserve exact git revision as baseline; a same-number registry crate is not equivalent |
| Indexed `v2026.9.0` monorepo | Workspace version `2026.9.0` | Source discovery/comparison only; no Multimmit module in this tree |
| Nunchi SDK `eea35ced709f68c15d6fbc8bcc754696a7e44374` | SDK packages `2026.9.0-alpha.1`; lockfile Commonware `2026.9.0` from crates.io | Whole actor source candidate, not unchanged native-crate interoperability |
| Tempo `61c979a524f9af5de9c540a0088c429a44741e4c` | Lockfile Commonware `2026.9.0` from crates.io | Copy composition; Simplex/Reth/runtime/types remain version-specific |
| Alto `1d87569348b5560699465a72d691d90f18affb9c` | Lockfile Commonware `2026.9.0` from crates.io | Copy handle startup/ownership recipe, not its whole consensus application |

Exact files: [native workspace](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/Cargo.toml#L63), [release workspace](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/Cargo.toml#L64), [Nunchi lock](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/Cargo.lock#L666), [Tempo lock](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/Cargo.lock#L3120), [Alto lock](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/Cargo.lock#L748).

Cargo version requirements, git sources and path sources are distinct dependency selection inputs. Two resolved library identities exposing similarly named types do not share those types. A patch is still subject to the requesting version requirement: a native package reporting `2026.7.0` cannot satisfy the SDK's `2026.9.0` minimum unchanged. Changing only a direct dependency may leave transitive codec/crypto/runtime/P2P packages split. A candidate source adaptation must reconcile the actor **and its dependent packages** onto one native graph; this report makes no manifest edit. [Cargo specifying dependencies](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#the-role-of-the-version-key), [Cargo incompatibility hazards](https://doc.rust-lang.org/cargo/reference/resolver.html#version-incompatibility-hazards), [Cargo patch requirements](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html#the-patch-section).

Manifests use ordinary caret requirements, whereas these checked-in lockfiles record the inspected resolutions. A future consumer importing an ecosystem package must not assume its dependency lockfile pins the consumer's whole graph; the actual consumer lock/source identities need checking. No claim is made about the currently installed registry package or future resolver output.

## Exact native assembly checklist

All items below use native-pin package definitions, not imports from a second release graph. This is a constructor/type-input checklist, not an executable implementation or selected config.

| Attachment | Existing public entry and required connections | Application input still needed |
|---|---|---|
| Authenticated network | `commonware_p2p::authenticated::discovery::Network<E,C>::new(context, Config<C>) -> (Network, Oracle<C::PublicKey>)`; `C: Signer`; runtime E satisfies Spawner, BufferPooler, Clock, CryptoRng, runtime Network, Resolver, Metrics | Signer/namespace, deployment endpoints and authorized peer/config policy; transport identity does not replace application signer eligibility |
| Logical channels | `Network::register(channel: Channel, rate: Quota) -> (channels::Sender<C::PublicKey,E>, channels::Receiver<C::PublicKey>)` | Channel IDs and quotas remain open; register before consuming Network in start |
| Body buffer | `commonware_broadcast::buffered::Engine<E,P,M,D>::new(context, Config<P,M::Cfg,D>) -> (Engine, Mailbox<P,M>)`; `M: Digestible + Codec`, `D: Provider<PublicKey=P>` | Native body codec/decode config, exact body digest and retained mapping; fields public_key, mailbox_size, deque_size, priority, codec_config, peer_provider |
| Body buffer channel | `Engine::start((impl Sender<PublicKey=P>, impl Receiver<PublicKey=P>)) -> Handle<()>` | Pass the raw registered pair; the engine wraps its own wire codec; body publication still needs recipients and custody integration |
| Generic fetch | `commonware_resolver::p2p::Engine<E,P,D,B,Key,Con,Pro,NetS,NetR>::new(context, Config<...>)`; Con: Consumer<Key=Key,Value=Bytes>, Pro: Producer<Key=Key>, Key: Span | Native archive-backed Producer, validating Consumer, exact peer-visible key; subscribers represent local interest and not peer validity |
| Generic fetch channel | `Engine::start((NetS,NetR)) -> Handle<()>`; both channel PublicKey=P; provider and blocker also use P; subscriber Clone+Ord+Send+'static | Native Config includes peer_provider, blocker, consumer, producer, mailbox_size, me, **initial**, timeout, fetch_retry_timeout, priority_requests, priority_responses; no numerical values selected |
| Execution drafts/storage | `commonware_glue::stateful::db::{Shared,DatabaseSet,ManagedDb,Unmerkleized,Merkleized}` with selected concrete Any/Current wrappers | Runtime E and concrete DB bounds; explicit reverse type equality for generic sealing; tuple component sealing; rootless access adapter and canonical authority remain application contracts |
| Tx actor source candidate | Nunchi `Mempool<T>::new(PoolConfig) -> (Mempool<T>,MempoolHandle<T>)`, then start(context) or start_p2p(context,pair) | Fit workload and source-package adaptation; custom PoolTransaction implementation, canonical nonce/outcome/restart/packing integration remain unresolved |

Native signatures: [network constructor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L67), [register](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L169), [buffer bounds/new](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L44), [buffer Config](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/config.rs#L6), [resolver bounds/new](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/engine.rs#L36), [resolver Config](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/config.rs#L9), [DB projections](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L341).

The Producer method is `produce(&mut self, key) -> oneshot::Receiver<Bytes>`. Consumer delivery receives `Delivery<Key,Subscriber>` and Bytes, returning a receiver of its Outcome. Constructor bounds impose Subscriber ordering in addition to the Consumer trait's clone/equality/send requirements. Reuse those correlation/serve/validation mechanisms rather than writing another request engine. Native Resolver E additionally requires runtime Rng. Source: [Producer](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L100), [Consumer](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L149).

## Digest, codec and peer identities

Native `Digestible::Digest` and `Hasher::Digest` refer to the native cryptography Digest trait. A body buffer's cache key is its actual `M::Digest`; it must join the intended native payload digest. Generic resolver Key can be another Span representation, but its exact identity mapping remains explicit. Do not silently cast same-length hashes or identify transaction ID, body ID, history commitment and execution root merely because all may use SHA-256 bytes. Execution root choice remains open and need not be the payload hash algorithm.

Nunchi's PoolTransaction returns the concrete `commonware_cryptography::sha256::Digest` from **its graph**, not a generic Hasher projection. Its custom NonceKey is independent of the network PublicKey type. Its P2P bounds require the channel pair to agree on PublicKey; they do not require transport identity to equal an account signer. Default Nunchi Transaction semantics bring its own Address, signature curves and domains; custom PoolTransaction avoids those application assumptions but still lives in the actor's package graph. [PoolTransaction](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/tx.rs#L34), [native digest projections](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs#L221).

`start_p2p` has this exact additional constraint:

```rust,ignore
E: Spawner + RuntimeMetrics,
S: Sender + 'static,
R: Receiver<PublicKey = S::PublicKey> + 'static,
T: Encode + Read<Cfg = ()>,
```

[Source](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L292). A payload requiring `Read<Cfg=Bounds>` cannot be passed unchanged to this entry. One candidate is a bounded ingress attachment driving start/submit through the existing actor; another is source-adapting the actor to carry selected decode config. Neither option is adopted. Unit config does not prove bounded decoding; the custom Read implementation and complete wire maximum still need verification. Buffered body and generic resolver engines should receive raw native channel pairs instead of externally prewrapped typed receivers.

Nunchi mempool also depends on nunchi-common and nunchi-crypto even for a custom PoolTransaction. nunchi-common's default `state` feature pulls Commonware glue/runtime/storage/parallel/utils. Therefore “pool only” does not imply a graph with only a queue and P2P. Source adaptation may assess whether unnecessary default state dependencies can be disabled, but this audit changes no features and requires no SDK chain builder/Application lifecycle. [Mempool dependencies](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/Cargo.toml#L10), [Common default state feature](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/common/Cargo.toml#L10).

## Native versus release deltas relevant to porting

[Source comparison](source-comparison.json) and `diffs/` retain the fresh inspected comparisons. Native discovery network and buffered Engine/Config files are byte-identical to the indexed release in this sample; the module docs and package graphs still differ. This supports copying the existing body constructor wiring. It does not establish whole release compatibility.

Generic resolver differs materially. Native Config contains `initial`, consumed by the Fetcher constructor. Release Config removes that field. Release P2P Blocker gains `blocked()` and resolver subscribes to that set; native's trait contains only block. A release actor/custom provider copied wholesale must be adapted to the native definitions. [Native Config](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/config.rs#L38), [release Config](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/resolver/src/p2p/config.rs#L35), [native Blocker](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/lib.rs#L375), [release Blocker](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/p2p/src/lib.rs#L380).

Codec release adds mode helpers and other runtime implementation files differ. Crypto SHA-256 digest computation differs internally but uses the same public form in the inspected source. None removes Rust package identity constraints or supplies an automatic cross-version conversion. Existing native/release QMDB lifecycle differences from wave3 remain mandatory: native finalize(batch), release apply(batch) then finalize(). A source package rebased to native must use the native sequence.

## Minimal realistic reuse path and reader changes

Use a coherent native-revision graph for Multimmit plus its existing network, broadcast, generic resolver, storage and crypto/runtime crates. Adapt real-chain body startup/handle ownership to those native constructors, preserving the existing native semantics and custody/dense-order gaps. This requires no new network or broadcast/fetch engine and no release upgrade. Tempo/Alto's Simplex Marshal wiring remains an assembly reference rather than a Multimmit adapter.

Assess Nunchi's **whole pool actor source** as one backend candidate after workload fit. Reconcile its direct/transitive Commonware imports and constructor calls to native as a bounded source adaptation, rather than importing a release actor and building a parallel native pool around it. A release-isolated component with an explicit byte/application bridge is possible in principle but supplies no unchanged native handle reuse; it is an alternative to evaluate, not this report's recommended default or a second engine requirement. Registry artifact availability/maturity and actual type compatibility still require later verification.

Suggested focused edits:

1. In integration.md's version section, state the native workspace identity and the three actual release registry lock resolutions, plus the practical public-type boundary. Add the native `initial` / release `blocked()` delta as a short exact API example. Keep no dependency upgrade adopted.
2. In the Nunchi recipe, qualify “whole actor candidate” as source adaptation onto the native graph, and spell out fixed SHA-256 plus unit-config P2P decoding. Preserve canonical outcome/restart/packing gaps and blank backend policy.
3. In rust-interfaces.md's introductory compatibility note, state that associated-type equality must be between types from the same resolved upstream graph, not only the same type name. Keep the five declarations unchanged. Application root/input/codec choices stay separate from this package-coherence requirement.

## Evidence and limits

[Source manifest](source-manifest.json) records fresh raw downloads, SHA-256, Git blob hashes and comparison to five pinned repository-tree receipts. Successful source contents were checked rather than inferred from inventory. Exploratory 404s are retained as failures: release Multimmit and the incorrect codec/src/types.rs guesses. Correct codec definitions were subsequently retrieved from codec/src/codec.rs. Official Cargo documentation was read directly for resolver/source/patch semantics; source-code claims above use pinned raw snapshots.

This does not prove any native build, registry-to-tag equivalence, selected backend, protocol integration, result safety or performance. Constructor fields and associated-type requirements supply a future compilation checklist. No new public traits/methods, cryptographic scheme, numeric limits, nonce policy, storage variant or signing boundary was selected. Exact execution/provenance/root-before-sign, clone-wide access validity, durability linkage and no-wait cut requirements remain unchanged.
