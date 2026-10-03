# Executor interfaces and result certification

**Executor owns execution paths and result certification; Storage owns roots and durable state.** Executor links children to valid parents, computes completed changes, selects the canonical path and certifies or imports results. Baton owns direction selection.

## Interface overview

Rust declarations: [Executor](../overview/rust-interfaces.md#executor) and [Storage](../overview/rust-interfaces.md#storage). Each async application method returns a Future with `Result<SuccessType, Self::Error>` as its output. These are integration boundaries, not replacements for QMDB algorithms or separate deployment requirements.

`Executor::Block` carries a block hash, parent block hash, exact ordered body/input references, and execution context. The parent resolves an execution checkpoint with the same base, application rules, and exact preceding input; it is not simply a producer-header parent. `execute(block)` validates that parent, links the child, and computes its transaction effects on branch-scoped state. Missing or unfinished parents leave work pending or require recovery. Reuse requires identical completed work and context; a partial or canceled attempt is not successful ExecutionResult. Hash encoding and concrete fields remain open.

Direction selection belongs to [Baton::plan](../baton/direction.md). Direction changes submit parent-linked blocks through execute(block); task priority, reuse, and stale-result fencing remain internal to Executor. No separate planning, Runtime, ResultService, or reschedule interface is needed for tree handling.

`execute(block)` returns completed unsealed effects and outputs. Storage prepares a root only when a selected storage/signing boundary needs it. Upstream sealed-parent child batches can be reused directly; rootless children require the additional read/effects adapter described in [QMDB](qmdb.md#defer-roots-without-inventing-an-unsealed-parent-fork).

Storage supplies [authorized concrete branch handles](qmdb.md#give-executor-concrete-branch-access) internally through existing batch creation/fork APIs. Executor uses their keyed methods; canonical Storage::read is not a pending-parent query. If ExecutionResult owns an upstream one-shot unsealed draft, prepare consumes it. Retain exact effects beforehand when the same rootless prefix must support another child or preparation; sealed material instead uses existing cheap clones and child forks.

`commit(range)` validates irrevocable exact input and its canonical predecessor, completes missing work, and selects the matching execution path. It calls Storage to prepare/apply exact material, fences conflicts and logically prunes branches while retaining valid descendants. Storage controls physical reclamation after worker/query/result/sync/recovery references permit it. CommitResult means state, outputs, cursor and provenance are recoverably durable. Advisory cancellation cannot drop a canonical mutation future.

| Proposed interface | Input | Responsibility | Successful result |
|---|---|---|---|
| `Executor::execute` | `Self::Block`: execution-parent hash, exact inputs/context | Link valid parent → compute or reuse completed changes/outputs without compulsory hashing | `Self::ExecutionResult` |
| `Executor::commit` | `Self::OrderedRange`: exact input, predecessor, evidence | Select canonical path → Storage preparation/application → logical pruning | `Self::CommitResult` |
| `Executor::recover` | `Self::Recovery` | Coordinate Storage recovery; rebuild only valid execution branches | `Self::Checkpoint` |
| `Storage::prepare` | Completed `ExecutionResult`, selected `Preparation` | Materialize exact prefix, merkleize and bind rule/result/outputs/material | `Self::PreparedResult` |
| `Storage::apply` | Authorized `CanonicalInput`, `PreparedResult` | Check applicability/writer; apply and complete durable linkage | `Self::CommitResult` |
| `Storage::recover` / `read` | Recovery context / retained-version query | Restore durable bases/provenance / read readiness and outputs | `Self::Checkpoint` / `Self::ReadResult` |
| `Executor::sign_result` | `Self::PreparedResult` | Require computed commitment, own direct provenance and irrevocable input before signing | `Self::SignedStatement` |
| `Executor::collect_result` | `Self::SignedStatement` | Check full subject and eligible distinct identities; collect f+1 matches | `Option<Self::ResultCertificate>` |
| `Executor::verify_result` | `Self::ResultCertificate` | Verify signatures, exact order, and canonical input-state chain | `Self::ExecutionStatement` |
| `Executor::result_certificate` | `Self::ResultQuery` | Query retained certification for an exact subject | `Option<Self::ResultCertificate>` |

Application transaction rules execute inside Executor against Storage-provided valid branch access. Commonware task runtime drives jobs/I/O; QMDB provides batches, roots and persistence rather than transaction semantics. Partial or canceled work cannot be adopted as a completed result. Worker generations and storage writer/retention metadata are local authority fields, not shared execution-signature fields. The stable statement binds exact range/base/runtime/rule/result and chosen output/material commitments.

Startup calls recover; state callers use read. Check base-state identity, application version, exact input prefix, worker generation, and canonical cursor binding before reuse. A readable result and a certified result remain different milestones. See [result certification](../e2e/results.md#result-endpoint-direct-execution-and-f1-certification) and [state sync](state-sync.md#state-sync-from-certified-execution-results).

<a id="result-certification-trait"></a>

## Result certification inside Executor

Executor receives peer messages and handles them through `collect_result` / `verify_result`. Successful verification can establish state finalization or allow the state-sync material verification and application path to proceed. A successful certificate query does not establish material availability or local durable application. Reuse Commonware Signer / Verifier and authenticated P2P. Those primitives verify signatures and transport bytes; Executor must bind the application statement, validate its irrevocable input and eligible epoch identities, and enforce f+1 matching subjects. That application verification remains necessary, without a standalone ResultService module. Concrete peer codec, request/response, and sync-switching APIs remain open.

Rust declaration: [Executor](../overview/rust-interfaces.md#executor). The Rust interfaces page owns the complete declaration.

`sign_result` uses a Storage-prepared commitment plus Executor-retained own direct execution/validation evidence. Preparation preserves the selected rule and exact input/base/result/outputs binding; it cannot turn an imported result into direct execution. Complete effects → Storage root preparation → full statement → signature is the order. Advisory speculative order alone cannot be signed. Correctness and local durability remain separate. Per-block/per-chunk boundaries and root/encoding choices remain open; retain statement/provenance obligations through recovery.

`collect_result` verifies the exact full statement and signatures from distinct eligible epoch identities. Fewer than f+1 produces `Ok(None)` and adds no barrier to subsequent execution or native cut. `verify_result` returns a statement only after checking signatures, irrevocable exact order, and canonical input-state chain. One primitive `Verifier::verify` call does not implement this full application verification. `result_certificate` returning `None` means no certified result is available yet, distinct from absent local state. Serving the original certificate and signing own direct work are separate paths. Key, domain, codec, root type, common boundary, and retention remain open.

## Reuse certificate building blocks

**Receive result messages through existing typed P2P; validate and collect them inside Executor.** `p2p::utils::codec::wrap` adapts the raw authenticated Sender/Receiver pair to typed messages. It supplies encoding/decoding and the transport peer identity; Executor checks the full execution subject and original eligible signers. Accepted sends do not prove remote receipt or result certification. [Typed wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/utils/codec.rs#L16).

| Existing exchange component | Use | Application boundary |
|---|---|---|
| Typed P2P sender/receiver | Receive signatures and certificates in the existing Executor owner | Bounded codec, exact statement, eligible original signer and signature checks |
| Optional buffered broadcast | Share/cache an identified certificate or material artifact; get/subscribe by known digest | One object per digest; individual signers' different responses cannot all use only their shared statement digest as the cache key |
| Conditional collector | Solicit request-bound responses using Handler/Monitor and separate request/response channels | Counts requested transport peers before application validation; count is not f+1 verified signers, and cancellation/reissue is explicit |

The buffered cache is transient and has no arbitrary incoming-signature stream. Collector does not supply the resolver's timeout/retry loop. Neither replaces Executor's full-subject signer accumulator. These are conditional existing-handle recipes; message codec, solicitation, topology and budgets remain open. [Buffer cache identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/engine.rs#L327), [Collector response counting](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/p2p/engine.rs#L207), [Collector cancellation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/lib.rs#L35).

**Commonware can verify and package the signatures; Executor decides what they certify.** Reuse `cryptography::certificate::{Subject, Attestation, Scheme, Signers}` when the selected signing scheme fits. These are existing crypto APIs, distinct from Multimmit's protocol-specific Scheme. They can avoid another implementation of signer encoding, batch signature verification and cryptographic aggregation. Result-signing keys and scheme remain undecided. [Certificate APIs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/certificate.rs#L178).

| Step | Existing API | Executor connection |
|---|---|---|
| Define what is signed | `Subject::namespace/message` | Full exact input/range, epoch, canonical base, runtime and result/output commitment |
| Sign direct work | `Scheme::sign` or lower-level `Signer` | Require own direct execution evidence and the Storage-prepared commitment |
| Verify peer signatures | `Scheme::verify_attestation/verify_attestations` | Use the authenticated epoch roster; validate indices and deduplicate before batch verification |
| Package valid signatures | `Scheme::assemble`, existing signer/certificate codecs | Supply only verified distinct signatures for one full subject; enforce the result threshold |
| Verify a received certificate | `certificate::Verifier::verify_certificate` | Also check irrevocable exact order, canonical base, runtime and the full application statement |

**The result threshold remains f+1.** Built-in `N5f1` certificate schemes use `n-f`, which is `4f+1` when `n=5f+1`; they cannot be copied unchanged for execution results. Existing `N5f1::f_plus_one` supplies the arithmetic for the same full authenticated committee. If a generic certificate wrapper is selected, its result-quorum adapter must enforce f+1 consistently during assembly and verification. Lower-level signature/batch/bitmap APIs can be reused while that choice is open. This does not alter native consensus quorums. [Quorum delegation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/ordered.rs#L274), [fault model and f+1](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/utils/src/faults.rs#L62).

An upstream attestation contains a signer index and signature, and its certificate representation contains signature data; neither supplies our execution statement. Keep a bounded, versioned subject envelope and collect by its exact full identity. `assemble` is not signature validation. Duplicate input to scheme batch/assembly APIs is unsupported, and `Signers::from` can panic on duplicate or invalid indices. Validate before construction, and use roster-bounded certificate decoding on peer input. BLS multisig additionally requires caller-verified proofs of possession; non-attributable threshold BLS cannot be assumed to retain the required original signer evidence. These are conditional reuse requirements, not a selected key or certificate format. [Scheme caller contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/certificate.rs#L346), [signer codec](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/certificate.rs#L509), [scheme distinctions](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/certificate.rs#L10).
