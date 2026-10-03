# Commonware integration and development order

**Start with the native example, then attach one application responsibility at a time.** This page maps existing Commonware code to the bridges needed for bodies, ordered delivery, execution, and Baton. The stages are a development plan, not implementation results.

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
| [QMDB Stateful](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/mod.rs) | Batch fork, merkleize, apply, pending-state management | Branch/canonical adapter for Multimmit exact execution order |
| [Cryptography](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs) | Namespace/message signing and verification primitives | ExecutionStatement encoding, epoch keys, signer/collector integration |
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
| 4 | Executor / Runtime / QMDB | Canonical ranges, result certification, Executor peer state sync, durable application |
| 5 | Baton candidate intake / parent-linked block requests | Exact-prefix reuse and suffix reexecution |
| 6 | Reports / Executor planning / direction | No reports, late reports, leader change, cut preemption |
| 7 | Native policy adoption / continuation / recovery | Selected-prefix inclusion, exact leading order, no-wait behavior |

Without stage-7 adoption and continuation proofs, advisory scheduling and protected-prefix Baton integration are different completion states. Choose test workloads after deciding application semantics. The plan does not prescribe building a Bank module first.

Stage 4 connects stage-3 canonical input directly through [Orderer → Executor::commit](../consensus/ordered-input.md#consensus-and-baton-integration). Stage 5 then adds candidate intake and speculative execution-tree branches. [Direct-result signing / collection / queries](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [Executor peer state sync](../e2e/state-sync.md#state-sync-from-certified-execution-results) also belong to stage 4 inside Executor, rather than result transport through Baton. Implement concrete signature boundaries, roots, codecs, and key bindings after reviewing their open decisions.
