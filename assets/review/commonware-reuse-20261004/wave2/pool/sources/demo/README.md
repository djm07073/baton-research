# Commonware Mempool

Dual-stack validator demonstrating [Mosaik](https://github.com/flashbots/mosaik) transaction dissemination feeding [Commonware](https://github.com/commonwarexyz/monorepo) Simplex BFT consensus.

## Overview

Each validator runs **two P2P stacks** in one process:

- **Commonware `authenticated::Network`** -- consensus traffic (votes, certificates, block resolver)
- **Mosaik `Network`** -- transaction dissemination via typed streams with tag-based routing

Transaction sources (wallets, gateways) run Mosaik only and do not participate in consensus. They produce transactions on Mosaik streams routed to the current proposer via `subscribe_if` predicates that react to discovery tag changes.

### Architecture

```
Tx Sources (Mosaik only)
  |
  | Stream<Transaction> -- subscribe_if("proposer")
  v
Validators (dual stack)
  |-- Mosaik: consume txs, publish Stream<FinalizedBlock> for inclusion confirmation
  |-- Commonware: Simplex BFT consensus (votes, certificates)
  |
  | TagBridge: Simplex view events --> Mosaik tag updates
  v
Finalized blocks via Simplex
  |
  | Stream<FinalizedBlock> -- reverse confirmation to sources
  v
Tx Sources remove confirmed txs from local pools
```

### How It Works

1. **Dual-stack startup**: Inside Commonware's tokio runtime, the validator creates both a Commonware authenticated P2P network and a Mosaik network. Both run as concurrent tasks in the same process.

2. **TagBridge**: When Simplex advances views (via `propose()` or `verify()` callbacks), the `TagBridge` updates Mosaik discovery tags on this validator's peer entry: `"proposer"`, `"proposer-next"`, `"proposer-soon"`. This uses Simplex's deterministic round-robin schedule: `leader = (epoch + view) % N`.

3. **Stream routing**: Transaction sources use `subscribe_if(|peer| peer.tags().contains("proposer"))` on their producer streams. When tags change (proposer rotates), Mosaik's predicate re-evaluation automatically disconnects from the old proposer and connects to the new one.

4. **MempoolActor**: Uses `tokio::select!` to simultaneously process consensus messages from Simplex AND incoming transactions from the Mosaik `Consumer<Transaction>` stream. When elected leader, it drains pending transactions, hashes them into a block digest for consensus, and publishes a `FinalizedBlock` on a Mosaik stream for source-side inclusion confirmation.

5. **Source-retains-ownership**: Transaction sources maintain local pools of unconfirmed transactions. They consume `FinalizedBlock` messages to learn which transactions were included, removing confirmed ones. Unincluded transactions are periodically re-produced. When proposer rotates, sources automatically re-route to the new proposer via tag-driven stream reconnection.

6. **Pipeline pre-connection**: The 3-tier tag system (`proposer` / `proposer-next` / `proposer-soon`) allows sources to pre-establish Mosaik stream connections to upcoming proposers before they become active, eliminating connection setup latency during fast BFT view rotation.

## When to Use Mosaik vs Commonware P2P

| Layer | Stack | Why |
|---|---|---|
| Consensus protocol (votes, certs) | Commonware P2P | Fixed validator set, authenticated, rate-limited channels |
| Transaction dissemination | Mosaik Streams | Open participation, dynamic routing via tags, typed streams |
| Inclusion confirmation | Mosaik Streams | Proposer to sources, decoupled pub/sub |
| State sync / block relay | Either | Depends on whether open or validator-only |

**Commonware P2P** is built for closed validator-to-validator protocol traffic with known identity, per-peer rate limiting, and cryptographic authentication.

**Mosaik** is built for application-layer data flows where participants change, routing needs to be dynamic (tag-driven predicate re-evaluation), and you want typed `Producer<T>` / `Consumer<T>` streams rather than raw byte channels.

## Project Structure

```
src/
  main.rs          # Dual-stack startup, CLI, Simplex engine config
  mempool.rs       # MempoolActor + Automaton/Relay/Reporter trait impls
  bridge.rs        # TagBridge: Simplex view events --> Mosaik tag updates
  source.rs        # TxSourceNode: source-retains-ownership loop
  types.rs         # Transaction, FinalizedBlock, ViewUpdate
  schedule.rs      # Deterministic leader schedule pre-computation
```

### Key Components

**`MempoolActor`** (mempool.rs) -- The central actor bridging both stacks. Implements Commonware's `Automaton`, `CertifiableAutomaton`, `Relay`, and `Reporter` traits via a `Mailbox` proxy pattern. The actor's run loop uses `tokio::select!` over the consensus mailbox and the Mosaik consumer stream.

**`TagBridge`** (bridge.rs) -- Watches a `tokio::sync::watch` channel for view updates from the MempoolActor. On each view change, computes the current, next, and soon leaders from the deterministic schedule and updates this node's Mosaik discovery tags accordingly. Mosaik's predicate re-evaluation handles the rest.

**`TxSourceNode`** (source.rs) -- A Mosaik-only node (no consensus) implementing source-retains-ownership. Maintains a `HashMap<u64, Transaction>` local pool, consumes `FinalizedBlock` for settlement, and periodically re-produces unincluded transactions.

**`LeaderSchedule`** (schedule.rs) -- Pre-computes the deterministic round-robin leader schedule: `leader = (epoch + view) % num_participants`. Provides a lookahead window for pipeline pre-connection.

## Usage

Run at least 3 out of 4 validators to achieve BFT quorum (3f+1 where f=1).

### Validator 0 (bootstrapper)

```sh
cargo run --release -- \
  --me 0@3000 \
  --participants 0,1,2,3 \
  --storage-dir /tmp/commonware-mempool/0
```

### Validator 1

```sh
cargo run --release -- \
  --bootstrappers 0@127.0.0.1:3000 \
  --me 1@3001 \
  --participants 0,1,2,3 \
  --storage-dir /tmp/commonware-mempool/1
```

### Validator 2

```sh
cargo run --release -- \
  --bootstrappers 0@127.0.0.1:3000 \
  --me 2@3002 \
  --participants 0,1,2,3 \
  --storage-dir /tmp/commonware-mempool/2
```

### Validator 3

```sh
cargo run --release -- \
  --bootstrappers 0@127.0.0.1:3000 \
  --me 3@3003 \
  --participants 0,1,2,3 \
  --storage-dir /tmp/commonware-mempool/3
```

### Environment

Set `RUST_LOG=info` (default) or `RUST_LOG=debug` for verbose output.

## Dependencies

**Commonware** (v2026.2.0):
- `commonware-consensus` -- Simplex BFT engine
- `commonware-p2p` -- Authenticated peer networking with discovery
- `commonware-cryptography` -- Ed25519 signing, SHA256 hashing
- `commonware-runtime` -- Tokio-backed async runtime
- `commonware-parallel` -- Execution strategies
- `commonware-storage` -- Persistent journal storage
- `commonware-utils` -- Ordered sets, channels, macros

**Mosaik** ([feature/dynamic-predicate-reevaluation](https://github.com/zmanian/mosaik/tree/feature/dynamic-predicate-reevaluation)):
- Typed streams (`Producer<T>` / `Consumer<T>`) with `Datum` auto-impl
- Discovery with tags and `subscribe_if` predicate re-evaluation
- iroh-based QUIC transport

## Future Work

- Wire `TxSourceNode` into main as a separate binary or CLI subcommand
- Add a load generator for benchmarking transaction throughput
- Implement full block broadcast via the `Relay` trait (currently stub)
- Add gateway/aggregator pattern for scaling to many transaction sources
- Switch to BLS threshold signatures for compact cross-chain certificates
- Implement epoch transitions with validator set changes

## License

MIT
