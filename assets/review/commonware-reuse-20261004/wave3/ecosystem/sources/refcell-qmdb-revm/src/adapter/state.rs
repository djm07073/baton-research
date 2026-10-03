//! QMDB state management.

use alloy_primitives::B256;
use tokio::runtime::Handle;

use super::{QmdbAsyncDb, RevmDb, create_revm_db_with_handle};
use crate::{store::QmdbBackend, utils::StateRootBuilder};

/// High-level state management for QMDB-backed REVM execution.
#[derive(Debug, Clone)]
pub struct QmdbState<B: QmdbBackend> {
    backend: B,
}

impl<B: QmdbBackend> QmdbState<B> {
    /// Creates a new state manager with the given backend.
    pub const fn new(backend: B) -> Self {
        Self { backend }
    }

    /// Returns a reference to the underlying backend.
    #[must_use]
    pub const fn backend(&self) -> &B {
        &self.backend
    }

    /// Returns a mutable reference to the underlying backend.
    pub const fn backend_mut(&mut self) -> &mut B {
        &mut self.backend
    }

    /// Consumes self and returns the backend.
    #[must_use]
    pub fn into_backend(self) -> B {
        self.backend
    }

    /// Creates a REVM database view for execution.
    pub fn database(&self, handle: Handle) -> RevmDb<B> {
        create_revm_db_with_handle(self.backend.clone(), handle)
    }

    /// Creates an async database view without caching layer.
    #[must_use]
    pub fn async_database(&self) -> QmdbAsyncDb<B> {
        QmdbAsyncDb::new(self.backend.clone())
    }

    /// Computes the current state root from partition roots.
    #[must_use]
    pub fn compute_root(&self) -> B256 {
        StateRootBuilder::new()
            .with_accounts(self.backend.account_root())
            .with_storage(self.backend.storage_root())
            .with_code(self.backend.code_root())
            .build()
    }

    /// Returns the individual partition roots.
    #[must_use]
    pub fn partition_roots(&self) -> (B256, B256, B256) {
        (self.backend.account_root(), self.backend.storage_root(), self.backend.code_root())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::store::mock::MockBackend;

    #[test]
    fn test_state_compute_root() {
        let backend = MockBackend::new();
        let state = QmdbState::new(backend);

        let root = state.compute_root();
        assert_ne!(root, B256::ZERO);
    }

    #[test]
    fn test_partition_roots() {
        let backend = MockBackend::new();
        let state = QmdbState::new(backend);

        let (accounts, storage, code) = state.partition_roots();
        assert_eq!(accounts, B256::ZERO);
        assert_eq!(storage, B256::ZERO);
        assert_eq!(code, B256::ZERO);
    }
}
