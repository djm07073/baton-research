# Receiving direction and reexecuting

**Non-leader Baton requests a new schedule; Executor reuses valid completed work.** Baton verifies the leader and context, resolves required inputs, and sends a reschedule request. Only a completed prefix with the same execution context is reusable.

## Non-leader lifecycle: direction and rescheduling

```mermaid
sequenceDiagram
    participant L as Leader Baton
    participant B as Non-leader Baton
    participant S as BlockService: storage / fetch
    participant E as Executor
    L-->>B: Direction(context, order, prefix)
    B->>B: Check leader / epoch / view / parent / frontier / wire freshness
    alt Stale or different context
        B->>B: Discard advisory update
    else Valid for current context
        B->>S: Resolve required bodies
        alt Body or base state unavailable
            B->>B: Keep local work pending, native cut path continues
        else Execution input ready
            B->>B: Assign current local job generation
            B->>E: reschedule(exact base, new order, generation)
            E->>E: Find reusable exact prefix / supersede stale suffix work
            E->>E: Fork retained checkpoint / execute new suffix
            E-->>B: ExecutionResult (completed prefix of new request)
        end
    end
    Note over L,B: No round waiting for execution results or direction approval
```

[Open full-size diagram](../assets/diagrams/diagram-07.svg)

A direction change does not require reexecuting every block. Executor reuses only a checkpoint for an exact prefix already completed in the same order from the same input state and runtime. Advisory requests cannot roll back canonically applied state.
