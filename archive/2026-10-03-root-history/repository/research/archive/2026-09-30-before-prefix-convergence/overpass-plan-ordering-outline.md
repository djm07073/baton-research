# Overpass: Advance Ordering Plans for Pipelined State Finalization

> 2026-09-29 사용자 정정: **Hermes를 기본 합의 엔진으로 채택한 설계가 아니다.** 아래는 연구 개요이며 protocol 구현·증명·성능 검증 완료를 뜻하지 않는다.
> [논리 전개](overpass-research-logic.md) / [Hermes-advisory 정정 전 보관본](research/archive/2026-09-29-hermes-advisory/INDEX.md)

## 핵심 주장과 범위

**Overpass는 block dissemination·cut consensus와 execution을 pipeline화하고, cut 전에 사전 ordering plan으로 실행 순서를 조율하며, 수용된 plans와 producer tips를 함께 사용해 최종 cut의 순서를 결정한다. 목표는 늦은 block 삽입으로 발생하는 speculative-work invalidation과 state-finalization latency를 줄이는 것이다.**

Plan은 알려진 exact block references·tips, 유효 parent와 공통 ordering rule에서 구성한다. 원격 실행 이력·진척·완료 보고·재사용량 주장이나 execution proof는 plan 생성·선택의 입력으로 사용하지 않는다. 내부 실행 검증과 offline benchmark 계측은 유지한다. 실행 증명이 원리적으로 불가능하다는 주장이 아니라 연구 범위의 선택이다.

**Plan은 단순 scheduling hint로 한정하지 않는다.** 무엇을 수용하고 최종 cut이 어떤 순서 관계를 보존해야 하는지는 제안 protocol의 일부다. 다만 plan 수신 자체가 ordering finality나 state finality는 아니다. 수용 quorum과 보존 규칙은 아직 확정되지 않았다.

### 직전 개요의 정정

| 잘못 좁힌 설명 | 현재 방향 |
|---|---|
| Hermes를 초기 reference consensus로 채택 | Autobahn-family 기반 확장 연구; Hermes는 참고 연구 |
| Plan은 실행 hint이고 실제 ordering에는 별도 보존 의무 없음 | 수용된 plans와 tips가 최종 순서 결정의 입력 |
| 별도 plan 수용/quorum이 없다고 확정 | 수용 조건·quorum·상충 방지·보존 규칙을 설계해야 함 |
| Hermes의 fixed interleaving과 prefix 추출 안에서만 최적화 | 자체 plan–cut 결합 규칙을 정의하고 안전성·진행성을 검증 |
| Advisory이므로 기존 합의 안전성을 그대로 상속 | Ordering validity를 바꾸므로 recovery까지 포함한 통합 논증 필요 |

이 정정으로 이전 3f+1 plan certificate, 마지막 plan 무조건 완료 대기, 실행 이력 optimizer를 자동 복원하지 않는다. Producer placement/Multilevel, state-owner sharding, ZK/PAC, receipt bridge와 repair lane도 제외한다. Commonware는 가능한 artifact stack이며 현재 모델은 미구현이다.

## 1. Introduction

### 문제 → pipeline → 후속 비용

Autobahn-family의 parallel dissemination과 cut agreement를 출발점으로 설명한다. 빠른 ordering만으로 application state가 준비되지는 않는다. Cut 이후 실행하는 구성에서는 실행 비용이 노출되므로, block 수신·sync·consensus와 execution을 겹치는 것이 첫 접근이다.

그런데 늦은 선행 block이나 후보 변경이 이미 수행한 실행을 무효화할 수 있다. 이 재실행 비용이 pipeline의 이득을 상쇄할 수 있다는 후속 문제를 제시한다. 기존 연구가 execution을 전혀 다루지 않았다고 단정하지 않는다.

### 제안과 기여 후보

