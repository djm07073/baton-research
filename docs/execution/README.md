# Execution: roles and responsibilities

**Executor turns ordered transactions into durable application state.** It manages the parent-linked execution tree, certifies results with peer Executors, imports verified peer state when useful, and recovers after restart. Transaction computation and certification are internal Executor responsibilities.

## Roles and responsibilities

Executor receives parent-linked execute(block) inputs from Baton, and finalized commit(range) inputs directly from Orderer. Baton owns direction planning; there is no separate reschedule API. It computes transaction effects and uses QMDB to manage state and outputs. It communicates directly with other validators' Executors to certify results or synchronize local state from verified results. The application-specific Bank balance and nonce model is outside the current scope.

| Responsibility | Executor owns | Boundary and completion condition |
|---|---|---|
| Execution tree | Resolve parent hashes, link children, track completed checkpoints, promote canonical path, prune conflicting branches | Parent is an execution predecessor; compatible canonical descendants remain pending |
| Direct execution | Transaction computation, branch management, prefix reuse, suffix reexecution | Completed ExecutionResult; speculative work is not canonical application |
| Result signing | Validate and sign its directly executed result through Executor::sign_result using Commonware cryptography | Bind finalized exact input, canonical input state, runtime, and full result; never sign an imported result as its own execution |
| State finalization | Verify peer signatures / certificates; retain and disseminate the original certificate | f+1 distinct eligible signatures on one full statement, with irrevocable order and input-state chain verified |
| Executor peer communication | Exchange signatures, certificates, change sets, and outputs; query, retry, and serve | Executor ↔ Executor over Commonware P2P, without Baton relay or approval |
| Switching to state sync | Stop remaining execution and apply verified material when certificate and usable material are ready first | Matching base, safe cancellation, writer fence; a certificate alone is insufficient to stop execution |
| Local application and recovery | Persist directly computed or verified state, outputs, and cursor in QMDB and commit metadata | Recoverable durable CommitResult, separate from state finalization |
| Completion delivery | Durable delivery ACK to Orderer; canonical tx outcomes to TxPool; execution results / optional progress notice to Baton | No Baton response or approval required for certification, sync, application, or ACK |

Executor owns signing, collection, and certificate verification. Executor owns peer transport and state-material verification, application, persistence, and recovery. This is a separate path from Baton reports and directions. Continue direct execution while certificate or material is unavailable; do not add a shared barrier that waits for peers before starting work. A certificate arriving before local ordered input stays pending or triggers authenticated-history recovery. It cannot settle unresolved order.

Keep speculative and canonical state separate. Execute produces branch results without canonical commit authority. Commit and state sync apply only results bound to proven exact ordered input and the correct canonical predecessor. Both share the canonical single writer. An arriving sync result cannot drop an ongoing canonical mutation or bypass it through a competing writer. Switching, race, and failure contracts remain open.

## Open decisions

| Item | Decision |
|---|---|
| Application transaction semantics | |
| QMDB database variant / state encoding / root type | |
| Canonical operations / batch-boundary derivation / logical-root integration | |
| Scope of Stateful actor reuse | |
| Block / parent-hash encoding and binding / checkpoint granularity | |
| Execution scheduling / cancellation / worker-fencing contract | |
| Atomic commit of state / outputs / cursor | |
| Branch pruning / memory / disk budget | |
| Replay / checkpoint / state sync | |
| Query interface / certified-result integration | |

## Commonware primitives in the execution layer

**Executor owns execution, canonical state, result certification and peer state sync.** Reuse database, collection and fetch primitives inside it; these do not require separate public Runtime or ResultService modules.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_storage::qmdb` and `commonware_glue::stateful::db` (`Unmerkleized`, `Merkleized`, `DatabaseSet`, `Barrier`) | Fork a parent state, produce a Merkle commitment and apply/flush the canonical result | Parent/hash correlation, transaction effects, branch reuse/pruning, single canonical writer and durable delivery acknowledgement |
| `commonware_glue::stateful::{Stateful, Application}` (integration reference/candidate) | Existing pending-parent execution and finalization/pruning lifecycle | Adapt to native Multimmit exact merged order; upstream application hooks still require our transaction logic |
| `commonware_cryptography::{Signer, Verifier}` and `commonware_codec::Codec` | `sign_result`, `verify_result` and certificate wire data | Full execution subject, epoch eligibility, distinct signer counting and direct-versus-imported provenance |
| `commonware_collector::p2p::Engine`; `Originator`, `Handler`, `Monitor` (candidate) | Request an execution attestation and collect responses within Executor | Validate every response before counting f+1 matching eligible signatures; bind request/response commitments and integrate unsolicited statements separately |
| `commonware_resolver::p2p` and `commonware_storage::qmdb::sync::Source`; `commonware_glue::stateful::db::p2p` (candidate) | Obtain missing authenticated state operations/material from Executor peers | Certificate/range/base validation, applicable change-set verification, safe switch fencing and ongoing normal-path state sync |
| `commonware_storage::{journal, metadata}`; runtime/actor primitives | Persist cursors and coordinate compute, apply, flush and recovery | State/cursor crash consistency, task cancellation and readiness publication |

`collector::Monitor` receives a count for responses with the same commitment, once per handler. That count alone is not an execution certificate: Executor must verify signatures, validator membership and equality of the complete execution subject. Adopt the engine only after checking its request/response identity contract and compatibility with the selected source pin.

The indexed Stateful actor documents a one-time bootstrap sync from a Marshal floor, followed by recovery on later startups. Our repeated validator-to-validator sync during normal execution is additional integration logic. Reusing its resolver/QMDB building blocks does not provide that lifecycle automatically. Stop unfinished execution only after both certificate and applicable state material are verified.

See [QMDB lifecycle](qmdb.md), [state-sync contract](state-sync.md) and [versioned primitive evidence](../reference/integration.md#primitive-reuse-catalog).
