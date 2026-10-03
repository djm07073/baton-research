# Executor interfaces and result certification

**Executor owns execution, tree handling, and result certification.** It links children to valid parent states, computes transaction effects, promotes the canonical path, and certifies or imports results. Baton owns direction selection.

## Interface overview

Rust declaration: [Executor](../overview/rust-interfaces.md#executor). Transaction computation, execution-tree handling, canonical application, and result certification belong to this one interface. Each async method returns a Future with `Result<SuccessType, Self::Error>` as its output.

`Executor::Block` carries a block hash, parent block hash, exact ordered body/input references, and execution context. The parent resolves an execution checkpoint with the same base, application rules, and exact preceding input; it is not simply a producer-header parent. `execute(block)` validates that parent, links the child, and computes its transaction effects on branch-scoped state. Missing or unfinished parents leave work pending or require recovery. Reuse requires identical completed work and context; a partial or canceled attempt is not successful ExecutionResult. Hash encoding and concrete fields remain open.

Direction selection belongs to [Baton::plan](../baton/direction.md). Direction changes submit parent-linked blocks through execute(block); task priority, reuse, and stale-result fencing remain internal to Executor. No separate planning, Runtime, ResultService, or reschedule interface is needed for tree handling.

`commit(range)` validates irrevocable exact input and its canonical predecessor, completes missing work, and promotes the matching execution path. It fences conflicting workers and logically prunes conflicting branches while retaining valid descendants. Physical deletion waits for worker references and required query, result, sync, and recovery retention. CommitResult means state, outputs, and cursor are recoverably durable. Advisory cancellation cannot drop a canonical mutation future.

| Proposed interface | Input | Responsibility | Successful result |
|---|---|---|---|
| `Executor::execute` | `Self::Block`: hash, execution-parent hash, exact inputs/context | Link a valid parent → compute transaction effects or reuse matching completed work | `Self::ExecutionResult` |
| `Executor::commit` | `Self::OrderedRange`: exact input, predecessor, evidence | Promote canonical path → durable QMDB application → prune conflicting branches | `Self::CommitResult` |
| `Executor::recover` | `Self::Recovery`: state / outputs / cursor | Restore canonical checkpoint; reconstruct only valid branches | `Self::Checkpoint` |
| `Executor::read` | `Self::Query`: retained canonical version | Read retained state and readiness | `Self::ReadResult` |
| `Executor::sign_result` | `Self::ExecutionResult` | Check direct-execution provenance and irrevocable input before signing | `Self::SignedStatement` |
| `Executor::collect_result` | `Self::SignedStatement` | Check full subject and eligible distinct identities; collect f+1 matches | `Option<Self::ResultCertificate>` |
| `Executor::verify_result` | `Self::ResultCertificate` | Verify signatures, exact order, and canonical input-state chain | `Self::ExecutionStatement` |
| `Executor::result_certificate` | `Self::ResultQuery` | Query retained certification for an exact subject | `Option<Self::ResultCertificate>` |

Application transaction rules execute inside Executor against valid branch-scoped QMDB access. Commonware task runtime drives jobs and I/O; it does not supply those application rules. QMDB provides storage batches, roots, and durability rather than a transaction VM. Concrete execution semantics remain undecided. An attempt that failed after partial writes cannot be adopted as completed work. Internal helpers or worker tasks can organize implementation without adding a public trait or service for each responsibility.

Startup calls recover; state callers use read. Check base-state identity, application version, exact input prefix, worker generation, and canonical cursor binding before reuse. A readable result and a certified result remain different milestones. See [result certification](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [state sync](state-sync.md#state-sync-from-certified-execution-results).

<a id="result-certification-trait"></a>

## Result certification inside Executor

Executor receives peer messages and handles them through `collect_result` / `verify_result`. Successful verification can establish state finalization or allow the state-sync material verification and application path to proceed. A successful certificate query does not establish material availability or local durable application. Reuse Commonware Signer / Verifier and authenticated P2P. Those primitives verify signatures and transport bytes; Executor must bind the application statement, validate its irrevocable input and eligible epoch identities, and enforce f+1 matching subjects. That application verification remains necessary, without a standalone ResultService module. Concrete peer codec, request/response, and sync-switching APIs remain open.

Rust declaration: [Executor](../overview/rust-interfaces.md#executor). The Rust interfaces page owns the complete declaration.

`sign_result` validates own direct execution/validation provenance and the binding to irrevocable exact range, canonical input state, and runtime before creating the full statement. A result for an advisory speculative order alone cannot be signed. ImportedVerified cannot be relabeled as own direct execution. Correctness of the signed result and local apply/durability are separate. Per-block or per-chunk common signing boundaries remain undecided. Retain own statement/signature obligations according to the selected recovery contract.

`collect_result` verifies the exact full statement and signatures from distinct eligible epoch identities. Fewer than f+1 produces `Ok(None)` and adds no barrier to subsequent execution or native cut. `verify_result` returns a statement only after checking signatures, irrevocable exact order, and canonical input-state chain. One primitive `Verifier::verify` call does not implement this full application verification. `result_certificate` returning `None` means no certified result is available yet, distinct from absent local state. Serving the original certificate and signing own direct work are separate paths. Key, domain, codec, root type, common boundary, and retention remain open.
