# Tx layer: roles and flow

**TxPool manages the transactions available for the next block.** It accepts candidates, keeps them available, supplies bounded batches to BlockService, and updates their lifecycle after canonical results. TxPolicy supplies static analysis; whether it runs in a router or during block packing remains undecided.

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
