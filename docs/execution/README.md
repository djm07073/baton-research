# Execution: roles and responsibilities

**Executor computes transaction changes; Storage calculates roots and makes selected changes durable.** Executor manages execution-tree paths, certifies results with peer Executors and orchestrates normal-path state sync. Storage owns QMDB, canonical mutation, queries, physical retention and recovery. Both roles can share an implementation without becoming separate actors.

## Roles and responsibilities

Executor receives parent-linked execute(block) inputs from Baton and finalized commit(range) inputs directly from Orderer. Baton owns direction planning; there is no reschedule API. Executor produces completed changes/batches and outputs. Storage supplies valid branch access and prepares the selected QMDB commitment. Executors communicate directly to certify or import results. The Bank balance and nonce model is outside the current scope.

| Responsibility | Executor owns | Boundary and completion condition |
|---|---|---|
| Execution tree | Resolve parent hashes, link children, track completed checkpoints, promote canonical path, prune conflicting branches | Parent is an execution predecessor; compatible canonical descendants remain pending |
| Direct execution | Transaction computation, branch management, prefix reuse, suffix reexecution | Completed ExecutionResult; speculative work is not canonical application |
| Result signing | Validate and sign its directly executed result through Executor::sign_result using Commonware cryptography | Bind finalized exact input, canonical input state, runtime, and full result; never sign an imported result as its own execution |
| State finalization | Verify peer signatures / certificates; retain and disseminate the original certificate | f+1 distinct eligible signatures on one full statement, with irrevocable order and input-state chain verified |
| Executor peer communication | Exchange signatures, certificates, change sets, and outputs; query, retry, and serve | Executor ↔ Executor over Commonware P2P, without Baton relay or approval |
| Switching to state sync | Stop remaining execution and apply verified material when certificate and usable material are ready first | Matching base, safe cancellation, writer fence; a certificate alone is insufficient to stop execution |
| Canonical application orchestration | Validate exact input/base; select direct or verified imported material; call Storage | Storage owns apply/flush and recoverable state/output/cursor/provenance linkage |
| Completion delivery | Durable delivery ACK to Orderer; canonical tx outcomes to TxPool; execution results / optional progress notice to Baton | No Baton response or approval required for certification, sync, application, or ACK |

Executor owns signing, collection, certificate verification and peer result/sync control. Storage owns roots, material validation against the authorized target, physical application, persistence and storage recovery. This path is separate from Baton reports and directions. Continue direct execution while certificate or material is unavailable; do not add a peer barrier before starting work. A certificate arriving before local ordered input stays pending or triggers history recovery. It cannot settle unresolved order.

| Storage responsibility | Existing Commonware work | Application integration |
|---|---|---|
| Valid branch access | QMDB unmerkleized reads/writes and sealed-parent batches | Exact execution base, live-DB access fence, optional rootless read/effects adapter |
| Root preparation | Concrete batch `merkleize`, sealed root/ancestry | Selected deterministic storage/signing boundary and complete result/output binding |
| Canonical writer | `DatabaseSet` / `ManagedDb` apply/finalize lifecycle | One authority across shared/cloned handles; no advisory cancellation of mutations |
| Durability and recovery | Barrier, journal, metadata, rewind/prune APIs | Recoverable state, outputs, cursor and direct/imported provenance linkage |
| Serving and retention | QMDB readers/sync source and storage primitives | Retained query/material scope and reference-aware physical reclamation |

