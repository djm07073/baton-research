# App scheduler simplification audit

Reviewer: `/root/simplification`. Source inspected: Commonware `6233438985d8249d2b2bc1204191d5d405652288`; research baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31`. First source pass: 2026-10-09 07:02 UTC. This records source/design review, not protocol execution or proof completion.

## Minimal ownership

One application owns transaction admission/selection, one selected scheduling mode (`PreCut` or `Baton`), execution work, branch state, result certification and durable canonical application. These are concrete responsibilities, not required public TxPool, Baton, Executor or Storage traits. Retain existing Commonware `Automaton`, `Reporter`, Marshal mailbox/relay and the selected concrete runtime/storage/P2P APIs. Do not create a BlockService, separate Orderer or a second native-proof/backfill/cursor engine.

`Automaton::propose` builds a body from the app pool. `verify` validates that exact body/context and establishes durable custody. Successful verification can admit speculative work; it does not wait for execution. Marshal `Reporter<Update>` supplies complete blocks in canonical index order; the app reconciles/apply state and then acknowledges. Native `Reporter<Activity>` is a distinct observation domain. Small typed handles may enter the same application owner; combining associated Activity types into one trait implementation is not possible.

## Findings that must survive simplification

| Question | Source finding / required design |
|---|---|
| Is verify another-lane packet receipt? | No. Live chain-plane eligibility dispatches it after native checks; local producer custody invokes it before header signing; startup rechecks recovered payloads. Qualify phase, lane, exact context/reference and duplicate/applied status before interpreting it as newly usable peer input. |
| Can temporary body loss produce false? | No. Automaton is single-shot per request; missing body/dependency stays pending. False means permanently invalid. Response closure is terminal too. |
| Does stage completion mean disk custody? | `stage_block` returns a Custody token; `wait` is durable completion. `put_block` combines the two. `subscribe_block` establishes custody and does not itself start a peer fetch. |
| Must scheduler capacity gate verify? | No execution or speculative-capacity barrier belongs in the custody verdict. Bounded app admission/retry or an explicit skipped speculative opportunity is sufficient; native Marshal Update later supplies canonical work. Do not invent a durable scheduler journal merely to preserve a speculative hint. |
| What identifies the execution parent? | Exact execution prefix/base/runtime and checkpoint. `Context.parent` is a producer-header parent and cannot substitute for merged execution ancestry. |
| Who computes ordinary dense order? | Current Multimmit Marshal already verifies L-QCs, walks history, backfills bodies/proofs, commits ordered catalog rows and tracks ACK cursor. Old docs assigning this to Baton are superseded. |
| Can Update implement Baton protected prefixes? | No. It supplies the already ordered native block stream. Reordering Updates violates that stream. Native authenticated policy adoption/validation/continuation/recovery remains an open extension. |
| Does ACK wait for execution? | Marshal waits for app durable application. When valid speculative effects already exist, remaining work can be preparation/apply I/O. Missing or mismatching work requires completion/repair first. The token itself is an in-memory signal. |
| Does consensus wait for ACK? | No. The delivery window is bounded by outstanding application ACKs, independently from native voting/finality. ACK releases contiguous pending slots; Marshal separately syncs its cursor. |
| What survives crash? | App durable state/output/applied index/provenance and Marshal durable ACK cursor are distinct. Crash between them can redeliver; app must idempotently validate the exact already-applied identity before ACK. |
| Can roots be removed with Storage trait? | Remove the trait, not preparation/durability responsibilities. Effects may remain unsealed until needed; signatures require a complete committed result. Exact QMDB ancestry and writer fencing remain. |

## Decisive current source

- `consensus/src/lib.rs:125` — Automaton receiver and single-shot semantics; `:258` — synchronous Reporter.
- `consensus/src/multimmit/actors/voter/chain_plane.rs:522` — live verification dispatch.
- `consensus/src/multimmit/actors/voter/actor/app.rs:121` — local pre-sign custody callback.
- `consensus/src/multimmit/storage/recovery.rs:473` — startup payload verification.
- `consensus/src/multimmit/marshal/mailbox.rs:337` — staging; `:431` — custody subscription.
- `consensus/src/multimmit/marshal/mod.rs:1` — current custody/order/delivery ownership.
- `consensus/src/multimmit/marshal/types.rs:130` — Update and durable-apply ACK contract.
- `consensus/src/multimmit/marshal/actors/delivery/actor.rs:236` — bounded delivery; `:303` — report; `:330` — separate cursor sync.
- `consensus/src/multimmit/marshal/actors/delivery/acks.rs:1` — pending window versus cursor durability.
- `glue/src/stateful/db/mod.rs:563` / `:570` — current apply then finalize, superseding the old finalize(batch) recipe.

## Preserved research conditions

PreCut has no Baton instance/reports/direction/policy extension; both modes share pool, body custody, execution/backend, resource budgets and completion endpoints. Preserve started valid `F`, sort only eligible pending work, and use exact-parent repair on new canonical input. `F` is local speculation, never native finality. Direction-conflict precedence, root/batch boundaries, global comparator and other open policy cells remain open.

Baton retains authenticated original same-context reports, first `4f+1` valid admissions or fixed deadline closure, `2f+1` entire-prefix priority over completed bounded candidate evaluation, raw sum-LCP fallback and native cut no-wait. Reports establish intentions only. Authenticated protected prefixes cannot be silently dropped. Execution result certification remains `f+1` distinct eligible signatures over exact irrevocable input/base/runtime/result; imported work cannot be signed as the node's direct execution. Certification/state sync/canonical apply never require scheduler approval.

## Review status

Initial audit and companion rewrite complete; the independent second pass is recorded in [round 2](round2-simplification.md). The overall requested three-hour review remains active under the root agent. No protocol implementation, runtime tests, benchmark, external publication, commit or push performed by this reviewer.

## Companion rewrite evidence

Checked 2026-10-09T07:14:29+00:00: seven owned Markdown pages, 32 local path/anchor links, and `git diff --check` pass. Diagram 17/18/19 inline sources match the edited `.mmd` sources; root owns generated rendering/manifest verification.

- `docs/baselines/precut.md`: `857d600d83592f368f58dac2fe2e2894dd44332a2b7addb91db281f4fd0a8949`
- `docs/execution/README.md`: `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273`
- `docs/execution/interfaces.md`: `b0df7a7f8f593fa9cb73b20124c7eabe12a40e66daf501fa2195aca17a3c66ff`
- `docs/execution/qmdb.md`: `62484b59aacd023ffe70274bb44bada1a1ec352395535b61cf3ca596b5a9ac93`
- `docs/execution/state-sync.md`: `7d74fd8ecea1058f6b44c92efd5eacab0af0cd538315179f70bbe43783751d2f`
- `docs/tx/README.md`: `9953f897747f913471c8486d088f108be78afe344bbede64a173b94fed9ccacb`
- `docs/tx/interfaces.md`: `3e5d12166f572e886f54d4161f570b720b8bc71ff99f0c3342a8efb43a9ef17f`
