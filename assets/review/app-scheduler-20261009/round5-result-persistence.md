# Round 5: result, checkpoint and persistence boundaries

Reviewer: `/root/simplification`. Fresh source and analytical scenario audit at Commonware `6233438985d8249d2b2bc1204191d5d405652288`. No protocol test, execution benchmark or root calculation was run. The outcomes below assess documented contracts; they do not claim an implemented App.

## Checkpoint and batch scenarios

| Analytical input / event sequence | Required behavior | Current documentation assessment |
|---|---|---|
| Direct speculative ABC exists; only AB becomes canonical; completed AB checkpoint/effects retained | Apply exactly AB. Retain C only if its exact execution context and actual QMDB ancestry remain applicable. | Pass: `execution/qmdb.md` canonical section and PreCut partial-prefix case. |
| Same input, but only one sealed ABC batch remains | Never apply ABC and hide C. Reconstruct AB from retained exact effects at a valid ancestor, or reexecute through AB. A batch does not expose arbitrary execution-prefix slicing. | Pass: explicitly stated. No additional public storage trait needed. |
| AB was rootless; its only draft is consumed to seal ABC; AB effects were not separately retained | Do not claim rootless AB still exists or can be forked. Use retained effects/checkpoint or reexecute. | Pass: single-owner consumption and effect retention are explicit. |
| App prepares a new AB with different operation/batch normalization than ABC's original ancestry | Logical equality is insufficient. Old C/ABC sealed material cannot be assumed applicable to this new AB commitment. | Pass: exact ancestry and deterministic batch boundary obligations retained. |
| Two nodes execute identical A,B ending at k=2; one seals once, another seals between k=1 and k=2 | Final logical values do not guarantee equal operation histories/roots. Normalize canonical boundaries/root interpretation before expecting f+1 matching result statements. | Pass; source confirms last-write-wins within a batch and a commit record per merkleization. No particular boundary/root scheme is adopted. |
| An old branch worker reads after the canonical DB advances to a sibling | Prevent invalid read/fork/materialization access or discard/fence the job safely; a generation check only after completion is insufficient to claim it read its advertised parent. | Pass: active-access fencing is explicit. Fresh source evidence below strengthens why it is necessary. |
| Child holds its immediate parent but older unapplied ancestors are released | Do not assume leaf retention supplies the full ancestor chain for later hashing/proofs. Retain required handles until dependent work and serving obligations end. | Pass: weak ancestor retention is explicit. |

Current source evidence:

- `storage/src/qmdb/any/batch.rs:1746-1755`: repeated writes within one draft overwrite the mutation map's prior value.
- `storage/src/qmdb/any/batch.rs:1273-1275`: merkleization appends a CommitFloor operation. This supports differing possible histories, not a claim of measured roots.
- `storage/src/qmdb/chain.rs:1-16,65-112`: applicability binds operation-size/root commitments and ancestor states, plus floor rules. Equal key values do not substitute for those commitments.
- `storage/src/qmdb/any/batch.rs:2855-2862`: all needed unapplied ancestors must remain alive for descendant merkleization.
- `glue/src/stateful/db/any.rs:107-118`: concrete reads acquire the current shared DB.
- `storage/src/qmdb/any/batch.rs:1915-1944`: get_many reads mutations/ancestors/current DB and can directly call db.get_many; it does not perform a general stale-branch validation at this read entry. Later apply/merkleize checks do not retroactively establish that transaction reads used one valid advertised parent.

This is a source-grounded App fencing obligation, not a reported QMDB bug. The concrete access/fencing policy remains open, and no new facade or lock protocol is selected.

## Certification and material scenarios

| Analytical input / event sequence | Required behavior | Current documentation assessment |
|---|---|---|
| f+1 signatures exist for ABC, but consumer asks for AB | Reject substitution. A longer-range statement/certificate cannot be sliced into a shorter-range one; exact inputs/base/runtime/result/output subject must match. | Pass: range binding and no slicing are explicit. |
| Signatures share a state root but differ in canonical base, ordered inputs, runtime or result outputs | Do not combine them. Collect by full subject and distinct eligible epoch identity. | Pass. |
| Valid f+1 matching certificate exists, but material or outputs are missing | Certificate acceptance and material/read readiness remain distinct. Keep valid direct work running and retrieve/recover applicable material; no ACK for absent durable application. | Pass. |
| Certificate arrives before matching irrevocable input or canonical predecessor | Retain pending/recover ordering. Result signatures cannot settle native unresolved order. | Pass. |
| Node durably applies direct exact work while fewer than f+1 peer signatures exist | ACK can follow valid local durability. Continue collecting signatures for the separate research state-finalization endpoint. | Pass; root callback/Rust pages state this explicitly. |
| Import becomes applicable before unfinished direct work completes | Verify certificate AND material; serialize writer transition; fence conflicting accesses/results; persist imported provenance. | Pass. |
| A canceled/stale direct worker completes after import | It cannot replace canonical state, bypass the writer or upgrade imported material into own direct evidence. Context/generation/access checks still apply. | Pass under the stated worker contract. |
| A separately complete, independently direct-executed exact result arrives after an import | Arrival order alone is not provenance. Consider it only if its own direct evidence, exact statement and valid access/context pass the App's chosen policy; merely importing cannot establish those facts. | Current wording is appropriately scoped to “work merely imported.” No blanket new post-import signing prohibition is adopted. |
| Latest state is kept but an earlier common signing boundary/result material was discarded | Do not claim the latest root/certificate can reproduce it. Retention or reexecution from a valid retained anchor is required for any service obligation; common boundaries/retention remain open. | Pass: QMDB retention and E2E result-serving paragraphs preserve the obligation. Concrete liveness is not claimed. |

