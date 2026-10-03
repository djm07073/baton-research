# Cases to verify

**Validation should exercise each responsibility at its failure boundary.** The plan covers normal flow, missing input, stale completion, cancellation, crashes, and recovery. These cases are planned, not executed test results.

## Verification cases by component

| Component | Cases to verify | Execution status |
|---|---|---|
| Tx / pool | New, duplicate, structurally invalid; proposal cancellation; no cleanup before canonical outcome | Not run |
| Builder / custody | Digest mismatch, missing body/parent, durability failure, late build completion | Not run |
| Native / delivery | Unresolved gap, authenticated empty, extension, missing history, preserved emitted prefix after restart | Not run |
| Leader Baton | Threshold/deadline race, duplicate identity, stale context, incomplete Baton planning, cut ready first | Not run |
| Non-leader Baton | Missed/late direction, missing body, order change, separated producer/executor roles | Not run |
| Execution | Prefix reuse, input-state/runtime mismatch, canceled-job completion, partial-prefix commit | Not run |
| Storage / QMDB | Sealed-parent forks vs rootless overlay; exact-prefix preparation; root/boundary determinism; valid-access fences through merkleize | Not run |
| QMDB recovery | Crash during commit, lost ACK, same-range redelivery, state/output/cursor/provenance linkage and retained-checkpoint recovery | Not run |
| Primitive adapters | Occupied/below-floor archive puts; local feedback vs custody; resolver cancellation; collector invalid-first-response slot and distinct validated signatures | Not run |

See [proposal freeze](../e2e/leader.md#planning-completion-versus-proposal-freeze) and the [native recovery owner](../consensus/README.md#native-actors-and-source-layout) for leader/view/context changes. Old reports and advisory work cannot enter a new context; preserve authenticated interpretation and emitted canonical prefixes. Adoption, continuation, and recovery bridges still need implementation and proofs.

With missed direction, the [non-leader path](../e2e/reschedule.md#non-leader-lifecycle-direction-and-branch-execution) continues local intended work and canonical commit. Distinguish late builds through [native request correlation](../consensus/block-body.md#select-transactions-and-build-a-block) and late execution through [generation and access fencing](../execution/qmdb.md#manage-the-branch-tree-for-execution-requests). Neither direction receipt nor canceled-worker completion adds a cut barrier.
