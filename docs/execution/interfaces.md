# Executor, Runtime, and result certification interfaces

**Runtime computes; Executor coordinates and persists; ResultService certifies.** Runtime receives a valid branch state and computes transaction effects. Executor manages branch lifecycle, peer communication, and canonical application. Its internal ResultService signs and verifies execution results.

## Interface overview

Rust declarations: [Executor](../overview/rust-interfaces.md#executor) and [Runtime](../overview/rust-interfaces.md#runtime). The Rust interfaces page owns the complete declarations. Each async method returns a Future with `Result<SuccessType, Self::Error>` as its output. The table uses associated types from the trait and describes the successful value; Error is a separate failure result.

`ExecuteRequest` identifies an exact base checkpoint, input order, runtime identity, and generation. `RescheduleRequest` identifies the new request and superseded generation. Concrete struct layouts remain open. Success from `execute` or `reschedule` means a completed ExecutionResult for the requested prefix; cancellation or incomplete work is not success. `commit` validates exact OrderedRange, predecessor, and evidence, executes missing work, and returns CommitResult only after state, outputs, and cursor are recoverably durable. Advisory cancellation cannot drop a canonical mutation future. Failures or lost completions follow the QMDB recovery contract.

`Runtime::State` supplies valid branch-scoped access for the selected QMDB variant. Do not assume QMDB provides a generic KV API or immutable historical snapshots. `Runtime::Input` carries transactions/body and runtime context; `Output` carries application results and outputs. Runtime cannot promote a branch or determine native order. Executor cannot adopt a branch that failed after partial writes as a completed checkpoint. `read` is limited to retained versions and readiness; certification is a separate ResultService boundary.

| Proposed interface | Input | Responsibility | Result |
|---|---|---|---|
| `Executor::execute` | `Self::ExecuteRequest`: base, order, runtime, generation | Fork from parent branch → execute Runtime → produce batch / outputs | `Self::ExecutionResult`: completed checkpoint/context/outputs |
| `Executor::reschedule` | `Self::RescheduleRequest`: order/context and superseded generation | Verify reusable prefix → cancel old suffix → execute new suffix | `Self::ExecutionResult`: completed new-request prefix |
| `Executor::commit` | `Self::OrderedRange`: exact range, predecessor, evidence | Match completed work or execute missing work → apply canonically to QMDB | `Self::CommitResult`: recoverable durable application |
| `Executor::recover` | `Self::Recovery`: durable state / outputs / cursor | Restore canonical checkpoint; reconstruct transient branches | `Self::Checkpoint`: recovered execution base |
| `Executor::read` | `Self::Query`: retained canonical state query | Read retained state at that commit | `Self::ReadResult`: state/outputs and readiness |

Startup/recovery integration calls `Executor::recover`; query callers use `Executor::read`. A branch handle does not replace context validation. Check at least base-state identity, runtime/version, exact input prefix, generation, and canonical cursor binding.

Executor supplies Runtime with exact input transaction/body bytes, runtime identity, and valid branch-scoped state access. Runtime returns pending mutations, outputs, and execution results. Executor retains authority over checkpoint context and canonical application. This describes a new runtime integration contract, without asserting direct compatibility with existing `stateful::Application`.

A transaction outcome computed by Runtime differs from a worker failing to finish its requested execution attempt. Executor cannot adopt an unfinished range as a completed branch outcome. State/output semantics of transaction failure, incomplete-attempt notifications to Baton, and retry policy remain undecided.

Local readiness through `Executor::read` is separate from f+1 result certification. See [Result signing and certification](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [Executor peer state sync](state-sync.md#state-sync-from-certified-execution-results).

## Result certification trait

ResultService operates inside Executor. Executor receives peer messages and passes them to `collect` / `verify`. Successful verification can establish state finalization or allow the state-sync material verification and application path to proceed. A successful certificate query does not establish material availability or local durable application. Concrete peer transport, codec, request/response, and sync-switching APIs remain open.

Rust declaration: [ResultService](../overview/rust-interfaces.md#resultservice). The Rust interfaces page owns the complete declaration.

`sign` validates own direct execution/validation provenance and the binding to irrevocable exact range, canonical input state, and runtime before creating the full statement. A result for an advisory speculative order alone cannot be signed. ImportedVerified cannot be relabeled as own direct execution. Correctness of the signed result and local apply/durability are separate. Per-block or per-chunk common signing boundaries remain undecided. Retain own statement/signature obligations according to the selected recovery contract.

`collect` verifies the exact full statement and signatures from distinct eligible epoch identities. Fewer than f+1 produces `Ok(None)` and adds no barrier to subsequent execution or native cut. `verify` returns a statement only after checking signatures, irrevocable exact order, and canonical input-state chain. One primitive `Verifier::verify` call does not implement this full application verification. `certificate` returning `None` means no certified result is available yet, distinct from absent local state. Serving the original certificate and signing own direct work are separate paths. Key, domain, codec, root type, common boundary, and retention remain open.
