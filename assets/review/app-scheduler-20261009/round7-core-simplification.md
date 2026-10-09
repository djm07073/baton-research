# Round 7: simplify the first core implementation read

Reviewer: `/root/docs_alignment`, 2026-10-09 07:49 UTC. Read-only review of current `docs/baton/{README,interfaces,direction}.md` and `docs/overview/interfaces.md` against existing current companion pages. No core page or diagram was changed. At most three changes are recommended below; none changes a protocol decision or removes an owner check.

The main sequence is now clear: staged proposal → validity/custody with independent candidate admission → exact-parent dispatch → retained canonical Update → durable apply → ACK. The callback page's new current-attempt and writer checks should stay explicit. The remaining friction is order and duplicated exposition: startup imports interrupt the first callback read, ordinary delivery capacity appears after a floor-reset caveat, and direction repeats an older, less detailed canonical-worker recipe.

## 1. Shorten startup and link the existing lifecycle/import contracts

**Target:** `docs/baton/interfaces.md`, replace the prose under “Assemble before opening the engine” (`:7–13` at review time), leaving the heading and following propose section unchanged.

Exact suggested replacement:

```markdown
Restore App's canonical state/applied binding, or initialize the agreed App genesis; Marshal's index 0 is genesis and is never delivered as an Update. Use the [existing assembly](../reference/integration.md#body-assembly-to-implement), with App custody and retained Update intake available before `Engine::open` invokes recovery verification. Gate speculative dispatch during recovery, not the custody answers needed to finish open.

Pass App's Automaton, Marshal's relay and the native activity reporter into Engine. Start its planes, await native readiness and App's recovered base, then activate scheduling and re-evaluate retained candidates; another successful verify callback is not guaranteed. Native `ready` is only a startup milestone. The example supplies wiring, not the transaction executor or durable Update consumer.

Keep failed startup, sibling-service lifetimes and shutdown under the [existing node owner](../reference/integration.md#service-lifetimes). Checkpoint imports must also follow the [floor-to-App-state authority contract](../execution/state-sync.md#coordinate-the-app-checkpoint-with-marshal), including authentication before using `Start::Floor`.
```

This keeps the assembly prerequisites a developer needs before implementing either callback, while moving the detailed floor-import discussion out of the path to `propose`.

| Detail no longer repeated in full here | Existing authoritative location |
|---|---|
| Buffer, resolver bridge, Service/Relay/SchemeVerifier and typed mailbox construction | `reference/integration.md#body-assembly-to-implement`, with current source links and assembly pseudocode |
| App custody before Engine open; startup phase, live activation, no guaranteed second verify | Essential rule retained above; `e2e/recovery.md#startup-prepare-custody-before-native-recovery` supplies the sequence and qualifications |
| Separate service subtrees do not automatically stop siblings; failed-open cleanup, cancellation and shutdown | `reference/integration.md#service-lifetimes`, paragraphs beginning “Own service handles” and “Use the callback response” |
| Peer floor uses Genesis then verifying install; Start::Floor is caller-authenticated/fresh-namespace; later verifier is not retroactive | `execution/state-sync.md#coordinate-the-app-checkpoint-with-marshal` and `reference/integration.md` checkpoint-bootstrap paragraph explicitly preserve all these facts |
| Synthetic example is not a transaction/durable-consumer implementation | Retained above; `e2e/canonical.md#what-the-ack-waits-for` supplies the exact OutputReporter source distinction |

Do not shorten the fresh-genesis or custody-before-open rules to “follow startup guidance”: those prerequisites belong in the core path.

## 2. Put ordinary Update delivery before floor/reset handling and merge duplicate window prose

**Target:** `docs/baton/interfaces.md`, “Marshal report(Update): canonical input and ACK.” Keep the local-authority paragraph, full canonical-worker pseudocode, first-seen Update paragraph and synchronous-handler rule (`:87–115`) intact. Move the existing three-column milestone table (`:121–126`) immediately after that synchronous-handler paragraph. Replace the other prose currently at `:117–132` with the following, after the table:

```markdown
Within one active delivery window, Marshal can report up to `max_pending_acks` outstanding Updates. A full window pauses further App delivery; native voting, leader finality and producer progress continue independently. Retain every accepted Update and its Exact token in a queue sized for that window. `Closed` terminates delivery; `Backoff` does not retry a dropped Update. Every Exact clone must acknowledge, and dropping an unacknowledged clone cancels its live waiter.

ACK is an in-memory signal after App durability. Marshal subsequently persists its own cursor, so a crash between those boundaries can redeliver already-applied input. Compare recovered position and exact identity before ACKing replay; do not duplicate effects. A gap or conflicting identity stops application for recovery/error handling. An included block with a missing body is never an empty slot.

For floor/import transitions, the active-window bound does not cover old Updates still retained by App after Marshal resets its window. Update has no generation field. Serialize the transition through App ownership: fence/reconcile old inputs and tokens against matching durable App state, or explicitly budget bounded overlap before accepting a fresh window. The [detailed handoff](../execution/state-sync.md#coordinate-the-app-checkpoint-with-marshal) remains implementation work.

Result certification remains separate: irrevocable exact input/base/runtime plus `f+1` distinct matching execution signatures. Direct canonical work can apply while peer signatures are collected; imported material additionally needs its certificate and applicability checks. ACK is not result certification, and direction support does not authorize canonical state. [Execution result contract](../execution/interfaces.md#result-certification-inside-executor).
```

