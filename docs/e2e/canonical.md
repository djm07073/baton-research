# Finalized order and canonical state application

**Orderer delivers the agreed inputs; Executor makes their effects durable.** Executor selects matching completed work, executes missing work, or verifies usable peer material. It acknowledges delivery only after canonical application is recoverably durable.

## Cut commit → ordered range → execution commit

```mermaid
sequenceDiagram
    participant N as Native Multimmit
    participant M as Orderer
    participant E as Executor
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
        E->>E: Validate results, apply QMDB changes, durable commit
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
    participant O as Executor
    participant Q as QMDB batches
    participant A as Runtime
    B->>O: execute(base checkpoint, exact order, runtime, generation)
    O->>O: Locate valid base / retain reusable prefix
    O->>Q: Fork parent batch / create branch
    Q-->>O: Mutable batch
    loop Ordered input blocks
        O->>A: Runtime executes body against branch state
        A-->>O: State writes + outputs
        O->>Q: Apply pending writes to branch
    end
    O->>Q: Merkleize at requested checkpoint boundary, granularity undecided
    O-->>B: ExecutionResult(branch handle, context, results)
    M-->>O: OrderedRange(irrevocable range, canonical predecessor)
    O->>O: commit(range)
    O->>O: Verify branch exactly matches committed input
    O->>O: Fence incompatible / unknown active branch workers
    O->>Q: DatabaseSet::finalize(matching batches)
    Q-->>O: Applied / readable state + Barrier
    O->>Q: Barrier::durable()
    alt Durable barrier succeeds and metadata linkage completes
        Q-->>O: Durable flush completion
        O->>O: Complete recoverable state + outputs + cursor linkage
        O-->>M: CommitResult / durable delivery ACK
        opt Local scheduling notification
            O-->>B: Applied progress, no finalization approval
        end
        opt Safe retention boundary permits cleanup
            O->>O: Prune incompatible forks / retain compatible suffixes
        end
    else Shutdown, flush failure, or incomplete metadata linkage
        Q-->>O: No successful durable completion
        Note over M,O: No CommitResult / delivery ACK, handle at recovery boundary
    end
```

[Open full-size diagram](../assets/diagrams/diagram-09.svg)

This sequence assumes completed branch work exactly matches the canonical range. If it is missing or different, follow [canonical execution / repair](canonical.md#cut-commit--ordered-range--execution-commit). Branch construction and pruning are proposed Executor behavior; cleanup is optional and concrete GC scheduling is open. `DatabaseSet::finalize` and `Barrier::durable` are upstream APIs, but applied/readable state is not durable completion. See [canonical application](../execution/qmdb.md#commit-a-branch-to-canonical-state) for state/output/cursor linkage, failures, and acknowledgement boundaries, and the [durability barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L469).