The four unadopted defaults stay open: per-block signing, incumbent-first tail, inline policy bytes and finite-prefix permutation continuation. In particular, one Update per block does not force one signature or one QMDB seal per block. No automatic liveness guarantee is inferred from the f+1 threshold alone.

## Persistence and crash scenarios

| Analytical input / event sequence | Required behavior | Current documentation assessment |
|---|---|---|
| apply returns, DB is readable, finalize barrier is pending | No durable completion/ACK for that boundary yet. | Pass. |
| New batch is applied while an earlier finalize barrier is pending | Earlier barrier does not cover the later apply. A later finalize is needed after the earlier barrier resolves; mutation method bodies do not overlap. | Pass: current QMDB API recipe specifies this scope. |
| Barrier closes/aborts or storage mutation fails | No successful ACK. Do not reuse a failed mutable DB instance or claim rollback/zero writes; recover authoritative state. | Pass. |
| QMDB state persists but applied identity/outputs/provenance linkage is incomplete | Do not ACK merely because one store flushed. App recovery contract must establish exact linked state before completion. | Pass; no cross-store atomicity is falsely supplied by Metadata or DatabaseSet. |
| App state and applied identity are durable; ACK occurs; Marshal cursor remains behind at crash | Redelivery compares exact index/block and linked applied state; return ACK without duplicate effects. Marshal cursor durability remains a separate boundary. | Pass. |
| A verified import covers retained Updates while floor changes | Only matching exact covered inputs can be acknowledged/reconciled; serialize floor transition and bound old/new retained-window overlap. | Pass after prior floor finding. |

Source: `glue/src/stateful/db/mod.rs:387-414,463-497,563-581` separates apply, finalize/barrier coverage, failure and mutation ordering. `storage/src/qmdb/sync/engine.rs:745-770` persists/reconstructs/checks the sync result before returning the completed DB. Marshal `Update` and delivery cursor code remain independent of the app's state stores.

## Result

No missing retention or batch-normalization condition was found in the current reader contracts. The concrete app implementations, statement/batch boundary policy, storage recovery transaction and liveness proof remain open rather than being silently replaced with easy defaults. No canonical text change is required from this pass; the most valuable new evidence is the current get_many read path confirming that live access fencing cannot be reduced to late stale-result rejection.

## Reviewed fingerprints

Captured 2026-10-09T07:27:53+00:00.

- `docs/baselines/precut.md`: `9c50951ab8c26fe030362ad4d35c8a7c23753c8a503bcb6e0c22bdefacfdcaed`
- `docs/baton/direction.md`: `376104a6b096b9fc7bf53877f290667e32e433d18b042ff634cc5f1fc04f1e76`
- `docs/baton/interfaces.md`: `64b9e84aa6b7ef0e402b30af28b8815eeaed3053dddf09293f032720fe307b80`
- `docs/e2e/canonical.md`: `0919bd9ac05f4b99deafc340c30de402ba5e4bafc974f2decbb244784f3aff25`
- `docs/e2e/results.md`: `fe48138a0ef55784eed6a27a724755f27fed0f1a1ea4a18ca17b9e45e1990edb`
- `docs/e2e/state-sync.md`: `9b46bee7d882ac3f2a2783ab4ddb7d0e965e955448235653592d820d9f47134b`
- `docs/execution/README.md`: `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273`
- `docs/execution/interfaces.md`: `b0df7a7f8f593fa9cb73b20124c7eabe12a40e66daf501fa2195aca17a3c66ff`
- `docs/execution/qmdb.md`: `d9de7f53bbcec34dfa86466e42c54dc6bd46ef28897e344067665bae05f81381`
- `docs/execution/state-sync.md`: `7d74fd8ecea1058f6b44c92efd5eacab0af0cd538315179f70bbe43783751d2f`
