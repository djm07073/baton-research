# Small proposed reader delta — not adopted

Baseline `99dc2c456c4b318fefb368cb39a145298f7d86b7` after CR10. Keep existing sections, five traits/signatures, diagrams and empty choices. No repeated lifecycle/Baton-task section is needed.

## docs/execution/README.md existing primitive table

One runtime/future row can replace the vague runtime part of the current journal/metadata row (keep journal/metadata as durability):

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `runtime::{Spawner, Strategizer}`; `utils::futures::{Pool, AbortablePool, OptionFuture}` | Existing worker ownership, compatible Rayon construction and completion polling | Selected placement/work bounds, exact completion context and safe worker/access fencing; cancellation is not quiescence |

Add one short paragraph if needed:

> The public `OptionFuture` keeps an empty active-work slot pending; its native implementation does not remove a completed future, so its owner must clear or replace that slot. `Strategizer::strategy` constructs the runtime-owned Rayon strategy without another thread-pool factory. Aborting a completion waiter does not stop separately spawned work; keep worker authority and canonical mutation ownership through their actual completion. Placement, parallelism and cancellation policy stay open. [Optional future](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/futures.rs#L150), [Strategy factory](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/lib.rs#L357), [Task/completion distinction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/utils/handle.rs#L28).

## Other pages

No Rust/E2E/Storage trait or diagram change. Existing state-sync stop-only-after verified matching certificate plus applicable material, shared writer, direct/imported provenance and durability rules already apply. Do not add generic worker priority or quiescence APIs. The report's Tempo private OptionFuture auto-clear/FusedFuture difference is source-port guidance; if a reader comparison is added, label it as a pattern rather than unchanged native reuse. Other public conveniences (ContextCell, reservations, rebind) need no new reader inventory.
