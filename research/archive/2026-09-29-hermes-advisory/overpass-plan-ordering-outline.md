# Overpass: Advance Ordering Plans for Pipelined State Finalization

> 2026-09-29 · Hermes 기반의 새 연구 방향과 논문 개요. Protocol 구현·증명·성능 검증 완료를 뜻하지 않는다.
> [논리 전개 요약](overpass-research-logic.md) / [실행 이력 기반 plan 보관본](research/archive/2026-09-29-execution-history-plan/INDEX.md) / [이전 binding-plan 설계](research/archive/2026-09-29-binding-plan/INDEX.md) / [placement archive](research/archive/2026-09-29-before-plan-ordering/README.md)

## 핵심 주장과 범위

**Overpass는 사전 ordering plan을 조기에 공유하여 dissemination·ordering consensus와 speculative execution을 중첩하고, 노드들의 실행 방향을 유효한 consensus 후보에 미리 맞춰 재실행과 state-finalization latency를 줄이는 것을 목표로 한다.**

Plan은 공통 prefix를 직접 확정하는 별도 consensus가 아니다. **알려진 block·tip, 유효 parent와 공통 ordering rule**을 바탕으로 앞으로 실행할 후보 순서를 예고한다. 이미 누가 얼마나 실행했는지 조사하여 순서를 선택하지 않는다. 최종 ordering은 Hermes가 결정하며, plan은 proposal과 speculative execution이 같은 방향으로 준비되도록 돕는다.

**설계에서 제외하는 입력:** 원격 노드의 실행 완료 주장, 실행 이력·진척 보고, 재사용량 주장과 그에 대한 execution proof. 이러한 주장을 신뢰하거나 증명·검증하는 후속 protocol을 이번 연구에 도입하지 않는다. “실행 이력의 증명이 원리적으로 불가능하다”는 일반 명제를 주장하는 것은 아니다. 각 노드의 내부 재사용 검증과 실험용 실행 계측은 유지하되 plan 선택에 피드백하지 않는다.

초기 연구는 **Hermes의 유효 proposal·parent·vote·finalization 규칙 안에서 동작하는 advisory 설계**로 한정한다. 임의 순서 재배열이나 새로운 plan quorum을 요구하는 확장은 별도 protocol 연구이며 이 개요에 섞지 않는다. Hermes는 2026년 preprint를 기준으로 검토 중이며, Commonware fork에 이미 구현되어 있다고 가정하지 않는다.

### 이전 개요에서 바뀐 결정

| 이전 binding-plan 모델 | 현재 연구 방향 |
|---|---|
| Plan 자체를 3f+1로 인증하고 prefix를 보호 | Plan은 서명 가능한 scheduling hint; 별도 binding quorum 없음 |
| 마지막 plan 인증을 완료한 다음 cut 제안 | 준비된 plan만 활용; plan 수집·완료를 consensus의 선행조건으로 두지 않음 |
| Plan chain과 tips를 별도 fixed-cut consensus에 결합 | Hermes에서 유효한 후보 선택과 execution 준비를 보조 |
| 공통 prefix를 보호하여 insertion 금지 | 사전 ordering 예고로 후보·실행을 수렴; 실제 prefix 보존은 Hermes의 역할 |
| Cut마다 반드시 하나의 전체 후보를 확정 | Hermes가 실제 finalize한 prefix만 canonical 입력으로 채택 |

직전 개요의 execution-aware planning도 보관한다. 공통 실행 조각을 찾는 optimizer 대신, 사전 plan과 실제 consensus 후보의 연결·변경 규칙을 연구한다.

Producer placement, Multilevel grouping, state-owner sharding, ZK/PAC, receipt bridge와 repair lane은 계속 제외한다. Commonware 수정·영문 LaTeX·Google Docs 갱신은 이 문서화에 포함하지 않는다.

## 논리 전개

