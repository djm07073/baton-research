# Baton: roles and reports

**Baton decides what speculative work to start or change.** It manages intended-order reports and advisory directions so Executors can begin useful work before order is final. Executor owns state finalization and state sync.

## Roles and responsibilities

Baton receives candidate blocks from the consensus attachment and schedules speculative execution. It forms an intended order from locally known inputs and exchanges reports. The leader evaluates the report snapshot inside Baton, then disseminates the prepared direction. Non-leaders use a valid direction to adjust their execution plans. Orderer and Executor directly handle finalized input delivery, canonical application, state finalization, and state sync. These paths require no Baton approval or acknowledgement.

**Baton** owns report admission, direction messages, and speculative block requests. **Baton** also selects direction. **Executor** owns parent-linked execution branches, transaction effects, result certification, canonical promotion, and pruning. Executor serializes canonical application through a single writer. Native signing, voting, and finality authority remain with consensus.

## Report connection

Use Commonware P2P to carry authenticated window context, intended-order reports, and advisory directions. Messages bind epoch, view, history, actual parent, rule, window, and immutable frontier. A leader-local timer does not establish that remote nodes know the window.

A report expresses **execution intent**. It is not execution progress, a state root, a completion proof, or a direction vote. Count one valid original report per identity in the same window. Worker verification and admission into the leader-owned snapshot are separate events. Reports that arrive after closure cannot enter that snapshot.

## Commonware primitives in the Baton layer

**Baton selects direction; its infrastructure should reuse Commonware rather than add a second networking or task framework.** `Baton::plan` consumes the fixed report snapshot and candidate set. Executor owns the execution tree.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_p2p::authenticated`, `Sender`, `Receiver` | Report and direction logical channels on the existing network | Message admission, one report per eligible identity, context correlation and bounded retention |
| `commonware_cryptography::{Signer, Verifier}` and `commonware_codec::Codec` | Authenticate reports/direction and encode bounded policy subjects | Exact epoch/view/history/parent/rule/window/frontier binding and frozen proposal interpretation |
| `commonware_runtime::Clock` and runtime tasks; `commonware_actor::Feedback` | Fixed report deadline, bounded planning task and local completion delivery | Close once at first 4f+1 valid reports or deadline; correlate completed work to its original context |
| `commonware_parallel` (candidate) | Bounded candidate evaluation or cryptographic work if profiling justifies it | Entire-prefix support checks, sum-LCP scoring and deterministic tie rules; the parallel framework does not implement the policy |

Do not use a request/response collector to introduce direction acknowledgements or a readiness quorum. Cut reads an already prepared valid result or uses the admissible base path; it never waits for reports, the timer or planning. Commonware supplies mechanisms, while the direction-preserving native integration remains an open proof obligation.

See [versioned primitive evidence and compatibility checks](../reference/integration.md#primitive-reuse-catalog).
