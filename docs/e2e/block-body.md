# Block body 송수신

Producer가 tx 본문을 만들어 전파하고, 수신 노드가 누락된 본문을 조회·검증·보관하는 과정을 설명한다.

## Block lifecycle: mempool → propose → body 전파

```mermaid
sequenceDiagram
    participant N as Native producer owner
    participant A as BlockService: Automaton 연결
    participant P as BlockService: body build
    participant S as BlockService: storage / fetch
    participant R as BlockService: Relay 연결
    participant V as Peer BlockService
    N->>A: Automaton::propose(Context)
    A->>P: Select / build bounded body
    P-->>A: Body bytes + commitment
    A->>S: Put body and required parent custody
    S-->>A: Durable after sync
    A-->>N: Payload digest
    N->>N: Native header construction / signing
    N->>R: Relay::broadcast(payload digest)
    R->>S: Resolve body bytes
    S-->>R: Body
    R-->>V: Publish body
    Note over N,V: Native headers / DA messages는 별도 native data plane
```

[그림 크게 보기](../assets/diagrams/diagram-04.svg)

Native core가 producer header의 signing authority를 소유한다. Builder는 body를 만들고 digest를 돌려준다. Application이 native header signer를 대신 호출하지 않는다.

## Block body 송수신: 조회·검증·누락 처리

```mermaid
sequenceDiagram
    participant N as Native engine
    participant A as BlockService: Automaton 연결
    participant S as BlockService: storage / fetch
    participant P as Body peer
    participant I as Baton: block 수신
    participant B as Baton: scheduling
    N->>A: Automaton::verify(Context from native header, payload)
    A->>S: Lookup body and required parent
    alt 필요한 body / parent가 없음
        S->>P: Fetch by exact reference
        P-->>S: Response bytes
        S->>S: Validate expected digest and context
        opt Correct response for exact expected reference
            S-->>A: Expected body / parent bytes
        end
        Note over A,S: Missing / bad peer response는 요청의 pending 상태
    else 이미 보관됨
        S-->>A: Stored bytes
    end
    alt Required bytes remain unresolved
        A->>A: Keep pending request, retry / await correct bytes
        Note over N,A: 이 요청의 true / false 결과를 아직 반환하지 않음
    else Expected bytes are available
        alt 구조적으로 무효인 expected payload
            A-->>N: verify(false)
        else Structurally valid expected payload
            A->>S: Store / sync custody
            alt Covering durable custody succeeds
                S-->>A: Durable body reference
                A-->>N: verify(true)
                A-->>I: StoredBody(durable body, producer context)
                alt Matching authenticated header observation is available
                    I->>I: Match exact body / header identity and source provenance
                    I-->>B: CandidateBlock(block_ref, body, context)
                else Header observation or matching context remains unresolved
                    Note over I,B: Candidate join stays pending, native verify completion above is independent
                end
            else Local storage / sync failure
                Note over N,S: Custody success를 보고하지 않음, peer-invalidity와 구분
            end
        end
    end
```

[그림 크게 보기](../assets/diagrams/diagram-05.svg)

Bad peer가 다른 digest의 bytes를 보내는 것과 expected payload 자체의 permanent invalidity는 구분한다. 임시 미가용·본문 fetch 지연을 invalid 판정이나 empty slot 판정으로 바꾸지 않는다. Native DA 검증은 speculative execution 완료를 기다리는 계약으로 만들지 않는다. `StoredBody`는 application validity / custody 사건이다. Baton의 block 수신 부분은 Reporter의 accepted-artifact 알림에서 인증된 header를 찾는다. 보관한 body와 producer context가 이 header에 정확히 대응하면 `CandidateBlock` 후보를 만든다. 이 그림은 body 준비 흐름만 보여주며, Reporter 알림은 StoredBody보다 먼저 또는 나중에 올 수 있다. 둘 다 ordering inclusion / finality 증거는 아니다.
