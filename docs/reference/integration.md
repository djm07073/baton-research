# Commonware integration and development order

**Start with the native example, then attach one application responsibility at a time.** This page maps existing Commonware code to the bridges needed for bodies, ordered delivery, execution, and Baton. The stages are a development plan, not implementation results.

## Copy the assembly from real chains

**Reuse the existing engines and add only the connections whose semantics differ.** Tempo and Alto show body propagation assembled from Commonware handles. Constantinople supplies a real pool and staged state computation. These references explain where to put primitives; they do not select Baton's workload or replace Multimmit with Simplex.

| Reference and inspected source | Component composition | Baton reuse recipe |
|---|---|---|
| [Tempo consensus engine](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L207) | Buffered full-block broadcast, Marshal/backfill resolver, reporters and a separate execution attachment | Reuse generic buffer + resolver + archive; connect native Automaton/Relay/Reporter directly |
| [Alto chain engine](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/engine.rs#L177) | Full-block buffer, Deferred wrapper, immutable finalized archives | Copy handle ownership/startup composition; preserve Multimmit custody and order semantics |
| [Constantinople pool](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L402) | Bounded queues, local digest dedup, byte packing, proposal/status tracking | Assess whole package first; adapt fixed tx/context and destructive selection/canonical outcome coupling |
| [Nunchi pool](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L258) | Public generic nonce-lane actor, non-destructive selection and Commonware P2P | Whole-actor candidate for matching SHA-256/nonce payloads; adapt byte packing, canonical refresh/restart and bounded ingress |
| [Tempo node](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/node/src/node.rs#L772) | Reth pool, transaction network, maintenance and execution-aware payload builder | Whole-stack candidate only for an explicitly Ethereum-compatible backend; generic txs do not fit unchanged |
| [Constantinople execution](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/application/src/consensus/execution.rs) | Staged application computation, then state/history Merkleization | Executor emits changes; Storage performs selected preparation/root computation using QMDB |

### Body assembly to implement

1. Create the existing authenticated network; register logical body-distribution and fetch channels before starting it. At the native pin use `Network::register(channel, quota)`, not the stale three-argument example call. Use the chosen revision's exact configuration/types and complete wire-message size bounds.
2. Construct `commonware_broadcast::buffered::Engine`; share its Mailbox with the body attachment. It provides dissemination/cache/availability subscription, not durable storage or active missing-body fetch.
3. Construct public `commonware_resolver::p2p::Engine` with archive-backed Producer and verifying Consumer. Use its keyed fetch, peer retry and subscriber lifecycle.
4. Open existing archives and connect exact body/header/context lookup, covering sync and reference-aware retention. `Automaton::propose/verify` complete only at the required custody boundary.
5. Implement `Relay::broadcast(digest, ())` by scheduling retained-body lookup and `buffered::Mailbox::broadcast_shared`. Implement Reporter for opportunistic accepted-header/body joining. Orderer's durable evidence export remains separate.

That is the minimal BlockService role: codec/construction, identity/context checks, custody and retention glue. It does not require a second public body trait, a new generic fetch/broadcast engine or a new actor for each task. [Detailed body contracts](../consensus/block-body.md#reuse-the-same-body-components-as-tempo).

**Do not copy Marshal unchanged.** The adopted native Marshal is Simplex-only, and standard Inline/Deferred require Simplex Context. Its specialized resolver receiving bridge has crate-private methods. Reuse the generic resolver underneath it, not an inaccessible receiver loop. Tempo's Hybrid archive also depends on its execution backend's finalized watermark before hot-cache eviction; that is a retention-handoff example, not an automatic Baton GC rule. [Native Marshal limits](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/mod.rs#L61), [resolver receiver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/resolver/handler.rs#L118), [Tempo retention](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/storage/hybrid/mod.rs#L360).

### Pool and storage assembly to evaluate

Keep TxPool as the application admission/selection/static-policy seam in front of a selected backend. Do not build another pool beside a reused one. Constantinople's HTTP admission and fixed types are not a generic tx gossip protocol; a new ingress bridge must perform its own bounded decoding, subject/signature checks and identity alignment. Reth offers a larger complete pool/network/maintenance surface but brings Ethereum assumptions. [Candidate comparison and lifecycle](../tx/README.md#reuse-an-existing-pool-without-importing-the-wrong-lifecycle).

For a custom SHA-256 nonce-lane workload, Nunchi offers a generic whole actor and Commonware P2P entry. Use its actual admission and non-destructive pending APIs, then connect linked durable Executor outcomes to reconciled nonce cleanup. Its fire-and-forget finalized notification, restart hydration, decode bounds and count-only selection need explicit integration. Do not adopt its chain builder's execution/merkleization lifecycle just to reuse its pool. [Nunchi connection](../tx/README.md#nunchi-whole-actor-connection).

Use QMDB unmerkleized/sealed batches and database lifecycle directly beneath Storage. Do not require `glue::stateful::Application`: Executor returns completed effects, Storage prepares the selected commitment, then Executor may sign the full result. Rootless parent branching needs an application effects/read adapter; built-in `fork_batches` requires a sealed parent. Storage owns canonical access/flush/recovery; Executor owns exact input selection, certification, peer sync and delivery ACK. [Versioned storage recipe](../execution/qmdb.md#existing-apis-at-the-native-pin-and-indexed-release).

Use public Shared-backed Any/Current wrappers for concrete branch reads/writes when that variant fits. Unsealed drafts are one-shot; preserve required exact effects before consuming them. Tuple batches need per-component sealing, and generic single-DB preparation needs the explicit reverse associated-type equality. Existing concrete validate_batch checks ancestry/floor applicability under the same canonical authority, alongside application checks. [Concrete batch connections](../execution/qmdb.md#give-executor-concrete-branch-access).

### Orderer assembly

Reuse native Scheme verification and public Tally body opening, ViewProof/TipRecord codecs, archive gap tracking and generic resolver. Keep original witness versions using the selected Archive/MultiArchive schema. Use existing Journal replay and Metadata for local delivery/cursor records; their durability does not form an automatic transaction with QMDB. Only native-selected witness handoff, private tip extraction access and exact policy/order interpretation require the native/application bridge. [Proof and storage recipe](../consensus/ordered-input.md#reuse-proof-verification-and-storage).

### Reference versions are not one compatible dependency graph

| Source | Inspected revision | Compatibility scope |
|---|---|---|
| Native Commonware baseline | `534af0ede48affd35b2111522527547b4cc9bf72` | Adopted Multimmit pin; implementation API baseline |
| Commonware MCP | Explicit `v2026.9.0`, server `0.0.5` | Discovery/corroboration; different database apply/finalize API |
| Tempo | `61c979a524f9af5de9c540a0088c429a44741e4c` | Uses Commonware `2026.9.0`; Reth `038edab20dfff017f7a7502e683c732e5628ad89` |
| Alto | `1d87569348b5560699465a72d691d90f18affb9c` | Uses Commonware `2026.9.0`; Simplex assembly reference |
| Constantinople | `3b6c92e76bf582855615844a4175b8304808f6a9` | Uses Commonware `92036f4beefedc9817f0954d98fb99e0b52431cb`; historical source example |
| Nunchi SDK | `eea35ced709f68c15d6fbc8bcc754696a7e44374` | Declares Commonware `2026.9.0`; generic pool actor reference, not a confirmed registry artifact or native-pin build |

These are pinned source inspections, not a compiled Baton assembly or a production/maturity assessment. Check selected imports/signatures against the adopted dependency graph before reuse. A successful MCP response is not source evidence if it contains homepage HTML or a guessed nonexistent path. [Tempo dependencies](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/Cargo.toml#L255), [Alto dependencies](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/Cargo.toml#L23), [Constantinople dependencies](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/Cargo.toml#L51).

## Commonware integration anchors

All native links are pinned to commit `534af0ede48affd35b2111522527547b4cc9bf72`. New bridges in the table are proposed contracts that still need implementation.

Assembly starts at log-multimmit/main.rs. The example creates commonware_runtime::tokio::Runner, then registers authenticated discovery Network and native logical channels in its context. It passes Application as Automaton/Relay and configures Rayon crypto strategy, profile, and committee in EngineConfig. Startup runs network.start → engine.start → running.ready. Baton integration first prepares body services under the [startup sequence](../e2e/recovery.md#startup-prepare-custody-before-native-recovery), then connects application planes and execution. [Runtime / network assembly](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L293).

The example derives an ordinary BLS roster and separate DA/nullification threshold sharing from mock seeds. This is example key setup, not an adopted production setup. Transport identity, native signing domains, and application tx/result signature domains are not assumed to share one key or namespace. [Example keys](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L17).

| Anchor | Reuse | Adapt / implement |
|---|---|---|
| [Example main](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L358) | Runtime, committee, authenticated network, channels, Engine wiring | Start tx/body/report/direction channels and Baton/execution tasks |
| [Example Application](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/application/actor.rs#L40) | Automaton/Relay boundaries and Reporter wiring | Replace mock callbacks with pool/body/custody adapters; reuse Reporter for candidate intake |
| [Native view owner](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L1269) | Actual leader proposal context and native authority | Read-only planning-context export and prepared-result correlation |
| [Leader block](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L563) | LeaderBlock structure and canonical codec | Frozen policy binding, proposal validity, recovery integration |
| [Finality owner](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs) | Exact native facts and authentication provenance | Resumable evidence export, retention handoff, history backfill |
| [Native tip algebra](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143) | Extraction and settledness rules | Verified shared extraction facade and continuous ordered delivery; address private API access |
| [QMDB / Stateful reference](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/mod.rs) | Reuse lower-level DB/batch APIs; inspect actor lifecycle as a reference | Executor/Storage exact-input adapter; no dependency on full Stateful/Application; sealed-parent forks differ from rootless views |
| [Cryptography](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs) | Namespace/message signing and verification primitives | Executor statement encoding, epoch keys, signing and collection |
| [Codec](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/lib.rs) | Write, Read, EncodeSize APIs | Schema, version, and limits for tx/body/report/direction/result |

#### Source reading order

Source exploration differs from development order. First understand the flow owned by upstream, then implement application/Baton attachments.

Start with [pool reuse candidates](../tx/README.md#roles-and-responsibilities) for transaction storage/selection and [body primitives](../consensus/block-body.md#body-dissemination-lookup-and-custody) for storage, distribution, and fetch. Then connect the native callbacks in the order below.

The pinned [reshare validator assembly](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/reshare/src/validator.rs#L122) illustrates handles passed to resolver, buffer, archives, Marshal, Stateful, and application wrappers in one file. Its Simplex [Deferred wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/standard/deferred.rs#L488) returns a digest before durability and waits at a separate certify gate. It is not an unchanged adapter for native Multimmit producer Context, custody/signing, and recovery.

| Order | Source entry | What to understand |
|---|---|---|
| 1. Node assembly | [log-multimmit main.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs) | Where channels, application, and Engine config connect |
| 2. Native startup / recovery | [Engine::start](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs) | Why journal replay and recovered-payload verification precede actor startup |
| 3. Wire → observation → verification | [Wire](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/wire.rs), [Batcher](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/batcher/mod.rs) | Untrusted observation versus owner-issued verification completion |
| 4. Native state owner | [Machine ownership](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/mod.rs), [Voter executor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs) | Authority over semantic state versus execution of async jobs |
| 5. Producer / leader | [Chain](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs), [View](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs) | Payload build callbacks versus multi-lane cut construction |
| 6. Native output boundary | [Finality](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs), [State machine](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md) | Evidence that must be exported/retained to recover continuous order |
| 7. QMDB internals | [Lifecycle](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/mod.rs), [Batch chain](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/batch_chain.rs) | Pending checkpoint, actual DB ancestor, operation commitment |
| 8. Apply / durability | [DatabaseSet / Barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs), [Stateful processor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/actor/processor/mod.rs) | Readable callbacks versus flush ACKs and added Executor obligations |

## Development stages and validation flows

| Stage | Integration to develop | Lifecycle to validate |
|---|---|---|
| 1 | Pin existing Multimmit example and dependencies | Native producer / DA / consensus |
| 2 | TxPool / BlockService | Tx admission and body exchange, without requiring an application runtime |
| 3 | Orderer / native evidence export | Sparse native finality → continuous exact input; gap backfill |
| 4 | Executor / Storage over QMDB | Completed effects, selected roots before signing, canonical ranges, result certification, peer sync and durable application |
| 5 | Baton candidate intake / parent-linked block requests | Exact-prefix reuse and suffix reexecution |
| 6 | Baton reports / candidate selection / direction | No reports, late reports, leader change, cut preemption |
| 7 | Native policy adoption / continuation / recovery | Selected-prefix inclusion, exact leading order, no-wait behavior |

Without stage-7 adoption and continuation proofs, advisory scheduling and protected-prefix Baton integration are different completion states. Choose test workloads after deciding application semantics. The plan does not prescribe building a Bank module first.

Stage 4 connects stage-3 canonical input directly through [Orderer → Executor::commit](../consensus/ordered-input.md#consensus-and-baton-integration). Stage 5 then adds candidate intake and speculative execution-tree branches. [Direct-result signing / collection / queries](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [Executor peer state sync](../e2e/state-sync.md#state-sync-from-certified-execution-results) also belong to stage 4 inside Executor, rather than result transport through Baton. Implement concrete signature boundaries, roots, codecs, and key bindings after reviewing their open decisions.

## Primitive reuse catalog

**Prefer an existing primitive before writing a generic service.** The application traits describe responsibility boundaries; they do not prescribe separate implementations of networking, retry, storage or cryptography.

Primitive discovery used the public [Commonware library MCP](https://mcp.commonware.xyz), server `commonware-library` version `0.0.5`, with an explicit `v2026.9.0` source version. `list_versions`, `list_crates`, `get_file` and focused `search_code` queries supplied the inventory below. The adopted native Multimmit source remains pinned to `534af0ede48affd35b2111522527547b4cc9bf72`. A Multimmit search in the indexed release returned no matches; this is a limit of that release inventory, not a reason to replace the native engine.

| Layer | Preferred building blocks | Compatibility / custom boundary |
|---|---|---|
| [Transaction](../tx/README.md#commonware-primitives-in-the-transaction-layer) | Actual pool backend where compatible; authenticated P2P/buffer/resolver, codec, crypto, runtime/actor | Fixed workload/lifecycle adaptation and static routing/filtering; a queue/provider alone is not a pool |
| [Consensus](../consensus/README.md#commonware-primitives-in-the-consensus-layer) | Pinned Multimmit callbacks; buffered broadcast, archive, journal, metadata and resolver | Body/custody integration and exact merged-order delivery need adapters |
| [Baton](../baton/README.md#commonware-primitives-in-the-baton-layer) | Existing P2P, crypto, codec, clock/task infrastructure; optional parallel work | Report rules, direction selection and protected-prefix adoption are custom |
| [Execution](../execution/README.md#commonware-primitives-in-the-execution-layer) | Lower-level QMDB/DatabaseSet lifecycle, crypto, collector, resolver and QMDB sync | Executor/Storage binding, deferred-root views, f+1 semantics and normal-path validator switching are custom |

### Source evidence from the indexed release

| Source | What was verified |
|---|---|
| [Collector traits](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/collector/src/lib.rs) and [P2P collector](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/collector/src/p2p/mod.rs) | `Originator::send/cancel`, `Handler::process`, `Monitor::collected`, P2P Engine/Config/Mailbox; request and response share commitment/digest types |
| [Buffered broadcast](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/broadcast/src/buffered/mod.rs) | Broadcast, bounded per-peer cache and on-demand cached retrieval; Engine/Mailbox exports |
| [Resolver](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/resolver/src/lib.rs) and [P2P resolver](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/resolver/src/p2p/mod.rs) | Producer/Consumer verification boundary, retries, targeted and subscriber-aware fetch lifecycle |
| [Stateful](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/mod.rs) | Sealed pending-parent forks, compute/merkleize lifecycle and one-time bootstrap sync; reference only, not an adopted Application dependency |
| [Storage inventory](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/lib.rs) | QMDB, queue, archive, journal and metadata modules; this inventory alone does not establish a complete mempool |
| [P2P interfaces](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/p2p/src/lib.rs) | Shared authenticated network and sender/receiver abstractions; local send feedback does not guarantee remote delivery |

Before adopting a candidate, check that it exists at the chosen dependency revision, inspect its concrete trait bounds and wire/storage behavior, and validate the adapter against native Multimmit contexts. If it requires a dependency change, document that change and revalidate native compatibility first. Do not mix the indexed release and native pin into an assumed compatible build. Existing source-pinned links above remain the implementation baseline; MCP discovery is additional design evidence.
