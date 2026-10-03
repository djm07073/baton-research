# Reader-page review of concrete storage wiring

Reviewed the current uncommitted additions above baseline `3c5ec96c91883dae892ee99832dee315c789eaee`, against this wave's fresh native/release receipts. This reviewer changed only this report. It is source-fit and document-contract review, not compiled upstream integration or protocol verification.

| Reviewed file | SHA-256 |
|---|---|
| docs/execution/qmdb.md | `7744127a7cfdc28935b13c631fece4768e6da449da8ad2608b49a5c219afbef9` |
| docs/execution/interfaces.md | `fca62ea8e0fa841cc7d389372b1d0b07df84239d98124b6df13c10757b6bed82` |
| docs/overview/rust-interfaces.md | `005135b3d1bc0009e0647380a48cba989ec025199f463746928af510e3e47fd3` |
| docs/reference/integration.md | `6d912ad6a6d7a95e5378903c9f1d89b387d010745083b8863d8f1eca7b7a2b5c` |

## Verdict

The additions correctly close the missing internal branch-access explanation without adding an application trait or public method. Concrete wrapper methods perform keyed access; canonical Storage::read is not a pending-parent reader. Executor still computes effects, Storage prepares chosen roots and owns database application, and glue Application/full actor are not required. Rootless branching, deterministic commitments, access fencing, result provenance and crash linkage remain explicitly unresolved integration contracts.

Two small precision improvements are recommended before publication:

1. Scope the new non-Clone statement to the inspected **Any/Current** unsealed and staged wrappers. The source receipts prove those types, not a universal property of every undecided QMDB variant. Apply that qualifier wherever the new overview/interface prose says “QMDB unsealed/staged handles.” Owned consumption remains correct for the inspected paths.
2. Add a precise [ManagedDb bound citation at native L341](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L341) beside the reverse equality claim. The new “Lifecycle bounds” citation at L508 correctly points to DatabaseSet's tuple-shaped types, but not the preceding ManagedDb bound that motivates the additional equality.

These are scope/attribution refinements, not requests to change responsibility ownership, adopt a storage variant or introduce a new method.

## Verified contracts

- `commonware_glue::stateful::db` is public through glue::stateful; db publicly exposes Shared, lifecycle traits and any/current modules. Importing these utilities does not require implementing Application or starting Stateful. The crate still has its ordinary dependencies, and glue's module is explicitly ALPHA in glue/src/lib.rs. Current prose preserves both facts.
- At a validated applied base, DatabaseSet::new_batches returns owned batch handles and releases construction read access. At a sealed pending parent, fork_batches / Merkleized::new_batch reuse the actual ancestor overlay. Neither API forks an unsealed parent. Concrete Storage supply is described as internal composition rather than a fabricated upstream Storage trait.
- AnyUnmerkleized's inherent get/get_many/write/stage methods are public; Current has matching access methods. Generic Unmerkleized provides merkleize, not generic keyed methods. DatabaseSet::Unmerkleized is only Send and may be a tuple. Any's generic test trait module is cfg(test/test-traits). Reader returns access to the applied DB and has no pending-prefix overlay. Current prose reflects those production boundaries.
- ManagedDb::Merkleized has `Merkleized<Unmerkleized = Self::Unmerkleized>`, but ManagedDb::Unmerkleized lacks the reverse equality to DB::Merkleized. The explicitly stated generic helper bound is therefore necessary; actual supported wrappers satisfy it. Tuple sealing and application commitment composition remain distinct and no tuple-wide upstream merkleize/root is claimed.
- Inspected Any/Current unsealed/staged types lack Clone, retain private batch/mutation storage, and are consumed by seal/stage operations. Retaining effects before preparation or retaining a sealed checkpoint for its existing fork correctly explains prefix/multiple-child reuse. The new text does not promise extraction from private maps, arbitrary rootless fork or old sealed-ABC ancestry preservation after a new AB commitment.
- AnyMerkleized clones Arc plus the matching Shared handle, so cloneable prepared material can reuse it directly. PreparedResult still contains application input/result/provenance binding; upstream material does not provide that binding by itself.
- Concrete Any/Current validate_batch validates ancestry/floors against the current DB without consuming it. The text requires the same application writer/access authority through validation/use, preserves separate exact-input/provenance checks, and explicitly excludes arbitrary material verification, later I/O/grafted-state/cancellation guarantees. It does not claim preflight makes mutation atomic or safe against uncontrolled clones.
- Existing native finalize(batch) versus release apply(batch)/finalize() lifecycle distinctions remain intact. No result signature is moved before root preparation, imported work gains no own direct provenance, and no readable/selected/materialized state is promoted to durable acknowledgement without the existing crash-linkage contract.

## Citation and interface check

New citation anchors resolve to these actual native lines:

| Citation | Exact source at anchor | Assessment |
|---|---|---|
| glue/src/stateful/db/mod.rs L106 | `pub mod any;` | Public variant modules; lifecycle types are later in the same file |
| glue/src/stateful/db/any.rs L110 | Wrapper keyed read documentation immediately before public get | Correct method section |
| glue/src/stateful/db/mod.rs L508 | `pub trait DatabaseSet<E>` | Correct tuple/set bounds; supplement with ManagedDb L341 |
| glue/src/stateful/db/any.rs L174 | Clone implementation for AnyMerkleized | Exact cheap sealed-clone source |
| storage/src/qmdb/any/batch.rs L2733 | Public `validate_batch` | Exact native preflight |
| storage/src/qmdb/current/db.rs L776 | Public `validate_batch` | Exact native Current preflight |

Comparison of public trait declarations, associated types and method signature shapes against HEAD shows no change: the diff only extends Storage comments and surrounding explanation. All five application traits remain; branch access is internal and no new method is inserted. The reviewed integration paragraph accurately summarizes wrapper reuse, one-shot retention, tuple component sealing, reverse equality and scoped preflight. Other pool/network/Orderer changes in integration.md are outside this targeted storage review.

Reviewed hashes apply only to the snapshot above. Subsequent corrections or concurrent changes require their own readback; publication and upstream compiler compatibility are not established by this report.
