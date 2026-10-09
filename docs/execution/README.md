# Execution inside the application

**The app owns transaction execution, its execution tree and durable state.** Its selected scheduler is either PreCut or Baton. Commonware `Automaton::propose/verify` and Marshal `Reporter<Update>` are the external entry points; they do not require public Executor or Storage traits. Names such as execution worker and storage below describe internal responsibilities and existing concrete handles.

Native Multimmit's internal `AppExecutor` invokes local propose/verify jobs and tracks their completion. It does not interpret transactions or supply an application execution backend. The app must implement that work. See [the callback sequence](../baton/interfaces.md) and [execution connection](interfaces.md).

## Roles and responsibilities

| App responsibility | Trigger | Completion condition |
|---|---|---|
| Speculative scheduling | Valid, durably custodied and eligible candidate | Pending order updated; execution is dispatched separately |
| Direct execution | Scheduler selects a block and its valid exact predecessor | Completed effects/outputs associated with exact base, runtime and input prefix |
| Canonical reconciliation | Marshal `Update { index, block, acknowledgement }` | Reuse matching work, finish/repair missing work, or select verified applicable imported material |
| Root preparation | A selected storage/signing boundary needs a commitment | Deterministic exact-prefix material and complete result/output binding |
| Durable application | Canonical reconciliation has valid material | One writer makes state, outputs, applied identity and direct/imported provenance recoverable |
| Delivery completion | Matching durable application established | App signals the Update ACK; Marshal persists its own delivery cursor separately |
| Result certification | Direct or peer result statements | Irrevocable exact input/base plus `f+1` distinct eligible matching signatures |
| Peer state sync | Valid certificate and applicable material available | Safe handoff through the same canonical writer; imported provenance retained |
| Pool maintenance | Applicable durable outcomes | Backend candidates/nonces/status reconciled internally |

The [callback contract](../baton/interfaces.md) defines candidate admission, synchronous Update retention, replay and durable ACK. Both scheduler modes use the same exact-parent execution state and canonical writer: valid speculation is reusable only for matching input, parent and runtime, and a differing canonical path needs repair. Keep started work fixed on ordinary arrival and sort only eligible pending work under [the shared scheduling rule](../baton/direction.md#global-rule-for-local-execution-and-reports).

## Execution effects and storage roots

Use concrete QMDB batches/database handles and Commonware runtime tasks. Transaction execution produces effects and outputs; prepare roots only when useful. Root calculation must precede full-result signing, but need not run for every abandoned speculative attempt. Existing sealed-parent forks are reusable; an unsealed-parent tree is still application integration. [QMDB recipes](qmdb.md).

Do not require `commonware_glue::stateful::Application` or the full Stateful actor for this app. Its lifecycle is a reference; the app needs merged Multimmit input and deferred-root speculation. Its [mailbox](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/glue/src/stateful/actor/core/mailbox.rs#L8) targets the block/ancestry `commonware_consensus::Application` and Simplex Marshal `Update` contracts; Multimmit uses a different callback boundary. Concrete `glue::stateful::db` utilities can be reused independently when their selected DB types fit.

One canonical writer covers direct execution and verified imports. Stale worker generations prevent result adoption, while database-access fences prevent reads/forks/application from an invalid live base. Dropping a waiter does not necessarily stop submitted CPU work or storage I/O. Canonical mutations cannot be canceled by an advisory direction change. Retain all state still needed by workers, queries, recovery, result serving and sync.

## Result certification and state sync

Execution result messages travel directly between app peers over existing authenticated P2P. The Baton scheduler does not relay, approve or gate them. Check the full exact input/range, canonical input state, runtime/rule, result and chosen output/material commitments before counting distinct epoch validators. The threshold remains `f+1`; native consensus quorum types cannot be copied unchanged. [Certification](interfaces.md#result-certification-inside-executor).

An app may import a certified result during normal execution after both the certificate and applicable material have been verified. Continue valid direct work while either is unavailable. An imported result cannot produce the node's own direct-execution signature; the node may relay the original certificate and directly execute/sign a later range. State finalization and local durable/read readiness remain separate endpoints. [State sync](state-sync.md).

## Open decisions

| Item | Decision |
|---|---|
| Application transaction semantics | |
| QMDB variant / state encoding / result root | |
| Deterministic canonical operation and batch boundaries | |
| Root-deferred effects/read representation and checkpoint policy | |
| Execution identity / parent binding / checkpoint granularity | |
| Worker placement / cancellation / access-fencing contract | |
| Recoverable linkage of state / outputs / applied position / provenance | |
| Branch retention / memory / disk budgets | |
| Query / result material / certified state-sync protocol | |

## Commonware primitives in the execution layer

| Reused mechanism | App responsibility still required |
|---|---|
| QMDB and concrete `glue::stateful::db` utilities | Transaction semantics, exact execution ancestry and deterministic selected commitment |
| Runtime `Spawner`, `Strategizer`, existing future pools | Placement/work bounds and context-checked completion; a future pool alone does not bound work |
| Crypto signatures/certificates and typed P2P | Full execution subject, eligible distinct signers, `f+1` and direct/imported provenance |
| QMDB sync plus resolver | Trusted execution target, compatible material and active-validator writer handoff |
| Existing journal/metadata/barriers | App state/output/applied-index crash consistency; Marshal separately owns its delivery cursor |

The [source catalog](../reference/integration.md#primitive-reuse-catalog) and [QMDB page](qmdb.md) distinguish current source from older reuse investigations. No transaction backend, result protocol, runnable scheduler or benchmark is implemented by this documentation.
