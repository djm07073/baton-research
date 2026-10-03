# qmdb-revm

> [!CAUTION]
>
> Qmdb-revm walked, so [kora](https://github.com/refcell/kora) could run.
> This repository is now archived.

QMDB-backed database adapter for [REVM] execution.

## Installation

```toml
qmdb-revm = "0.1"
```

## Why

[REVM]'s database interface expects synchronous access patterns, but modern authenticated storage systems like [QMDB] operate asynchronously with separate partitions for accounts, storage slots, and bytecode. Bridging these two models typically requires wrapper layers that obscure the underlying data structure or force awkward blocking patterns.

qmdb-revm provides a thin adapter that maps REVM's [`Database`] trait onto QMDB's three-partition layout. Accounts live in a 20-byte keyed partition, storage slots use a 60-byte composite key encoding address, generation counter, and slot index, and bytecode is addressed by its 32-byte keccak hash. The generation counter enables efficient storage invalidation when an account is selfdestructed or recreated via CREATE2, without requiring deletion of existing slot entries.

The adapter uses REVM's [`DatabaseAsyncRef`] infrastructure internally while presenting a synchronous interface via tokio runtime handles. A [`CacheDB`] layer sits on top for in-memory caching during execution, with the underlying QMDB partitions serving as the persistent backing store.

## Usage

Implement the `QmdbBackend` trait to connect your QMDB instance. This requires async methods for fetching accounts, storage slots, and bytecode, plus methods returning the merkle roots of each partition.

```rust,ignore
use qmdb_revm::{QmdbBackend, AccountKey, StorageKey, CodeKey, AccountRecord};

struct MyBackend { /* ... */ }

impl QmdbBackend for MyBackend {
    type Error = MyError;

    async fn get_account(&self, key: &AccountKey) -> Result<Option<AccountRecord>, Self::Error> {
        // Fetch from accounts partition
    }

    async fn get_storage(&self, key: &StorageKey) -> Result<Option<U256>, Self::Error> {
        // Fetch from storage partition
    }

    async fn get_code(&self, key: &CodeKey) -> Result<Option<Vec<u8>>, Self::Error> {
        // Fetch from code partition
    }

    fn account_root(&self) -> B256 { /* ... */ }
    fn storage_root(&self) -> B256 { /* ... */ }
    fn code_root(&self) -> B256 { /* ... */ }
}
```

Create a `QmdbState` for high-level state management, which handles database creation and state root computation.

```rust,ignore
use qmdb_revm::QmdbState;
use tokio::runtime::Handle;

let state = QmdbState::new(backend);

// Create a REVM-compatible database
let db = state.database(Handle::current());

// Compute state root from partition roots
let root = state.compute_root();
```

Use extension traits for zero-copy key construction. These encode keys directly into fixed-size byte arrays without intermediate allocations.

```rust,ignore
use qmdb_revm::{IntoAccountKey, IntoStorageKey, IntoCodeKey};

let account_key = address.into_account_key();
let storage_key = address.into_storage_key(generation, slot);
let code_key = code_hash.into_code_key();
```

## Architecture

The crate is organized around a clear separation between REVM integration and QMDB abstraction.

The `QmdbBackend` trait provides the interface to QMDB storage without depending on specific QMDB implementations. Backends implement async accessors for the three partitions plus methods returning partition merkle roots. This allows testing with mock backends and swapping storage implementations without modifying the adapter layer.

`QmdbAsyncDb` implements REVM's [`DatabaseAsyncRef`] trait, translating REVM's account and storage queries into QMDB partition lookups. Storage queries first fetch the account to retrieve the current generation counter, then construct the composite storage key. This ensures that recreated accounts automatically see fresh storage without explicit deletion.

`RevmDb` wraps the async adapter in REVM's [`CacheDB`] for in-memory caching during execution. The cache accumulates reads and writes, which can later be extracted as a changeset for committing back to QMDB.

State roots are computed as `keccak256(prefix || account_root || storage_root || code_root)` using `StateRootBuilder`, combining the three partition roots with a domain separator for collision resistance.

## Benchmarks

Run benchmarks with `cargo bench`. Key results on Apple M3 Max:

| Operation | Time | Throughput |
|-----------|------|------------|
| Account key construction | 12 ns | 81 M/s |
| Storage key construction | 34 ns | 30 M/s |
| Account lookup | 111 ns | 9 M/s |
| Storage lookup | 117 ns | 8.5 M/s |
| State root computation | 273 ns | 3.7 M/s |
| Changeset merge (1k entries) | 44 µs | 23 M/s |

## License

Licensed under either of Apache License, Version 2.0 or MIT license at your option.

## Acknowledgments

This adapter is based on the QMDB integration originally implemented by [@diegomrsantos](https://github.com/diegomrsantos) in the [commonware REVM example](https://github.com/commonwarexyz/monorepo/pull/2495).

This project is built on [commonware-storage] which provides the QMDB authenticated merkle database, and [REVM] which provides the Ethereum Virtual Machine implementation. The QMDB design enables efficient authenticated storage with separate partitions for different data types, while REVM's async database interface allows non-blocking integration with backend storage systems.

[REVM]: https://github.com/bluealloy/revm
[QMDB]: https://docs.rs/commonware-storage/latest/commonware_storage/qmdb/index.html
[commonware-storage]: https://docs.rs/commonware-storage
[`Database`]: https://docs.rs/revm/latest/revm/database/trait.Database.html
[`DatabaseAsyncRef`]: https://docs.rs/revm/latest/revm/database_interface/async_db/trait.DatabaseAsyncRef.html
[`CacheDB`]: https://docs.rs/revm/latest/revm/database/struct.CacheDB.html
