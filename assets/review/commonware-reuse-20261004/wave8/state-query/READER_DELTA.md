# Minimal proposed reader delta — state query

Keep five public traits/signatures, policies and query/result types open. No new actor, query module, HTTP API, certified-answer format or historical snapshot abstraction is needed.

## docs/execution/qmdb.md — a short paragraph beside durability/read readiness

Suggested prose:

> Storage can reuse guarded QMDB reads and the selected variant's existing proof APIs. If Current fits the chosen root scheme, ordered/unordered `key_value_proof` authenticates an active value against its canonical root; ordered also supplies `exclusion_proof`. Their verifiers and bounded codecs already exist. Capture value, proof and root under the same valid DB read authority, then bind the retained canonical checkpoint and readiness metadata through Storage's existing contract. Local `None` and historical operation inclusion do not prove current absence. A DB proof does not supply the f+1 full execution certificate, runtime/order checks or local durability; certificate queries remain in Executor. Reader handles are guarded access, not arbitrary historical snapshots.

Citations: [Current value verifier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/unordered/db.rs#L58), [Ordered absence verifier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/ordered/db.rs#L144), [Public proof generation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/ordered/db.rs#L204), [Reader guard](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L205), [Historical operation scope](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/db.rs#L477).

No interface changes or additional state-sync inventory needed. A real-chain example may be omitted from reader prose: Constantinople's small lookup adapter is useful evidence but its account/error-flattening/HTTP contract is not adopted.
