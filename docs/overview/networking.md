# P2P and message paths

**Commonware P2P carries the messages between nodes.** Logical channels separate transactions, bodies, native consensus, Baton scheduling, and execution results while sharing the same network.

## P2P connections and message planes

| Plane | Participants | Payload | Channel ID |
|---|---|---|---|
| Native data | Native peers | `DataMessage::Block / DaVote / DaCertificate` | Existing example: `0` |
| Native consensus | Native peers | `ConsensusMessage::Proposal / Vote / NoVote / Nullify` | Existing example: `1` |
| Native certificates | Native peers | `CertificateMessage::Nullification / Vqc / Lqc` | Existing example: `2` |
| Native resolver | Native peers | Native view proofs and recovery material | Existing example: `3` |
| Application tx | Tx peers, admission adapter, producer pool | Transaction bytes / inventory; concrete format undecided | |
| Application body | Body store / resolver peers | Body bytes and fetch responses for exact references | |
| Baton report | Validator Baton ↔ leader Baton | Window announcement / signed intended-order report | |
| Baton direction | Leader Baton → producer / executor Baton | Advisory direction | |
| Execution result / state sync | Validator Executor ↔ Executor; query consumer → Executor | Exact statement signatures, result certificates, change sets, queries, and retries | |

Additional planes can use logical channels on the same Commonware network. The design does not require a new physical connection or a separate P2P stack per plane. Transport authentication and message-context verification are separate responsibilities. Transactions, bodies, and reports still compete for CPU, queues, and bandwidth. A logical no-wait rule does not guarantee physical resource isolation. Runtime placement and quotas remain undecided.

## Reuse the existing network handles

**Register channels once, then pass their handles to existing engines.** At the native pin, `discovery::Network::register(channel, quota)` returns a Sender/Receiver pair. Register all channels before starting the network. The pinned log-multimmit example still passes a third `256` argument; use the actual two-argument primitive signature when adapting that wiring reference. This is a source mismatch, not a recorded compiler result or a reason to change the native pin. [Network API](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/network.rs#L169), [example calls](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L366).

| Connection | Existing handle or API | Application responsibility |
|---|---|---|
| Body broadcast channel | `buffered::Engine::start((sender, receiver))` | Body codec/config, retained body mapping and recipients |
| Missing-body/history channel | `resolver::p2p::Engine::start((sender, receiver))` | Archive-backed Producer, verifying Consumer and exact request keys |
| Peer discovery/availability | Network Oracle, Provider and Blocker | Use the tracked peer set appropriate for serving; no separate peer-discovery actor is required just to connect engines |
| Typed application messages | `p2p::utils::codec::wrap` | Supply tx/report/direction/result schemas, decode limits and subject verification |

Both ends of a channel and the consuming engine must use the same authenticated public-key type. A relay peer can serve a body authored by another producer. Transport peers, currently connected recipients and eligible execution-result signers are different sets; verify author/committee membership in the signed application subject. An Oracle clone supplies transport services, not trusted epoch-signing provenance. [Typed channel wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L16).

Buffered broadcast and resolver already wrap their own wire types. Pass them raw registered channel pairs. For an application receive loop that needs parallel decoding, the existing `WrappedBackgroundReceiver` is a conditional option; it is not the raw Receiver these engines expect. Its decoded mailbox is bounded and lossy, and codec-invalid frames can trigger peer blocking. Local storage failure or stale context must not be treated as a codec-invalid peer response. [Background receiver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L169).

Bound the complete encoded application message, including fetch response framing, against the transport maximum. A configured mailbox size alone does not bound pending subscribers, queued overflow or concurrent serving work. Numeric limits, targeting and runtime placement remain open. See [body wire budgets](../consensus/block-body.md#select-transactions-and-build-a-block).
