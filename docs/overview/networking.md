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
