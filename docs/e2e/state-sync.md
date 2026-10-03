# State sync from certified execution results

**A validator can import a verified peer result while still executing.** Its Executor checks the certificate and applicable state material, fences unfinished work, and applies the result at the correct canonical base.

## State sync from certified execution results

This sequence illustrates state sync as an option on the **normal validator path**. The receiving Executor verifies and applies certified results and material from a peer Executor. No Baton-to-Baton exchange or separate catch-up coordinator is added. It shares the single writer, access fencing, and durability contract of [canonical application](../execution/qmdb.md#commit-a-branch-to-canonical-state). Responsibility and path are adopted, while wire format, switching, storage, and validation remain unimplemented.

```mermaid
sequenceDiagram
    participant P as Peer Validator Executor
    participant E as Local Validator Executor
    participant Q as QMDB / Logical commit adapter
    participant B as Local Baton
    E->>E: Continue direct execution while result is unavailable
    P-->>E: Result certificate
    E->>E: Verify eligible f+1 signatures and irrevocable exact context
    alt Ordering / predecessor evidence unresolved
        E->>E: Keep certificate pending, recover evidence / continue valid local work
    else Result certificate verified
        E->>P: Request matching change set / outputs
        P-->>E: State material
        E->>E: Check exact local base and target / output commitments
        alt Material missing, invalid or not applicable
            E->>E: Keep executing / request valid material, no canonical adoption
        else Applicable target and material verified
            E->>E: Fence unfinished work at a safe boundary
            E->>Q: Apply material at matching canonical base
            Q-->>E: Applied state + durability observation
            E->>Q: Await durable state / outputs / cursor linkage
            alt Durable import completes
                Q-->>E: Recoverable target checkpoint
                E->>E: Preserve imported provenance and original certificate
                E->>E: Complete delivery ACK / tx outcome handoff
                opt Local scheduling notification
                    E-->>B: Applied progress only, no approval / ACK required
                end
                E->>E: Execute next range from synced canonical state
            else Durable completion unconfirmed or failed
                Note over E,B: No local ready / CommitResult, recheck during recovery
            end
        end
    end
    Note over P,E: No own direct-execution signature for imported range
```

[Open full-size diagram](../assets/diagrams/diagram-14.svg)

Relaying the original certificate, establishing state finalization, and achieving durable local readiness are different events. A certificate alone does not stop remaining execution; verified applicable material must also be available. Do not append a canonical-base delta to partially executed state. Material format, checkpoint switching, root verification, and import commit remain undecided. The next range can use the existing execution interface for direct execution from the correct canonical base.
