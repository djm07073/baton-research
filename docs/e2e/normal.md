# Normal flow: transaction to applied state

**A transaction moves from a candidate to a block, then to an ordered input and durable state.** TxPool admits it, BlockService packages it, consensus fixes the order, and Executor applies the result. The sequences below show the normal path and transaction-admission cases.

## Full E2E: transaction input to canonical state

```mermaid
sequenceDiagram
    participant C as Client
    participant T as TxPool
    participant N as Multimmit / body attachment / Orderer
    participant B as Baton
    participant E as Executor
    participant S as Storage / QMDB
    C->>T: admit(tx)
    T-->>C: Admission result
    N->>T: TxPool::select(producer context, limits)
    T-->>N: Candidate tx batch
    N->>N: Body codec + Archive sync, Relay uses buffered broadcast
    N-->>B: CandidateBlock(exact authenticated header + retained body)
    B->>E: execute(block, execution-parent hash, exact context)
    E-->>B: Completed changes / outputs, no root required per attempt
    Note over N,E: Native consensus and Baton reports/directions proceed in parallel
    N-->>E: Orderer delivers irrevocable OrderedRange
    E->>E: commit(range): reuse exact prefix / finish missing work
    E->>S: prepare(completed changes, selected boundary/rule)
    S-->>E: Prepared material + result commitment
    Note over E,S: Root exists before direct-result signing, peer collection does not gate native cut
    E->>S: apply(authorized canonical input, prepared material)
    S->>S: QMDB apply/flush + recoverable metadata linkage
    S-->>E: Durable CommitResult
    E-->>N: Delivery ACK after durability
    E-->>T: Canonical tx outcomes
    opt Optional scheduling notification
        E-->>B: Applied progress, no approval/ACK
    end
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
