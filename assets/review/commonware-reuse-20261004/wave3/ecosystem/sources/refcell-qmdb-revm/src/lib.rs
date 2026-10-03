//! QMDB-backed state database adapter for the Rust Ethereum Virtual Machine (REVM).
//!
//! This crate provides a storage abstraction layer that connects REVM to QMDB, a
//! high-performance append-only database optimized for blockchain state. The adapter
//! implements REVM's database traits while leveraging QMDB's partitioned storage model
//! with separate namespaces for accounts, storage slots, and contract bytecode.
//!
//! # Architecture
//!
//! The storage model uses three distinct partitions with content-addressed keys.
//! Account data is keyed by 20-byte addresses. Storage slots use 60-byte composite
//! keys encoding the address, a generation counter for SELFDESTRUCT handling, and
//! the 32-byte slot index. Bytecode is keyed by its keccak256 hash, enabling
//! deduplication across contracts with identical code.
//!
//! Generation counters provide O(1) storage invalidation on SELFDESTRUCT. Rather
//! than deleting storage entries, the account's generation is incremented, causing
//! all prior storage keys to become unreachable. New storage writes use the updated
//! generation, effectively creating a fresh namespace.
//!
//! State roots are computed by hashing the concatenation of partition merkle roots
//! with a domain separator prefix. This enables independent partition updates while
//! maintaining a single canonical state commitment.
//!
//! # Core Types
//!
//! [`QmdbBackend`] defines the async trait that storage implementations must satisfy.
//! It exposes methods for account, storage, and code retrieval along with partition
//! root accessors. Implementors handle the actual QMDB interaction.
//!
//! [`QmdbAsyncDb`] wraps a backend and implements REVM's [`DatabaseAsyncRef`] trait.
//! It translates REVM queries into backend calls, handling key construction and
//! generation-aware storage lookups.
//!
//! [`RevmDb`] is the synchronous database type used during EVM execution. It combines
//! the async wrapper with REVM's [`CacheDB`] for in-memory caching of accessed state.
//! A tokio runtime handle is required to bridge async backend calls.
//!
//! [`QmdbState`] provides a high-level interface for managing execution state. It
//! constructs database views, computes state roots, and exposes partition roots for
//! merkle proof generation.
//!
//! [`QmdbChangeSet`] accumulates state modifications from EVM execution. It tracks
//! per-account updates including balance, nonce, code, and storage changes. The
//! changeset can be merged across transactions and applied to the backend atomically.
//!
//! [`AccountRecord`] is the canonical encoding for account data in the accounts
//! partition. It stores nonce, balance, code hash, generation, and a code presence
//! flag in an 81-byte fixed layout.
//!
//! # Key Types
//!
//! [`AccountKey`], [`StorageKey`], and [`CodeKey`] are fixed-size byte arrays for
//! partition keys. The [`IntoAccountKey`], [`IntoStorageKey`], and [`IntoCodeKey`]
//! traits provide ergonomic conversions from alloy primitives. [`StorageKeyExt`]
//! enables extraction of address, generation, and slot components from storage keys.
//!
//! # Example
//!
//! ```ignore
//! use qmdb_revm::{QmdbState, QmdbBackend};
//! use tokio::runtime::Handle;
//!
//! fn execute_with_qmdb<B: QmdbBackend>(backend: B, handle: Handle) {
//!     let state = QmdbState::new(backend);
//!     let db = state.database(handle);
//!     // Pass db to REVM for execution
//!     let root = state.compute_root();
//! }
//! ```
//!
//! [`DatabaseAsyncRef`]: revm::database_interface::async_db::DatabaseAsyncRef
//! [`CacheDB`]: revm::database::CacheDB

#![cfg_attr(not(test), warn(unused_crate_dependencies))]

mod adapter;
pub use adapter::{QmdbAsyncDb, QmdbState, RevmDb};

mod changes;
pub use changes::{AccountUpdate, QmdbChangeSet};

mod error;
pub use error::{QmdbError, Result};

mod keys;
pub use keys::{
    AccountKey, CodeKey, IntoAccountKey, IntoCodeKey, IntoStorageKey, StorageKey, StorageKeyExt,
};

mod model;
pub use model::AccountRecord;

mod store;
pub use store::QmdbBackend;

mod utils;
pub use commonware_storage as storage;
pub use utils::StateRootBuilder;
