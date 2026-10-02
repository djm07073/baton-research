> **Historical snapshot — superseded by Baton (2026-09-30).**
> Current research: [Baton paper](baton-paper.md), [implementation specification](IMPLEMENTATION_SPEC.md), and [current handoff](BATON_HANDOFF.md).
> The body below is preserved as research/citation history. Its sum-only selection, plan/advisory descriptions, incumbent preferences and “current/latest/source of truth” claims do not override 2f+1-prefix-first selection or the adopted direction-preserving cut requirement. The four proposed implementation defaults remain unadopted; native integration and performance remain unproved.

# Overpass: 논리 전개와 주장 경계

> 2026-09-30 최신 결정. [연구 개요](overpass-plan-ordering-outline.md) / [점수 기반 plan·수집 정책](overpass-prefix-plan.md). 구현·증명·평가 완료가 아니다.

## 한 문장

**Overpass는 Autobahn-family consensus를 위한 execution-aware ordering extension이다. Validator들의 intended order를 이용해 speculative execution을 보존하기 유리한 ordering 후보를 선택하며, 별도 plan 승인 단계나 기존 cut consensus의 대기 없이 state-finalization latency를 줄이는 것을 목표로 한다.**

## 연구 positioning과 변경 경계

- 기반 구현은 Native Multimmit을 유지한다. 기존 tip 추출·extension과 plan을 결합하며, 과거 fixed-cut 변형은 재채택하지 않는다. Membership 결정과 실행 순서 결정을 구분하고, native ordered-delivery 경계를 보존하는 통합을 검토한다.
- 새로운 consensus safety protocol이나 execution engine을 제안하는 것이 아니다. 분산된 intended order를 ordering 후보 선택에 반영하는 것이 중심 설계다.
- 정해진 순서를 실행기가 미리 따라가기만 하는 것이 아니라, finality 전에 유효한 ordering 후보 중 어느 것을 제안할지 조율한다. Intended order는 실행 이력·완료 proof가 아니다.
- LCP score, 4f+1-or-deadline, 변경 억제는 이 조율을 구현하는 메커니즘이며 각각 독립적인 novelty 주장으로 나열하지 않는다.
- Proposal 이전 advisory plan은 mutable하다. 선택한 ordering policy는 leader block 인증 대상에 결속하고 같은 proposal에서 고정하는 방식을 채택했다. Native ordered delivery 및 voting·lock·leader recovery의 안전성을 보존하는 통합은 별도로 입증해야 한다.
- State finalization은 exact ordering finality와 동일 input·canonical parent·runtime·결과에 대한 해당 epoch validator f+1명의 유효 일치 실행 서명으로 정의한다. Durable/read readiness는 보조 지표이며 결과 인증과 구분한다.
- No-wait는 plan 준비를 cut의 선행조건으로 만들지 않는다는 뜻이다. 실제 자원 경쟁까지 비용이 없다는 뜻은 아니며 latency 개선은 평가할 가설이다.

## 논리 전개

| 단계 | 논리 |
|---|---|
| 목적 | Ordering 이후 남는 application state-finalization 지연을 줄인다 |
| Pipeline | Dissemination·cut consensus와 speculative execution을 겹친다 |
| 후속 문제 | Late predecessor·후보 변경으로 실행이 무효화된다 |
| Leader-local 반례 | Leader에게만 X가 늦으면 leader 순서 유지가 다수의 실행을 뒤집을 수 있다 |
| 관측 공유 | 같은 cut·parent의 예정 순서 보고를 비동기로 모은다 |
| 선택 | Intended order를 ordering 후보 선택에 반영한다. LCP 길이 합을 재사용 가능성의 proxy로 사용한다 |
| 전파 시점 | 4f+1 보고 또는 local deadline 중 먼저 도달한 때 계산·필요 시 전파한다 |
| 실행 | 추가 support를 기다리지 않고 plan에 맞춰 scheduling·검증·재실행한다 |
| 확정 | Native 인증 자료와 공통 규칙으로 irrevocable ordered prefix를 도출하고 그 exact 문맥에서 실행을 검증한다 |
| State finalization | 위 finality와 f+1 일치 실행 서명의 유효성·parent 연결을 모두 확인한다 |
| 평가 | 절약한 실행 비용과 수집·계산·통신·후보 변경 비용의 E2E 순효과를 측정한다 |

