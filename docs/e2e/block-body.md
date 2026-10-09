# Block body send, fetch, and receive

**Use the existing Multimmit Marshal for complete-block custody and exchange.** The App defines the transaction body codec, digest and validity checks. Native Multimmit handles signed producer headers, DA and ordering; the body travels through Marshal's buffered broadcast and backfill services.

## Block lifecycle: mempool → propose → body dissemination

```mermaid
sequenceDiagram
    participant N as Native producer
    participant A as App Automaton
    participant P as App TxPool
    participant M as Multimmit Marshal
    participant B as Buffered broadcast
    participant R as Peer node
    N->>A: propose(producer Context)
    A->>P: Select retained transactions within limits
    P-->>A: Candidate batch
    A->>A: Build complete block from body and Context
    A->>M: stage_block(complete block)
    M-->>A: Custody token for accepted storage work
    A-->>N: Proposal receiver resolves to body digest
    N->>A: verify(Context, body digest), local custody check
    A->>M: subscribe_block(exact BlockRef) or await retained custody
    M-->>A: Durable custody established
    A->>A: Check expected header/body and payload validity
    A-->>N: Verification receiver resolves true
    N->>N: Sign producer header
    N->>M: Relay::broadcast(header digest, ())
    M->>B: Broadcast staged complete block
    B-->>R: Header and body together
    N-->>R: Signed header through separate native data plane
    Note over N,R: Separate channels may deliver in either order
```

[Open full-size diagram](../assets/diagrams/diagram-04.svg)

`stage_block().await` returns a `Custody` token after admission of storage work. Awaiting `Custody::wait()` establishes durable recovery; `put_block()` combines staging and that wait. Dropping the token does not cancel accepted storage work. The local native custody verify provides the required gate before header signing. An App may wait earlier in propose, but need not add a second durability path. [Marshal mailbox](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/mailbox.rs#L327)

The body digest commits to the payload. The header digest identifies the native producer block, including its producer Context and body digest. `propose` returns the body digest; native `Relay::broadcast` requests propagation using the header digest. The existing Marshal Relay resolves that digest to the staged complete block. Its local Feedback does not prove remote receipt or custody, and even `Ok` can mean no matching staged block was found. [Relay completion](../overview/networking.md)

## Body lookup, verification, and missing-content handling

```mermaid
sequenceDiagram
    participant N as Native engine
    participant A as App Automaton
    participant M as Multimmit Marshal
    participant Q as App scheduler
    N->>A: verify(Context, body digest)
    A->>A: Derive exact header and BlockRef
    A->>M: subscribe_block(BlockRef)
    Note over A,M: Waits for durable local / buffered custody, no explicit peer fetch
    opt Concurrent active retrieval if required
        A->>M: fetch_block(BlockRef)
        M->>M: Existing resolver / peer backfill
    end
    alt Required exact block still unavailable
        Note over N,A: Keep verdict pending while the condition may change
    else Expected block available
        M-->>A: subscribe_block resolves with durable complete block
        A->>A: Check context, digest and application payload validity
        alt Expected payload permanently invalid
            A-->>N: Verification receiver resolves false
        else Valid payload with durable custody
            A->>A: Deduplicate and retain validated candidate facts
            A-->>N: Verification receiver resolves true
            opt Live candidate has required authentication / ancestry
                A->>Q: Internal eligible pending admission
                Q->>Q: Sort pending, dispatch only with exact parent ready
            end
        end
    end
    Note over A,Q: Speculative execution completion does not gate verify
```

[Open full-size diagram](../assets/diagrams/diagram-05.svg)

`subscribe_block` waits for local storage or buffered ingress to establish custody. It does not initiate peer fetch; DA evidence may independently cause Marshal backfill. `fetch_block` is the explicit network retrieval API and can return buffered bytes before storage sync; a fetch response alone does not establish custody. A wrong peer response is not proof that the expected payload itself is permanently invalid. Local storage failure is also distinct from invalid peer content.

The diagram shows one eligible live validation request. `verify` also runs locally before signing and during recovery; qualify role/lane, lifecycle and exact identity before treating success as a new peer candidate. Nonproducing validators have no own-lane exclusion, while Observers normally enter through Update. [Role and origin rules](../baton/README.md#when-speculative-execution-begins).

Admission uses the App owner's current state after custody completes. Required producer ancestry and authentication still apply, and the scheduler waits for the exact execution checkpoint before dispatch. Already-applied or retired speculative work can still require an honest native custody response. Follow the [candidate/dispatch handler](../baton/interfaces.md#automatonverify-validity-custody-and-scheduling) for deferred-capacity, duplicate and stale-request handling.

Transactions retire through durable canonical outcomes, not body publication, `verify(true)`, or selection. See [TxPool](../tx/interfaces.md) for internal backend reconciliation and [canonical delivery](canonical.md) for the later Update path.
