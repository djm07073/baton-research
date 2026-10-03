# Block construction and body exchange

**BlockService connects producer bodies to Commonware's existing distribution, fetch and storage primitives.** It defines the body format, binds bytes to native context/header identity, and establishes durable custody. Executor decides application transaction outcomes during ordered execution. No new generic broadcast, cache or retry engine is needed.

## Interface overview

Implement existing Commonware Automaton, Relay, and Reporter directly over shared primitive handles. BlockService names that logical attachment; it does not require an additional public trait or separate actor. Slow storage/network work runs under attachment ownership outside synchronous Relay/Reporter callbacks.

Existing Rust callback signatures: [BlockService attachment](../overview/rust-interfaces.md#blockservice). The application-specific byte/context checks sit around those upstream calls.

## Reuse the same body components as Tempo

Tempo assembles `commonware_broadcast::buffered::Engine` in its consensus node and starts it on the body channel. It passes the buffer mailbox and a backfill resolver into Marshal, while its Executor is attached separately. Alto uses the same full-block buffer composition. These are concrete assembly examples, not merely a list of available crates. [Tempo buffer construction](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L207), [Tempo startup](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L526), [Alto assembly](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/engine.rs#L177).

For native Multimmit, copy the component composition and connect its existing callbacks:

| Native request or local need | Existing component to call | Adapter work |
|---|---|---|
| `Automaton::propose(Context)` | Selected TxPool, body codec, Archive write/sync | Build bounded bytes; bind producer parent/context; establish exact custody before digest success |
| `Relay::broadcast(digest, ())` | Retained-body lookup → `buffered::Mailbox::broadcast_shared` | Schedule lookup/publication and map digest to body; local feedback is not a peer ACK |
| `Automaton::verify(Context, digest)` | Archive lookup; buffer `get`/`subscribe`; generic resolver fetch | Validate exact requested bytes/context, required parents and covering durability |
| Missing body request | `commonware_resolver::p2p::Engine` with upstream Producer/Consumer | Producer reads archive; Consumer checks the key and hands validated bytes to custody processing |
| Accepted header + body available | Upstream `Reporter::report` plus local join | Match exact authenticated producer artifact/context to the retained body |
| Safe release | Existing Archive pruning | Native custody/history and local execution/query/sync references must permit release |

The buffer provides temporary local availability, not durable custody. Its `get`/`subscribe` do not start a peer request. Resolver already supplies requests, correlation, retry and subscriber cancellation; use it instead of another fetch engine. [Buffer mailbox](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/ingress.rs#L89), [generic resolver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/engine.rs#L36).

**Tempo's Marshal wrapper cannot be copied unchanged into Multimmit.** At the native pin, Marshal is Simplex-only and its Inline/Deferred wrappers require Simplex Context. Its specialized resolver initializer returns a bridge whose receiving methods are `pub(crate)`. Use the public generic resolver Engine with Producer/Consumer instead. Ordering interpretation remains Orderer's separate integration. [Marshal limitation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/mod.rs#L61), [Inline Context](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/standard/inline.rs#L223), [private handler receiver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/resolver/handler.rs#L118).

This assembly does not depend on `commonware_glue::stateful::Application`. Tempo's `commonware_consensus::Application` is a different interface. [Real-chain source/version mapping](../reference/integration.md#copy-the-assembly-from-real-chains) identifies the exact reference revisions.

The body type's upstream `Digestible::digest` supplies its content commitment. In `Automaton::propose`, build/select bytes for the supplied producer context, establish exact body/parent custody, then resolve the digest receiver. A definite build decline may close that receiver; temporary missing dependencies keep it pending. In verify, false is reserved for permanent invalidity of the expected payload. Missing bytes and bad peer responses trigger primitive lookup/fetch; local storage failure cannot become custody success. Do not map every error to receiver closure or false.

| Existing Commonware attachment | Direct body integration |
|---|---|
| `Automaton::propose` | Resolve the completed body's digest through the existing oneshot receiver |
| `Automaton::verify` | Resolve permanent validity/custody verdict through the existing bool receiver |
| `Relay::broadcast` | Schedule retained-body lookup and buffered publication; no peer custody ACK |
| `Reporter::report` | Admit the relevant accepted producer-artifact notice for joining; no slow fetch inside the callback |

Native publication Retire is not a Relay callback or archive-release permission. The native egress owner retains/retries its own artifacts until the matching native lifecycle retires them; that does not automatically provide a repeated body-broadcast service. Body publication/retry and retention integration remain adapter choices over existing buffer/resolver handles. Preserve native custody/history, worker/query/sync and serving references before release. Receiver timing and live closure follow the callback behavior below.

| Boundary | Existing API / proposed integration | Input → responsibility → output |
|---|---|---|
| Producer payload request | Existing `Automaton::propose(Context)` | Native producer parent/context → pool batch and body custody → payload digest |
| Payload verification | Existing `Automaton::verify(Context, payload)` | Payload reference → body/parent lookup, structural checks, durable custody → verdict |
| Body dissemination | Existing `Relay::broadcast` + adapter | Digest → owner-scheduled publication → Commonware broadcast / body P2P |
| Body ready | Proposed StoredBody | Exact-context body/parent custody → local attachment readiness |
| Candidate header observation | Existing `Reporter::report(Activity)` + adapter | Accepted TransactionBlock artifact → exact header reference for body join |
| Candidate execution delivery | Proposed CandidateBlock | Match authenticated header to exact body → Baton intake |
| Planning context | New native owner hook | Leader view / V-QC parent / history / frontier → read-only planning context |
| Policy adoption | New native policy hook | Prepared matching candidate → proposal-bound frozen policy |
| Canonical input delivery | New evidence export + ordered-delivery adapter | Exact authenticated evidence / policy history → Executor ordered range |

CandidateBlock requires authenticated correspondence to a producer header, not just a body digest. A locally built body whose header is still unsigned remains a local speculative candidate. An authenticated header also does not prove final cut inclusion. A node's AppliedCursor cannot replace the global frontier limiting reorderable input.

Existing `Activity::ProtocolAccepted` supplies an Arc of the exact authenticated artifact admitted into the contextually ready set. Ready here means native cryptographic/context admission, not completed body verification or native Retained completion. Reuse a shared attachment that extracts the header from TransactionBlock and joins it with StoredBody. Either event may arrive first; compare exact context, commitment, and header identity. [Accepted activity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/activity.rs#L1).

ArtifactId is a domain-separated hash of artifact kind and the full exact canonical artifact encoding. TransactionBlock encodes SignedTransactionBlock, so this ID differs from producer `header.block_ref`. [Artifact identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/admission.rs#L145).

Reporter is synchronous, and native dispatch ignores its Feedback. Forward work to the adapter owner rather than awaiting slow storage, fetch, or unlimited retry. Queue/budget policy remains open; the notice promises neither acknowledged retention nor lossless delivery. Missed observation is a pending/retry issue for opportunistic candidate intake, without adding a native ACK gate. Exact witness export and retention for canonical order are a [separate Orderer integration](ordered-input.md#consensus-and-baton-integration). [Reporter dispatch](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L1655).

Automaton callbacks return `oneshot::Receiver<Digest>` or `oneshot::Receiver<bool>` through a future. Unavailable dependencies keep the receiver pending. After resolution, native Core checks completion against request correlation.

A closed live propose receiver produces build completion without a commitment. For the current matching request this is a build decline and creates no header. A live verify receiver closure becomes `Fatal::Automaton` when consumed as a currently valid task completion; this differs from the invalid-payload verdict `verify(false)`. [Build completion](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L811), [Current build decline](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1187), [Live validation completion](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L848).

Producer Context supplies epoch, chain, height, and producer parent header ID. It does not supply leader V-QC or policy history. Public header construction/digest APIs can reconstruct an exact reference from Context and commitment. But propose, live verification, and recovery share the same Context without a callback mode tag: reconstructed metadata alone does not establish that a signed artifact is accepted/current. [Header reconstruction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L126).

## Select transactions and build a block

**Select candidates from the one chosen pool, then pack and retain one exact body.** Native producer Context supplies the producer-chain parent, not the canonical execution parent used by a nonce-aware pool. Preserve that context while applying selected payload-only filtering and complete body byte limits; no full Stateful/execution-dependent chain builder is required for this body attachment. [Pool-to-trait mapping](../tx/interfaces.md#connect-the-trait-to-one-existing-backend).

Count-based non-destructive selection may return the same candidates on refills. Keep selected IDs/order under bounded per-build ownership, exclude or re-evaluate dependent successors when a filter or capacity exclusion removes their predecessor, and retain the already selected bytes if a same-nonce candidate is replaced later. Reuse a compatible backend dependency iterator rather than another pool. Iterator exclusion and local cancellation do not canonically retire transactions; cross-producer duplicate execution semantics remain open. [Nunchi selection/replacement](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L108), [Reth iterator contract](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1109).

On `propose(Context)`, preserve the native-specified producer-chain parent and request a pool batch. Apply body codec, commitment, and limits; establish durable body and required-parent custody; return the digest. Native executor retains build job ID, generation, and parent and correlates completion. These tokens are not in Automaton Context, so the attachment has no assumed separate job-token API. [Build correlation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L683).

Producer-lane parent-state filtering cannot stand in for global canonical state. Stateful transaction success or failure is decided during actual ordered execution.

Transaction-byte budget differs from complete encoded body size. Bound the final body including framing and metadata, not only the transaction list.

The same body must also fit a **fetch response**, whose envelope is larger than raw body broadcast. At the native pin, generic resolver response size is `8 + 1 + body_bytes.encode_size()`: an eight-byte request ID, one-byte tag and Bytes encoding including its length prefix. Requests similarly add `8 + 1` to the key's encoded size. Use checked size arithmetic and the chosen public codecs; the resolver's wire Message type is private. The network already accounts for its own transport framing. [Resolver encoding](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/wire.rs#L109), [Bytes codec](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/types/bytes.rs#L23).

Allowing raw body bytes to consume the entire configured transport maximum can make that body's later fetch response oversized. The native Sender asserts its maximum payload size, so validate the whole envelope before serving it. Consumer also applies bounded application body decoding; the resolver's opaque Bytes bound does not choose tx-count, nested-object or validation-work limits. Limits and any fragmentation strategy remain open. [Sender maximum](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/channels.rs#L51).

Commonware [`EncodeSize::encode_size`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/codec.rs#L26) supplies the complete encoded-size calculation for the selected body type. [`Read::Cfg`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/codec.rs#L197) supplies type-specific decode limits on reception. Fields, versions, limits, and concrete codecs remain open and require application adapter integration.

## Body dissemination, lookup, and custody

Prefer Commonware storage/archive, `broadcast::buffered`, and `resolver::p2p`. Bounded broadcast cache does not replace durable custody. The attachment connects archive writes and sync completion, expected-digest checks, parent recovery, and startup order. [Broadcast](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/mod.rs), [Resolver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs).

| Existing primitive / API | Provides | Body adapter responsibility |
|---|---|---|
| Archive `put`, `get`, `sync` / `start_sync` | Buffered writes, key/index lookup, covering durable completion | Bind header ID to body commitment/context; establish body/parent custody and sync completion |
| `broadcast::buffered` cache lookup | Bytes for a recently cached digest, if present | Verify expected body; look up / promote durable archive content |
| Buffered broadcast subscription | Local waiter for a cache hit or future body | Distinguish subscription from active peer fetch |
| Generic resolver fetch / shared subscribers | Key requests, peer retries, shared subscribers | Exact-key Consumer verification, context correlation, pending wants/bytes/validation capacity |
| Existing `resolver::p2p::Producer` trait | Async application byte lookup for key requests | Archive-backed implementation, retention, request limits, storage-error handling |

Archive put success alone does not establish custody. Sync or the returned sync handle must complete and cover the exact expected bytes, while retention prevents their release during the verdict handoff. Ordinary immutable/prunable archives ignore writes at occupied indices; a prunable archive can also accept a below-floor put without storing it. Existing `marshal::store::Blocks` indexes finalized blocks by global height and digest. Reusing producer-lane height as a global index could collide across lanes and forks. Choose an injective schema or an explicitly suitable existing multi-index store, map header ID to digest, and verify exact retained presence rather than interpreting any successful put as a new stored body. The layout remains open. [Blocks contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L118), [Archive uniqueness](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/immutable/mod.rs#L6), [below-floor behavior](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/prunable/mod.rs#L97).

Resolver Consumer determines whether returned bytes match the peer-visible key. A key-valid body may still be irrelevant to a stale local subscriber or inadmissible for another context; those local dispositions are not peer invalidity. Wrong-digest/invalid peer response, subscriber cancellation and local archive-sync failure are distinct. Do not penalize peers for local storage failure or stale generation. A missing body keeps fetch/dependency work pending; it proves neither permanent payload invalidity nor an empty canonical slot. [Resolver delivery](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L149).

Canceling fetch may discard a subscriber result without rolling back custody writes. Storage ownership/completion lifetime is separate from subscriber cancellation. Archive mutation consumes and returns its handle; retain that ownership through completion under a storage owner. Existing combined put/sync helpers can reduce wiring without turning a no-op put into exact custody. Similarly, Blocks mutating calls consume the store; dropping a future or an error may lose its handle, and a failed sync handle prevents continued store use. This store has not been adopted unchanged. Review its [cancellation/storage contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L115) when connecting the adapter.

Targeted fetch does not automatically fall back outside selected targets. Outbound peers are selected from `latest.primary`, and targets cannot bypass that filter; the adapter must preserve serving feasibility as peer sets change. [Peer selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L64). Concurrent resolver fetch support does not bound application pending keys, subscribers, bytes, or validation work by itself. The owner separates native custody obligations from cancelable speculative subscribers. Concrete admission limits, retry, and targeting remain open.

Relay broadcast is synchronous. Forward slow archive lookup, fetch, and sync to the publication owner. Native dispatch defers an attempt on `Feedback::Closed` and otherwise attempts sending. This establishes no remote receipt or custody-quorum acknowledgement.

Native sender retries the same native artifact effect and encoded bytes even after a local sender accepts a request. Core issues Retire based on persisted successor state, removing that publication. This retry must not become a report/direction approval wait. [Relay dispatch](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L2286), [Retry ownership](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/egress.rs#L1).

Resolver retain selects pending fetch subscribers. Fetch completion/cancellation, native publication Retire, and archive release are separate lifecycles. Canceling a speculative subscriber or dropping cached bytes does not end native custody, recovery, or serving obligations. Relay has no retire callback: connect any required native lifecycle handoff explicitly. Tempo's Hybrid body store uses the execution backend's finalized watermark before evicting its hot archive; Alto retains finalized blocks in an immutable archive. Follow this handoff pattern only when Baton serving/retention obligations are met; neither is a selected storage layout. [Subscriber retention](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L216), [Tempo backend handoff](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/storage/hybrid/mod.rs#L360).

The [P2P message-plane table](../overview/networking.md#p2p-connections-and-message-planes) lists native/application planes and example channel IDs. Native data messages do not themselves distribute application bodies. Actual tx/body/report/direction channel IDs remain undecided. [Channel wiring](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L358).
