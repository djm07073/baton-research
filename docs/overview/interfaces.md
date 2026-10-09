# Reading the application connections

**Start with the existing callback and follow the work it starts.** The [Rust reference](rust-interfaces.md) contains Commonware API excerpts. App pool, scheduler, execution and state functions are internal implementation choices, not a new public trait graph.

<a id="how-to-read-the-rust-traits"></a>

## Call flow and completion

| Entry | App work | Completion boundary |
|---|---|---|
| Client / transaction peer | Validate and retain pool candidates | Admission, not canonical inclusion |
| `Automaton::propose` | Select batch, construct producer block, stage in Marshal | Body digest through the returned receiver; local custody verification follows |
| `Automaton::verify` | Validate payload/custody and record usable scheduler input | Validity through the returned receiver; no speculative execution wait |
| Optional native `Reporter<Activity>` | Correlate native observations | Best-effort hint |
| Marshal `Reporter<Update>` | Retain canonical index, full block and ACK | Immediate local handoff |
| App canonical worker | Reuse/repair exact work and durably apply | ACK; Marshal cursor persistence is separate |
| Peer execution messages | Validate exact results and applicable state material | Result certification or safe import, independent of Baton reports |

Names such as candidate admission, dispatch, canonical reconciliation and apply describe private application code. They add no native method or mandatory actor. `&mut self` refers to a callback handle; it neither serializes all workers nor supplies a database writer fence. Existing cloneable handles and Commonware channels connect an App owner to asynchronous work.

## Read the detailed contract once

| Question | Canonical page |
|---|---|
| What goes inside App, and what does Marshal already implement? | [Application connection guide](../baton/README.md) |
| What does verify do; how are local, remote, recovery and repeated calls handled? | [Callback behavior and pseudocode](../baton/interfaces.md#automatonverify-validity-custody-and-scheduling) |
| What exactly waits for ACK and how does crash redelivery work? | [Update, queue and durability contract](../baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack) |
| Which digest, parent, index or context does a value identify? | [Terminology](glossary.md), [Rust types and callbacks](rust-interfaces.md) |
| How do Pre-cut and Baton differ, and what native work remains? | [Schedulers and policy gap](../baton/direction.md) |
| How are execution effects, roots, writer access and imported results connected? | [Execution](../execution/interfaces.md), [QMDB](../execution/qmdb.md), [State sync](../execution/state-sync.md) |

Use types from one resolved Commonware dependency graph; matching names or digest bytes across versions do not establish Rust type compatibility. Native Activity and Marshal Update need separate typed reporter handles when both enter one App, because Reporter has one associated Activity per implementation.

## Finding calls in E2E cases

| Case | Page |
|---|---|
| Transaction through durable application | [Normal flow](../e2e/normal.md) |
| Propose, relay, verify and missing body | [Body exchange](../e2e/block-body.md) |
| Producer DA, leader proposal and native finality | [Native consensus](../e2e/native-consensus.md) |
| Report windows, direction and proposal freeze | [Leader](../e2e/leader.md) |
| Pending sorting and exact-parent dispatch | [Scheduling](../e2e/reschedule.md) |
| Update, reuse/repair, durable apply and ACK | [Canonical flow](../e2e/canonical.md) |
| Startup, restart and redelivery | [Recovery](../e2e/recovery.md) |
| Result signatures and certified import | [Results](../e2e/results.md), [State sync](../e2e/state-sync.md) |
