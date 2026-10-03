# State sync from certified execution results

**Executor may finish a range by importing a verified peer result.** When a matching certificate and usable change set arrive before local execution finishes, it can safely stop remaining work and apply that result. Executors communicate directly. Switching and storage details remain open.

## State sync from certified execution results

Certified execution-result sync is an option on the **normal validator path**, not only restart or lag recovery. A validator already executing can reduce remaining work when certified results and applicable change sets become ready first. Responsibility and peer communication are adopted requirements; transition policy, material format, verification, persistence, and safety/liveness validation remain implementation work. The requirement does not force replacement of direct execution or waiting for certificates. Application and recovery follow [Executor durability](qmdb.md#commit-a-branch-to-canonical-state). Certificate and material verification are separate, as shown below. QMDB sync-target verification does not automatically authenticate native order or execution-certificate provenance.

| Stage | Verify | Pass to the next stage |
|---|---|---|
| Certificate | f+1 distinct eligible epoch validators on the same statement; exact native range, input state, runtime, result | Verified target statement |
| Material | Delta / checkpoint / outputs match the exact local base and target commitment | Importable state material |
| Application / recovery | Selected durable commit contract for state, outputs, cursor | Imported verified canonical checkpoint |
| Subsequent execution | Direct execution / validation of the next exact range from the imported checkpoint | Next range's direct result and potential signature |

The import commit contract also binds ImportedVerified provenance to canonical-checkpoint recovery. If recovery cannot restore direct-execution evidence for a range, the node cannot produce its own signature for that range. Verifying and applying imported material cannot become an own `DirectExecuted` signature. The receiver may relay or serve the original signers' certificate. It may sign the **next range** after directly executing that range from the adopted canonical base. A correctness certificate does not establish material retention, dissemination, or availability; serving and retention need separate contracts. Delta/checkpoint format, root type, signer boundary, import codec, and crash recovery remain open.
