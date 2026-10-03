# Independent source review — worker/future helpers

Reviewer `/root/reuse_network_v3`. Reviewed execution-workers REPORT SHA-256 `841e9cda433be0692860660727ceb06f360aceb478043792c83ef154bd4fdfcc` and READER_DELTA `0459d07442836ade34843fb6e010b84ad4d7f7075090ec99f4fe56bf949ffb4c`. **Pass; no remaining material correction.** Source/API fit only, not compilation, runtime execution, fairness/preemption evidence, strict worker quiescence or native integration proof.

## Decisive checks

Native public OptionFuture keeps None pending, exposes Option through Deref/DerefMut, and delegates polling without clearing Some on Ready. It has no FusedFuture implementation in the inspected file. Tempo's actual crate-private vendored wrapper instead sets None after completion and implements FusedFuture. The report and delta correctly reuse only the public mechanism while requiring explicit owner clearing/replacement. Native Pool/AbortablePool require static pushed futures; fresh release allows lifetime-bound futures. Release source corroboration does not falsely equate those graphs.

Strategizer is a public Spawner subtrait returning Rayon for NonZeroUsize parallelism. Native Tokio constructs a ThreadPoolBuilder with dedicated runtime child tasks. It supplies construction/ownership plumbing, not a scheduler, cancellation/fairness rule or a selected capacity/parallelism default. ContextCell is publicly reexported; spawn_cell restores it synchronously in the task constructor and documents default placement. CPU work must remain inside the appropriately placed body because Tokio constructs the future synchronously, Sequential computes immediately and single-thread Rayon also computes immediately. Multi-thread Rayon closures continue after result receiver loss.

Task Handles and completion Handles have different authority. Plain Handle drop has no abort-on-drop implementation; explicit task abort requests cancellation, whereas from_future/from_receiver wraps waiting. Handle::select deliberately aborts its owned group on completion/drop; it is unsuitable as an implicit cancel-every-other-branch default. AbortablePool's dropped Aborter aborts the registered polled future, which may only be awaiting separately spawned work. Exact completed-context/authority checks and worker/access fencing remain application obligations.

Handle result sending precedes descendant abort requests; this does not establish signing-material quiescence or durable Storage completion. The report preserves the prior lifecycle caveat, distinguishes abort from physical stoppage, and makes no observed-race claim. Existing reservation/rebind helpers accurately retain bounded-send values/consume mutation handles without automatic total-work bounds, rollback or cancellation recovery.

Actual Tempo sources support one execution slot, prioritized application scheduling and retained abortable parent subscriptions. Its payload-resolution cancellation is a selected backend seam rather than universal CPU/storage preemption. Constantinople computes staged changes via existing Strategy and seals separately; native voter generation/permit completion and Stateful verification barriers are private. No public Runtime/Planner/tree-worker owner is newly required.

The small README table/paragraph stays within Executor/Storage ownership. It does not move Baton::plan, make Baton approve apply, relax certificate-plus-applicable-material switching, import private Simplex controls, select policy numbers, add reschedule APIs or create a native cut wait.

## Independent receipts

Fifteen newly fetched decisive native/release/Tempo/Constantinople files (including public ContextCell reexport) were Git-blob checked against own complete native/release/Tempo trees and a newly fetched complete Constantinople tree. Own freshly retrieved Tempo Executor from the ACK review closes the actor examples. Twenty-one combined cross-review source receipts are preserved in cross-review-source-manifest.json.

EXECUTION_WORKERS_CROSS_REVIEW_RECEIPT.json maps all 30 report anchors to own fresh files and independently verifies both actual explicit-release MCP contents: 91 Handle lines plus 50 futures lines match release bytes using zero-based labels. Handle is byte-identical to native; futures differs exactly in the scoped pool lifetime surface. No successful wrapper or borrowed foreign manifest substituted for source inspection.

No canonical file or foreign report was edited.