Leader는 알려진 ordering 입력에서 사전 plan을 계속 제안하고 replicas는 실행 방향을 조정한다. 최종 cut은 tips뿐 아니라 protocol상 수용된 plan을 반영한다. 단순 예상 공지를 넘어, 미리 조율한 순서가 최종 결정으로 이어지게 하는 것이 설계 대상이다.

- Advance ordering plans: 실행 보고 없이 순서를 조율하고 수용된 plan을 cut에 연결하는 protocol.
- Pipelined state finalization: production·dissemination·planning·execution을 겹치고 exact final order에 실행을 재사용·보정.
- Correctness와 평가: plan 수용·보존·종료·복구 규칙의 안전성 및 추가 비용을 포함한 latency 효과.

모두 기여 후보이며 최초성·성능 우월성은 미검증이다. 연구 질문은 “사전 순서 조율을 최종 cut에 반영하면서 production과 execution을 지속하고, cut liveness를 해치지 않으며 state-finalization latency를 줄일 수 있는가?”다.

## 2. Background and Motivation

### 2.1 Autobahn-family ordering과 실행의 경계

Producer lane은 block 생성 chain이고 validator는 consensus·실행 참여자다. Lane을 독점 state owner로 정의하지 않는다. DA, ordering finality, 실행 결과 인증과 durable readiness를 구분한다. Cut vote는 모든 voter가 같은 body·실행 완료 상태를 보유한다는 증거가 아니다.

