# State sync from certified execution results

**Executor may finish a range by importing a verified peer result.** When a matching certificate and usable change set arrive before local execution finishes, it can safely stop remaining work and apply that result. Executors communicate directly. Switching and storage details remain open.

## State sync from certified execution results

Certified execution-result sync is an option on the **normal validator path**, not only restart or lag recovery. A validator already executing can reduce remaining work when certified results and applicable change sets become ready first. Responsibility and peer communication are adopted requirements; transition policy, material format, verification, persistence, and safety/liveness validation remain implementation work. The requirement does not force replacement of direct execution or waiting for certificates. Executor orchestrates switching; Storage owns target/material validation, canonical mutation and recovery under [the storage durability contract](qmdb.md#commit-a-branch-to-canonical-state). Certificate and material verification are separate, as shown below. QMDB sync-target verification does not automatically authenticate native order or execution-certificate provenance.

| Stage | Verify | Pass to the next stage |
|---|---|---|
| Certificate | f+1 distinct eligible epoch validators on the same statement; exact native range, input state, runtime, result | Verified target statement |
| Material | Delta / checkpoint / outputs match the exact local base and target commitment | Importable state material |
| Storage application / recovery | Selected durable commit contract for state, outputs, cursor and provenance | Imported verified canonical checkpoint |
| Subsequent execution | Direct execution / validation of the next exact range from the imported checkpoint | Next range's direct result and potential signature |

The import commit contract also binds ImportedVerified provenance to canonical-checkpoint recovery. If recovery cannot restore direct-execution evidence for a range, the node cannot produce its own signature for that range. Verifying and applying imported material cannot become an own `DirectExecuted` signature. The receiver may relay or serve the original signers' certificate. It may sign the **next range** after directly executing that range from the adopted canonical base. A correctness certificate does not establish material retention, dissemination, or availability; serving and retention need separate contracts. Delta/checkpoint format, root type, signer boundary, import codec, and crash recovery remain open.

## Reuse Commonware material transport and proof validation

**Reuse QMDB's authenticated operation sync; add the certified execution target and safe active-validator switch.** At the adopted native pin, `qmdb::sync::Source` serves operation batches/proofs, and `glue::stateful::db::p2p::{Actor, Mailbox}` adapts that source to generic resolver networking. Fresh source comparison found these core sync files and the P2P module identical to indexed `v2026.9.0`; the DB mutation wrappers still have version differences. Reuse these lower-level components without depending on glue Application/full actor; connect them using the selected native DB types. [Sync Source](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/source.rs), [database P2P adapter](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/p2p/mod.rs).

| Existing component | Provides | Executor / Storage connection |
|---|---|---|
| Generic resolver + DB P2P adapter | Keyed operation/material fetch, retries and serving | Executor authorizes the exact target; Storage serves/verifies compatible material and controls retention |
| QMDB sync Target/engine | Checks operations/proofs and rebuilt storage state against caller-trusted ops root/range | Bind that target to the verified execution statement, canonical base, runtime and chosen result root |
| `StateSyncDb::sync_db` / set coordination | Initializes a synchronized DB with anchor metadata | Active-validator writer fencing/swap and recoverable state/output/cursor/provenance linkage remain additional work |
| Executor certificate exchange | Existing authenticated P2P and signature primitives | Full f+1 distinct eligible signatures, exact input-state chain and direct/imported provenance remain application checks |

The QMDB target is an **operations root plus operation range**, not an execution certificate. Current's canonical `root()` differs from its `ops_root`; selecting Current requires verifying the chosen result commitment as well as the sync proof target. Target-update support requires strictly advancing targets on the same history; it is not an arbitrary branch switch. [Target](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/target.rs#L9), [engine target contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/sync/engine.rs).

The existing Stateful bootstrap lifecycle does not provide repeated normal-path certified-result switching. Executor continues direct work until both certificate and applicable material are ready; Storage then uses the same canonical authority as local execution. Partial local writes cannot become the base of a delta meant for another checkpoint. Root/material codecs, switch policy and storage replacement protocol remain open.
