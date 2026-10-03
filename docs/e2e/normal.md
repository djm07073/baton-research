# Normal flow: transaction to applied state

**A transaction moves from a candidate to a block, then to an ordered input and durable state.** TxPool admits it, BlockService packages it, consensus fixes the order, and Executor applies the result. The sequences below show the normal path and transaction-admission cases.

## Full E2E: transaction input to canonical state

```mermaid
sequenceDiagram
    participant C as Client
    participant T as TxPool
    participant N as Multimmit + BlockService + Orderer
    participant B as Baton
    participant E as Executor
    C->>T: admit(tx)
    T-->>C: Admitted(tx_id)
    N->>T: TxPool::select(producer context, limits)
    T-->>N: Candidate tx batch
    N->>N: Build body, store + sync, native header / DA
    N-->>B: CandidateBlock(block_ref, verified body, context)
    B->>E: execute(block hash, parent block hash, exact inputs/context)
    E-->>B: ExecutionResult / branch handle
    Note over N,B: Native consensus and reports / directions proceed in parallel
    N-->>E: Orderer delivers OrderedRange(exact order, predecessor, evidence)
    E->>E: commit(ordered range)
    E->>E: Reuse matching work / execute or verify peer state material
    E->>E: Durable canonical state + outputs + cursor
    E-->>N: CommitResult / delivery ACK after durability, not native vote
    E-->>T: TxPool::on_commit(exact range / tx outcomes)
    opt Local scheduling notification
        E-->>B: Applied progress notification, no approval / ACK required
    end
    Note over E: Executor peer finalization / sync: exact order + f+1 signatures on one statement
```

[Open full-size diagram](../assets/diagrams/diagram-02.svg)

This diagram shows one arrival order where speculative work finishes first. If cut or OrderedRange arrives first, use [canonical execution / repair](canonical.md#cut-commit--ordered-range--execution-commit). Admission does not establish block inclusion or transaction success. Local durable commit and f+1 result certification are separate events. Certification does not become a prerequisite for the next native cut or speculative execution.

## Tx lifecycle: new, duplicate, and invalid transactions

```mermaid
sequenceDiagram
    participant C as Client / Tx peer
    participant A as TxPool: admission
    participant P as TxPool: candidate storage
    participant B as BlockService
    participant O as Executor
    C->>A: Tx bytes
    A->>A: Decode / domain / signature / size checks
    alt Structurally invalid transaction
        A-->>C: Rejected
    else Valid transaction
        opt Static analysis placed at admission
            A->>A: TxPool::analyze / classify(tx payload) → static policy input
        end
        A->>P: Admit(tx_id, tx, optional metadata)
        alt Same tx_id already retained
            P-->>A: Existing admission
        else New transaction
            P-->>A: New admission
        end
        A-->>C: Admission result
        B->>P: TxPool::select(context, limits)
        opt Static analysis placed at packing
            P->>P: TxPool::analyze / classify → filter candidates
        end
        P-->>B: Candidate batch
        Note over P,B: Selection / proposal cancellation / reselection policy is open
        O-->>P: Durable canonical outcome
        P->>P: Reconcile lifecycle using canonical outcome
    end
```

[Open full-size diagram](../assets/diagrams/diagram-03.svg)

The two optional branches show alternative static-analysis placements. They do not require analysis at both admission and packing. A separate router versus an inclusion adapter above the pool remains undecided.

Several producers may include the same transaction in their bodies. Local pool duplicate detection and canonical duplicate execution semantics are separate contracts; admission deduplication does not establish global exactly-once behavior. Do not permanently delete a transaction merely because it entered an unagreed body. Concrete semantics and cleanup remain open in the Tx decisions.
