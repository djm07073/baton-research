# Minimal proposed reader delta

Source/API clarification only. No public trait/signature change; no new diagram, actor, backend or policy. Current docs already cover deferred-root read/replay, live-DB fencing and logical-versus-physical pruning. Do not duplicate those sections.

## docs/execution/qmdb.md — after the branch-scoped-view paragraph

Suggested prose:

> Retain the existing prepared batch handles for each still-needed unapplied ancestor. A child draft holds its immediate sealed parent strongly, while sealed parent links are Weak; keeping only the leaf does not preserve every ancestor object needed for later reads, forks and merkleization. Public `bounds()` exposes storage commitments and ancestor bounds, not live parent handles or execution-node identity. With Current, these bounds carry the ops-only root; `root()` returns the canonical root. Use the existing DB applicability checks alongside Executor's exact-context association and shared access fence. Release unused handles separately from Storage's durable-history pruning.

Suggested citations: [Child lifetime](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L2587), [Weak sealed parent](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L338), [Public bounds](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/batch_chain.rs#L65), [Current root distinction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/batch.rs#L1052).

The phrase “still-needed” preserves open retention/sealing choices. It does not promise that all callers can discard an ancestor immediately on child merkleization, or that Arc strong counts prove worker quiescence/durable recovery.

## docs/execution/interfaces.md

No additional prose needed. The existing internal completed/prepared handoff and Storage ownership already fit concrete handles. Do not add a public tree/view trait or require Stateful Application.
