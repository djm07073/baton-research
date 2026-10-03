# Independent cross-review of the storage first wave

Reviewed `storage-wave1/REPORT.md` and `storage-wave1/storage-contract.rs.txt` against pinned primary source. This review writes only this file. It does not change the other report, canonical docs, source pin, public traits or open decisions. No protocol implementation, compilation or benchmark was performed.

## Verdict

The report's central reuse claims are supported: QMDB permits work in an unmerkleized batch before hashing; its existing parent-fork interface accepts sealed parents; native and release lifecycle recipes differ; pending reads are branch-scoped rather than immutable snapshots; the generic collector and sync engine do not authenticate Baton's execution certificate. The report appropriately marks rootless overlays, normal-path imported switching and cross-database state/output/cursor/provenance atomicity as application integration work.

Do not promote the sketch to an implementation contract without the clarifications below. These are missing explicit obligations in a design sketch, not findings from an executed implementation. None requires choosing a concrete root, wire codec, signing interval or new public trait.

## Independently checked source boundaries

Fresh raw GitHub fetches matched the native source receipts byte-for-byte:

- Native `glue/src/stateful/db/mod.rs`: SHA-256 `36036c705fc5e2b78cf3bae2bed816d25481f612f624ef93abfac1b3c4a39201`.
- Native `storage/src/qmdb/any/batch.rs`: SHA-256 `35b1c70f82cf9f0de607f13908b272b15c6f5aed6b1e06491c6b7ac51ff0d582`.

Six release MCP text receipts were independently compared line-by-line with raw `v2026.9.0` source: Any batch, glue DB lifecycle, Any wrappers, collector engine, sync engine and sync database. All substantive lines matched; each indexed extract adds one final empty line. The report's explicitly invalid HTML receipts must remain excluded.