The ordinary path is then readable in order: **trusted local input → retain → reconcile/apply → ACK → finite delivery window → crash replay → floor/import exception → separate result certification**. No worker or authority steps are hidden in a generic “process correctly” instruction.

| Preserved fact / removed repetition | Where it remains |
|---|---|
| Synchronous intake; no execution or await in Reporter | Existing section opening, report pseudocode and unchanged synchronous-handler paragraph |
| Exact predecessor recheck at writer, durable metadata linkage, current owner once-only apply completion | Full canonical-worker pseudocode stays unchanged |
| Update may be first encounter without verify/candidate metadata | Existing paragraph stays unchanged |
| Complete speculation may leave mainly I/O; incomplete work must finish before honest ACK; no unconditional reexecution | Existing worker's reuse/repair branch plus `baton/README.md#when-canonical-application-begins` and `e2e/canonical.md#what-the-ack-waits-for` |
| Retained full Update, compatible ordinary capacity, Backoff no retry, Closed terminal, Exact clone/drop semantics | All retained in the first replacement paragraph; full source evidence stays in `consensus/ordered-input.md#delivery-backpressure-and-recovery` |
| Separate App/Marshal durability and exact-identity redelivery | Retained in the second paragraph and milestone table |
| Per-window bound, old/fresh overlap, no Update generation, App-owned fence/reconciliation, matching durable imported state | All retained in the third paragraph; exact startup/import authority stays in the linked state-sync section |
| Direct apply versus imported verification and f+1 result endpoint | Retained in the final paragraph, with the existing execution detail link |

This is primarily an ordering improvement. Current prose is correct, but the ordinary `max_pending_acks` explanation comes after the floor exception, making a reader learn the exception before the normal behavior it modifies.

## 3. Let direction own scheduler reconciliation, not a second apply implementation

**Target:** `docs/baton/direction.md`, replace the code block and paragraph under “Canonical reconciliation is shared” (`:41–56`). Leave the heading, pending-order examples, report-window rules and native-policy gap unchanged.

Exact suggested replacement:

```markdown
Both schedulers use the same [canonical Update worker](interfaces.md#marshal-reportupdate-canonical-input-and-ack). Compare retained work with the exact canonical predecessor, ordered prefix, input state and runtime. A matching block digest alone is insufficient, and a producer-header parent is not the merged execution parent. Missing required bodies or state keep work pending; they do not create empty inputs.

The shared worker reuses valid work or finishes/repairs the canonical path, fences incompatible workers and live database access, and durably applies before ACK. After application, advance App's canonical base once, remove applied pending entries and rebase/fence conflicting work. Retain compatible descendants only within the resource and retention budget. Reports and direction add no approval step.
```

This replaces a second apply algorithm with the scheduler-specific consequence of the authoritative worker. It also avoids a subtle drift risk: the core worker now names writer predecessor rechecks and current-owner once-only completion, while the older direction pseudocode only says “durably apply in order.”

| Current direction fact | Authority after replacement |
|---|---|
| Exact canonical predecessor/prefix/base/runtime matching; header parent differs from execution parent; missing body/state never empty | Retained explicitly in the first paragraph |
| Reuse or finish/repair; incompatible-worker/live-access fencing; root/apply/durability before ACK | Core Update pseudocode and execution/QMDB contracts; fences and durable-before-ACK retained explicitly in the second paragraph |
| Retain compatible descendants under budget | Retained explicitly; not assumed to follow merely from canonical advancement |
| Applied identity, once-only canonical-base advance and pending/conflict reconciliation | Core worker and Native activities section; the local scheduler effect remains explicit in the replacement |
| Certified import alternative and independent result handling | Core worker and execution state-sync contract; no second direction-specific import algorithm |

## Keep the other core guidance as it is

`baton/README.md` already gives a short composition and the user's four requested connections. Its three verify origins and local/nonproducer/Observer qualification answer the original misunderstanding; cutting them would make the main entry less useful. The deeper callback races remain in the callback page.

`overview/interfaces.md` is already a compact routing page. Keep its unique warning that a cloneable handle's `&mut self` is not App-wide serialization or a writer fence. Its tables route readers to current contracts and E2E cases rather than historical layers. No cosmetic diagram edits, new page, new service, public type or protocol choice is recommended.

Only this review artifact was written. No doc build or unchanged render check was rerun for a read-only simplification proposal.

## Authorized pool clarification

Root subsequently authorized one sentence in `docs/tx/interfaces.md`, immediately after the local selection contract:

> Local pool membership, selection and readiness govern this node's proposals; peer or canonical blocks are validated under the agreed payload rules without requiring their transactions to have been locally admitted or selected.

This follows the existing distinction between node-local batch selection and App payload validation. It does not declare all unselected transactions valid in blocks or choose an open transaction policy: any agreed payload rule still applies independently of local pool state. This follow-up changed only that page and this report; no diagram changed. Targeted `git diff --check` passed. Root retains ownership of the three core simplification proposals.
