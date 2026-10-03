# Baton: roles and reports

**Baton decides what speculative work to start or change.** It manages intended-order reports and advisory directions so Executors can begin useful work before order is final. Executor owns state finalization and state sync.

## Roles and responsibilities

Baton receives candidate blocks from the consensus attachment and schedules speculative execution. It forms an intended order from locally known inputs and exchanges reports. The leader asks Executor to evaluate the report snapshot, then disseminates the prepared direction. Non-leaders use a valid direction to adjust their execution plans. Orderer and Executor directly handle finalized input delivery, canonical application, state finalization, and state sync. These paths require no Baton approval or acknowledgement.

**Baton** owns report admission, direction messages, and speculative block requests. **Executor** owns planning, parent-linked execution branches, canonical promotion, and pruning. **Runtime** computes transaction effects. Executor serializes canonical application through a single writer. Native signing, voting, and finality authority remain with consensus.

## Report connection

Use Commonware P2P to carry authenticated window context, intended-order reports, and advisory directions. Messages bind epoch, view, history, actual parent, rule, window, and immutable frontier. A leader-local timer does not establish that remote nodes know the window.

A report expresses **execution intent**. It is not execution progress, a state root, a completion proof, or a direction vote. Count one valid original report per identity in the same window. Worker verification and admission into the leader-owned snapshot are separate events. Reports that arrive after closure cannot enter that snapshot.
