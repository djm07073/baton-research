# Roles and terminology

**Each module has one main job.** TxPool manages transaction candidates, BlockService manages block bodies, Orderer delivers the agreed order, Baton schedules speculative work, Executor manages the execution tree, transaction effects, certification, and state. The tables below define their exact responsibilities and the facts each result establishes.

## Roles and terms

Use the five module names below consistently. Words such as `owner`, `controller`, and `adapter` describe internal responsibilities or Commonware integration points. They do not introduce extra top-level modules. A trait boundary also does not determine how many actors, crates, or servers to deploy.

| Module | Main responsibility | Detailed contract |
|---|---|---|
| `TxPool` | Admit and retain transactions; analyze static payload features and policy; select batches; track results | [Tx interfaces](../tx/interfaces.md#interface-overview) |
| `BlockService` | Build, durably store, distribute, fetch, and retain custody of producer bodies | [Block body interfaces](../consensus/block-body.md#interface-overview) |
| `Orderer` | Interpret native evidence and history; deliver finalized execution order | [Ordered input](../consensus/ordered-input.md#consensus-and-baton-integration) |
| `Baton` | Collect intended-order reports, select and disseminate direction, request speculative blocks | [Baton interfaces](../baton/interfaces.md#interface-overview) |
| `Executor` | Link execution-tree parents; compute transaction effects; execute, promote, prune, certify, sync, and recover | [Execution interfaces](../execution/interfaces.md#interface-overview) |

Static policy methods belong to TxPool. Direction selection belongs to Baton. Transaction computation and result certification belong to Executor; Runtime and ResultService are no longer separate application traits. Commonware runtime means task/I/O infrastructure, not our transaction executor. Module boundaries do not prescribe separate actors or crates. Keep upstream names such as `Multimmit`, `Automaton`, `Relay`, `Reporter`, and `DatabaseSet` unchanged.

| Data name | Meaning and completion condition |
|---|---|
| `StoredBody` | Durable local custody of a body and required parent material. Native header authentication is a separate step. |
| `CandidateBlock` | An authenticated producer header joined with the matching StoredBody in the exact context. Cut inclusion and final order remain separate. |
| `Executor::Block` | A parent-linked execution-tree input: block hash, parent block hash, exact input/body references, and execution context. Its parent is an execution predecessor, not one producer lane's header parent. |
| `Report` / `Direction` | A report of intended execution order / the leader's advisory ordering guidance. Baton is the module; direction is the message. |
| `PreparedPolicy` | A proposal-binding candidate from completed evaluation of valid candidates. The native owner still rechecks and adopts it in the actual context. |
| `OrderedRange` | A continuous, irreversible sequence of exact execution inputs established from authenticated history. |
| `Checkpoint` | Completed work for a particular base state, runtime, and input prefix that may be reused. It is not a raw QMDB batch. |
| `ExecutionResult` | Checkpoint, context, and outputs of completed speculative execution. It does not establish canonical application. |
| `CommitResult` | Durable local application of the exact ordered range, with state, outputs, and cursor recoverable together. |
| `ExecutionStatement` / `ResultCertificate` | The signed subject binding exact range, base, runtime, and result / f+1 distinct eligible signatures on that same subject. |

Producer, validator, leader, and non-leader are node **roles**. A cut is a native finality event. The **immutable ordering frontier** ends the input prefix that direction cannot rearrange. `AppliedCursor` records how far local state has been durably applied. Keep these boundaries separate, along with the completion conditions of ExecutionResult, CommitResult, and ResultCertificate.

<details>
<summary>Mapping older names to the current names</summary>

| Earlier name | Current name |
|---|---|
| ExecutionController / scheduling controller | Baton admits scheduling messages; Executor owns execution-tree scheduling |
| Planner / reschedule request | Baton::plan / parent-linked Executor::execute; no separate trait or reschedule API |
| BranchOwner / CanonicalApplyOwner / Execution owner | Executor's branch management / canonical single writer |
| TxPolicy | TxPool::analyze / classify |
| Application runtime | Transaction execution inside Executor |
| ExecutionSigner / ResultCollector | Executor's sign_result / collect_result responsibilities |
| BodyService / body builder / custody adapter | Internal BlockService responsibilities |
| ProofArchive / HistoryResolver / ordered delivery / Marshal responsibilities | Orderer's history retention, interpretation, and delivery. Distinct from the upstream Marshal trait. |
| BodyReady / BlockAvailable | StoredBody / CandidateBlock; keep both stages |
| BranchReady / speculative outcome | ExecutionResult |
| CommitApplied / durable commit result | CommitResult |
| OnBlockAvailable / OnCommitApplied | Baton::on_block / on_commit; local input / optional applied notification |
| OnOrderedRange / earlier commit delivery through Baton | Orderer → Executor::commit; direct delivery |

</details>

Producer and validator are separate roles; a node may perform both. Leader direction must reach producers and the validator Baton instances responsible for the affected execution. Sending only to producers does not establish that every Executor received it.

**A native producer-parent header ID differs from an application input state root.** One producer lane's parent does not determine the execution state of a merged multi-lane order. Also distinguish the body digest, producer header ID, leader proposal ID, and canonical ordered-input ID.

Fixing each producer prefix still leaves the exact merged execution order to establish. Once verified, that continuous input becomes an OrderedRange. [Canonical delivery](../e2e/canonical.md#cut-commit--ordered-range--execution-commit) explains history gaps and ordering settledness.

Transactions live in the [producer payload/body](../e2e/block-body.md#block-lifecycle-mempool--propose--body-dissemination). The native leader proposal gathers ordering evidence across lanes and is itself transaction-free. [Proposal freeze](../e2e/leader.md#planning-completion-versus-proposal-freeze) explains how Baton policy is attached to its actual proposal context.