Do not require `commonware_glue::stateful::Application`. Its propose/verify/apply outputs are merkleized; using that lifecycle for every speculative attempt can force a commitment before it is useful. Reuse the lower-level batch/database primitives directly. **Root calculation is deferred until preparation needs it, but always precedes full-result signatures.** Continuing one unsealed batch is supported; branching from an unsealed completed parent still requires an application overlay or another compatible API. [QMDB paths and source versions](qmdb.md#existing-apis-at-the-native-pin-and-indexed-release).

Keep speculative and canonical state separate. Execute produces changes without canonical commit authority. Commit and state sync use Storage only for results bound to proven exact input and the correct predecessor. They share the same canonical writer. An arriving sync result cannot drop an ongoing mutation or bypass it through another cloned DB handle. Fencing covers execution, lazy reads, staged expansion, materialization and Merkleization wherever live database access remains. Switching, race and failure contracts remain open.

## Open decisions

| Item | Decision |
|---|---|
| Application transaction semantics | |
| QMDB database variant / state encoding / root type | |
| Canonical operations / batch-boundary derivation / logical-root integration | |
| Root-deferred read/effects view / checkpoint sealing policy | |
| Block / parent-hash encoding and binding / checkpoint granularity | |
| Execution scheduling / cancellation / worker-fencing contract | |
| Atomic commit of state / outputs / cursor | |
| Branch pruning / memory / disk budget | |
| Replay / checkpoint / state sync | |
| Query interface / certified-result integration | |

## Commonware primitives in the execution layer

**Use existing storage and transport algorithms beneath the Executor/Storage boundary.** No public Runtime or ResultService module is required, and no full Stateful actor is adopted.

| Primitive | Where it connects | Application responsibility |
|---|---|---|
| `commonware_storage::qmdb` and `commonware_glue::stateful::db` (`Unmerkleized`, `Merkleized`, `DatabaseSet`, `Barrier`) | Storage batch/read access, selected commitment preparation and canonical apply/flush | Exact base/ancestry, deterministic materialization, rootless overlay if needed, canonical writer and durable linkage |
| `commonware_glue::stateful::{Stateful, Application}` (reference only) | Demonstrates sealed-parent lifecycle and startup sync | Do not make our Executor depend on this Application or full actor; Multimmit input and deferred-root requirements differ |
| `commonware_cryptography::{Signer, Verifier}` and `commonware_codec::Codec` | `sign_result`, `verify_result` and certificate wire data | Full execution subject, epoch eligibility, distinct signer counting and direct-versus-imported provenance |
| `commonware_cryptography::certificate::{Subject, Attestation, Scheme, Signers}` (conditional) | Existing indexed attestations, signer encoding, batch verification and certificate assembly | Selected execution scheme must preserve full-subject binding and f+1; built-in N5f1 certificate quorum is n-f |
| `commonware_collector::p2p::Engine`; `Originator`, `Handler`, `Monitor` (candidate) | Request an execution attestation and collect responses within Executor | Validate every response before counting f+1 matching eligible signatures; bind request/response commitments and integrate unsolicited statements separately |
| `commonware_resolver::p2p` and `commonware_storage::qmdb::sync::Source`; `commonware_glue::stateful::db::p2p` (candidate) | Obtain missing authenticated state operations/material from Executor peers | Certificate/range/base validation, applicable change-set verification, safe switch fencing and ongoing normal-path state sync |
| `commonware_storage::{journal, metadata}` | Persist cursors and recover applied linkage | State/output/cursor/provenance crash consistency and readiness publication |
| `runtime::{Spawner, Strategizer}`; `utils::futures::{Pool, AbortablePool, OptionFuture}` | Existing worker ownership, compatible Rayon construction and completion polling | Selected placement/work bounds, exact completion context and safe worker/access fencing; cancellation is not quiescence |

**Reuse runtime and future helpers inside the existing worker owner.** Public `OptionFuture` keeps an empty active-work slot pending; its native implementation retains a completed future, so the owner must clear or replace that slot. `Strategizer::strategy` constructs the runtime-owned Rayon strategy without another thread-pool factory. Aborting a completion waiter does not stop separately spawned work; retain worker authority and canonical mutation ownership through actual completion. Placement, parallelism and cancellation policy remain open. [Optional future](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/futures.rs#L150), [Strategy factory](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/lib.rs#L357), [Task/completion distinction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/runtime/src/utils/handle.rs#L28).

Collector is a possible pull-attestation engine, not the f+1 certificate verifier. It marks a requested peer as seen before calling Monitor and counts responses sharing a commitment. Executor keeps its own map of full subjects to validated distinct eligible signatures. An invalid first response can consume a peer slot until cancel/reissue; unsolicited push responses are not accepted as arbitrary new requests. Use direct authenticated P2P for push statements/certificates and reuse collector where its pull lifecycle fits. [Collector response handling](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/p2p/engine.rs).

Reuse existing crypto collection/encoding work through the [certificate recipe](interfaces.md#reuse-certificate-building-blocks). Executor still owns validated distinct collection and application checks; a transport response count or an unchanged native consensus certificate threshold does not provide our execution certificate.

The indexed Stateful actor documents a one-time bootstrap sync from a Marshal floor, followed by recovery on later startups. Our repeated validator-to-validator sync during normal execution is additional integration logic. Reusing its resolver/QMDB building blocks does not provide that lifecycle automatically. Stop unfinished execution only after both certificate and applicable state material are verified.

See [QMDB lifecycle](qmdb.md), [state-sync contract](state-sync.md) and [versioned primitive evidence](../reference/integration.md#primitive-reuse-catalog).
