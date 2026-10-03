# Leader report·direction과 proposal 경합

Report window 종료와 direction 선택·전파를 설명한다. Planner 완료와 native proposal freeze가 경합해도 cut은 기다리지 않는다.

## Baton lifecycle: leader report 수집과 direction 전파

```mermaid
sequenceDiagram
    participant N as Native owner / proposed planning bridge
    participant L as Leader Baton
    participant V as Validator Baton
    participant P as Planner
    participant X as Producer / Executor Baton peers
    par Report window / planner
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
        opt 유효한 direction이 준비됨
            L-->>X: Direction(context, order, selected prefix)
            X->>X: Local speculative reschedule
        end
        Note over L,X: Direction vote / ACK / Ready quorum 없음
        L->>L: Local cycle closes, fresh work / context starts next cycle
    and Native cut path
        N->>N: Prepared matching policy or valid NativeBase
        Note over N,L: Cut은 report 수 / deadline / planner 완료를 기다리지 않음
        N->>N: Freeze authenticated proposal policy, native votes
    end
```

[그림 크게 보기](../assets/diagrams/diagram-06.svg)

Window 안내와 prepared policy를 실제 proposal에 결속하는 hook은 구현할 adapter다. 그림이 그 API가 이미 존재하거나 prefix-adoption 증명이 완료되었음을 뜻하지 않는다. Local cycle 종료는 모든 노드의 실행 완료나 native cut branch 종료를 기다리는 barrier가 아니다.

## Planner completion과 proposal freeze의 경합

```mermaid
sequenceDiagram
    participant L as Leader Baton
    participant P as Planner
    participant N as Native leader proposal owner
    participant V as Native validators
    L->>P: Frozen reports / exact planning context
    alt Evaluated candidate reaches owner before proposal freeze
        P-->>N: PreparedPolicy(context, validity material)
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
    opt Late planner result / new report / larger native pool
        P-->>N: Late prepared result
        N->>N: Do not mutate this proposal policy
    end
    Note over L,V: Native votes는 direction 회신 quorum이 아님
```

[그림 크게 보기](../assets/diagrams/diagram-12.svg)

Planner job 자체가 없는 경우에도 native proposal은 유효한 actual-parent base 경로로 진행한다. 이 그림은 job이 시작된 경우의 completion 경합을 설명한다.

Prepared result를 채택할 availability와 exact-prefix 보존 조건은 아직 닫히지 않았다. 이 그림은 구현할 freeze 경계를 설명하며 특정 ready-only policy variant를 채택하지 않는다. View가 바뀌면 old reports·advisory work는 새 context에 넣지 않고, 이미 인증·방출·적용된 history는 원래 해석을 보존한다.
