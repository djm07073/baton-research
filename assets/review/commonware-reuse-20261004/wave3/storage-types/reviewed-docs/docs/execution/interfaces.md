# Executor interfaces and result certification

**Executor owns execution paths and result certification; Storage owns roots and durable state.** Executor links children to valid parents, computes completed changes, selects the canonical path and certifies or imports results. Baton owns direction selection.

## Interface overview

Rust declarations: [Executor](../overview/rust-interfaces.md#executor) and [Storage](../overview/rust-interfaces.md#storage). Each async application method returns a Future with `Result<SuccessType, Self::Error>` as its output. These are integration boundaries, not replacements for QMDB algorithms or separate deployment requirements.

`Executor::Block` carries a block hash, parent block hash, exact ordered body/input references, and execution context. The parent resolves an execution checkpoint with the same base, application rules, and exact preceding input; it is not simply a producer-header parent. `execute(block)` validates that parent, links the child, and computes its transaction effects on branch-scoped state. Missing or unfinished parents leave work pending or require recovery. Reuse requires identical completed work and context; a partial or canceled attempt is not successful ExecutionResult. Hash encoding and concrete fields remain open.

Direction selection belongs to [Baton::plan](../baton/direction.md). Direction changes submit parent-linked blocks through execute(block); task priority, reuse, and stale-result fencing remain internal to Executor. No separate planning, Runtime, ResultService, or reschedule interface is needed for tree handling.

`execute(block)` returns completed unsealed effects and outputs. Storage prepares a root only when a selected storage/signing boundary needs it. Upstream sealed-parent child batches can be reused directly; rootless children require the additional read/effects adapter described in [QMDB](qmdb.md#defer-roots-without-inventing-an-unsealed-parent-fork).

`commit(range)` validates irrevocable exact input and its canonical predecessor, completes missing work, and selects the matching execution path. It calls Storage to prepare/apply exact material, fences conflicts and logically prunes branches while retaining valid descendants. Storage controls physical reclamation after worker/query/result/sync/recovery references permit it. CommitResult means state, outputs, cursor and provenance are recoverably durable. Advisory cancellation cannot drop a canonical mutation future.

| Proposed interface | Input | Responsibility | Successful result |
|---|---|---|---|
| `Executor::execute` | `Self::Block`: execution-parent hash, exact inputs/context | Link valid parent → compute or reuse completed changes/outputs without compulsory hashing | `Self::ExecutionResult` |
| `Executor::commit` | `Self::OrderedRange`: exact input, predecessor, evidence | Select canonical path → Storage preparation/application → logical pruning | `Self::CommitResult` |
| `Executor::recover` | `Self::Recovery` | Coordinate Storage recovery; rebuild only valid execution branches | `Self::Checkpoint` |
| `Storage::prepare` | Completed `ExecutionResult`, selected `Preparation` | Materialize exact prefix, merkleize and bind rule/result/outputs/material | `Self::PreparedResult` |
| `Storage::apply` | Authorized `CanonicalInput`, `PreparedResult` | Check applicability/writer; apply and complete durable linkage | `Self::CommitResult` |
| `Storage::recover` / `read` | Recovery context / retained-version query | Restore durable bases/provenance / read readiness and outputs | `Self::Checkpoint` / `Self::ReadResult` |
| `Executor::sign_result` | `Self::PreparedResult` | Require computed commitment, own direct provenance and irrevocable input before signing | `Self::SignedStatement` |
| `Executor::collect_result` | `Self::SignedStatement` | Check full subject and eligible distinct identities; collect f+1 matches | `Option<Self::ResultCertificate>` |
| `Executor::verify_result` | `Self::ResultCertificate` | Verify signatures, exact order, and canonical input-state chain | `Self::ExecutionStatement` |
| `Executor::result_certificate` | `Self::ResultQuery` | Query retained certification for an exact subject | `Option<Self::ResultCertificate>` |

Application transaction rules execute inside Executor against Storage-provided valid branch access. Commonware task runtime drives jobs/I/O; QMDB provides batches, roots and persistence rather than transaction semantics. Partial or canceled work cannot be adopted as a completed result. Worker generations and storage writer/retention metadata are local authority fields, not shared execution-signature fields. The stable statement binds exact range/base/runtime/rule/result and chosen output/material commitments.

Startup calls recover; state callers use read. Check base-state identity, application version, exact input prefix, worker generation, and canonical cursor binding before reuse. A readable result and a certified result remain different milestones. See [result certification](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [state sync](state-sync.md#state-sync-from-certified-execution-results).

<a id="result-certification-trait"></a>

## Result certification inside Executor

Executor receives peer messages and handles them through `collect_result` / `verify_result`. Successful verification can establish state finalization or allow the state-sync material verification and application path to proceed. A successful certificate query does not establish material availability or local durable application. Reuse Commonware Signer / Verifier and authenticated P2P. Those primitives verify signatures and transport bytes; Executor must bind the application statement, validate its irrevocable input and eligible epoch identities, and enforce f+1 matching subjects. That application verification remains necessary, without a standalone ResultService module. Concrete peer codec, request/response, and sync-switching APIs remain open.

Rust declaration: [Executor](../overview/rust-interfaces.md#executor). The Rust interfaces page owns the complete declaration.

`sign_result` uses a Storage-prepared commitment plus Executor-retained own direct execution/validation evidence. Preparation preserves the selected rule and exact input/base/result/outputs binding; it cannot turn an imported result into direct execution. Complete effects → Storage root preparation → full statement → signature is the order. Advisory speculative order alone cannot be signed. Correctness and local durability remain separate. Per-block/per-chunk boundaries and root/encoding choices remain open; retain statement/provenance obligations through recovery.

`collect_result` verifies the exact full statement and signatures from distinct eligible epoch identities. Fewer than f+1 produces `Ok(None)` and adds no barrier to subsequent execution or native cut. `verify_result` returns a statement only after checking signatures, irrevocable exact order, and canonical input-state chain. One primitive `Verifier::verify` call does not implement this full application verification. `result_certificate` returning `None` means no certified result is available yet, distinct from absent local state. Serving the original certificate and signing own direct work are separate paths. Key, domain, codec, root type, common boundary, and retention remain open.