## 흐름

```text
같은 문맥의 예정 순서 보고
              ↓
     4f+1 확보 OR deadline
              ↓
LCP 합 점수로 유효 후보 선택·전파
              ↓
    실행 방향 조정 (추가 투표 없음)
              ↓
   Native 인증 자료 + ordered-delivery 규칙
              ↓
   해당 입력의 irrevocable ordering 도출
              ↓
      exact-context 실행 검증
              ↓
  Ordering evidence + f+1 실행 서명 검증
              ↓
       State finalization

수집·계산보다 cut이 먼저 준비되면:
  이미 준비된 후보 / 기본 rule로 진행; 기다리지 않음
```

## 이번에 대체한 주장

- 3f+1 공통 prefix를 반드시 발견하거나 조정 후 3f+1 support를 만드는 모델은 보관한다.
- 4f+1은 서로 다른 보고의 수집 목표이며 동일 plan 지지·순서 확정·실행 인증이 아니다.
- 높은 LCP 점수는 예정 순서 보존 proxy이지 실제 재실행 최소화 증명이 아니다.
- Plan은 영구 lock이 아니며 leader 교체·최종 후보 변경으로 실행을 보정할 수 있다.
- Hermes는 참고 연구이며 채택한 합의 엔진이 아니다.

## 수집과 갱신 정책

첫 미반영 실행 가능 block에서 t0를 정하고 고정 duration τ의 local deadline을 둔다. 새 보고가 와도 deadline을 연장하지 않는다. 같은 window에서 identity당 하나만 계수하고 다른 cut·parent·view를 섞지 않는다.

Deadline에서 보고가 부족하면 확보한 snapshot만 사용한다. 보고가 없으면 incumbent 또는 기본 rule을 사용한다. Cut은 report 수, timer 또는 계산 완료를 기다리지 않는다.

Incumbent와 새 후보는 같은 snapshot으로 비교한다. 동점이면 incumbent를 유지하고, 재정렬에는 개선 폭을 요구한다. 무변화 재전파를 생략하고 갱신 빈도를 제한한다. τ와 개선 폭·window 길이는 실험으로 정한다.

## 논문 주장

- H1: 실행 조정을 finality 이전에 처리해 post-cut 잔여 작업을 줄인다.
- H2: 여러 노드의 예정 순서를 반영하고 불필요한 후보 변경을 억제해 총 invalidation을 줄인다.
- 두 성능 가설은 정상 leader·workload·network 조건에 의존하며 보장된 결과가 아니다.
- Safety는 점수가 아니라 실제 finalized order·parent·runtime의 실행 검증 및 합의 통합에서 확보해야 한다.
- Byzantine 보고·leader는 heuristic 품질을 낮출 수 있다. Report 수집 목표를 성능 공격 방지 보장으로 사용하지 않는다.

## 작은 cut과의 차이

새 plan마다 합의하지 않는다. Report 수집과 후보 전파만 추가하고 finality는 기존 합의 경로에 남긴다. 추가 비용까지 포함해 Original / Pre-cut execution / Overpass를 비교한다. Frequent cuts는 별도 민감도 실험이며 early proposal을 Pre-cut execution과 동일시하지 않는다.

## 논문 positioning

> Overpass is an execution-aware ordering extension for Autobahn-family consensus, rather than a new consensus safety protocol. It uses validators' intended orders to select ordering candidates favorable to preserving speculative execution. This coordination requires no additional plan-approval phase and does not make existing cut consensus wait, aiming to reduce state-finalization latency.

이를 구현하기 위해 bounded candidate set에서 aggregate common-prefix score로 후보를 선택한다. 계산은 4f+1 보고 또는 local deadline 중 먼저 도달한 때 시작하며, cut이 먼저 준비되면 이미 준비된 유효 후보 또는 기본 rule로 진행한다. 기존 cut 합의가 최종 순서를 인증한다.
