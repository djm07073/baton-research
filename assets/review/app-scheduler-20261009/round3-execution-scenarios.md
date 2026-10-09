# Round 3: execution scenarios, callback roles and completion endpoints

Reviewer: `/root/simplification`. This is a read-only scenario/source audit. The traces below are analytical control-flow checks, not executed tests or benchmarks. Current Commonware source: `6233438985d8249d2b2bc1204191d5d405652288`.

## Callback and role traces

| Analytical trace | Current source behavior / required app behavior | Documentation result |
|---|---|---|
| Remote validator verify begins; body is temporarily unavailable; App retains reply | App should keep the verdict pending and do custody/body work independently of transaction execution. No speculative worker is required to answer true once valid custody is established. | Pass: root callbacks and owned execution/baseline describe this. |
| Remote validator verify receiver closes | Chain plane maps None to Unavailable; eligibility restores Ready, and a new validation job can call verify for the same header in the same run. Deduplicate repeated candidate intake. | Pass in current root interfaces after native-agent correction. Owned pages do not promise no live retry. Earlier initial audit single-shot/terminal wording is superseded by this source finding. |
| Local producer returns body digest, then uncanceled custody verify resolves false or closes | Live voter requires Some(true), otherwise Fatal::Automaton. App cannot use closure as a portable body-missing retry. | Pass: root callback qualification. Owned pool/baseline maintain valid durable custody and temporary-pending rules. |
| Engine::open recovery verify fails/closes | verify_recovered_payloads returns RecoveredPayloadUnverified. Startup cannot depend on native ready before answering custody. | Pass: root startup and baseline link to the callback contract. |
| Validator does not own a producer lane | It still creates one verification plane per producer chain. No invented local chain is needed; authenticate the source and qualify lifecycle. | Pass in root README's no-local-producer qualification. |
| Observer receives peer traffic | ChainTasks::new returns default with no live chain-validation planes. A verify-driven speculative intake cannot be promised for this role. Canonical Update remains usable if its App/Marshal are configured. | Small clarification needed in baseline inputs: explicitly scope live verify intake to Validators, including nonproducers; Observer speculation needs explicit intake if desired. Root notified. |
| Child producer header arrives while its parent validation is pending | Native parent_available accepts Pending or Valid parent state. Native dispatch is not proof all ancestor body validations or execution parents are ready. App retains dependent work until exact readiness. | Pass: current root verify prose and owned exact-parent dispatch rules cover it. |

Decisive source: `actors/voter/chain_plane.rs:522-585`; `machine/eligibility.rs:309-319,352-357,797-812`; `actors/voter/actor/chains.rs:114-129`; `actors/voter/actor/live.rs:578-607`; `storage/recovery.rs:473-496` under `consensus/src/multimmit/`.

The shared `Automaton` docs still specify single-shot/terminal closure. The current remote implementation exception does not authorize relying on closure as a general retry protocol. Source behavior and portable App design are now distinguished explicitly.

## Worker and storage traces

| Analytical trace | Required result | Documentation result |
|---|---|---|
| A executes; C admitted; B admitted before C starts | Pending reorder gives B,C; preserve A; execute B from A, then C from AB. | Pass: root scheduling and PreCut examples. |
| C already runs on A; eligible B arrives | Preserve started AC; queue B; do not rerun C merely for arrival. | Pass. Canonical ABC can still require repair later. |
| Canonical sibling is applied while an old worker later reads shared Any DB | Stale-result rejection alone is insufficient. Fence invalid reads/forks/materialization and mutation under shared access authority, then reject late completion. | Detailed contract passes in execution README/QMDB. Root direction pseudocode still says only “fence incompatible worker results”; internal execution pseudocode can also name access fencing explicitly for standalone readers. Small wording fix recommended, no new actor/trait. |
| ABC exists as one sealed batch; Update requires AB | Prepare exact AB from retained effects/valid predecessor or reexecute. Do not apply ABC and hide C. Old C reuse requires actual storage ancestry after AB preparation. | Pass: QMDB canonical application and baseline partial-prefix case. |
| Direction task is canceled during canonical apply | Canonical mutation remains under its writer lifetime; cancellation cannot abandon a by-value DB instance as a normal retry. Failed mutable storage is not reused. | Pass: QMDB and root owner responsibilities. |

Current Any wrapper `glue/src/stateful/db/any.rs:1-5` explicitly reads current shared applied state. Database access protection is consequently separate from worker-generation result selection. `ManagedDb` mutation ownership appears at `glue/src/stateful/db/mod.rs:327-397`.

