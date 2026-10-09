# Normal flow: transaction to applied state

**One App owns the transaction pool, scheduler and transaction execution.** Multimmit calls the App through `Automaton`; Marshal stores and broadcasts complete blocks and delivers their finalized order through `Reporter<Update>`. App storage applies the matching execution result durably.

## Full E2E: transaction input to canonical state

```mermaid
sequenceDiagram
    participant C as Client / tx peer
    participant A as App
    participant N as Multimmit Engine
    participant M as Multimmit Marshal
    participant Q as App scheduler / workers
    participant S as App storage / QMDB
    C->>A: Submit transaction
    A->>A: Validate, deduplicate, retain in TxPool
    N->>A: Automaton::propose(producer Context)
    A->>A: Select bounded batch and build complete block
    A->>M: stage_block(header + body)
    M-->>A: Custody token: accepted storage work
    A-->>N: Resolve proposal receiver with body digest
    N->>A: Automaton::verify(same Context, body digest)
    A->>M: Establish exact durable custody
    M-->>A: Complete retained block
    A->>A: Validate payload and retain candidate state
    A-->>N: Resolve verification receiver true
    N->>N: Sign producer header
    N->>M: Relay::broadcast(header digest, ())
    M->>M: Broadcast complete block through existing buffer
    opt Eligible live candidate
        A->>Q: Admit or update pending candidate
        Q->>Q: Start asynchronous work when exact parent and worker capacity are ready
    end
    N-->>M: Reporter::report(native Activity)
    M->>M: Verify history, order, recover bodies, retain outputs
    M-->>A: Reporter::report(Update(index, block, acknowledgement))
    A->>A: Retain Update and return Feedback promptly
    A->>A: Reconcile confirmed input in exact index order
    A->>Q: Select matching work or finish / repair from canonical base
    Q->>S: Prepare selected result, apply and persist
    S-->>A: Durable state + outputs + applied identity / provenance
    A->>A: Advance applied base, schedule pool maintenance
    A-->>M: acknowledgement.acknowledge()
    M->>M: Persist acknowledged continuous delivery cursor
```

[Open full-size diagram](../assets/diagrams/diagram-02.svg)

Speculative execution may finish before or after `Update` arrives. `verify(true)` establishes payload validity and custody; it does not wait for that execution. For local blocks, candidate admission must respect the fact that this verify occurs before native header signing. The [callback contract](../baton/interfaces.md) covers peer, local and recovery requests.

Marshal already delivers the ordinary native total order. The App reconciles retained work against these Updates and its canonical worker applies their exact sequence. It does not sort Updates again or require an earlier speculative candidate. In Baton mode, reports and direction operate alongside this path; native proposal-policy integration remains [open](../consensus/decisions.md).

Local durable application and f+1 result certification are separate milestones. Neither creates a wait in native cut formation. If the matching speculative result already exists, confirmation can consist of selecting it and completing storage work. Otherwise the App still needs the missing execution or verified peer material before durable application and ACK.

## Tx lifecycle: new, duplicate, and invalid transactions

```mermaid
sequenceDiagram
    participant C as Client / tx peer
    participant A as App
    participant P as App TxPool
    participant W as App canonical worker
    C->>A: Submit transaction
    A->>P: Internal admit(tx, source)
    P->>P: Stateless validation and payload policy
    alt Invalid input
        P-->>A: Reject
    else Valid selected candidate
        P->>P: Deduplicate and retain as selected
        P-->>A: Admission accepted
    else Valid unselected candidate
        P->>P: Retain for selected propagation / retention policy
        P-->>A: Admission accepted, excluded from local batches
    end
    A->>P: Internal select(Context, limits) during propose
    P-->>A: Bounded candidate batch, candidates retained
    Note over A,P: Selection and proposal cancellation are not canonical retirement
    W-->>P: Durable canonical transaction outcomes
    P->>P: Reconcile candidates through the selected backend
```

[Open full-size diagram](../assets/diagrams/diagram-03.svg)

`admit` and `select` name App-internal pool operations, not a new public consensus trait. Selected/unselected are logical classes; their physical representation and policy remain open. RPC and peer input use the same validation and admission policy. Duplicate suppression in one pool does not establish global exactly-once execution when multiple producers include the same transaction.

See [transaction admission and selection](../tx/interfaces.md) for the App pool contract, the [backend survey](../tx/README.md) for reuse options, and [canonical application](canonical.md) for durable outcome handling. The node assembly is grounded in the current [log-multimmit example](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/node.rs#L242); its synthetic payload generator does not implement this transaction application.
