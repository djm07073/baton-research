# Independent limited join/quiescence source check

Reviewer: `/root/reuse_storage_types_v3` (wave4 compatibility role). Fresh source retrievals are recorded in [source-manifest.json](source-manifest.json) and matched the native repository tree at `534af0ede48affd35b2111522527547b4cc9bf72`.

Sources inspected directly:

- [Engine](sources/native/consensus/src/multimmit/engine.rs): Running::join at L589–591 awaits only `self.task`; root selection at L816–830 exits on shutdown or one child completion without explicitly awaiting all remaining children.
- [Handle](sources/native/runtime/src/utils/handle.rs): runner success sends the root's result at L129, followed by descendant tree abort at L139; Handle::select L215 documents aborting an owned group on first completion/drop rather than joining every descendant.

Running's documented API intention says join waits for every engine child to stop and is completion evidence. These implementation excerpts establish root-handle waiting and supervised abort requests. They alone do not establish that every child's future is dropped, all in-progress work completes, or every signing capability is revoked before the root result receiver resolves across all supported runtimes. This is a remaining verification boundary, **not a demonstrated race or runtime violation**. Avoid using the source inspection as strict cross-owner signing-authority quiescence proof; qualify the documented intention until implementation closure/integration verification supports it.

The source check does not propose another task supervisor, shutdown method or native-engine implementation. No protocol/runtime build or fault test was run.