| Boundary | Checked primary evidence | Assessment |
|---|---|---|
| Native apply + durability recipe | [ManagedDb::finalize L384](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L384), [DatabaseSet::finalize L559](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L559) | Native finalize takes sealed batches and returns a durability Barrier; there is no native DatabaseSet::apply split in the inspected file. |
| Release split and flush concurrency | [ManagedDb L390](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L390), [mutation safety L520](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L520), [DatabaseSet lifecycle L578](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L578) | Release apply returns readable, independently rewindable state; finalize starts durability. Later apply is allowed while a returned barrier remains pending; mutation method bodies must not overlap, and the barrier must be observed before finalize again or pruning. Report states this correctly. |
| Durability truthfulness | [Native Barrier L449](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L449) | `durable()` returns false on runtime abort/closure and panics on other flush failures. Neither is success. Empty barriers are immediately durable and therefore cannot alone certify a nonempty application commit. |
| Public imports in sketch | [Native qmdb module L85](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/mod.rs#L85), [native Unmerkleized/Merkleized L291](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L291) | `qmdb::batch_chain` is public; Commitment is an upstream operation-history identity, not a chosen application result root. Reusing DatabaseSet/Barrier does not require the Stateful actor or stateful::Application. |
| Deferred read-your-writes | [Native write L1302](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L1302), [native get/get_many L1760](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L1760) | Writes are last-write-wins in the unsealed batch; reads consult mutations, ancestor diffs and then supplied live DB. Execution before hashing is supported for this batch. |
| Fork boundary and live views | [native fork_batches L548](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L548), [Any branch validity L334](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L334), [release Shared read L110](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/any.rs#L110) | Existing child forks use Merkleized parents. Shared read locks protect an individual operation but do not make a branch an immutable historical snapshot across calls. |
| Staged execution | [release stage expansion L1319](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/any/batch.rs#L1319) | Stable appended indices do not deduplicate keys or expose future indexed writes as a working execution view. Report correctly assigns overlay read-your-writes to the application. |
| Storage applicability | [release Bounds L67](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/batch_chain.rs#L67), [applicability L183](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/batch_chain.rs#L183) | Apply uses operation size/root and ancestor boundaries plus floors. Equal final key/value state is insufficient; application execution-parent identity cannot replace storage ancestry. |
| Collector | [release admission L208](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/collector/src/p2p/engine.rs#L208) | Decoded response commitment and requested peer are checked, then the seen-peer slot is consumed before Monitor. Raw count is not cryptographic full-subject agreement or f+1 eligibility. |
| Sync | [release target L28](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/target.rs#L28), [rebuild/persist L59](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/database.rs#L59) | Targets describe the same append-only operation log; root verification/persistence do not authenticate epoch/runtime/order or execution signatures. Repeated active-node swap is not supplied by the one-time Stateful sync recipe. |

## Required clarification 1: separate shared statement fields from local fences

Sketch lines 19–38 place `writer_generation`, retained ranges and `worker_generation` in StorageBase/ExecutionBinding. These are useful local validity data. They must not automatically become the cross-validator execution-result equality/signature subject. Honest validators can have different worker generations, physical prune floors and locally retained ranges while agreeing on the same canonical result.

The report should explicitly distinguish a deterministic shared result statement from a local execution/storage access binding. Shared subject fields must bind the adopted exact input/range, canonical input commitment, application/runtime semantics, result and relevant common encoding/boundary rule. Local worker/writer generation, cancellation correlation and physical retention metadata fence local access/adoption. If a storage operation identity is part of the shared result, it must arise from the chosen common materialization rule, not a node's incidental physical state.

Required correction: add this distinction beside the illustrative binding record and prohibit signing/collecting the entire local record by default. No concrete statement schema is selected here.

## Required clarification 2: preparation must retain the selected rule and full result binding

Sketch `Storage::prepare` receives `StorageRule` at line 103, but `Prepared` at lines 49–56 contains the same generic Binding as Executed and no explicit rule. A comment promises that the rule is added to the signing subject; the sketch does not say how the prepared object preserves or verifies that addition. Likewise `result_commitment` and `outputs` are separate fields, with no explicit shared subject linking them.

Required correction: Prepared must carry a prepared subject/binding that commits to the selected storage boundary/materialization rule and the defined complete result, or explicitly retain a rule/result witness from which Executor verifies that subject. If outcomes belong to the application result, the full statement must bind them as well as the state commitment. Do not infer that a state root authenticates arbitrary output bytes. Preserve rule/root/output choices as undecided; specify the obligation without inventing a hash or default.

This matters for root deferral: it is safe to defer hashing abandoned work, but the actual signed subject must be fixed before any signature. Re-preparing a range under a different rule cannot silently reuse a certificate for the previous subject.

## Required clarification 3: the valid-read fence covers preparation too

The report correctly warns that a final generation check cannot repair intermediate live-DB reads. Extend that warning to `stage`, `expand`, materialization and Merkleization, not just transaction get/fallback reads. The Any glue wrapper acquires Shared's current read guard for each call; that lock is not an application branch lease lasting from begin to prepare.

Sketch `begin_applied` promises binding validation coupled to valid access; `prepare` only describes delayed Merkleization. Required correction: state how prepare validates/holds an admissible sealed/applied base while resolving reads and sealing, and how canonical apply or imported state swap invalidates/rebases affected work. Upstream StaleBatch rejection at apply is valuable but is not permission to sign outputs computed against incompatible intermediate reads.

An implementation can satisfy this with appropriate serialization, read leases or an independently materialized immutable read base. This review chooses none. It requires that the interface describe the lifetime/ownership guarantee rather than merely capture a starting generation.

## Required clarification 4: preserve direct-versus-imported provenance through preparation

The prose correctly rejects signing imported state as direct execution. The sketch's sole preparation input is named Executed; its comments say direct evidence is retained in Executor, but Prepared and Applied do not expose provenance or a retained evidence reference. Imported material is only mentioned in the final call-flow comment.

Required correction: specify a direct preparation route requiring retained direct execution/validation evidence and a verified-import route requiring the full authorized certificate plus applicable material. These can share the same Storage methods with explicit provenance/evidence bindings; separate actors or public traits are unnecessary. Executor's signing eligibility must query preserved direct evidence, never infer direct execution from possession of a Prepared batch or successful imported root verification.

The f+1 check remains distinct eligible epoch validators over the identical full subject, with irrevocable exact order and canonical input linkage at state finalization. Honest direct signers need not be members of a particular ordering QC. Baton is outside the sign/certificate/import/apply gates. Normal-path switching stops unfinished local execution only after the certificate and applicable material are verified.

## Required clarification 5: one canonical writer spans aliases and durable metadata

Using `&mut self` on the Storage facade is helpful but does not serialize all cloned DatabaseSet handles: upstream DatabaseSet is Clone and its mutation methods take `&self`. Tuple finalize performs independently locked member mutations; it does not provide a crash-atomic application state/output/cursor/provenance commit record. The report recognizes this limitation; keep it prominent in the sketch.

Required correction: document that canonical permit, writer generation and fencing belong to the one logical mutation authority across every alias, recovery, prune and imported swap route. A permit must bind the exact authorized prepared subject/base; imported permissions require the verified certificate/material route, while direct canonical apply need not wait for peer collection after the adopted exact-order/base checks.

`Applied` currently returns only Binding and Barrier after consuming Prepared and its outputs. The adapter must retain a recoverable application commit/linkage record, or a reference to it, carrying the selected result, outputs, order/cursor and immutable direct/imported provenance before durable ACK. An empty/mismatched barrier must never discharge that record. `durable()` must verify the barrier covers the intended state/material and complete the application record's durability/recovery protocol before Orderer ACK or canonical TxPool outcomes. Details of that record remain open.

## Smaller clarification: pending read view and minimal facade

The sketch's tuple of Unmerkleized batches does not expose a generic read/write interface; callers dispatch concrete Any/Current methods, as the report already does for tuple Merkleization. State this explicitly so readers do not mistake DatabaseSet for a universal Executor transaction API. The rootless pending-parent overlay is optional application machinery; no upstream unsealed-parent fork or arbitrary snapshot API has been established.

A minimum Storage logical role can own concrete upstream read/batch handles, preparation and canonical mutation/durability, plus narrow applicability/fencing/recovery adapters. It need not add a new mandatory actor or adopt Stateful. Avoid promoting the draft Storage trait count solely because imports happen to reside under `glue::stateful::db`.

## Cross-review completion

No unsupported claim was found that the native pin already has the release apply/finalize split or an unsealed-parent fork. Imports and the principal primitive boundaries are truthful. The five clarifications above should accompany any canonical synchronization or reviewable interface revision. They preserve latest ownership decisions, full-subject certificate semantics, root deferral, no direction ACK/quorum, no added cut wait, and all blank policy choices.