1. **목표:** 빠른 ordering만으로 application state가 준비되지는 않는다.
2. **기회:** Block은 ordering finality 전에 전파되므로 먼저 실행할 수 있다.
3. **Pipeline:** 수신·sync·consensus·speculative execution을 중첩한다.
4. **후속 비용:** Local inputs·예정 순서가 달라 실행이 최종 ordering과 불일치할 수 있다.
5. **관찰:** 실행 결과를 수집하지 않아도 block references와 공통 규칙으로 유효한 후보 순서를 예고할 수 있다.
6. **Plan:** 사전 ordering plan을 일찍 공유하고 실제 consensus 후보와 연결하여 execution과 proposal 선택을 수렴시킨다.
7. **확정:** Hermes가 ordering prefix를 확정하고 exact-context 검증을 통과한 실행을 채택한다.
8. **평가:** Cut 이후 복구를 앞당긴 효과, 총 재실행량 감소, 계획 비용을 포함한 E2E 순이득을 각각 검증한다.

## 1. Introduction

### 문제와 접근

Autobahn의 parallel dissemination과 cut agreement를 배경으로, ordering 이후 실행을 시작하는 구성에서 남는 state-finalization 지연을 설명한다. 기존 연구가 execution을 전혀 다루지 않았다고 쓰지 않는다. [Autobahn](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

그 지연을 숨기기 위해 같은 ordering 구간의 dissemination·consensus와 execution을 겹친다. 다만 관측한 blocks와 후보 순서가 다르면 speculative work를 고쳐야 한다. 이 비용이 사전 실행의 이득을 상쇄할 수 있다는 후속 문제로 연결한다.

해결 방향은 transaction을 producer에 새로 배치하거나 실행 완료 보고를 수집하는 것이 아니다. Block·tip과 ordering 규칙으로 **앞으로 사용할 후보 순서를 일찍 공유하는 plan**이다. 최종 순서 선택의 권한은 기반 consensus에 남긴다.

### 연구 질문과 기여 후보

> 실행 이력 보고 없이 사전 ordering plan을 유효한 Hermes 후보와 연결하여, consensus 진행을 plan 대기로 막지 않으면서 speculative execution의 불일치와 state-finalization latency를 줄일 수 있는가?

- Advance ordering planning: 검증 가능한 ordering 입력에서 후보를 구성·예고하고, 그 plan을 실제 consensus proposal과 일관되게 연결하는 정책.
- Non-blocking pipeline: advisory plan과 실제 consensus 결과를 구분하여 실행을 준비·검증·보정하는 구조.
- Correctness 및 평가: 기반 consensus와의 호환성, 안전한 실행 재사용, 추가 planning 비용 대비 latency 순이득.

Speculative execution·공통 prefix·quorum 자체의 최초성을 주장하지 않는다. 위는 검증할 기여 후보이지 달성한 결과가 아니다.

## 2. Background and Motivation

### 2.1 Autobahn-style lanes와 Hermes

Producer lane은 block 생성 chain이고 validator는 consensus·실행 검증 참여자다. Lane을 독점 state owner로 정의하지 않는다.

Hermes의 초기 reference는 n=5f+1이다. 같은 view의 4f+1 vote로부터 공통 prefix를 finalize하며, 2f+1 comparable votes에 의한 view 진행 근거와 구분한다. Vote가 지지한 proposal과 local 실행 결과는 다른 객체다. [Hermes §2–3](https://arxiv.org/html/2607.25916v2)

이 개요의 “cut 이후”는 **관찰 노드에서 해당 ordering prefix의 finality가 확인된 이후**를 뜻한다. 별도의 전체 fixed-cut 결정을 Hermes 뒤에 한 번 더 붙이지 않는다. 다른 길이의 인증 prefix를 같은 실행 입력으로 취급하지 않는다.

### 2.2 사전 실행의 기회와 비용

Block 수신부터 ordering finality까지의 시간에 실행을 수행할 수 있다. 그러나 늦은 선행 block, 후보의 범위 변경, 다른 parent state가 기존 실행의 관측을 바꿀 수 있다.

같은 A→B 순서를 계획했어도 parent나 앞선 X의 효과가 다르면 실행 결과는 다를 수 있다. **동일한 예정 순서, 동일 실행 문맥, 재사용 가능한 결과**를 구분한다. Plan 공유가 모든 노드의 데이터 보유·실행 완료 일치를 뜻하지는 않는다.

### 2.3 두 가지 별도 가설

- H1 — 보정 시점 이동: 최종 방향을 일찍 알면 어차피 필요한 재검증·재실행을 finality 이전에 처리할 수 있다.
- H2 — 낭비 예방: 아직 실행하지 않은 작업을 공통 후보에 맞춰 시작하면 이후 잘못된 추측 실행 자체가 줄 수 있다.

H1만 성립해도 post-finality 잔여 시간이 줄 수 있다. H2는 별도 검증 대상이며 plan churn이 크면 역전될 수 있다. 공통 prefix 길이 증가와 실행 재사용률 증가도 같은 지표가 아니다.

**Figure 1:** Post-order execution / unguided speculation / plan-guided speculation의 동일 입력 시간선. 노출된 실행 시간과 보정 시간을 구분한다.

## 3. System Design

### 3.1 Roles와 동시에 진행하는 작업

고정 위원회, bounded Byzantine faults, 인증된 메시지, deterministic application, eventual synchrony를 전제로 한다. 최초 실험은 같은 application·실행 backend를 사용한다. STM은 구현 선택이지 기여가 아니다.

- Producer: block 생성·전파.
- Validator: 데이터 수신·검증·sync, 기존 consensus 규칙에 따른 proposal/vote, 실행·재검증.
- 현재 leader의 planning 경로: 알려진 block·tip과 공통 ordering rule에서 유효한 후보 순서를 구성·예고. 원격 실행 보고를 요구하지 않음.

Planning은 새로운 독립 validator committee가 아니다. 실행 완료를 DA acknowledgement나 ordering vote의 조건으로 추가하지 않는다. Plan이 없어도 기존 consensus와 실행 fallback은 동작해야 한다. “Non-blocking”은 자원·데이터 의존 대기가 전혀 없다는 뜻이 아니다.

### 3.2 사전 ordering plan의 입력·구성과 공유

Plan의 입력은 알려진 exact block references와 tips, producer ancestry, 기반 protocol의 availability·proposal-validity 자료, 정당화된 parent와 ordering-rule version이다. 여기서 인증 자료는 입력·합의 문맥을 검증하기 위한 것이지 application 실행 proof가 아니다. 단순 tip 광고만으로 body 가용성이나 application 성공을 인정하지 않는다.

선언된 접근 state·dependency를 내부 실행 scheduling에 사용할 수 있지만 plan 생성에 사전 실행을 요구하지 않는다. Runtime correctness는 별도이며, 미검증 선언으로 consensus 순서를 임의 변경하지 않는다.

1. Leader가 현재의 유효 ordering 입력으로 후보를 구성한다.
2. 공통 canonical ordering rule로 해당 후보의 예정 순서를 결정한다. 나머지 block도 같은 rule을 따르며 leader가 실행 이력 점수로 재배열하지 않는다.
3. 대상 epoch/view, parent·justification reference, exact candidate/block references, rule version과 plan revision/digest를 묶어 공유한다.
4. 노드는 plan의 문맥·후보 유효성을 확인하고 필요한 body를 sync하면서 실행을 준비한다. 같은 plan은 같은 예정 순서를 뜻하지만 같은 local state나 동시 실행 완료를 보장하지 않는다.
5. 실제 proposal·finalized prefix가 도착하면 해당 문맥에 결과를 맞춰 재검증·필요한 재실행을 한다.

```text
알려진 blocks / tips + 유효 parent + 공통 ordering rule
                         ↓
                  사전 ordering plan
                         ↓
           노드별 sync + speculative execution
                         ↓
       실제 consensus 후보·확정 prefix와 대조
```

Plan의 서명·digest는 발신자와 내용을 식별하기 위한 것이며 순서 확정 인증이 아니다. 알려진 입력 집합이 다르면 후보가 다를 수 있으므로 결정적 rule만으로 모든 local plan이 같아진다고 주장하지 않는다.

**알고리즘 미정:** 후보 범위를 언제 정할지, plan 공개 시점·갱신 주기·revision 전이·tie-break·bytes/계산 상한은 남은 설계 과제다. 중심 질문은 “누가 얼마나 실행했는가”가 아니라 **“미리 공유한 순서가 실제 proposal과 어떻게 일관되게 이어지는가”**다.

### 3.3 Hermes에 연결하는 범위와 시점

Hermes의 multi-lane 값은 고정 interleaving과 block/skip 위치로 표현된다. 따라서 plan은 이 표현과 parent 제약을 만족해야 하며, block을 임의로 앞으로 옮기는 일반 permutation 기능을 전제로 하지 않는다. Advisory plan에서 skip을 예고하는 것과 consensus가 그 skip을 보존·확정하는 것은 다르다. [Hermes §4.2](https://arxiv.org/html/2607.25916v2)

초기 통합은 **실행 scheduling에 plan을 쓰는 부분**과 **유효한 consensus 후보의 선택에 쓰는 부분**을 분리한다.

- Proposal 이전: 이미 준비된 plan을 사용할 수 있다. 원격 실행 보고나 별도 plan quorum을 기다리지 않는다.
- Proposal 이후: broadcast한 proposal을 같은 view의 새 plan으로 교체하지 않는다. 실행 준비는 실제 proposal·parent 문맥과 대조한다.
- Vote 이후: plan 수신을 이유로 같은 view에서 다시 투표하거나 기존 vote를 철회하지 않는다.
- Fallback 선택: 기반 protocol이 허용하는 선택 지점 안에서 검토한다. 기존 leader 우선 투표·timer·진행 조건을 우회하지 않는다.
- 다음 view: 유효 justification의 parent 위에서 다시 검토한다. 오래된 plan은 canonical parent를 결정하지 못한다.

Hermes가 이미 정상 leader의 proposal로 votes를 수렴시킨다는 점이 중요하다. 추가 이득이 **더 이른 실행 준비**에서 오는지, fallback 때의 **후보 일치 개선**에서 오는지 나누어 분석한다.

**검증 필요:** 어떤 선택 hook을 바꿀 수 있는지, 정상 proposal보다 plan을 일찍 공유할 실제 시간 여유가 있는지, 원래 liveness·inclusion 가정을 유지하는지 확인해야 한다. 단순히 정상 proposal을 더 일찍 broadcast하는 것과의 차이도 입증해야 한다. Plan을 먼저 보낸다는 이유로 원래 가능한 proposal 전송을 늦추지 않는다. Advisory라고 해서 비용·검열·starvation 위험이 사라지지는 않으며, plan이 늦으면 기존 경로를 그대로 사용한다.

### 3.4 실행 조정과 state finalization

Plan 수신 시 아직 실행하지 않은 작업은 유효한 예상 순서로 scheduling하고, 수행 중이거나 완료한 작업은 실제 관측이 달라질 때 검증·취소·재실행한다. 무조건 전체 suffix를 다시 실행하지 않는다. 아직 불확실한 재사용은 최종 입력 기준으로 검증한다.

Ordering finality가 오면 **실제로 finalize된 prefix**, canonical parent와 runtime에 결과를 맞춘다. Plan의 전체 후보나 selected continuation을 곧바로 finalized 입력으로 취급하지 않는다. 더 긴 speculative 결과의 root를 짧은 prefix의 결과로 잘라 사용할 수 없으며, 검증 가능한 prefix checkpoint 또는 필요한 실행이 있어야 한다.

별도 plan certificate는 없다. f+1 matching execution signatures 같은 기존 결과 인증을 선택할 수 있지만, 이는 고정된 exact input의 결과를 인증하는 별도 경로다. 채택 시 직접 실행·검증한 signer와 subject·보관·복구 조건을 명시하고 비교군에 동일하게 적용한다. 결과 인증 시각과 durable read readiness는 구분한다.

**Figure 2:** Blocks/tips + parent + ordering rule → 사전 plan → sync/speculative execution; 별도 경로에서 실제 proposal·Hermes finality → exact-prefix validation → state apply.
**Figure 3:** Plan이 유지되어 재사용하는 경우·유효 후보 변경으로 재실행하는 경우·무효/stale plan을 거부하는 경우.

## 4. Correctness and Liveness

### 4.1 입증할 조건

- Advisory separation: plan만으로 canonical order·state를 정하지 않는다. 실행 완료 주장을 planning 입력으로 신뢰하는 경로가 없다.
- Consensus compatibility: 실제 proposal·vote·parent·finalization 전이가 선택한 Hermes 사양을 준수한다.
- Safe reuse: 최종 exact prefix에 대한 재사용 결과가 deterministic reference execution과 같다.
- Prefix-specific result: 더 긴 후보의 효과·실패 상태·fee·events가 짧은 확정 prefix에 누출되지 않는다.
- Progress independence: plan 누락·충돌·leader planning 실패 때문에 기존 consensus의 실행 가능한 전이를 막지 않는다.

새 ordering safety theorem을 증명했다는 주장이 아니라, 기반 protocol에 대한 refinement와 execution adapter의 정확성을 증명해야 하는 상황이다. 후보 선택 정책을 변경하면 진행성에 미치는 영향도 별도 확인한다.

### 4.2 Byzantine behavior

| 사례 | 원칙 / 검증 과제 |
|---|---|
| Leader가 서로 다른 plan을 전송 | 서로 다른 speculation은 가능하나 canonicality는 기존 consensus만 결정; churn budget 필요 |
| 위조된 block/tip·availability 자료 | Digest·서명·ancestry·기반 validity 규칙 검사; 필요 자료 복구 전 신뢰하지 않음 |
| 오래된 plan·잘못된 parent·vote 변경 유도 | Context 확인과 기존 consensus 전이 유지; stale plan 거부 |
| Plan 은닉·planning 중단 | Plan을 기다리지 않고 기존 proposal/fallback 경로 진행 |
| 특정 block을 계속 후보에서 배제 | 기존 inclusion 규칙 보존, starvation·producer별 대기 평가 |
| Plan flood·body 누락 | 메시지·계산·speculation 상한, 별도 sync·data recovery; 자원 격리 필요 |

실행이 계속되어도 canonical progress가 정지할 수 있다. 정상 leader·synchrony 아래의 진행과 Byzantine 상황의 비용 증폭을 구분한다.

## 5. Evaluation

### 5.1 주요 비교군

| 비교군 | 검증 목적 |
|---|---|
| 같은 Hermes + post-finality execution | 노출된 실행 비용 |
| 같은 Hermes + unguided speculative execution | Pipeline 자체의 이득과 보정 비용 |
| 같은 Hermes + plan-guided execution만 적용 | 후보 선택 변경 없이 조기 실행 정보의 효과 |
| 같은 Hermes + planning과 유효 후보 선택 연동 | 후보·실행 수렴의 추가 효과 |
| 같은 Hermes + 유효해지는 즉시 정상 proposal 전파 | 별도 사전 plan과 단순 early proposal의 차이 |
| 더 짧은 consensus view/결정 간격 + speculation | 단순히 더 자주 확정하는 방법과 비교 |

마지막 비교는 해당 protocol에서 실제 조정 가능한 proposal cadence·batching·timeout을 명시한다. 좋은 경로가 이미 network speed라면 “간격만 줄이면 된다”고 가정하지 않는다. 정상·fallback 설정과 자원 예산을 함께 공개한다. Native Multimmit 비교는 다른 consensus 간 비교이며 planning의 직접 ablation으로 대신하지 않는다.

### 5.2 지표와 workload

- 최상위: ingress→state-finalization의 p50/p95/p99와 successful goodput.
- 분해: ordering-finality→state-finalization, durable apply/read readiness, ordering latency.
- H1: 보정 작업 중 finality 이전/이후 비율과 잔여 critical-path 시간.
- H2: 총 실행 시도·재검증·재실행량, CPU·메모리·network bytes.
- 후보 수렴: 선택 quorum의 공통 prefix 길이·새 확정량, 실제 재사용량, plan 채택·변경·무효율을 별도 계측.
- Workload: RTT × application operation 수, conflict density, 늦은 선행 block, lane imbalance, offered load, parent 지연.
- 경로: 정상 leader와 delayed/crashed leader·fallback을 분리한다. 보정 시점 이동을 총 작업량 감소로 포장하지 않는다.
- Control: 같은 backend·worker·bandwidth·application semantics·완료 조건. 같은 exact order의 trace replay와 E2E 실험을 구분한다.

실행량·재사용률·진척은 offline 분석과 실험 계측에만 사용한다. Benchmark에서 그 정보를 plan 선택에 제공하면 다른 설계가 되므로 현재 제안의 비교 조건에 포함하지 않는다.

안전성 확인은 plan equivocation, 잘못된 block reference·입력 인증, stale parent, vote 후 plan 변경, 짧은 finalized prefix, leader 중단 등 작은 deterministic 사례로 시작한다. 기존 toy tests는 이 Hermes 통합을 검증한 결과가 아니다.

## 6. Related Work

- **Autobahn:** 병렬 dissemination과 ordering 분리의 배경. [SOSP 2024 논문](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- **Hermes:** 초기 reference consensus. Prefix 추출을 새로 발명했다고 주장하지 않는다. [2026 preprint v2](https://arxiv.org/html/2607.25916v2)
- **HotStuff-1:** speculative execution과 prefix 안전성·연속 slot 처리의 비교 대상. [논문](https://arxiv.org/html/2408.04728v3)
- **Rashnu:** local ordering 보고로 leader가 dependency graph를 구성하는 선행 연구. 해당 보고를 실행 완료 증명과 혼동하지 않는다. 우리는 입력에서 사전 순서를 예고하는 정책과 latency 효과를 비교한다. [PVLDB 2024](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)
- **Zyzzyva·ISOS:** speculation과 dependency ordering의 선행성. 우리의 차별성은 사전 plan–실제 후보의 연결과 state-finalization 평가에서 입증해야 한다. [Zyzzyva](https://consensus.app/papers/zyzzyva-speculative-byzantine-fault-tolerance-kotla-alvisi/f813ba27c02655079a441850afd3194b/?utm_source=chatgpt), [ISOS](https://arxiv.org/abs/2109.06811)

문헌 검토에서 얻은 설계 가설과 해당 논문이 실제 보장한 성질을 구별한다. 기여의 새로움은 확정된 사실이 아니라 추가 검토 대상이다.

## 7. Discussion and Limitations

- 같은 plan을 받아도 같은 state 입력·데이터 보유·실행 완료는 보장되지 않는다.
- 긴 공통 prefix와 적은 재실행은 다를 수 있고, 한 divergent vote가 확정 범위를 제한할 수 있다.
- Plan은 변경 가능한 예고이므로 잘못된 예고·잦은 변경은 비용을 늘린다.
- 고정 interleaving 아래 선택 자유도가 작으면 planning 이득도 작을 수 있다. 임의 재배열이 꼭 필요하다면 범위를 다시 결정해야 한다.
- 정상 leader의 기존 수렴이나 단순 early proposal보다 이점이 없을 수 있다. 추가 plan 전파 비용 때문에 더 느려지는 조건도 보고한다.
- 입력 가용성, 후보 선택의 검열·fairness, 자원 격리와 speculation 상한은 별도 검증 대상이다.
- Commonware는 가능한 artifact stack일 뿐 Hermes 구현과 호환 adapter가 준비되었다는 뜻이 아니다.

## 8. Conclusion

**실행을 앞당긴다 → 후보 불일치가 복구 비용을 만든다 → 사전 ordering plan으로 실행 방향을 미리 공유한다 → 실제 consensus 후보와 일관되게 연결한다 → Hermes가 확정한 prefix에 결과를 검증한다 → E2E latency 순이득을 평가한다.**

첫 검증은 “Hermes가 허용하는 후보 선택 자유도 안에 실제로 유용한 planning 기회가 있는가?”다. 다음은 adapter 정확성과 H1/H2의 분리 측정이다. 새 quorum·placement·새 VM을 추가하기 전에 이 좁은 가설의 성립 여부를 확인한다.