## ACK, result certification and import traces

| Analytical trace | Allowed or forbidden next step | Documentation result |
|---|---|---|
| Exact canonical Update arrives; valid direct speculative effects exist; only one signature exists where f+1 is larger | Prepare/apply direct effects and ACK after durability. Continue collecting peer signatures for the separate research state-finalization endpoint. No f+1 wait on direct application/ACK. | Pass. Root callback and Rust pages state this explicitly; owned application pseudocode has no certificate gate on its direct branch. |
| Direct effects exist but DB flush is still pending | No successful ACK yet. Existing apply/readability alone is not covering durability; outputs/applied identity/provenance must also recover coherently. | Pass. |
| Direct result is durable; App ACKs; Marshal cursor flush has not finished; crash occurs | App may be ahead of Marshal. On redelivery check exact index/block and durable applied record; ACK without duplicate effects. | Pass. |
| Matching f+1 certificate arrives before its irrevocable order/base is known | Retain pending certificate/recover ordering; it cannot settle native unresolved input or authorize import. | Pass in state-sync page and E2E. |
| Certificate is valid but material is missing/inapplicable | Continue valid direct work; do not stop solely for the certificate and do not ACK absent durable state. | Pass. |
| Certificate and material are valid; local speculative work is unfinished | Fence conflicting access/work; import through the same writer; persist imported provenance and exact applied identities; ACK only matching covered Updates. | Pass. |
| Imported range AB is applied; node attempts its own AB direct-execution signature | Forbidden: imported material is not own direct execution/validation evidence. Relay original certificate instead. | Pass. |
| Node directly executes the next range from an imported canonical base | It may sign the newly directly executed exact range after its normal checks; imported ancestry does not taint all future direct work. | Pass. |
| Correct f+1 certificate exists but local state/material is unavailable | Result certification may be established for the verified exact statement; local durable/read readiness remains false. A certificate query does not imply retained material. | Pass. |
| Floor reset occurs with old Updates retained by App | Single active-window bound does not cover old/new overlap. Serialized App transition reconciles old input and bounds overlap; Update has no native generation field. | Pass after round2 fix in root, execution state-sync, consensus and E2E pages. |

No current path reviewed accidentally waits for f+1 before direct durable application/ACK, or promotes imported work to the node's own direct-execution signature. No scheduler approval is required for certification, import, canonical application or ACK. The research state-finalization endpoint remains exact irrevocable input/base/runtime/result plus f+1 eligible distinct matching signatures; ACK proves local durable application only.

## Smallest follow-up

1. Add the Validator/Observer live-verify qualification to baseline input prose (root callback pages are already being updated).
2. Name both incompatible live-DB access and stale-result adoption in standalone canonical pseudocode. The detailed shared backend contract already contains both.
3. Retain source mismatch wording; do not modify protocol code as part of this documentation task.

## Reviewed document fingerprints

Captured 2026-10-09T07:17:03+00:00.

- `docs/baselines/precut.md`: `857d600d83592f368f58dac2fe2e2894dd44332a2b7addb91db281f4fd0a8949`
- `docs/baton/README.md`: `d989dbdc210d4fd515e8f5dd64e63bded8f91480410e29bee94810b9fcbc05fc`
- `docs/baton/direction.md`: `376104a6b096b9fc7bf53877f290667e32e433d18b042ff634cc5f1fc04f1e76`
- `docs/baton/interfaces.md`: `8d83fdb763d7d32edd143fdbc1eaa94e0baf7ceb077ed636c2c82e9ee7717505`
- `docs/e2e/results.md`: `fe48138a0ef55784eed6a27a724755f27fed0f1a1ea4a18ca17b9e45e1990edb`
- `docs/e2e/state-sync.md`: `e00e99119353ac6a6ccb33fa89c482841c62441bb41e8efe10fe9105f1a5973b`
- `docs/execution/README.md`: `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273`
- `docs/execution/interfaces.md`: `b0df7a7f8f593fa9cb73b20124c7eabe12a40e66daf501fa2195aca17a3c66ff`
- `docs/execution/qmdb.md`: `62484b59aacd023ffe70274bb44bada1a1ec352395535b61cf3ca596b5a9ac93`
- `docs/execution/state-sync.md`: `7d74fd8ecea1058f6b44c92efd5eacab0af0cd538315179f70bbe43783751d2f`
- `docs/overview/rust-interfaces.md`: `892d9de6e64b8adc48bec23254900b2137351988812b331168b836d5647ad1a3`
