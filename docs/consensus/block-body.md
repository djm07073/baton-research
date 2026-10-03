# Block construction and body exchange

**BlockService supplies the bytes behind a producer commitment.** It builds transaction bodies, retains durable custody, distributes them, and fetches missing content. Executor decides application transaction outcomes during ordered execution.

## Interface overview

Keep existing Commonware Automaton, Relay, and Reporter. Do not recreate them as a separate Consensus trait. BlockService is the application trait that supplies real bodies to their callbacks.

Rust declaration: [BlockService](../overview/rust-interfaces.md#blockservice). Its method arguments and return types define the input/output boundary; the Rust interfaces page owns the complete declaration.

`commitment(&StoredBody) -> Digest` exposes the digest bound to a verified retained body. The native adapter passes it to the existing propose receiver. `build(ProducerContext)` returns `Some(StoredBody)` only after durable custody of the body and required parents and commitment binding are established. `None` is a definite build decline; temporary missing dependencies keep the future/native receiver pending. `verify(false)` is reserved for permanent invalidity of the expected payload. Missing bytes and bad peer responses trigger fetch/retry; storage failures cannot produce custody success. Do not map every Error to receiver closure or false.

| Existing Commonware attachment | BlockService integration |
|---|---|
| `Automaton::propose` | Deliver the completed build's commitment through existing `oneshot::Receiver<Digest>` |
| `Automaton::verify` | Deliver the custody/validity verdict through existing `oneshot::Receiver<bool>` |
| `Relay::broadcast` | Schedule local publication via publish; this is not remote receipt or a custody ACK |
| `Reporter::report` | Hand accepted artifacts to local intake for joining with StoredBody; do not await slow fetch inside the callback |

Retire is a proposed attachment handoff from the matching native lifecycle; existing Relay has no assumed retire callback. Successful publish establishes local scheduling, not delivery. Publication retries remain active until matching native Retire. `on_retire` does not release the body archive. Release must account for custody, history, and serving references under the open storage/retention contracts. Receiver timing and live closure follow the existing callback behavior described below.

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

On `propose(Context)`, preserve the native-specified producer-chain parent and request a pool batch. Apply body codec, commitment, and limits; establish durable body and required-parent custody; return the digest. Native executor retains build job ID, generation, and parent and correlates completion. These tokens are not in Automaton Context, so the attachment has no assumed separate job-token API. [Build correlation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L683).

Producer-lane parent-state filtering cannot stand in for global canonical state. Stateful transaction success or failure is decided during actual ordered execution.

Transaction-byte budget differs from complete encoded body size. Bound the final body including framing and metadata, not only the transaction list.

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

Archive put success alone does not establish custody. Sync or the returned sync handle must complete and cover accepted writes. Existing `marshal::store::Blocks` indexes finalized blocks by global height and digest. Reusing producer-lane height as a global index could collide across lanes and forks. The selected adapter must map native header ID to body digest and choose a store layout. [Blocks contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L118), [Archive uniqueness](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/immutable/mod.rs#L6).

Resolver Consumer determines whether returned bytes match the key. Wrong-digest/invalid peer response, cancellation by a waiting subscriber, and local archive-sync failure are distinct. Do not penalize peers for local storage failure or stale generation. A missing body keeps fetch/dependency work pending; it proves neither permanent payload invalidity nor an empty canonical slot. [Resolver delivery](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L149).

Canceling fetch may discard validation results without rolling back application custody writes. Storage mutation/completion lifetime is separate from subscriber cancellation. For example, Blocks mutating calls consume the store; dropping a future or an error may lose its handle, and a failed sync handle prevents continued store use. This store has not been adopted unchanged. Review its [cancellation/storage contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L115) when connecting the adapter.

Targeted fetch does not automatically fall back outside selected targets. Outbound peers are selected from `latest.primary`, and targets cannot bypass that filter; the adapter must preserve serving feasibility as peer sets change. [Peer selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L64). Concurrent resolver fetch support does not bound application pending keys, subscribers, bytes, or validation work by itself. The owner separates native custody obligations from cancelable speculative subscribers. Concrete admission limits, retry, and targeting remain open.

Relay broadcast is synchronous. Forward slow archive lookup, fetch, and sync to the publication owner. Native dispatch defers an attempt on `Feedback::Closed` and otherwise attempts sending. This establishes no remote receipt or custody-quorum acknowledgement.

Native sender retries the same effect and encoded bytes even after a local sender accepts a request. Core issues Retire based on persisted successor state, removing that publication. This retry must not become a report/direction approval wait. [Relay dispatch](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L2286), [Retry ownership](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/egress.rs#L1).

Resolver retain selects pending fetch subscribers. Fetch completion/cancellation, native publication Retire, and archive release are separate lifecycles. Canceling a speculative subscriber or dropping cached bytes does not end native custody, recovery, or serving obligations. Retention/release must account for body/history references and durable handoff; concrete choices remain open. [Subscriber retention](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L216).

The [P2P message-plane table](../overview/networking.md#p2p-connections-and-message-planes) lists native/application planes and example channel IDs. Native data messages do not themselves distribute application bodies. Actual tx/body/report/direction channel IDs remain undecided. [Channel wiring](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L358).
