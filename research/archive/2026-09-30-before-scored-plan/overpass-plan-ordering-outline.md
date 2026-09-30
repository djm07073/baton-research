# Overpass: Common-Prefix Plans for Pipelined State Finalization

> 2026-09-30 대화 결정 반영. [상세 plan 기록](overpass-prefix-plan.md) / [논리 전개](overpass-research-logic.md) / [직전 문서 보관본](research/archive/2026-09-30-before-prefix-convergence/INDEX.md).
> Hermes는 참고 연구이며 채택한 합의 엔진이 아니다. 아래는 설계·평가 계획이지 구현·증명 완료 기록이 아니다.

## 핵심 결정

**Validators가 같은 기준 cut·canonical parent에서의 예정 ordering을 보고한다. Leader는 3f+1이 지지하는 가장 긴 유효 공통 prefix를 찾고, 새 prefix가 없으면 고정된 조정안을 제안해 노드들이 그 순서를 채택하도록 한다. 실행은 계속하며 support는 실행 완료를 기다리지 않는다.**

n=5f+1, 최대 f Byzantine identities에서 plan support 목표는 q=3f+1이다. 보고 q개를 모은 것과 동일 prefix에 q 지지가 생긴 것은 다르다. 중간 공통 조각·subsequence나 여러 보고의 불일치를 최소화하는 합성 optimizer가 아니다.

Plan support는 cut 전의 예정 순서 채택이며 별도 finality가 아니다. 정상 leader 경로에서는 채택 prefix를 확장하고 cut 후보에 반영하지만, leader 교체를 넘는 영구 lock이나 plan 불일치만을 이유로 유효 cut을 거부하는 규칙은 도입하지 않는다. 최종 exact order는 기존 cut 합의가 인증해야 한다.

실행 이력·진척·완료 보고·execution proof는 plan 입력에서 제외한다. 내부 실행 검증·offline 계측은 유지한다. Producer placement, Multilevel grouping, state-owner sharding, ZK/PAC, receipt bridge와 repair lane은 복원하지 않는다.

## 1. Introduction

### 문제 → pipeline → 후속 비용

Autobahn-family의 parallel dissemination과 cut agreement를 출발점으로 설명한다. 빠른 ordering만으로 application state가 준비되지는 않는다. Cut 이후 실행을 시작하면 실행 비용이 노출되므로 block 수신·sync·consensus와 execution을 겹친다.

늦은 선행 block이나 후보 변경이 speculative work를 무효화하여 pipeline 이득을 상쇄할 수 있다. Leader의 관측만 따라 기존 후보를 고정해도, 그 leader에게만 block이 늦었다면 다른 노드들의 실행을 더 많이 무효화할 수 있다.

### 제안과 기여 후보

여러 validator의 예정 순서를 공유하고, q-supported common prefix를 재사용한다. 자연스러운 공통 prefix가 생기지 않으면 leader가 하나의 유효 조정안을 제안해 순서를 수렴시킨다. 한 번의 조정 비용을 허용하되 이후 반복 insertion을 줄이려 한다.

- Common-prefix discovery: 실행 완료 증명 없이 동일 기준점의 예정 순서 지지를 모은다.
- Leader-guided adjustment: 기존 예정 순서가 달라도 유효 조정안을 채택하고 실행과 지지 수집을 겹친다.
- Pipelined state finalization: 최종 cut에 조율된 순서를 반영하고 exact-context 검증·재실행으로 state를 확정한다.

기여의 최초성·우월성은 미검증이다. “사전 실행 자체가 처음” 또는 “기존 연구가 실행을 전혀 다루지 않았다”고 주장하지 않는다.

## 2. Background and Motivation

### 2.1 Ordering과 실행의 경계

Producer lane과 validator identity를 구분한다. Support는 identity당 계수한다. DA, ordering finality, 실행 결과 인증과 durable readiness는 서로 다른 사건이다. Cut vote는 같은 body·execution view·실행 완료 상태를 보장하지 않는다.

