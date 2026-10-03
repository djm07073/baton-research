//! Async database implementation for REVM.

use std::sync::Arc;

use alloy_primitives::{Address, B256, U256};
use revm::{
    bytecode::Bytecode, database_interface::async_db::DatabaseAsyncRef, primitives::KECCAK_EMPTY,
    state::AccountInfo,
};

use crate::{
    error::QmdbError,
    keys::{IntoAccountKey, IntoCodeKey, IntoStorageKey},
    store::QmdbBackend,
};

/// Async database wrapper over a [`QmdbBackend`].
pub struct QmdbAsyncDb<B: QmdbBackend> {
    backend: Arc<B>,
    block_hashes: Arc<dyn Fn(u64) -> Option<B256> + Send + Sync>,
}

impl<B: QmdbBackend> Clone for QmdbAsyncDb<B> {
    fn clone(&self) -> Self {
        Self { backend: Arc::clone(&self.backend), block_hashes: Arc::clone(&self.block_hashes) }
    }
}

impl<B: QmdbBackend> core::fmt::Debug for QmdbAsyncDb<B> {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_struct("QmdbAsyncDb").field("backend", &"...").finish_non_exhaustive()
    }
}

impl<B: QmdbBackend> QmdbAsyncDb<B> {
    /// Creates a new async database wrapper.
    pub fn new(backend: B) -> Self {
        Self { backend: Arc::new(backend), block_hashes: Arc::new(|_| None) }
    }

    /// Creates a new async database with a block hash provider.
    pub fn with_block_hashes<F>(backend: B, block_hashes: F) -> Self
    where
        F: Fn(u64) -> Option<B256> + Send + Sync + 'static,
    {
        Self { backend: Arc::new(backend), block_hashes: Arc::new(block_hashes) }
    }

    /// Returns a reference to the underlying backend.
    #[must_use]
    pub fn backend(&self) -> &B {
        &self.backend
    }
}

impl<B: QmdbBackend> DatabaseAsyncRef for QmdbAsyncDb<B> {
    type Error = QmdbError;

    async fn basic_async_ref(&self, address: Address) -> Result<Option<AccountInfo>, Self::Error> {
        let key = address.into_account_key();

        let record =
            self.backend.get_account(&key).await.map_err(|e| QmdbError::Storage(e.to_string()))?;

        Ok(record.map(|rec| AccountInfo {
            nonce: rec.nonce,
            balance: rec.balance,
            code_hash: rec.code_hash,
            code: None,
        }))
    }

    async fn code_by_hash_async_ref(&self, code_hash: B256) -> Result<Bytecode, Self::Error> {
        if code_hash == KECCAK_EMPTY || code_hash == B256::ZERO {
            return Ok(Bytecode::default());
        }

        let key = code_hash.into_code_key();

        let code =
            self.backend.get_code(&key).await.map_err(|e| QmdbError::Storage(e.to_string()))?;

        Ok(code.map_or_else(Bytecode::default, |bytes| Bytecode::new_raw(bytes.into())))
    }

    async fn storage_async_ref(&self, address: Address, index: U256) -> Result<U256, Self::Error> {
        let key = address.into_account_key();

        let record =
            self.backend.get_account(&key).await.map_err(|e| QmdbError::Storage(e.to_string()))?;

        let generation = match record {
            Some(rec) => rec.generation,
            None => return Ok(U256::ZERO),
        };

        let storage_key = address.into_storage_key(generation, index);

        let value = self
            .backend
            .get_storage(&storage_key)
            .await
            .map_err(|e| QmdbError::Storage(e.to_string()))?;

        Ok(value.unwrap_or(U256::ZERO))
    }

    async fn block_hash_async_ref(&self, number: u64) -> Result<B256, Self::Error> {
        Ok((self.block_hashes)(number).unwrap_or(B256::ZERO))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{keys::IntoStorageKey, model::AccountRecord, store::mock::MockBackend};

    #[tokio::test]
    async fn test_basic_account_lookup() {
        let backend = MockBackend::new();

        let addr = Address::repeat_byte(0x42);
        let record = AccountRecord {
            nonce: 5,
            balance: U256::from(1000),
            code_hash: KECCAK_EMPTY,
            generation: 0,
            has_code: false,
        };

        backend.insert_account(addr.into_account_key(), record);

        let db = QmdbAsyncDb::new(backend);

        let info = db.basic_async_ref(addr).await.unwrap().unwrap();
        assert_eq!(info.nonce, 5);
        assert_eq!(info.balance, U256::from(1000));
        assert_eq!(info.code_hash, KECCAK_EMPTY);
    }

    #[tokio::test]
    async fn test_nonexistent_account() {
        let backend = MockBackend::new();
        let db = QmdbAsyncDb::new(backend);

        let addr = Address::repeat_byte(0xFF);
        let info = db.basic_async_ref(addr).await.unwrap();
        assert!(info.is_none());
    }

    #[tokio::test]
    async fn test_storage_lookup() {
        let backend = MockBackend::new();

        let addr = Address::repeat_byte(0x42);
        let slot = U256::from(1);
        let value = U256::from(12345);

        backend.insert_account(
            addr.into_account_key(),
            AccountRecord {
                nonce: 1,
                balance: U256::ZERO,
                code_hash: KECCAK_EMPTY,
                generation: 0,
                has_code: false,
            },
        );

        backend.insert_storage(addr.into_storage_key(0, slot), value);

        let db = QmdbAsyncDb::new(backend);

        let result = db.storage_async_ref(addr, slot).await.unwrap();
        assert_eq!(result, value);
    }

    #[tokio::test]
    async fn test_storage_generation_isolation() {
        let backend = MockBackend::new();

        let addr = Address::repeat_byte(0x42);
        let slot = U256::from(1);
        let value = U256::from(12345);

        backend.insert_storage(addr.into_storage_key(0, slot), value);

        backend.insert_account(
            addr.into_account_key(),
            AccountRecord {
                nonce: 0,
                balance: U256::ZERO,
                code_hash: KECCAK_EMPTY,
                generation: 1,
                has_code: false,
            },
        );

        let db = QmdbAsyncDb::new(backend);

        let result = db.storage_async_ref(addr, slot).await.unwrap();
        assert_eq!(result, U256::ZERO);
    }
}
