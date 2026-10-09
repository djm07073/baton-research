# State sync from certified execution results

**An App may import verified peer material during normal execution.** It verifies the result certificate and exact input context, checks applicable material, then fences conflicting work and applies through the same canonical writer used for direct execution.

## State sync from certified execution results

State sync belongs to App execution/storage code. Peer result messages do not pass through either scheduler mode for approval. The path shares the single writer, access fencing and durability contract of [canonical application](canonical.md).

```mermaid
sequenceDiagram
    participant P as Peer Validator App
    participant A as Local App
    participant S as App storage / QMDB
    participant M as Multimmit Marshal
    A->>A: Continue valid local execution while result is unavailable
    P-->>A: Result certificate
    A->>A: Verify f+1 eligible signatures and exact input / predecessor
    alt Irrevocable input or predecessor unresolved
        A->>A: Retain pending certificate and continue valid local work
    else Certificate valid in exact context
        A->>P: Request matching material and outputs
        P-->>A: State material
        A->>S: Validate material against authorized base and target
        S-->>A: Applicable material or failure
        alt Material unavailable or invalid
            A->>A: Keep executing / recover valid material
        else Material applicable
            A->>A: Fence conflicting unfinished work
            A->>S: Apply through canonical writer and persist linked metadata
            alt Durable import completes
                S-->>A: Durable applied identity / outputs / provenance
                A->>A: Keep imported provenance and original certificate
                A->>A: Advance canonical base and schedule pool maintenance
                opt Pending Updates covered by this exact durable prefix
                    A-->>M: Acknowledge retained matching Updates
                end
                A->>A: Resume work from imported canonical state
            else Durable completion fails
                A->>A: No ACK, recover authoritative state before reuse
            end
        end
    end
    Note over P,A: No own direct-execution signature for imported input
```

[Open full-size diagram](../assets/diagrams/diagram-14.svg)

A certificate alone does not justify stopping unfinished execution; applicable material must also be verified. Do not apply a canonical-base delta to arbitrary partial speculative state. A verified import can satisfy an outstanding Update only when its exact input and durable applied identity cover that Update in order. Do not synthesize ACK tokens or skip unrelated outstanding delivery.

For checkpoint catch-up, coordinate Marshal's authenticated floor and output identity with App state installation. `install_floor` restores Marshal's input prefix, not the application database. Serialize this App-owned transition with canonical intake and fence old workers; reconcile already retained Updates against the exact durable imported prefix before resuming. A Marshal floor reset may open a new delivery window while App still holds old Updates, so either prevent that overlap through the transition lifecycle or bound it explicitly. `Update` has no generation tag; local import ownership and exact identity checks must supply the fence. Wire/material formats, checkpoint switching, result verification and atomic recovery linkage remain implementation work. [State-sync responsibilities](../execution/state-sync.md)
