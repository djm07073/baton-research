# Leader reports, direction, and proposal races

**Leader Baton prepares an execution suggestion while native consensus keeps moving.** It closes a report window, asks Executor to choose a valid direction, and disseminates the result. Native Core may freeze a proposal before Baton planning finishes.

## Leader lifecycle: collect reports and disseminate direction

```mermaid
sequenceDiagram
    participant N as Native owner / proposed planning bridge
    participant L as Leader Baton
    participant V as Validator Baton
    participant P as Baton: planning task
    participant X as Producer / Executor Baton peers
    par Report window / Baton planning
        N-->>L: Read-only leader planning context
        L-->>V: Authenticated window context
        loop Valid reports arriving before closure, possibly none
            V->>V: Build intended order from known inputs
            V-->>L: Signed IntendedOrderReport
            L->>L: Same-context validation / distinct identity admission
        end
        L->>L: Close once at first 4f+1 OR fixed deadline
        L->>P: Frozen snapshot + bounded admissible candidates
        P-->>L: Evaluated selection or incomplete
        opt Valid direction prepared
            L-->>X: Direction(context, order, selected prefix)
            X->>X: Submit parent-linked blocks to local Executor
        end
        Note over L,X: No direction vote / ACK / Ready quorum
        L->>L: Local cycle closes, fresh work / context starts next cycle
    and Native cut path
        N->>N: Prepared matching policy or valid NativeBase
        Note over N,L: Cut does not wait for report count / deadline / Baton planning completion
        N->>N: Freeze authenticated proposal policy, native votes
    end
```

[Open full-size diagram](../assets/diagrams/diagram-06.svg)

Window announcement and binding prepared policy to an actual proposal require integration adapters. The diagram does not imply those APIs already exist or prefix adoption has been proved. Closing a local cycle does not wait for all nodes' execution or the native cut branch to finish.

<a id="planner-completion-versus-proposal-freeze"></a>

## Planning completion versus proposal freeze

```mermaid
sequenceDiagram
    participant L as Leader Baton
    participant P as Baton: planning task
    participant N as Native leader proposal owner
    participant V as Native validators
    L->>P: Frozen reports / exact planning context
    alt Evaluated candidate reaches owner before proposal freeze
        P-->>L: PreparedPolicy(context, validity material)
        L-->>N: Cached prepared policy for actual-context recheck
        N->>N: Recheck actual parent / history / frontier / request correlation
        alt Recheck admits candidate for this actual proposal
            N->>N: Freeze selected prefix and policy before signing
        else Context or admissibility recheck fails
            N->>N: Use actual-parent valid NativeBase before adoption
        end
    else Candidate is stale, unavailable, or unfinished
        N->>N: Use actual-parent valid NativeBase before adoption
    end
    N-->>V: Authenticated native proposal with fixed interpretation
    V-->>N: Native proposal votes
    opt Late planning result / new report / larger native pool
        P-->>L: Late prepared result
        L-->>N: Current cache, no mutation of frozen proposal
        N->>N: Do not mutate this proposal policy
    end
    Note over L,V: Native votes are not a direction-reply quorum
```

[Open full-size diagram](../assets/diagrams/diagram-12.svg)

Native proposal can use the valid actual-parent base path even when no planning job exists. The diagram describes the completion race when a job has been started.

Availability for adopting a prepared result and exact-prefix preservation remain unresolved. This diagram identifies the required freeze boundary without adopting a particular ready-only policy variant. On view change, old reports and advisory work cannot enter the new context. Already authenticated, emitted, or applied history keeps its original interpretation.
