# Execution: roles and responsibilities

**Executor turns ordered transactions into durable application state.** It manages execution branches, certifies results with peer Executors, imports verified peer state when useful, and recovers after restart. Runtime computes transaction effects. ResultService handles certification inside Executor.

## Roles and responsibilities

Executor receives speculative execute/reschedule requests from Baton and finalized inputs directly from Orderer. It uses Runtime and QMDB to manage state and outputs. It communicates directly with other validators' Executors to certify results or synchronize local state from verified results. The application-specific Bank balance and nonce model is outside the current scope.

| Responsibility | Executor owns | Boundary and completion condition |
|---|---|---|
| Direct execution | Runtime computation, branch management, prefix reuse, suffix reexecution | Completed ExecutionResult; speculative work is not canonical application |
| Result signing | Validate and sign its directly executed result through internal ResultService | Bind finalized exact input, canonical input state, runtime, and full result; never sign an imported result as its own execution |
| State finalization | Verify peer signatures / certificates; retain and disseminate the original certificate | f+1 distinct eligible signatures on one full statement, with irrevocable order and input-state chain verified |
| Executor peer communication | Exchange signatures, certificates, change sets, and outputs; query, retry, and serve | Executor ↔ Executor over Commonware P2P, without Baton relay or approval |
| Switching to state sync | Stop remaining execution and apply verified material when certificate and usable material are ready first | Matching base, safe cancellation, writer fence; a certificate alone is insufficient to stop execution |
| Local application and recovery | Persist directly computed or verified state, outputs, and cursor in QMDB and commit metadata | Recoverable durable CommitResult, separate from state finalization |
| Completion delivery | Durable delivery ACK to Orderer; canonical tx outcomes to TxPool; execution results / optional progress notice to Baton | No Baton response or approval required for certification, sync, application, or ACK |

ResultService separates signing, collection, and certificate verification within Executor. Executor owns peer transport and state-material verification, application, persistence, and recovery. This is a separate path from Baton reports and directions. Continue direct execution while certificate or material is unavailable; do not add a shared barrier that waits for peers before starting work. A certificate arriving before local ordered input stays pending or triggers authenticated-history recovery. It cannot settle unresolved order.

Keep speculative and canonical state separate. Execute produces branch results without canonical commit authority. Commit and state sync apply only results bound to proven exact ordered input and the correct canonical predecessor. Both share the canonical single writer. An arriving sync result cannot drop an ongoing canonical mutation or bypass it through a competing writer. Switching, race, and failure contracts remain open.

## Open decisions

| Item | Decision |
|---|---|
| Runtime / transaction semantics | |
| QMDB database variant / state encoding / root type | |
| Canonical operations / batch-boundary derivation / logical-root integration | |
| Scope of Stateful actor reuse | |
| Branch key / checkpoint granularity | |
| Execution scheduling / cancellation / worker-fencing contract | |
| Atomic commit of state / outputs / cursor | |
| Branch pruning / memory / disk budget | |
| Replay / checkpoint / state sync | |
| Query interface / certified-result integration | |
