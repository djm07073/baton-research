# Receiving direction and executing branches

**Non-leader Baton submits the new path; Executor links and executes its branches.** Baton verifies the leader and context, resolves required inputs, and sends parent-linked blocks through execute(block). Only a completed prefix with the same execution context is reusable.

<a id="non-leader-lifecycle-direction-and-rescheduling"></a>

## Non-leader lifecycle: direction and branch execution

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
            B->>B: Assemble block hash / execution-parent hash / exact context
            B->>E: execute(block)
            E->>E: Resolve valid parent checkpoint / link child in execution tree
            E->>E: Reuse matching completed child or compute its transaction effects inside Executor
            E-->>B: ExecutionResult (completed prefix of new request)
        end
    end
    Note over L,B: No round waiting for execution results or direction approval
```

[Open full-size diagram](../assets/diagrams/diagram-07.svg)

A direction change does not require reexecuting every block. Executor reuses only a checkpoint for an exact prefix already completed in the same order from the same input state and runtime. Advisory requests cannot roll back canonically applied state.
