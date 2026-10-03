# 확정 순서와 canonical 상태 적용

Orderer가 Executor에 직접 확정 입력을 전달한다. Executor는 맞는 실행 결과를 준비하고 QMDB 적용·durable 저장·delivery ACK를 완료한다.

## Cut commit → ordered range → 실행 commit

```mermaid
sequenceDiagram
    participant N as Native Multimmit
    participant M as Orderer
    participant E as Executor
    N-->>M: Authenticated finality / extension evidence
    M->>M: Recover exact history / frozen policy / slot evidence
    alt 앞선 slot 또는 이력이 unresolved
        M->>M: Backfill and stop dense emission at the gap
        Note over N,M: Native protocol은 자체 규칙에 따라 계속 진행
    else 다음 연속 exact range가 irrevocable
        M-->>E: OrderedRange(predecessor, inputs, evidence)
        E->>E: commit(range, expected canonical predecessor)
        alt Matching completed speculative branch prefix 존재
            E->>E: Select exact committed prefix, keep compatible suffix pending
        else 적용 가능한 peer certificate + state material 검증 완료
            E->>E: Fence unfinished work and apply material at matching base
        else local work / peer material이 준비되지 않음
            E->>E: Execute from canonical base / repair suffix, peer sync 병행
        end
        E->>E: Validate results, apply QMDB changes, durable commit
        E-->>M: CommitResult / delivery ACK after durability
    end
```

[그림 크게 보기](../assets/diagrams/diagram-08.svg)

첫 native leader-finality 알림을 곧바로 모든 body의 확정 순서로 해석하지 않는다. Native extensions와 history를 포함해 **실행할 exact range**를 먼저 확인한다. Included slot은 emit, 인증된 irrevocably-empty slot은 skip, unresolved slot은 stop이다. 본문 누락은 empty가 아니다. 순서가 irrevocable이어도 필요한 body / predecessor state가 없으면 해당 execution commit은 fetch·recovery를 기다린다. 이 local input 대기는 native cut을 direction 회신으로 막는 새로운 round와 다르다.

## Execution lifecycle: QMDB 분기 생성과 canonical 승격

```mermaid
sequenceDiagram
    participant B as Baton
    participant M as Orderer
    participant O as Executor
    participant Q as QMDB batches
    participant A as Runtime
    B->>O: execute(base checkpoint, exact order, runtime, generation)
    O->>O: Locate valid base / retain reusable prefix
    O->>Q: Fork parent batch / create branch
    Q-->>O: Mutable batch
    loop Ordered input blocks
        O->>A: Runtime executes body against branch state
        A-->>O: State writes + outputs
        O->>Q: Apply pending writes to branch
    end
    O->>Q: Merkleize at requested checkpoint boundary, granularity undecided
    O-->>B: ExecutionResult(branch handle, context, results)
    M-->>O: OrderedRange(irrevocable range, canonical predecessor)
    O->>O: commit(range)
    O->>O: Verify branch exactly matches committed input
    O->>O: Fence incompatible / unknown active branch workers
    O->>Q: DatabaseSet::finalize(matching batches)
    Q-->>O: Applied / readable state + Barrier
    O->>Q: Barrier::durable()
    alt Durable barrier succeeds and metadata linkage completes
        Q-->>O: Durable flush completion
        O->>O: Complete recoverable state + outputs + cursor linkage
        O-->>M: CommitResult / durable delivery ACK
        opt Local scheduling notification
            O-->>B: Applied progress, no finalization approval
        end
        opt Safe retention boundary permits cleanup
            O->>O: Prune incompatible forks / retain compatible suffixes
        end
    else Shutdown, flush failure, or incomplete metadata linkage
        Q-->>O: No successful durable completion
        Note over M,O: CommitResult / delivery ACK를 발행하지 않고 recovery 경계에서 처리
    end
```

[그림 크게 보기](../assets/diagrams/diagram-09.svg)

이 그림은 completed branch가 exact canonical range와 일치하는 경로다. Work가 없거나 다르면 [cut commit 흐름](canonical.md#cut-commit--ordered-range--실행-commit)의 canonical 실행/repair를 따른다. Branch 생성·pruning은 제안하는 owner 동작이고 cleanup은 optional이며 구체 GC scheduling은 미결정이다. `DatabaseSet::finalize`와 `Barrier::durable`은 upstream API지만 applied/readable 상태는 durable 완료가 아니다. State/output/cursor linkage와 실패 처리·ACK 경계는 [canonical apply](../execution/qmdb.md#commit-요청을-받으면-branch를-canonical로-만들기)에서 설명한다. [Durability barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L469).
