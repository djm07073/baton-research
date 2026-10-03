//! Synchronous database wrappers and type aliases.

use revm::{database::CacheDB, database_interface::async_db::WrapDatabaseAsync};
use tokio::runtime::Handle;

use super::QmdbAsyncDb;
use crate::store::QmdbBackend;

/// Synchronous wrapper around [`QmdbAsyncDb`].
pub(crate) type QmdbRefDb<B> = WrapDatabaseAsync<QmdbAsyncDb<B>>;

/// Complete REVM database with caching layer.
pub type RevmDb<B> = CacheDB<QmdbRefDb<B>>;

/// Creates a REVM database from a QMDB backend with an explicit runtime handle.
pub(crate) fn create_revm_db_with_handle<B: QmdbBackend>(backend: B, handle: Handle) -> RevmDb<B> {
    let async_db = QmdbAsyncDb::new(backend);
    let wrapped = WrapDatabaseAsync::with_handle(async_db, handle);
    CacheDB::new(wrapped)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::store::mock::MockBackend;

    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    async fn test_create_revm_db() {
        let backend = MockBackend::new();
        let async_db = QmdbAsyncDb::new(backend);
        let wrapped = WrapDatabaseAsync::new(async_db);
        assert!(wrapped.is_some());
    }

    #[tokio::test]
    async fn test_create_revm_db_with_handle() {
        let handle = Handle::current();
        let backend = MockBackend::new();
        let _db = create_revm_db_with_handle(backend, handle);
    }
}
