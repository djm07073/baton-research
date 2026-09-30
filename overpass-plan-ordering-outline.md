> **Historical snapshot — superseded by Baton (2026-09-30).**
> Current research: [Baton paper](baton-paper.md), [implementation specification](baton-implementation-spec.md), and [current handoff](BATON_HANDOFF.md).
> The body below is preserved as research/citation history. Its sum-only selection, plan/advisory descriptions, incumbent preferences and “current/latest/source of truth” claims do not override 2f+1-prefix-first selection or the adopted direction-preserving cut requirement. The four proposed implementation defaults remain unadopted; native integration and performance remain unproved.

# Overpass: Execution-Aware Ordering for Autobahn-Family Consensus

> 2026-09-30 최신 결정. [상세 plan 정책](overpass-prefix-plan.md) / [논리 전개](overpass-research-logic.md) / [이전 3f+1 모델 보관본](research/archive/2026-09-30-before-scored-plan/INDEX.md).
> Hermes는 참고 연구이며 채택한 합의 엔진이 아니다. 구현·증명·평가 완료를 뜻하지 않는다.

## 핵심 결정

**기반 구현 경로는 Native Multimmit이다.** 기존 tip 추출·extension을 유지하며 plan을 결합한다. Plan으로 native block inclusion을 대체하거나 extension을 제거하는 fixed-cut 변형은 채택하지 않는다. Native chain-local finality를 plan-aware canonical execution order로 연결하는 구체적 adapter는 설계·검증 대상이다. 상세 경계는 [plan 정책 §7.1](overpass-prefix-plan.md#71-native-multimmit과의-결합-검토)을 따른다.

**Overpass는 새로운 consensus safety protocol이 아니라 Autobahn-family consensus를 위한 execution-aware ordering extension이다. Validator들의 intended order를 이용해 speculative execution을 보존하기 유리한 ordering 후보를 선택하며, 별도 plan 승인 단계나 기존 cut consensus의 대기 없이 state-finalization latency를 줄이는 것을 목표로 한다.**

Validators는 같은 cut·canonical parent의 예정 순서를 비동기로 보고한다. Leader는 유효 후보 중 **보고들과 공통 prefix 길이 합이 큰 순서**를 선택해 실행 plan으로 전파한다. 별도의 plan 승인 quorum은 없다.

**채택 완료:** 선택한 ordering policy는 leader block의 인증 대상에 결속하고 같은 proposal에서 고정한다. State finalization은 exact ordering finality와 동일 input·canonical parent·runtime·결과에 대한 f+1 유효 validator의 일치 실행 서명이 모두 검증된 상태다. Durable/read readiness는 별도 측정한다. 상세 조건은 [plan 정책 §7.2](overpass-prefix-plan.md#72-policy-binding과-state-finalization의-채택-조건)에 기록한다. 구현·통합 증명은 아직 미완료다.

n=5f+1에서 **서로 다른 validator의 유효 보고 4f+1개 확보 또는 local 수집 deadline 중 먼저 발생한 시점**에 계산한다. Deadline에는 더 적은 보고로도 진행한다. Cut은 수집·timer·계산 완료를 기다리지 않는다.

이전 3f+1 공통 prefix 인증과 조정 후 support 수집 경로는 현재 설계가 아니다. 보고들은 서로 다른 순서를 제안할 수 있으며 4f+1이 선택된 후보를 승인했다는 뜻이 아니다. Finality는 기존 cut 합의에 남는다.

원격 실행 이력·완료 proof를 plan 선택에 요구하지 않는다. 내부 실행 검증·offline 계측은 유지한다. Producer placement, Multilevel grouping, state-owner sharding, ZK/PAC, receipt bridge와 repair lane은 제외한다.

## 1. Introduction

### 문제 → pipeline → 후속 비용

Autobahn-family의 parallel dissemination과 cut agreement를 배경으로 한다. Ordering finality 이후 application execution을 시작하면 실행 시간이 state-finalization latency로 노출된다. 이를 줄이기 위해 수신·sync·consensus와 speculative execution을 겹친다.

Late predecessors와 후보 변경은 사전 실행을 무효화할 수 있다. Leader의 순서만 고정해도 충분하지 않다. Leader에게만 X가 늦었다면 다수 노드가 수행하던 X→A→B를 A→B→X로 뒤집을 수 있기 때문이다.

### 제안과 기여 후보

중심 제안은 여러 validator의 intended order를 ordering 후보 선택에 반영하는 execution-aware ordering extension이다. 단순히 기존 순서에 맞춰 실행을 앞당기는 것을 넘어, finality 전에 speculative work를 보존하기 유리한 유효 후보를 선택한다. 실제 실행 이력·진척의 증명을 요구하는 모델은 아니다.

- 중심 설계: intended-order feedback으로 ordering 후보 선택과 speculative execution을 조율한다.
- 구현 메커니즘: LCP score, 4f+1-or-deadline, cut preemption, 변경 억제. 추가 plan 승인 단계를 만들지 않는다.
- 검증: 기존 cut consensus에 exact selected order를 안전하게 연결하고, 단순 pipeline 대비 재실행·post-cut 잔여 작업·E2E latency의 순이득을 평가한다.

기여의 최초성·우월성은 미검증이다. 공통 prefix·사전 실행·quorum 자체의 최초성을 주장하지 않는다.

## 2. Background and Motivation

### 2.1 Ordering과 state의 경계

Producer lane과 validator identity를 구분한다. DA, ordering finality, 실행 결과 인증과 durable readiness는 다른 사건이다. Cut vote는 같은 body·local execution view·완료 결과를 보장하지 않는다.

기반 합의의 전체 finality 절차를 유지한다. n=5f+1은 현재 수집 정책 profile이고, 구체적인 Autobahn/Commonware adapter와 cut voting 규칙은 별도 검증 대상이다. [Autobahn](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

Native Multimmit에서는 leader block finality, chain-local membership, irrevocable ordered prefix의 도출을 구분한다. 첫 leader-finality 관측만으로 관련 block 모두의 global execution 위치가 즉시 확정되었다고 가정하지 않는다. 아래의 “cut에서 최종 순서 확정”은 기반 인증 자료와 올바른 ordered-delivery 규칙으로 해당 입력의 exact order를 확정한다는 요구사항이며, 첫 L-QC만으로 plan 전체가 final이라는 뜻이 아니다. [구현 경계](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md)

### 2.2 Prefix를 점수로 사용하는 이유

X→A→B와 Y→A→B의 공통 중간 조각은 앞선 X/Y가 만든 입력 차이를 없애지 못한다. 같은 parent에서 처음부터 연속으로 일치한 길이를 재사용 가능성의 proxy로 사용한다.

예정 순서는 실제 실행 이력·진척을 의미하지 않는다. 긴 공통 prefix가 실제 절약 CPU와 얼마나 연관되는지는 측정해야 한다. 필수 producer ancestry나 application 선행 조건은 점수보다 우선한다.

### 2.3 연구 가설

- H1: 필요한 조정을 finality 전에 수행해 post-cut 잔여 시간을 줄인다.
- H2: 분산된 예정 순서를 반영하고 후보 churn을 억제해 총 invalidation을 줄인다.

추가 수집·계산·전파와 초기 재실행 비용으로 순이득이 사라질 수 있다. Figure 1은 Original / Pre-cut execution / Overpass의 세 경로와 비대칭 block 도착 반례를 보여준다. Leader 한 명의 관측에 의존할 때의 반례는 설명용이며 별도 필수 비교군은 아니다.

## 3. System Design

Extension은 최종 cut에 제안할 ordering 후보를 고르는 부분과 speculative scheduling을 연결한다. 새로운 safety quorum으로 cut finality를 대체하지 않는다. 다만 tips만 인증하던 protocol에 임의 순서를 덧붙일 수는 없으므로, selected order 또는 복구 가능한 commitment를 기존 cut 합의가 인증하도록 adapter를 설계·검증해야 한다.

### 3.1 역할과 보고

고정 위원회, deterministic application, 인증 메시지와 기반 BFT network/fault model을 전제로 한다.

- Producer: block 생성·전파 지속.
- Validator: sync·유효성 검증, 예정 순서 보고, plan에 따른 scheduling·재검증·재실행, 기존 cut vote.
- Leader: bounded report snapshot 구성, 점수 계산·후보 전파, 실제 cut proposal 구성.

보고는 epoch/view, 기준 cut·canonical parent, rule version, collection window와 exact block references를 묶는다. Identity당 window의 유효 보고 하나만 계수한다. 다른 문맥은 섞지 않는다. 보고는 실행 완료 proof나 선택된 plan에 대한 승인 서명이 아니다.

### 3.2 Score-guided candidate selection

Bounded horizon W 안에서 유효한 보고 후보들과 incumbent를 평가한다.

```text
Score(P; R) = Σ_i |LCP(P, R_i)|

R1: A → B → C
R2: A → B → D
R3: A → B → E
R4: B → A → X
R5: B → A → Z

Score(A→B→C) = 7
Score(B→A→X) = 5
```

이 예시에서 A→B→D/E도 7로 동점이다. Incumbent가 동점이면 유지하고 없으면 canonical tie-break를 적용한다. 제한된 후보 집합에서 선택하는 것이며 모든 순열의 최적해나 실제 재실행 최소화를 주장하지 않는다.

후보 유효성·ancestry·가용성 근거를 검사한다. 나머지 준비된 blocks는 필수 제약을 지키며 기본 ordering rule로 suffix에 추가할 수 있다. Candidate horizon과 suffix 정책을 고정해 실험한다.

### 3.3 4f+1-or-deadline collection

첫 미반영 실행 가능 block을 관측하면 t0에 수집 window를 시작한다. t0+τ를 고정 deadline으로 둔다.

```text
보고 수집
   ├─ distinct valid reports 4f+1개 → 계산
   └─ local deadline 도달          → 확보한 보고로 계산
                먼저 발생한 trigger로 window 종료
                              ↓
                        필요 시 plan 전파
                      (추가 승인 투표 없음)
```

- 새 보고가 와도 timer를 다시 시작하거나 deadline을 연장하지 않는다.
- 두 trigger가 함께 발생해도 window는 한 번만 닫는다.
- 보고가 없으면 incumbent 또는 기본 rule을 사용한다.
- τ는 leader-local duration이며 노드 clock 동기화나 Unix timestamp ordering을 요구하지 않는다.
- Window·메시지·계산 예산을 제한한다. 실제 τ와 갱신 간격은 실험 설정이다.

n=5f+1에서 보고 4f+1개에는 정상 보고자가 최소 3f+1명 포함되고 빠진 identity는 최대 f명이다. 하지만 같은 순서 지지나 실행 완료는 아니다. Byzantine f명이 침묵하면 strict threshold는 모든 정상 노드를 기다리므로 deadline을 둔다. Deadline에서 더 적은 보고로 선택한 경우 해당 coverage를 주장하지 않는다.

### 3.4 Update policy, execution과 cut 연결

새 후보와 incumbent는 같은 report snapshot·horizon에서 비교한다. 동점 유지, 충분한 개선에서만 재정렬, 무변화 전파 생략과 bounded update rate로 churn을 억제한다. 단순 suffix 확장과 기존 순서 변경을 별도 계측한다.

Plan을 받은 node는 문맥·refs를 확인하고 미실행 작업을 scheduling한다. 진행/완료 작업은 입력 의존성을 검증하고 필요한 부분만 다시 실행한다. Leader에게 별도의 plan support를 보내거나 수집할 필요가 없다.

```text
Report collection → score/plan → speculative scheduling·validation
                              │
Cut ready ────────────────────┘
   ↓ 수집·timer·계산을 기다리지 않음
준비된 최신 유효 후보 / 기본 ordering fallback으로 proposal
   ↓
Native 인증 자료 → irrevocable ordered prefix 도출
   ↓
해당 exact order·parent·runtime에 실행 결과 검증 → state
```

Cut이 먼저 준비되면 pending optimizer를 기다리지 않는다. 이미 보낸 proposal/vote를 늦은 보고로 수정하지 않는다. 계산 결과의 문맥이 오래됐으면 해당 cut에 사용하지 않고, 다음 계획에서 다시 유효성을 확인한다. Parent가 바뀌면 새 문맥의 보고를 요구한다.

최종 exact order는 인증된 문맥과 공통 규칙으로 유일하게 도출할 수 있어야 한다. 선택한 ordering policy를 leader block의 인증 subject에 결속하며 같은 proposal에서는 고정한다. Encoding·policy availability·extension continuation·recovery는 adapter의 미완료 과제다. 기존 tips-only 인증 뒤 임의 순서를 덧붙이지 않으며, 첫 leader finality와 plan 전체의 finality를 동일시하지 않는다. Proposal 이전 advisory plan은 영구 lock이나 finality가 아니므로 view change·최종 후보 변경 시 재실행이 남을 수 있다.

Finalized input의 parent·runtime에 결과를 검증한다. 긴 speculative root를 짧은 확정 입력의 root로 잘라 쓰지 않는다. 해당 epoch의 서로 다른 validator f+1명의 일치 실행 서명을 검증하며, 정직한 서명자는 직접 실행·검증한 결과에만 서명한다. Ordering QC에 참여하지 못했어도 올바르게 따라잡은 validator는 참여할 수 있다. 결과 인증의 f+1과 보고 수집 목표·native ordering quorum은 별개다.

## 4. Correctness and Liveness

### 4.1 입증할 성질

- Report context/identity 검증과 중복·stale 입력 배제.
- 유효한 후보·정해진 tie-break·동일 snapshot에서의 재현 가능한 선택.
- Plan 점수와 무관한 canonical ordering safety 및 exact-context 실행 검증.
- 최종 ordering·parent·runtime에 고정된 결과에서 f+1 일치 서명에 정직한 직접 실행자가 포함된다는 논거. 다른 문맥·중복 identity·잘못된 epoch 서명은 배제한다.
- Plan revision이 이미 보낸 proposal/vote와 finalized 결정을 변경하지 않음.
- 수집 deadline 고정·단일 trigger·stale 계산 무효화 및 cut의 no-wait 경로.
- Bounded planning 부하와 기존 합의 recovery의 조건부 진행성.

별도 plan quorum이 없으므로 이전 3f+1 intersection 논증을 현재 모델의 안전성 근거로 사용하지 않는다. 4f+1 보고도 plan uniqueness를 인증하지 않는다. Cut ordering adapter 변경의 안전성은 따로 검증해야 한다.

### 4.2 Byzantine behavior

| 사례 | 원칙 / 검증 과제 |
|---|---|
| 거짓 예정 순서·편향된 점수 | 성능 입력일 뿐 correctness 근거 아님; 최종 문맥에서 실행 검증 |
| 중복·상충 보고 | Window/identity binding, bounded handling; 보고 수 부풀림 방지 |
| Byzantine leader의 다른 plan·편향된 보고 선택 | Speculation이 갈릴 수 있음; 기존 cut finality가 canonical 순서 결정 |
| Stale parent·무효 refs·missing body | Parent·ancestry·가용성 검사와 sync |
| 보고 침묵·느린 정상 validator | Deadline fallback; cut은 수집을 기다리지 않음 |
| 지속적 새 보고로 deadline 연장 유도 | Deadline 불변, 계산·전파 budget |
| 계산 중 cut 도착·leader 교체 | Stale 결과 검사, 기존 proposal/vote와 recovery 규칙 유지 |

높은 보고 수나 점수가 Byzantine leader 아래 좋은 성능·fairness를 보장하지 않는다. Performance attack과 잘못된 canonical state 채택을 구분한다.

## 5. Evaluation

### 5.1 비교군

1. **Original:** 해당 block의 irrevocable execution order가 정해진 뒤 실행을 시작한다. Native Multimmit에서는 단순히 첫 leader-finality event를 실행 시작 조건으로 대신하지 않는다.
2. **Pre-cut execution:** 실제 수신한 blocks를 기본 ordering rule로 사전 실행하고, 확정 순서와 다르면 검증·재실행한다. 별도 leader plan 전파는 없다.
3. **Overpass:** 동일한 사전 실행 경로에 intended-order 수집·score-guided planning을 추가한다.

원인 분해용 ablation은 score 선택만/변경 억제 포함, timer-only/strict 4f+1/hybrid다. Frequent cuts는 별도의 민감도 실험으로 구분한다. Early proposal을 Pre-cut execution의 이름이나 전제 조건으로 사용하지 않는다.

같은 기반 consensus profile·backend·위원회·자원·완료 의미를 사용한다. 다른 protocol끼리의 비교를 직접 ablation으로 대신하지 않는다.

### 5.2 지표와 사례

측정 단위는 transaction의 canonical occurrence 또는 block이며, 동일한 관측 node의 monotonic clock으로 event 간 시간을 잰다. Native profile에서는 leader finality, 해당 입력의 irrevocable ordering 도출, body 준비, 최종 실행 검증/결과 인증, durable/read readiness를 구분한다. Primary endpoint는 지정 관측 node가 exact ordering finality와 f+1 일치 실행 서명을 올바른 canonical parent·runtime에 대해 모두 검증한 시점이다. Durable/read readiness는 보조 지표다. 서로 다른 node의 timestamp를 동기화 오차 설명 없이 빼지 않는다.

`cut→state`는 선택한 completion endpoint와 해당 입력의 ordering 확정 시각 사이의 차이로 명확히 정의한다. First L-QC→state는 별도 진단 지표다. 한 leader block에서 ordered prefix가 점진적으로 늘면 모든 block에 첫 L-QC 시각을 같은 ordering 확정 시각으로 부여하지 않는다. Body 준비와 실행은 순서 확정 전에도 진행될 수 있으므로 각 단계 시간을 무조건 직렬 합산하지 않는다.

간격 축소만으로 성능 개선을 주장하지 않는다. 예를 들어 같은 ingress 시각 0에서 기준 모델의 order/state가 12/20이고 Overpass가 25/26이면, order→state는 8에서 1로 줄어도 E2E는 20에서 26으로 악화된다. 이는 단위 없는 설명용 수치이지 측정 결과가 아니다. 동일 offered load·요청 집합·완료 의미에서 ingress→state와 backlog를 함께 보고한다. 각 node의 local ordered-delivery 지연도 계측 대상이며, timestamp를 나중에 기록해 간격을 인위적으로 줄이지 않는다.

- Ingress→state, cut→state, ordering latency, durable readiness p50/p95/p99와 successful goodput.
- Threshold/deadline/cut-preemption 비율, report 수·수집·계산 시간, plan-to-cut lead time.
- 점수·실제 reuse의 상관, 초기 조정·이후 invalidation, CPU·메모리·report/plan bytes.
- τ·candidate horizon·개선 폭 sweep, RTT × application operations, conflicts, lane imbalance·offered load.
- Leader에게만 X가 늦음 / 다수에 늦음 / f명 침묵+느린 정상 node / 보고 없음.
- Timer 재시작 공격, duplicate/stale report, 동일 점수 tie, 계산 중 cut 도착, view change.
- 순서 변경에 따른 application 성공률·fairness도 보고하고 backlog·미완료 요청을 포함한다.

최종 latency만 줄인 것처럼 보이도록 cut을 늦추지 않는다. Offline 실행 계측을 leader 선택에 몰래 피드백하지 않는다. 기존 fork/toy tests를 새 모델의 검증 증거로 인용하지 않는다.

### 5.3 순서 변경 효과와 재실행 절약의 원인 분리

Overpass는 최종 순서도 바꾸므로 동일 요청 집합만으로 application 작업량이 같다고 가정하지 않는다. 같은 거래가 다른 state를 읽으면 성공/실패뿐 아니라 실행 branch와 비용도 달라진다. 성공 거래 수나 최종 state가 같아도 이 혼동은 남는다.

- **통제된 진단:** Order-sensitive reads/writes는 있지만 거래당 application 작업량은 고정된 workload에서 실제 cache validation·재실행을 계측한다. 순서가 달라진 suffix 길이를 재실행량으로 대신하지 않는다.
- **일반 workload:** 각 run의 canonical input·parent·runtime·실행 환경·최종 순서를 저장하고, 그 순서를 처음부터 실행하는 reference replay로 결과와 기준 작업량을 확인한다. 서로 다른 순서의 reference 작업량 차이와 speculative attempt 낭비를 분리해 보고한다. Validation·planning·서명 비용도 별도로 포함한다.
- **주장의 기준:** E2E만 개선되면 성능 관측으로 보고할 수 있지만, 재실행 감소가 확인되지 않으면 이를 작업 보존 메커니즘의 증거라고 부르지 않는다. 반대로 재실행이 줄어도 E2E와 backlog가 악화되면 latency 목표 달성으로 보지 않는다.

Reference replay는 사후 원인 분석이며 네 번째 주 비교군이나 leader가 사용하는 oracle이 아니다. 실제 실행을 미리 알려 주거나 모든 online 구성의 final order를 강제로 같게 만들지 않는다. Parallel backend에서는 serial replay의 wall time을 online latency에서 빼지 않고, deterministic operation 수·runtime 계측과 attempt 기록으로 작업량을 비교한다. 세 주 비교군과 완료 조건은 그대로 유지한다.

## 6. Related Work

- **Autobahn:** dissemination과 cut agreement, parallel slots의 배경. [SOSP 2024](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- **Hermes:** prefix를 finalize하는 참고 연구이며 본 모델의 엔진이 아니다. [Preprint](https://arxiv.org/html/2607.25916v2)
- **HotStuff-1:** speculation과 prefix 안전성·leader 변경 비교. [논문](https://arxiv.org/html/2408.04728v3)
- **Rashnu:** local ordering 보고를 활용하는 선행 연구. 우리의 LCP proxy 선택·성능 목적과 비교한다. [PVLDB 2024](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)
- **Zyzzyva·ISOS:** speculation과 dependency ordering의 선행성. [ISOS](https://arxiv.org/abs/2109.06811)

Report 수집·prefix 점수·pipeline 개별 기법을 최초라고 주장하지 않는다. 구체적인 bounded planning과 실행 무효화·E2E 성능의 관계에서 차별성을 검증한다.

## 7. Discussion and Limitations

- LCP 점수는 예정 순서의 proxy이며 실제 절약 비용·최적 실행 순서를 보장하지 않는다.
- 수집된 보고의 수·길이·freshness와 Byzantine 편향이 선택에 영향을 준다.
- Deadline fallback은 coverage보다 조기 조율을 택하므로 최선 후보를 놓칠 수 있다.
- Plan이 너무 늦으면 동일한 Pre-cut execution보다 이득이 없거나 추가 비용만 발생할 수 있다.
- Candidate window 밖 transactions의 포함·fairness와 report/plan resource limits가 필요하다.
- 별도 approval round가 없어도 수집·계산·전파 비용은 존재한다.
- Plan이 finality가 아니므로 leader 교체·후보 변경의 재실행은 남는다.
- 실제 Commonware integration·LaTeX/PDF 갱신은 이번 문서화 범위 밖이다.

## 8. Conclusion

Overpass는 Autobahn-family consensus를 위한 execution-aware ordering extension이다. 분산된 intended order를 ordering 후보 선택에 반영하고 별도 plan 승인 단계 없이 사전 실행을 조율한다. 기존 cut consensus를 plan 준비에 종속시키지 않으면서 state-finalization latency를 줄이는 것이 목적이다.

**실행 pipeline → 분산된 예정 순서 수집 → 4f+1-or-deadline → LCP 점수로 후보 선택 → 추가 승인 없이 실행 조율 → 기존 cut에서 최종 결정 → exact-context state 검증.**

목표는 새 finality를 자주 만드는 것이 아니라, 기존 finality를 기다리는 동안 실행 낭비를 줄이는 것이다. Original / Pre-cut execution / Overpass를 비교해 수집·계산·통신·재실행 비용을 포함한 순이득을 검증한다.
