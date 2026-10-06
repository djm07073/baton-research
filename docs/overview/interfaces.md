# Reading the interfaces

**The traits show who calls whom and what each call establishes.** Read the complete declarations in [Rust interfaces](rust-interfaces.md). These are proposed application contracts; distinguish them from APIs that already exist in Commonware.

## How to read the Rust traits

The traits are **Rust design drafts for new application integration**. They are neither copies of native Commonware traits nor implemented crates. Associated `type` declarations leave concrete fields, codecs, identities, limits, and runtime placement to the open-decision tables. Naming a type does not adopt a wire schema or policy.

| Call flow | Trait method |
|---|---|
| Client / tx peer → pool | `TxPool::admit` |
| Producer request → tx selection → body preparation | Upstream `Automaton::propose` → `TxPool::select` |
| Peer body → custody / lookup | Upstream `Automaton::verify` → buffer/resolver/archive handles |
| Authenticated candidate → speculative execution | `Baton::on_block` → `Executor::execute` → internal transaction computation |
| Reports → direction → execution plan change | `Baton::on_report` → `Baton::plan` → `Baton::on_direction` → `Executor::execute(block)` |
| Native evidence → finalized order → local state application | `Baton::on_finality` → internal exact-order delivery` → `Executor::commit` → `Storage::prepare/apply` |
| Durable completion → delivery acknowledgement and pool update | Executor commit result → internal Baton delivery tracking; pool maintenance consumes canonical tx outcomes; advisory progress notification is optional |
| Executor's directly executed result → signature and certified query | `Executor::sign_result` / `collect_result` / `result_certificate`; peer transport is Executor ↔ Executor |

Connect the associated types below to the same concrete types during assembly. Matching trait names do not connect them automatically in Rust. Receivers must still validate context, identity, and evidence.

| Type connection | Meaning |
|---|---|
| `Baton::Context` / `Baton::PreparedPolicy` | Same-context selection inside Baton → native actual-context recheck hook |
| `Executor::OrderedRange` | Baton internally builds and delivers continuous finalized input; no extra public Baton range type |
| `Executor::ExecutionResult = Baton::ExecutionResult = Storage::ExecutionResult` | Completed changes/outputs → local context checks or selected root preparation |
| `Storage::PreparedResult = Executor::PreparedResult` | Computed commitment and binding → own direct-result signing after irrevocable-order checks |
| `Storage::CommitResult = Executor::CommitResult` | Recoverably durable application → canonical promotion and delivery handoff |
| `Executor::CommitResult = Baton::CommitResult` | Durable completion → internal delivery tracking; advisory on_commit is optional. Pool maintenance uses the backend outcome mapping internally |

`CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.

`Executor::Block` is assembled from authenticated CandidateBlock inputs plus their execution-parent hash and exact context. A CandidateBlock or a producer-header parent alone is not the execution-tree input. The concrete hash encoding remains open.

`&mut self` describes Rust ownership of the call handle. It does not serialize all branch computations or automatically enforce a database single writer. Shared handles, worker concurrency, canonical writer authority, and fencing need implementation. `impl Future + Send` follows a declaration style similar to Commonware callbacks; async runtime, dynamic dispatch, and boxing remain undecided.

`Baton::on_*` and upstream `Relay::broadcast` establish local admission or scheduling boundaries. Native Reporter and Relay synchronous callbacks must not wait for slow I/O through these methods. Baton finality intake schedules independent evidence/history and delivery work; it never waits for report-window closure or planning. Internal delivery observes Executor commit completion directly, regardless of the optional advisory on_commit handler. Futures describe application work, without adding native cut waits for reports, planning, or direction replies. `Executor::commit` orchestrates canonical selection; Storage owns the shared canonical mutation, which must not be canceled like an advisory job. Baton planning runs from an admitted snapshot in background workers; its future cannot block the immediate prepared-policy query or native cut. Executor tree handling proceeds independently through execute/commit.

## Finding calls in E2E cases

| Case | Sequence |
|---|---|
| Client admission through durable canonical application | [Normal E2E](../e2e/normal.md#full-e2e-transaction-input-to-canonical-state) |
| New, duplicate, and structurally invalid transactions | [Tx lifecycle](../e2e/normal.md#tx-lifecycle-new-duplicate-and-invalid-transactions) |
| Producer DA, leader proposal, voting, and local finality | [Native consensus](../e2e/native-consensus.md#normal-native-consensus-producer-da--leader-proposal--finality) |
| Body build, peer custody, missing or invalid body | [Propose](../e2e/block-body.md#block-lifecycle-mempool--propose--body-dissemination), [Verify](../e2e/block-body.md#body-lookup-verification-and-missing-content-handling) |
| Leader selection / dissemination and non-leader branch execution | [Leader](../e2e/leader.md#leader-lifecycle-collect-reports-and-disseminate-direction), [Non-leader](../e2e/reschedule.md#non-leader-lifecycle-direction-and-branch-execution) |
| Cut interpretation, gaps, matching branches, flush failures | [Ordered range](../e2e/canonical.md#cut-commit--ordered-range--execution-commit), [QMDB commit](../e2e/canonical.md#execution-lifecycle-qmdb-branches-and-canonical-promotion) |
| Redelivery of applied ranges and native startup | [Restart delivery](../e2e/recovery.md#restart-and-backfill), [Startup custody](../e2e/recovery.md#startup-prepare-custody-before-native-recovery) |
| Validator imports a certified result and stops remaining execution | [State sync](../e2e/state-sync.md#state-sync-from-certified-execution-results) |
| f+1 result certification and late planning completion | [Result endpoint](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification), [Proposal freeze](../e2e/leader.md#planning-completion-versus-proposal-freeze) |
