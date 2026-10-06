# Block body send, fetch, and receive

**BlockService makes block contents available and keeps them recoverable.** A producer builds and distributes the body; receiving nodes fetch missing bytes, verify the expected content, and establish durable custody. Native consensus handles the header and ordering separately.

## Block lifecycle: mempool → propose → body dissemination

```mermaid
sequenceDiagram
    participant N as Native producer owner
    participant A as BlockService / upstream callbacks
    participant T as TxPool
    participant S as Commonware Archive
    participant D as Commonware buffered Engine
    participant V as Peer body attachment
    N->>A: Automaton::propose(Context)
    A->>T: select(producer context, limits)
    T-->>A: Candidate transactions
    A->>A: Build bounded body, calculate digest/context binding
    A->>S: Put exact body/required parents and sync
    S-->>A: Covering durability + retained exact custody
    A-->>N: Resolve payload digest receiver
    N->>N: Native header signing under native authority
    N->>A: Relay::broadcast(digest, ())
    A->>A: Schedule retained-body lookup
    A->>D: Mailbox::broadcast_shared(recipients, retained Arc)
    D-->>V: Body over authenticated P2P channel
    Note over A,V: Local broadcast admission is not remote receipt/custody ACK
    Note over N,V: Native headers/DA use native data plane, bodies use application channels
```

[Open full-size diagram](../assets/diagrams/diagram-04.svg)

Native Core owns producer-header signing authority. The builder creates a body and returns its digest. Application code does not call the native header signer in Core's place.

TxPool selection retains candidates, so local proposal cancellation needs no public pool callback or generic reinsertion step. A destructively selecting backend requires internal retention/reselection integration to meet this contract. Cancellation does not undo retained native custody or establish canonical deletion.

Canonical lifecycle is a later, independent path: **durable Executor outcomes → internal pool maintenance → selected backend refresh/reconciliation**. It includes applicable certified imports and uses actual transaction outcomes/next canonical nonces. Body publication, accepted-header observation and native ordering alone cannot substitute for those results. A backend's lossy notification is not processed completion and adds no native cut/direction gate. [Backend completion contract](../tx/interfaces.md#connect-the-trait-to-one-existing-backend).

## Body lookup, verification, and missing-content handling

```mermaid
sequenceDiagram
    participant N as Native engine
    participant A as BlockService: Automaton adapter
    participant S as Commonware Archive / buffer / resolver
    participant P as Peer resolver / archive-backed Producer
    participant I as Baton: block intake
    participant B as Baton: scheduling
    N->>A: Automaton::verify(Context from native header, payload)
    A->>S: Lookup body and required parent
    alt Required body / parent missing
        S->>P: Generic resolver fetch by exact key
        P-->>S: Response bytes
        S->>S: Validate expected digest and context
        opt Correct response for exact expected reference
            S-->>A: Expected body / parent bytes
        end
        Note over A,S: Missing / bad peer response keeps request pending
    else Already stored
        S-->>A: Stored bytes
    end
    alt Required bytes remain unresolved
        A->>A: Keep receiver pending, resolver retries / buffer subscription waits
        Note over N,A: No true / false result returned for this request yet
    else Expected bytes are available
        alt Expected payload is structurally invalid
            A-->>N: verify(false)
        else Structurally valid expected payload
            A->>S: Store / sync custody
            alt Covering durable custody succeeds
                S-->>A: Durable body reference
                A-->>N: verify(true)
                A-->>I: StoredBody(durable body, producer context)
                alt Matching authenticated header observation is available
                    I->>I: Match exact body / header identity and source provenance
                    I-->>B: CandidateBlock(block_ref, body, context)
                else Header observation or matching context remains unresolved
                    Note over I,B: Candidate join stays pending, native verify completion above is independent
                end
            else Local storage / sync failure
                Note over N,S: No custody success, distinct from peer invalidity
            end
        end
    end
```

[Open full-size diagram](../assets/diagrams/diagram-05.svg)

A peer sending bytes with the wrong digest differs from permanent invalidity of the expected payload itself. Temporary unavailability or a delayed fetch cannot become an invalidity or empty-slot verdict. Native DA verification must not wait for completed speculative execution. StoredBody is an application validity/custody event. Baton intake obtains authenticated headers from Reporter accepted-artifact notices and joins a body and producer context to the exact matching header to form CandidateBlock. Reporter notices may arrive before or after StoredBody. Neither body availability nor candidate formation proves ordering inclusion or finality.
