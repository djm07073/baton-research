# Proposed narrow reader addition

Target: `docs/reference/verification.md`, immediately before its existing case table. Preserve every existing heading, case/status and diagram. Root's separate fixture audit can merge the Checkpoint/determinism paragraph; no other page change is needed from this audit.

**Use Commonware's existing deterministic runtime and simulated P2P for future E2E assembly.** Register native and application channels through `oracle.control(identity).register(channel, quota)`; the returned Sender/Receiver tuples use the same actor interfaces as deployment. Native Engine consumes four planes; full-body and Executor result transport use their separate application channels. Reuse the existing buffer/resolver/archive attachments and application contracts rather than building another transport or simulator. This is a source-grounded test plan; none of the following cases has been run.

| Existing assembly support | Reuse for future verification | Application boundary |
|---|---|---|
| `deterministic::Runner` + `simulated::Network/Oracle` | Seeded runtime, peer/channel handles, directed loss/latency links and bandwidth changes | Supply real TxPool/body/Orderer/Executor/Storage adapters; simulated transport does not exercise deployment handshake/discovery |
| Feature-gated `multimmit::mocks::cluster` | Complete native engine/journal startup, partitions, per-engine restart and native finality observation | Fixed MockApplication + NoopReporter; configured verification and a Relay that sends no body do not establish custody or application durability |
| Tempo E2E setup | Actual example of simulated consensus channels connected to a separate execution node | Tempo's Simplex/Reth registry graph is an assembly reference, not a directly compatible Baton/native harness |

Citations, with exact pins and independently checked anchors, are in `REPORT.md`: native Runner L541; simulated registration L421; native Engine start L688; native mock Cluster config L65 and attachment L302; Tempo setup L247 and channel wiring L352.

Retain a separate explanation that runtime audit/checkpoint scope and external worker/VM/I/O determinism differ from application state correctness. Native deterministic `Context::strategy` is a useful existing single-threaded Rayon strategy; independently constructed worker pools are outside that automatic determinism. No new Runtime trait, ACK gate, selected policy/limits/backend, implementation or executed result is implied.
