# Finalized order and canonical state application

**Orderer delivers exact input; Executor selects its effects; Storage makes them durable.** Executor selects matching completed work, executes missing work or authorizes verified peer material; Storage prepares roots and applies it. Executor acknowledges delivery only after Storage has made canonical state, outputs, cursor and provenance recoverably durable.

## Cut commit → ordered range → execution commit

```mermaid
sequenceDiagram
    participant N as Native Multimmit
    participant M as Orderer
    participant E as Executor
    participant S as Storage / QMDB
    N-->>M: Authenticated finality / extension evidence
    M->>M: Recover exact history / frozen policy / slot evidence
    alt Earlier slot or history unresolved
        M->>M: Backfill and stop dense emission at the gap
        Note over N,M: Native protocol continues under its own rules
    else Next continuous exact range is irrevocable
        M-->>E: OrderedRange(predecessor, inputs, evidence)
        E->>E: commit(range, expected canonical predecessor)
        alt Matching completed speculative prefix exists
            E->>E: Select exact committed prefix, keep compatible suffix pending
        else Applicable peer certificate and material verified
            E->>E: Fence unfinished work and apply material at matching base
        else Local work / peer material unavailable
            E->>E: Execute from canonical base / repair suffix, peer sync in parallel
        end
        E->>S: prepare / apply exact authorized material
        S-->>E: Durable CommitResult after state/output/cursor/provenance linkage
        E-->>M: CommitResult / delivery ACK after durability
    end
```

[Open full-size diagram](../assets/diagrams/diagram-08.svg)

The first native leader-finality notice does not immediately establish the complete body order. First identify the **exact execution range**, including native extensions and history. Emit included slots, skip authenticated irrevocably-empty slots, and stop at unresolved slots. Missing bodies are not empty slots. Even an irreversible range may need body fetch or predecessor-state recovery before execution commit. This local input wait is distinct from adding a native round for direction replies.

## Execution lifecycle: QMDB branches and canonical promotion

```mermaid
sequenceDiagram
    participant B as Baton
    participant M as Orderer
    participant E as Executor
    participant S as Storage / QMDB
    B->>E: execute(block, execution-parent hash, exact context)
    E->>E: Resolve completed parent, link execution child
    E->>S: Obtain valid branch access / working draft
    S-->>E: Unsealed batch or rootless read/effects adapter
    E->>E: Compute ordered transaction changes and outputs
    E-->>B: Completed ExecutionResult, hashing may be deferred
    M-->>E: OrderedRange(irrevocable input, canonical predecessor)
    E->>E: commit(range): select exact completed prefix
    E->>E: Finish missing work, fence incompatible/unknown workers
    E->>S: prepare(exact selected prefix, storage rule)
    S->>S: Materialize / concrete merkleize with valid read-access fence
    S-->>E: Prepared material, root and exact result/output binding
    E->>S: apply(authorized canonical range, prepared result)
    S->>S: Native DatabaseSet::finalize(matching sealed batches)
    S->>S: Observe Barrier::durable + metadata/provenance linkage
    alt Durable barrier and recoverable linkage succeed
        S-->>E: Durable CommitResult
        E->>E: Promote canonical path, logically prune conflicts
        E-->>M: Durable delivery ACK
        opt Optional scheduling notification
            E-->>B: Applied progress only
        end
        opt References and serving obligations permit release
            S->>S: Physically reclaim unreferenced material
        end
    else Failed flush / shutdown / incomplete linkage
        S-->>E: No successful durable completion
        Note over M,E: No CommitResult/ACK, recover authoritative durable state
    end
```

[Open full-size diagram](../assets/diagrams/diagram-09.svg)

This sequence assumes completed branch work exactly matches the canonical range. If it is missing or different, follow [canonical execution / repair](canonical.md#cut-commit--ordered-range--execution-commit). Branch construction, canonical promotion, and logical pruning belong to Executor. Storage performs physical reclamation after safe retention and worker-reference release; concrete GC scheduling remains open. The diagram uses the adopted native finalize(batch) recipe inside Storage; the release split is recorded in the QMDB page. `DatabaseSet::finalize` and `Barrier::durable` are upstream APIs, but applied/readable state is not durable completion. See [canonical application](../execution/qmdb.md#commit-a-branch-to-canonical-state) for state/output/cursor linkage, failures, and acknowledgement boundaries, and the [durability barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L469).
