# Baton interfaces and local progress notifications

**Baton coordinates advisory order and delivers confirmed input; Executor owns execution completion.** Baton handlers admit blocks and scheduling messages and plan direction inside Baton or request parent-linked execute work. Baton also accepts native finality/history through on_finality and internally delivers continuous exact ranges to Executor. Advisory applied progress remains an optional notification and requires no reply.

## Interface overview

Rust declaration: [Baton](../overview/rust-interfaces.md#baton). The Rust interfaces page owns the complete declaration.

`Context` binds the leader view, history, actual parent, rule, window, and immutable ordering frontier. It is not assumed to be the same type as upstream `Automaton::Context` for the body attachment. `on_block` admits a CandidateBlock whose body and authenticated header have been joined, then sorts eligible not-yet-started candidates, preserving completed/current execution order. It does not immediately append the block in arrival order. While the predecessor runs, this only updates the queue. Before dispatch, Baton rechecks pending order and uses the valid predecessor checkpoint. Reports use the same fixed prefix plus sorted pending sequence. A StoredBody notice alone is insufficient. Baton reception and the Commonware attachment perform the join and handler call.

The `on_*` handlers check context, admit local inputs, and schedule work. A task driver runs Baton planning jobs and Executor execution jobs and returns completion to handlers. Driver, queue, and task placement remain open; this contract adds no mandatory actor count. Baton planning completes through `on_planned(context, policy)`, which checks the original window and context before updating prepared state. Late or stale completion cannot overwrite a new context. `on_execution` receives only completed valid checkpoints; failure, incomplete-job notification, and retry contracts remain open in the Execution decisions. `prepared_policy()` is an immediate query that returns only a completed valid candidate currently available. Native Core rechecks actual context and freezes policy; the cut does not wait for `Some`.

| Proposed interface | Source | Responsibility and next output |
|---|---|---|
| `Baton::plan` | Leader Baton after once-closed report snapshot | Evaluate bounded admissible candidates → optional completed PreparedPolicy; native cut never awaits it |
| `Baton::on_block` | Consensus body attachment | Validate reference/context → sort pending only → dispatch after valid predecessor completion |
| `Baton::on_context` | Native owner hook | Manage exact context / immutable frontier → window / Baton::plan input |
| `Baton::on_report` | Report connection | Verify signature, context, identity, limits → leader snapshot admission |
| `Baton::on_finality` | Native exact evidence/history handoff | Admit independent processing → verified history → continuous OrderedRange → Executor::commit; observe durable completion internally |
| `Baton::on_direction` | Current leader | Authenticate and check context → parent-linked Executor::execute(block) |
| `Baton::on_planned` / `prepared_policy` | Baton planning completion → Baton → native owner | Check original request; retain prepared state → immediate query → actual proposal-context recheck |
| `Baton::on_execution` | Executor | Check result context → observe completed local work; tree links and workers remain Executor-owned |
| `Baton::on_commit` | Optional local applied notification from Executor | Update scheduling progress; no approval of delivery ACK, pool cleanup, or result certification |

Sending or handling `on_commit` does not condition Executor application, certification, state sync, or delivery acknowledgement. Executor proceeds without a Baton reply. `Baton::on_*` are local handlers, not separate wire messages. Successful return reports local handling or scheduling, not direction approval or a remote ACK. ExecutionResult represents completed speculative execution; its codec and concrete fields remain open.

## Finalized-state progress notifications

Baton independently verifies/retains native evidence and delivers confirmed exact ranges to Executor. Executor applies its direct result or verified peer state material. The internal delivery path observes the returned durable CommitResult and updates recoverable cursors; canonical tx outcomes feed internal pool maintenance. Advisory scheduling does not approve commit or delay this bookkeeping. Recovery/backfill and redelivery are internal Baton responsibilities; no extra public polling or ACK API is required.

Baton may consume a local applied-progress notification to avoid scheduling inputs that have already become canonical. Sending, handling, or replying to that notification is not a condition for state finalization, sync, or canonical application. Executors exchange f+1 result certification and change sets directly.

Confirmed-order processing is independent of report windows and planning tasks. Executor peer signatures, certificates and state-sync material continue to travel directly between Executors; Storage remains the canonical writer. See [native evidence and delivery details](../consensus/ordered-input.md#consensus-and-baton-integration).
