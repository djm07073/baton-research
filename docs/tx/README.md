# Tx layer: roles and flow

**TxPool manages the transactions available for the next block.** It accepts candidates, keeps them available, supplies bounded batches to BlockService, and updates their lifecycle after canonical results. TxPool also supplies static payload analysis and policy hooks; whether it runs in a router or during block packing remains undecided.

## Roles and responsibilities

TxPool receives transactions from clients and peers and retains candidates for producer body construction. Static analysis extracts features available from the transaction payload itself. Routing and packing policies may use those features. Live balances, nonces, and current node load are not static-analysis results.

A reuse candidate is the separate Constantinople `TransactionSource` and pool implementation. TransactionSource accepts a parent `Header`, consensus `Round`, and the byte count of signed transactions already selected; it returns `Vec<VerifiedTransaction>` and expects marshal finalized-block Updates. Native producer Context and digest callbacks do not supply these types. Selection and canonical-outcome adapters are therefore needed.

Its Commonware dependency revision also differs from the native pin, so direct Rust type compatibility is unverified. Reusing a whole crate or selected implementation pieces, along with queue and cleanup policies, remains open. [TransactionSource](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/lib.rs#L9), [Dependency pin](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/Cargo.toml#L50).

When BlockService calls `TxPool::select`, the pool returns candidates for the supplied context and limits. Creating or canceling a proposal does not turn admission into a canonical outcome. Transaction lifecycle cleanup follows canonical execution results.

## Tx P2P connection

Use existing Commonware authenticated P2P connections, with a logical tx channel separate from native consensus messages. Do not assume dedicated physical connections for transactions. Transaction floods compete with report, body, and native processing; concrete quotas, queues, and runtime placement remain open, as described in [P2P message planes](../overview/networking.md#p2p-connections-and-message-planes).

The wire protocol, inventory/body exchange, producer targeting, retransmission, and duplicate suppression remain undecided. The interface only identifies the connection from incoming peer transactions to `TxPool::admit`.

## Open decisions

| Item | Decision |
|---|---|
| Tx format / ID / signature domain | |
| Mempool implementation to reuse | |
| Static-analysis placement and result schema | |
| Router / packing policy and replacement interface | |
| Tx P2P wire protocol / logical channel ID | |
| Candidate selection order / byte and count limits | |
| Application semantics of duplicate transactions | |
| Durability of admission responses | |
| Proposal cancellation / reselection / retransmission | |
| Canonical cleanup / retention / GC | |

## Commonware primitives in the transaction layer

**TxPool owns admission and selection; Commonware supplies the networking, encoding and storage building blocks.** Keep static analysis inside `TxPool::analyze` / `classify`, whichever routing or block-filtering policy is eventually chosen.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_p2p::authenticated`, `Sender`, `Receiver`, `Recipients` | Tx propagation over logical channels on the existing authenticated network | Tx admission, duplicate identity, peer limits and routing/filtering policy |
| `commonware_codec::Codec` and `commonware_cryptography::{Signer, Verifier}` | Decode bounded tx messages and verify the chosen tx signature subject | Tx schema, domain, static features and application validity rules |
| `commonware_runtime` and `commonware_actor::Feedback` | Pool tasks, bounded mailboxes and local completion signals | Pool ownership, admission/selection coordination and feedback semantics |
| `commonware_storage::queue` (candidate) | Persistent pending-work storage if durable pool admission is selected | Deduplication, indexing, eviction and transaction selection; a queue is not a complete mempool |

The MCP release inventory does not expose a standalone mempool or block-builder crate. It does show that Stateful accepts an application provider that may be backed by a mempool. Keep the existing Constantinople pool candidate under review; do not infer that a ready-made pool exists from that provider interface. The router-versus-filtering-layer choice remains open.

See [versioned primitive evidence and compatibility checks](../reference/integration.md#primitive-reuse-catalog).
