# Startup, restart, and history recovery

**Recovery reconnects stored bodies, authenticated history, and durable application state.** Startup prepares custody and native readiness. Restart restores state and cursors and redelivers exact ranges whose acknowledgements were lost.

## Startup: prepare custody before native recovery

```mermaid
sequenceDiagram
    participant S as Node startup
    participant W as Commonware network
    participant A as BlockService: Automaton adapter
    participant N as Native Engine
    participant E as Executor
    participant B as Orderer / Executor integration
    S->>W: Register native and application logical channels
    S->>A: Open body storage / parent lookup, start service
    S->>W: Start authenticated network service
    par Native startup / context intake
        S->>N: Engine::start(native planes)
        N->>N: Replay native durable journal / signing history
        loop Required recovered payload contexts
            N->>A: Automaton::verify(recovered Context, payload)
            A->>A: Lookup / fetch exact body and required parent, sync custody
            A-->>N: Valid durable custody
        end
        N->>N: Construct actors and resume native obligations
        N-->>S: Running handle, readiness initially pending
        S->>N: Await Running::ready()
        N-->>S: Native readiness true or false
        opt Context / evidence intake service ready
            S->>B: Start authenticated intake / retention / history backfill
        end
    and Execution recovery
        S->>E: Recover execution base through Storage, with applied metadata/provenance
        E-->>S: Execution state readiness / recovery status
    end
    alt Execution state and exact input ready
        S->>B: Resume state-dependent Execute / Commit delivery
    else Input state unresolved or required execution service failed
        Note over S,B: Execution delivery pending / recovering, evidence retention proceeds separately
    end
    Note over N,E: Native startup adds no application QMDB recovery prerequisite
    Note over S,B: Resume from recovered canonical state and authenticated history, rebuild transient direction
```

[Open full-size diagram](../assets/diagrams/diagram-13.svg)

This sequence assumes recovered-payload verification succeeds. A false verification result or closed receiver makes `Engine::start` fail with `OpenError::RecoveredPayloadUnverified`. That differs from `ready=false` after a Running handle exists. [Pre-running custody fence](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L272).

`Engine::start` returns a Running handle with readiness initially pending. `Running::ready().await` returns true after native startup/recovery durability work and initial producer-wake submission; engine failure before readiness returns false. [Running readiness](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L549).

A Running handle does not prove every service is ready. Body-service, native-engine, ordered-delivery, and execution-state readiness are separate. Native startup cannot be reported successful before required recovered-payload verification resolves true. Startup dependencies do not add a report or direction approval round.

## Restart and backfill

```mermaid
sequenceDiagram
    participant S as Startup owner
    participant Q as Storage / QMDB / commit metadata
    participant M as Orderer
    participant E as Executor
    S->>Q: Recover last durable applied commit
    Q-->>S: State / outputs / AppliedCursor / provenance
    Note over S,M: Body custody follows the separate startup sequence
    S->>M: Recover archive and delivery cursors
    M->>M: Fetch missing authenticated history / bodies
    S->>E: Open recovered canonical checkpoint
    Note over E: Reconstruct speculative branches from durable canonical state
    M-->>E: Redeliver unacknowledged exact range
    E->>E: Idempotent commit(range)
    E-->>M: Existing matching durable CommitResult / delivery ACK
```

[Open full-size diagram](../assets/diagrams/diagram-10.svg)

| Progress coordinate | Owner and advancement condition | Relationship to the next stage |
|---|---|---|
| Native journal cursor | Native owner receives a durable domain-event prefix acknowledgement | Does not establish application evidence retention or state application |
| Proposed ArchiveCursor | Orderer recoverably stores exact source witnesses and interpretation | Evidence, policy, and history for emitted ranges must remain recoverable |
| Proposed OrderedCursor | Orderer appends exact continuous input from terminal slots | Range identity, predecessor, and interpretation bind to applied commit |
| Proposed AppliedCursor | Storage proves durable state/output/cursor/provenance linkage; Executor delivers its receipt | Lost acknowledgement for the same range can be recovered idempotently |

These coordinates cannot be compared by numeric magnitude. Witness coverage and exact identity connect archive, ordered input, and applied commit. Delivery acknowledgement alone does not justify deleting source material or guarantee permanent serving availability. Retention handoff, export lag, and bounded-buffering policy remain open. No separate archive quorum is added to native cut waits.

Recovered state, outputs, and cursor follow the chosen application recovery-adapter contract; QMDB alone does not guarantee automatic atomicity across them. The sequence handles lost acknowledgements and unacknowledged ranges using recovered execution state and history. Native custody and readiness follow the [separate startup sequence](recovery.md#startup-prepare-custody-before-native-recovery). Idempotence verifies exact commit identity and recoverable outputs/cursor, not merely equality of state roots.