기반 protocol의 전체 finality 절차를 생략하지 않는다. 구체적인 Autobahn 또는 Commonware/Multimmit profile과 quorum은 구현 선택 및 별도 안전성 검토 대상이다. [Autobahn 논문](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

### 2.2 늦은 insertion이 만드는 낭비

기본 ordering에서는 X가 A보다 앞이지만 X가 늦게 도착하면 먼저 실행한 A→B를 수정해야 할 수 있다. 사전 plan으로 A→B를 조율하고 최종 cut이 그 plan의 정해진 보존 범위를 지키게 만들면 이런 낭비를 줄일 여지가 있다.

단, A가 X의 필수 ancestry/dependency 뒤에 와야 하는 경우에는 plan으로 뒤집을 수 없다. 또한 A→B의 상대 순서만 보존해도 X→A→B 또는 A→X→B를 허용하면 입력이 바뀔 수 있다. **순서 관계 보존과 실행 결과 재사용을 같은 보장으로 취급하지 않는다.**

### 2.3 별도로 검증할 두 효과

- H1: 필요한 재검증·재실행을 finality 이전으로 옮겨 post-cut 잔여 시간을 줄인다.
- H2: 수용된 순서가 최종 순서로 이어져 잘못된 speculative execution 자체를 줄인다.

H1은 총 작업량이 줄지 않아도 가능하다. H2는 plan 안정성·보존 범위·실제 workload에 의존한다. Plan churn과 통신 비용 때문에 역효과가 날 수 있다.

Figure 1은 post-cut execution / unguided speculation / plan을 반영한 speculation의 시간선을 비교한다.

## 3. System Design

### 3.1 역할과 병렬 진행

고정 validator 위원회, bounded Byzantine faults, 인증 메시지, deterministic application과 eventual synchrony를 전제로 한다. STM은 평가 backend 선택이지 연구 기여가 아니다.

- Producer: block 생성·전파를 계속한다.
- Leader: 알려진 입력으로 사전 plan을 제안하고, cut 시점에는 plans와 tips를 반영한 최종 순서를 제안한다.
- Validator: block sync·검증, plan 검증·수용 절차, speculative execution·재검증, cut consensus에 참여한다.

실행 완료를 DA ACK나 ordering vote의 조건으로 두지 않는다. Planning은 실행과 병렬로 진행한다. **Production/실행의 지속과 cut consensus의 non-blocking liveness는 별도 성질**이며 후자는 아래 종료·복구 규칙으로 입증해야 한다.

### 3.2 사전 plan의 구성과 수용

Plan에는 epoch/view, canonical parent 문맥, exact block references, rule version, plan 식별자와 앞선 plan과의 관계가 필요하다. 정확한 encoding과 갱신 정책은 미정이다. Tip 광고나 leader 서명만으로 데이터 가용성·순서 수용·실행 성공을 인정하지 않는다.

흐름은 다음과 같다.

1. Leader가 알려진 blocks/tips·ancestry·가용성 자료와 ordering rule로 plan을 구성한다.
2. Replica가 문맥·입력·순서 제약을 검사하고 plan 수용 절차에 참여한다. 원격 실행 이력 증명은 요구하지 않는다.
3. Replica는 block sync와 실행을 계속하며 plan에 맞춰 speculative order를 조정한다.
4. Protocol상 수용된 plan은 최종 cut이 반영해야 할 자료가 된다.

**미정:** 수용 threshold, 서명 대상, 상충 판정, 중복 투표 방지, plan의 확장/중첩과 증거 복구. 이전 대화의 3f+1을 검증 없이 채택하지 않는다. 단순 발신자 서명과 수용 증거를 구분한다.

### 3.3 Plan과 tips로 최종 cut 구성

최종 순서는 수용된 plan의 보존 의무, cut tips가 정한 입력 집합, producer ancestry와 기본 ordering rule을 함께 만족해야 한다. Plan이 다루지 않는 부분은 공통 canonical rule로 결정한다. Relative-height round-robin 하나로 한정하지 않는다.

최종 제안은 tips와 plan 참조/종료 경계 및 도출된 order를 함께 검증할 수 있도록 묶어야 한다. Tips만 인증한 cut에 plan을 나중에 덧붙이는 것으로는 부족하다.

예시의 목적은 다음과 같다.

```text
기본 순서:       X → A → B → Y
사전 plan:       [A → B]
최종 순서 후보:  [A → B] → canonical(X, Y)
```

위 후보는 plan이 해당 배치를 허용하고 ancestry·필수 dependency와 충돌하지 않을 때만 가능하다. “A→B 상대 순서”인지 “앞/사이 insertion 금지”인지가 미정인 상태에서 이 후보를 보장하지 않는다. 여러 plan의 관계를 합치면 cycle이 생기는 경우도 수용 단계에서 처리해야 한다.

Leader는 현재 plan 구간을 닫고 cut으로 넘어간다. 다만 다음 규칙이 필요하다.

- 어느 plan까지 그 cut이 반드시 보존해야 하는가?
- Cut proposal 이후 도착하거나 인증되는 plan은 어디에 귀속되는가?
- 미완료 plan을 종료·이월할 때 이미 생긴 보존 의무를 어떻게 확인하는가?
- 새 leader가 이전 수용 이력을 복구하고 같은 의무를 지키는가?
- Plan이 요구하는 block이 cut tip에 없거나 body를 못 구하면 어떻게 진행하는가?

“Leader가 진행하던 plan까지”라는 방향만으로는 경계가 결정되지 않는다. Local 수신 시각이나 일방적인 종료 선언에 의존하지 않는 protocol 규칙이 필요하다. 이전의 무조건적인 마지막 plan 완료 대기도 확정하지 않는다.

### 3.4 실행 조정과 state finalization

```text
block 생성·전파 ──────────────── 계속 ───────────────>
          │ 알려진 ordering 입력
          v
사전 plan 제안 → 검증·수용 ────> 수용된 plans + tips
          │                              │
          v                              v
sync·speculative execution        최종 순서 구성·cut 합의
          │                              │
          └───────────────> exact-cut/parent/runtime 검증
                                  재사용 / 재실행
                                         ↓
                                 state finalization
```

Plan 수신·수용만으로 canonical state를 채택하지 않는다. 최종 cut이 결정한 exact order와 canonical parent·runtime에 결과를 대조하고 관측이 달라진 부분을 재검증·재실행한다. 긴 speculative state root를 짧은 확정 입력의 결과로 잘라 쓰지 않는다. Prefix checkpoint 또는 필요한 recomputation이 있어야 한다.

기존에 논의한 f+1 matching execution signatures는 고정된 exact input에 대한 결과 인증 경로이지 plan 수용 quorum이 아니다. 채택할 경우 직접 실행/검증, signer 자격, binding·보관·복구 조건을 별도로 명시한다. 결과 인증 시각과 durable read readiness도 구분한다.

Figure 2는 위 pipeline을, Figure 3은 plan 보존·늦은 block·상충 plan·leader 교체 사례를 설명한다.

## 4. Correctness and Liveness

### 4.1 증명 의무

- Plan compatibility: 상충하는 보존 의무를 정직한 노드가 동시에 수용하지 않도록 한다.
- Cut preservation: cut이 의무적으로 포함해야 하는 수용된 plan을 누락·위반하지 않는다.
- Deterministic composition: 같은 tips·parent·plan 집합·종료 경계에서 같은 유효 order를 도출한다.
- Closure and recovery: 늦은 plan 및 leader 교체가 상충하는 최종 순서를 허용하지 않는다.
- Safe reuse: 최종 exact input에 대해 재사용한 결과가 deterministic reference execution과 같다.
- Conditional liveness: eventual synchrony와 정상 참여 조건에서 미완료·은닉·상충 plan 때문에 영구 정지하지 않는다.

단순 advisory adapter의 정확성만 증명하면 되는 상황이 아니다. Ordering validity와 recovery에 plan 제약을 추가하므로 기반 합의와의 통합 safety/liveness 논증이 필요하다.

### 4.2 Byzantine behavior

| 사례 | 필요한 대응·검증 |
|---|---|
| Leader가 상충 plan 전파 | 수용·투표 충돌 규칙 및 후속 cut의 유효성 검사 |
| 개별 plan은 acyclic이나 합치면 cycle | 누적 제약 검증, 수용 시점과 충돌 처리 명시 |
| 수용된 plan 은닉·cut에서 누락 | 증거 가용성, 종료 경계, 복구·의무 포함 검증 |
| Cut 진행 중 늦은 plan 인증 | 현재/다음 구간 귀속과 기존 의무 보존 규칙 |
| Leader 교체·stale plan 재전송 | epoch/view/parent binding과 수용 이력 복구 |
| 잘못된 blocks/tips·누락 body | digest·ancestry·가용성 검증과 데이터 복구 |
| Producer/leader 중단 | 다른 작업 지속과 cut 진행/포함 liveness를 별도 검증 |
| Plan flood·반복 변경·검열 | 메시지·계산·speculation 예산, fairness·starvation 평가 |

DA 인증은 application correctness나 상충 plan 방지를 자동 제공하지 않는다. 이 표는 완성된 방어가 아니라 검증 의무다.

## 5. Evaluation

### 5.1 비교군

같은 기반 consensus profile·application·실행 backend·자원·완료 조건을 고정한다.

| 비교군 | 검증 목적 |
|---|---|
| Post-cut execution | 노출된 실행 비용 |
| Pipeline만 적용, 기본 ordering 유지 | 사전 실행의 이득과 재실행 비용 |
| 같은 plan을 실행 hint로만 전달, cut에 보존 의무 없음 | 단순 조기 정보 효과 |
| 제안: plan 수용·보존을 cut에 연결 | 순서 조율의 추가 이득과 protocol 비용 |
| 유효해지는 즉시 정상 cut proposal 전파 | 단순 early proposal 대비 차이 |
| 더 잦은 cut + speculation | 작은 batch/짧은 실제 설정 가능 cadence 대비 차이 |

Hermes를 모든 비교군의 엔진으로 지정하지 않는다. Artifact의 기반 profile을 먼저 확정한다. 서로 다른 consensus 비교를 plan의 직접 ablation으로 대신하지 않는다.

### 5.2 지표와 검증 사례

- 최상위: ingress→state-finalization p50/p95/p99와 successful goodput.
- 분해: ordering-finality→state-finalization, ordering latency, durable readiness.
- H1: finality 이전/이후 재검증·재실행량과 잔여 critical path.
- H2: 총 실행 시도·CPU·메모리·network bytes와 재사용률.
- Plan: 수용/변경/무효율, 최종 순서 보존 범위, plan 때문에 추가된 cut 대기.
- Workload: RTT × application operation 수, conflict density, 늦은 선행 block, lane imbalance, offered load, parent 지연.
- Faults: 정상/지연/중단 leader, equivocation, 수용 증거 은닉, 늦은 plan, leader 교체.
- Controls: 같은 exact order의 trace replay로 재사용 메커니즘을 검사하고, 순서가 달라지는 E2E 비교는 application 성공률·fairness 변화도 함께 보고한다.

실행 이력 계측은 offline 분석용이며 plan 선택에 피드백하지 않는다. Open-loop 부하·backlog·미완료 요청과 plan 비용을 포함한다. Cut 자체를 늦춰 cut-to-state 간격만 줄이는 결과를 성공으로 보지 않는다.

작은 deterministic 안전성 사례부터 검증한다. 기존 toy tests나 Commonware fork의 결과를 이 새 모델의 E2E 증거로 인용하지 않는다.

## 6. Related Work

- **Autobahn:** parallel dissemination과 cut agreement의 배경. [SOSP 2024](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- **Hermes:** 서로 다른 투표에서 공통 prefix를 확정하는 참고 연구. 우리 plan 수용·보존 메커니즘과 구분하고, 기본 엔진으로 채택했다고 쓰지 않는다. [2026 preprint v2](https://arxiv.org/html/2607.25916v2)
- **HotStuff-1:** speculation과 prefix 안전성, 연속 proposal·leader 교체 비교. [논문](https://arxiv.org/html/2408.04728v3)
- **Rashnu:** local ordering 보고와 dependency graph 구성의 선행성. 실행 완료 증명과 구분한다. [PVLDB 2024](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)
- **Zyzzyva·ISOS:** speculation·dependency ordering의 선행 연구. 사전 실행 자체의 최초성을 주장하지 않는다. [ISOS](https://arxiv.org/abs/2109.06811)

차별성은 사전 순서 조율을 cut에 연결하는 구체 규칙과 state-finalization 성능에서 입증해야 한다. 기존 논문의 보장과 우리 설계 가설을 구별한다.

## 7. Discussion and Limitations

- 같은 plan/order라도 parent·관측값·데이터 보유·완료 시점은 다를 수 있다.
- 상대 순서 보존만으로 insertion과 재실행이 제거되지 않는다.
- 강한 plan 보존은 실행 낭비를 줄이는 대신 ordering 선택 자유도·포함 진행성을 제한할 수 있다.
- Plan 수용이 사실상 작은 합의라면 추가 quorum·round·복구 비용을 숨기지 않는다.
- Production이 계속되어도 cut 또는 state progress가 막힐 수 있다.
- 순서 변경의 MEV·fairness·검열과 Byzantine plan churn을 평가해야 한다.
- Quorum·closure·recovery가 정해지기 전에는 완성된 consensus나 무조건적인 non-blocking을 주장하지 않는다.
- Commonware 구현·LaTeX/PDF·Google Docs는 이번 문서화 범위에 포함하지 않는다.

## 8. Conclusion

**실행을 앞당긴다 → 늦은 삽입이 재실행을 만든다 → 사전 plan으로 순서를 조율한다 → 수용된 plan과 tips를 최종 cut에 반영한다 → exact-context 검증으로 state를 확정한다 → E2E 순이득을 평가한다.**

우선 과제는 Hermes hook 탐색이 아니라 **plan 수용·보존·종료 경계·leader 교체 규칙의 완성**이다. 그 다음 안전성 검증과 H1/H2를 분리한 성능 실험을 수행한다.