기반 합의의 전체 finality 절차를 유지한다. n=5f+1은 현재 plan 설계 profile이며 구체적인 Autobahn/Commonware adapter 및 cut quorum은 별도로 검증한다. [Autobahn](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

### 2.2 왜 공통 조각이 아니라 prefix인가?

X→A→B와 Y→A→B의 공통 조각 A→B는 앞선 X/Y의 효과가 다를 수 있다. 같은 canonical parent에서 처음부터 A→B인 보고들만 그 prefix 지지로 센다. Prefix 전체와 parent를 맞추어 앞선 입력 차이를 제거하려는 설계다.

Block ancestry와 application이 강제하는 선행 조건을 어기면 안 된다. 필수 선행 X가 없는 A를 먼저 plan에 넣고 나중에 X를 뒤에 붙이는 방식은 허용하지 않는다.

### 2.3 연구 가설

- H1: 필요한 보정을 finality 이전으로 옮겨 post-cut 잔여 시간을 줄인다.
- H2: 공통 prefix로 수렴한 뒤 suffix만 확장하여 반복 late-insertion invalidation을 줄인다.

초기 조정은 재실행을 유발할 수 있고 계획된 순서가 같아도 실행 완료를 뜻하지 않는다. H1/H2와 추가 통신 비용을 따로 측정한다.

Figure 1: post-cut / unguided speculation / discovery+adjustment 시간선. Leader에게만 X가 늦은 반례를 함께 배치한다.

## 3. System Design

### 3.1 역할·입력·병렬 작업

고정 위원회, n=5f+1, deterministic application, 인증 메시지와 eventual synchrony를 전제로 한다.

- Producer: block 생성·전파 지속.
- Validator: sync·입력 검증, 예정 순서 보고, 조정안 채택·support, speculative execution·재검증, cut vote.
- Leader: prefix 발견, 필요 시 고정 조정안 제안, 근거 전파, 실제 cut 후보 구성.

예정 순서 보고는 epoch/view/round, 기준 cut·canonical parent, rule version과 exact ordered block references에 묶인다. 동일 counting context에서는 identity당 하나의 불변 sequence를 계수하고 갱신은 새 context에서 한다. Discovery report와 adjustment support를 구별한다.

실행 완료는 report/support·DA ACK·ordering vote의 선행 조건이 아니다. Body 확보와 실행은 sync와 겹칠 수 있지만 유효한 가용성 근거 없이 계획 서명을 DA 증거로 취급하지 않는다.

### 3.2 경로 A: 3f+1 공통 prefix 발견

보고를 trie로 구성해 처음부터 일치하는 prefix별 distinct signer 수를 센다. q 이상 지지받는 가장 긴 유효 prefix를 근거 보고와 전파한다.

```text
같은 cut·parent, n=6, f=1, q=4

V1: A → B → C → X
V2: A → B → C → Y
V3: A → B → D
V4: A → B → E
V5: X → A → B

발견 prefix: A → B
V5는 해당 prefix를 지지하지 않는다.
```

빈 prefix, 혹은 기존 채택 prefix와 같은 길이의 prefix는 새 진행으로 세지 않는다. q개 보고를 수신해도 새 q-supported prefix가 없을 수 있다. 이 경우 다음 경로로 수렴을 유도한다.

### 3.3 경로 B: Leader-guided adjustment

Leader는 유효 parent·ancestry·현재 유지 중인 prefix와 양립하는 하나의 순서를 제안한다. 미확정 suffix는 기본 ordering rule로 구성한다. 아직 노드들이 같은 순서를 쓰지 않더라도 정상 validator는 유효한 후보를 채택할 수 있다.

```text
기존 예정 순서:  A→B→C / B→A→C / C→A→B
                         ↓
Leader 조정안:       A→B→C
                         ↓
유효성 검사 → 예정 순서 채택 → support 전송
                  └────────> 필요한 재검증·재실행 병렬 수행
                         ↓
             같은 prefix에 3f+1 support
```

- Support는 실행 완료가 아니라 예정 순서 채택이다.
- 같은 adjustment round 동안 후보를 고정한다. 늦은 blocks는 다음 확장으로 넘긴다.
- Support가 갈리면 같은 context에서 중복 서명하지 않고 새 round/leader로 진행할 수 있어야 한다.
- Timeout은 경로 전환의 성능/복구 수단이지 비수신 증명이나 finality가 아니다.
- Discovery report와 adjustment support, 서로 다른 revisions/views의 서명을 임의로 합산하지 않는다.

정상 leader·안정된 문맥·유효한 후보·데이터 복구·eventual synchrony 아래 정상 노드는 최소 4f+1명이므로 Byzantine 협조 없이 q 지지가 가능하다. 정확한 round 전환·equivocation recovery는 추가 설계·검증 대상이다.

### 3.4 Prefix 확장, cut 연결과 실행

정상 경로에서는 채택 prefix 앞/내부에 늦은 blocks를 넣지 않고 suffix를 확장한다. Prefix와 다른 순서로 이미 실행한 노드는 초기 조정에서 재검증·필요한 재실행을 수행한다. 순서 변경만으로 모든 결과를 일괄 폐기하지 않는다.

```text
예정 순서 보고 → 공통 prefix 발견 / leader 조정 → 3f+1 support
                               │
                               ├→ sync·실행 조정·suffix 실행
                               │
                               └→ tips + 선택한 exact order로 cut proposal
                                                     ↓
                                              전체 cut finality
                                                     ↓
                                   exact cut·parent·runtime 검증 → state
```

Plan support는 영구 ordering lock이 아니다. Leader 교체나 기반 합의상 안전한 후보 변경 시 이전 plan과의 불일치를 허용하고 실행을 보정한다. Plan과 다르다는 이유만으로 기반 합의상 유효한 cut을 무조건 거부하지 않는다.

Cut proposal은 선택한 exact order 또는 이를 검증 가능한 commitment와 tips를 함께 인증해야 한다. Tips-only 인증 뒤 순서를 덧붙이지 않는다. Proposal/vote 전송 이후 새 support로 이미 보낸 대상을 바꾸지 않는다. 이 adapter의 정확성은 미검증이다.

Block 생성·전파·실행은 지지 수집 중에도 계속한다. 미완료 plan을 cut의 무조건적 대기 조건으로 두지 않는다. Finalized cut 도착 시 그 exact input이 우선한다. 긴 speculative root를 짧은 확정 prefix의 결과로 잘라 쓸 수 없고 checkpoint 또는 필요한 재실행이 있어야 한다.

f+1 matching execution signatures를 사용한다면 직접 실행/검증·subject·보관 조건을 별도로 명시한다. 그것은 plan q나 ordering finality를 대신하지 않는다. Durable readiness도 별도로 측정한다.

## 4. Correctness and Liveness

### 4.1 성질과 증명 범위

동일 context에서 정상 signer가 상충 sequence에 중복 서명하지 않는다면:

```text
q=3f+1, n=5f+1
|Q1 ∩ Q2| ≥ 2q−n = f+1
→ 정상 signer ≥ 1명
→ 양립 불가능한 두 prefix의 동시 q-support 불가
```

포함관계인 prefix는 양립 가능하다. 이 논증은 다른 phases/rounds/views의 인증 충돌이나 canonical finality를 해결하지 않는다.

입증할 항목:

- Exact prefix/context binding과 중복 identity 계수 방지.
- Report와 adjustment evidence의 구분 및 round 전환의 일관성.
- 기반 합의가 확정한 exact order·parent에 대한 canonical adoption.
- Speculative 결과 재사용의 reference execution 등가성.
- Stale plan·늦은 support가 기존 proposal/vote·최종 결정을 뒤집지 않음.
- 정상 leader 아래의 조건부 수렴과 계획 실패에도 가능한 cut 진행.

Plan이 finality가 아니어도 integration safety/liveness 검증은 필요하다. “advisory이므로 자동으로 안전”이라고 주장하지 않는다.

### 4.2 Byzantine behavior

| 사례 | 대응 원칙 / 검증 과제 |
|---|---|
| 거짓 예정 순서 | 성능 입력일 뿐 실행 결과 증거 아님; 최종 입력에 실행 검증 |
| 같은 round equivocation | 서명 context·identity·중복 검사; 정상 노드 중복 서명 금지 |
| Leader가 조정안을 분리 전파 | 지지 분산·실패 round 복구 검증; 강제 수렴 보장 없음 |
| 다른 rounds의 충돌 인증 | 합산 금지; 현 문맥·기반 합의 우선; 보정 가능성 명시 |
| Stale parent·위조 refs·누락 body | Parent·ancestry·가용성 검증 및 sync |
| Leader 중단·보고 은닉 | 계획 수집을 cut barrier로 두지 않음; 기존 recovery와의 연결 검증 |
| 반복 변경·flood·검열 | 후보 window·갱신·자원 예산과 fairness 평가 |

DA나 3f+1 support만으로 올바른 실행 또는 Byzantine leader 아래 좋은 성능을 주장하지 않는다.

## 5. Evaluation

### 5.1 비교군

| 비교군 | 검증 목적 |
|---|---|
| 같은 기반 합의 + post-cut execution | 노출된 실행 비용 |
| Unguided speculation | Pipeline 이득과 invalidation |
| Leader-local 순서 유지 | Leader의 편향된 수신 view가 만드는 비용 |
| Common-prefix discovery만 | 자연 발생하는 지지를 활용한 이득·한계 |
| Discovery + adjustment | 적극적 수렴의 추가 이득·통신 비용 |
| Early ordinary proposal | 기존 제안을 일찍 보내는 방법과 차이 |
| Frequent cuts + speculation | 짧은 ordering 결정 반복 대비 차이 |

동일 backend·위원회·자원·완료 의미를 고정한다. Hermes를 기본 엔진으로 지정하지 않는다. 서로 다른 protocol profile의 비교를 직접 ablation으로 대신하지 않는다.

### 5.2 지표와 workload

- Ingress→state-finalization p50/p95/p99, successful goodput, backlog·미완료 요청.
- Cut→state, ordering latency, durable readiness를 분리.
- 새 common-prefix 길이, discovery 성공률, adjustment 비율, q 형성 시간.
- 초기 조정 재실행과 이후 late-insertion 재실행, 총 CPU·시도·메모리·network bytes.
- RTT × application operations, conflicts, lane imbalance, offered load, parent 지연.
- Leader에게만 X가 늦는 경우, 다수 노드에 늦는 경우, 중간 공통 조각만 있고 공통 prefix는 없는 경우.
- 정상/Byzantine leader, equivocation, 오래된 보고, leader 교체와 cut 중 늦은 support.
- 순서가 달라지는 E2E 비교에서는 application 성공률·fairness 변화도 보고.

실행 진척 계측은 offline 분석용이며 plan 선택에 입력하지 않는다. Cut을 늦춰 cut-to-state만 줄이는 결과를 개선으로 보지 않는다. 기존 toy tests·fork 결과를 이 새 protocol의 검증으로 인용하지 않는다.

## 6. Related Work

- **Autobahn:** parallel dissemination·cut agreement·parallel slots의 배경. [SOSP 2024](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- **Hermes:** prefix를 실제 finalize하는 참고 연구. 우리의 예정 순서 discovery/adjustment와 finality를 구분한다. [Preprint](https://arxiv.org/html/2607.25916v2)
- **HotStuff-1:** speculation·prefix 안전성과 leader 교체 비교. [논문](https://arxiv.org/html/2408.04728v3)
- **Rashnu:** local ordering 보고·graph 구성의 선행성. 우리는 실행 완료 보고나 minimum-disagreement graph 합성을 채택하지 않는다. [PVLDB 2024](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)
- **Zyzzyva·ISOS:** speculation과 dependency ordering의 선행 연구. [ISOS](https://arxiv.org/abs/2109.06811)

Common prefix·quorum·사전 실행 각각의 최초성을 주장하지 않는다. 구체적인 수렴 정책과 추가 비용 대비 state-finalization 개선에서 차별성을 입증해야 한다.

## 7. Discussion and Limitations

- 공통 prefix 지지는 동일 실행 완료·데이터 보유나 옳은 결과의 증거가 아니다.
- Support는 cut finality가 아니므로 leader 교체·후보 변경에서 재실행 가능성이 남는다.
- 강한 불변 lock으로 바꾸면 작은 cut에 가까워진다. 현재는 변경 가능한 계획이며 정상 경로의 prefix 유지를 목표로 한다.
- Adjustment의 추가 메시지·q 수집 비용은 실제 비용이다. Non-blocking production만으로 latency 우위를 주장할 수 없다.
- Report가 오래됐거나 network·workload 변화가 크면 초기 조정 비용이 이득을 상쇄할 수 있다.
- 같은 context의 교집합 논증은 rounds/views를 넘는 프로토콜 증명이 아니다.
- Round recovery·cut 경계·가용성·resource limits는 아직 완성해야 한다.
- Commonware·LaTeX/PDF·Google Docs는 이번 문서화로 변경되지 않는다.

## 8. Conclusion

**실행 pipeline → late insertion 비용 → 3f+1 공통 prefix 발견 → 없으면 leader 조정으로 수렴 → 정상 경로에서 prefix 확장 → 기존 cut으로 최종 결정 → exact-context 실행 검증.**

연구 목적은 더 자주 finality를 만드는 것이 아니라, finality를 기다리는 동안 반복적인 실행 무효화를 줄이는 것이다. 실제 통신·복구 비용을 포함해 frequent cuts와 early proposal보다 나은지 검증한다.
