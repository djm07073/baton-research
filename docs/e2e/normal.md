# Normal flow: transaction to applied state

**A transaction moves from a candidate to a block, then to an ordered input and durable state.** TxPool admits it, BlockService packages it through existing body primitives, consensus fixes the order, Executor computes the changes, and Storage applies and persists them. The sequences below show the normal path and transaction-admission cases.

## Full E2E: transaction input to canonical state

```mermaid
sequenceDiagram
    participant C as Client
    participant T as TxPool
    participant N as Multimmit / body attachment
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
    N-->>B: Native exact finality / history evidence
    B->>B: Independently verify and retain continuous irrevocable input
    B-->>E: OrderedRange to Executor::commit
    E->>E: commit(range): reuse exact prefix / finish missing work
    E->>S: prepare(completed changes, selected boundary/rule)
    S-->>E: Prepared material + result commitment
    Note over E,S: Root exists before direct-result signing, peer collection does not gate native cut
    E->>S: apply(authorized canonical input, prepared material)
    S->>S: QMDB apply/flush + recoverable metadata linkage
    S-->>E: Durable CommitResult
    E-->>B: Durable result to internal delivery tracking
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
    participant P as TxPool
    participant B as BlockService
    participant E as Executor
    C->>P: admit(tx, source)
    P->>P: Stateless validation and internal payload policy
    alt Invalid input
        P-->>C: Admission: dropped
    else Valid selected candidate
        P->>P: Deduplicate and retain as selected
        P-->>C: Admission: selected
    else Valid unselected candidate
        P->>P: Deduplicate and retain as unselected
        P-->>C: Admission: unselected
        Note over C,P: Retained for chosen P2P policy, excluded from local batches
    end
    B->>P: select(producer context, limits)
    P->>P: Read selected candidates, preserve dependency and size limits
    P-->>B: Candidate batch, candidates remain retained
    Note over P,B: Proposal cancellation needs no public pool callback
    E-->>P: Durable canonical tx outcomes to internal maintenance
    P->>P: Reconcile retained candidates through existing backend
```

[Open full-size diagram](../assets/diagrams/diagram-03.svg)

RPC and peer transactions enter through the same `admit` contract. Static analysis and classification are internal. Selected/unselected are logical candidate classes in one reused pool; their physical representation and the chosen policy remain open. Duplicate admission preserves the retained candidate identity rather than creating a second entry. Invalid input differs from a valid unselected candidate.

Several producers may include the same transaction in their bodies. Local pool duplicate detection and canonical duplicate execution semantics are separate contracts; admission deduplication does not establish global exactly-once behavior. Do not permanently delete a transaction merely because it entered an unagreed body. Concrete semantics and cleanup remain open in the Tx decisions.
