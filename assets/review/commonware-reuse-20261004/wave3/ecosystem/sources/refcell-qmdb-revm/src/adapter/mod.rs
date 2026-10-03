//! REVM database adapter for QMDB.

mod async_db;
pub use async_db::QmdbAsyncDb;

mod state;
pub use state::QmdbState;

mod sync_db;
pub use sync_db::RevmDb;
pub(crate) use sync_db::create_revm_db_with_handle;
