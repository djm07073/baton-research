# Leader reports, direction, and proposal races

**Baton is one scheduler mode inside the App.** It gathers signed intended orders and prepares advisory direction while native consensus proceeds. Its report handling, bounded planning and worker dispatch are internal App operations; no public Baton or Executor trait is required.

## Leader lifecycle: collect reports and disseminate direction

The report protocol below remains application work. Native leader-window context and authenticated proposal-policy adoption additionally require the [unfinished native extension](../consensus/decisions.md). Producer `Automaton::propose` and `verify` are not leader-cut callbacks.

```mermaid
sequenceDiagram
    participant N as Native leader context / proposed policy integration
    participant L as Leader App / Baton scheduler
    participant V as Validator App / Baton scheduler
    participant P as App bounded planning task
    par Report collection and planning
        N-->>L: Exact leader window context through proposed integration
        L-->>V: Authenticated window announcement
        loop Valid reports before snapshot closure
            V->>V: Preserve started prefix F and sort eligible pending
            V-->>L: Signed intended order for exact context
            L->>L: Validate and admit each identity at most once
        end
        L->>L: Close once at first 4f+1 admissions or fixed deadline
        alt No reports admitted
            L->>L: No prepared candidate from empty snapshot
        else Nonempty report snapshot
            L->>P: Frozen original reports and bounded admissible candidate set
            P-->>L: Completed evaluation or unfinished result
            opt Valid evaluated direction prepared
                L-->>V: Authenticated advisory direction
                V->>V: Validate and update permitted scheduling decisions
            end
        end
        Note over L,V: No direction vote / ACK / Ready quorum
    and Native cut
        N->>N: Continue native proposal processing
        Note over N,L: Never wait for report count, deadline or planning
    end
```

[Open full-size diagram](../assets/diagrams/diagram-06.svg)

A report is the fixed completed/current local prefix `F` followed by `sort_G(S_pending)`. It is an intention, not an execution proof. Equal context, `F`, rule and pending set produce equal intended order; equal total known inputs alone do not. Later arrivals do not change an already signed report or a closed snapshot.

The leader counts at most `4f+1` distinct valid original reports. It closes on the first threshold/deadline event processed, without extending the deadline. With a nonempty snapshot and fully evaluated bounded admissible candidate set, select the longest nonempty entire prefix with at least `2f+1` original same-context supporters; if no such prefix exists, use raw sum-LCP. Before protected adoption, no reports or no prepared valid choice means the actual-parent valid native base path. Incomplete search does not establish a longest-prefix result.

<a id="planner-completion-versus-proposal-freeze"></a>

## Planning completion versus proposal freeze

This is the **required future integration flow**, not an API present in current Multimmit:

```mermaid
sequenceDiagram
    participant A as App Baton scheduler
    participant P as App planning task
    participant N as Native leader proposal owner
    participant V as Native validators
    A->>P: Frozen nonempty report snapshot and exact context
    alt Complete candidate is ready before proposal freeze
        P-->>A: Prepared policy candidate
        A-->>N: Candidate through future proposal-policy integration
        N->>N: Recheck actual parent, history, frontier and admissibility
        alt Valid and adoptable in actual proposal context
            N->>N: Freeze selected prefix and interpretation in signed subject
        else Recheck fails before adoption
            N->>N: Use valid actual-parent native base
        end
    else No valid prepared candidate
        N->>N: Use valid actual-parent native base without waiting
    end
    N-->>V: Authenticated proposal with fixed interpretation
    V->>V: Validate exact leading-prefix preservation
    V-->>N: Native votes
    opt Late report, completion or larger native pool
        P-->>A: Future scheduling information
        N->>N: Preserve this already authenticated proposal interpretation
    end
```

[Open full-size diagram](../assets/diagrams/diagram-12.svg)

Current `LeaderBlock` has no Baton policy field, and current Marshal uses the native order interpretation. Adding scheduling in `Automaton::verify` does not implement policy adoption, validator policy checks, exact leading-prefix preservation, continuation or recovery. The App cannot implement this by reordering finalized Updates after delivery.

Before adoption, no reports or no prepared candidate permits the valid native base path. After authenticated adoption, the protected prefix cannot silently disappear or be reinterpreted as fallback. Context binding, availability/adoption, native sufficiency, cross-lane continuation and view recovery remain open proof and implementation obligations. The local report window closing is distinct from that still-unspecified protected-adoption point.
