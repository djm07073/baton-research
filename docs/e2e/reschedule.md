# Direction 수신과 재실행

Non-leader가 direction을 검증하고 Executor에 새 실행 요청을 보낸다. 완료한 같은-context prefix만 재사용한다.

## Baton lifecycle: non-leader의 direction·재실행 요청

```mermaid
sequenceDiagram
    participant L as Leader Baton
    participant B as Non-leader Baton
    participant S as BlockService: storage / fetch
    participant E as Executor
    L-->>B: Direction(context, order, prefix)
    B->>B: Check leader / epoch / view / parent / frontier / wire freshness
    alt 오래되었거나 다른 context
        B->>B: Discard advisory update
    else 현재 context에 유효
        B->>S: Resolve required bodies
        alt 본문 또는 base state가 아직 없음
            B->>B: Keep local work pending, native cut path continues
        else 실행 입력 준비됨
            B->>B: Assign current local job generation
            B->>E: reschedule(exact base, new order, generation)
            E->>E: Find reusable exact prefix / supersede stale suffix work
            E->>E: Fork retained checkpoint / execute new suffix
            E-->>B: ExecutionResult (새 요청의 완료 prefix)
        end
    end
    Note over L,B: 실행 결과나 direction 승인 회신을 기다리는 round 없음
```

[그림 크게 보기](../assets/diagrams/diagram-07.svg)

Direction이 바뀌었다고 모든 block을 재실행하지 않는다. Executor는 같은 입력 state와 runtime에서 같은 순서로 실행을 끝낸 prefix checkpoint만 재사용한다. 이미 canonical에 적용한 state는 advisory 요청으로 되돌리지 않는다.
