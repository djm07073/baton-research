# Overpass: Execution-Aware Ordering for Autobahn-Family Consensus

## 이 저장소의 범위

2026-09-30의 연구 문서 snapshot이다. 최신 설계는 아래 source of truth를 따르며, **현재 Overpass의 구현·안전성 증명·E2E 성능 검증이 완료된 저장소는 아니다.**

- 시작점: [논문 개요](overpass-plan-ordering-outline.md), [설계 정책](overpass-prefix-plan.md), [논리 전개](overpass-research-logic.md).
- 검토 결과: [요약 및 남은 과제](overpass-review-next-decisions.md), [상세 검토](overpass-submission-readiness-review.md).
- `research/archive/`, 이전 설계 문서, `research/paper/`와 toy models는 연구 이력이다. 현재 설계의 구현이나 실험 결과로 해석하지 않는다.
- Commonware 및 다른 외부 코드 checkout, build outputs, 임시 파일, 원본 저장소의 Git history는 포함하지 않는다. 기존 작업 저장소는 별도로 유지한다.
- Commonware 검토 기준 commit: [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72). 로컬 checkout에는 미커밋 변경도 있었으며, 그 변경은 이 문서 snapshot에 포함하지 않는다. 문서 속 로컬 경로나 미포함 코드 참조는 당시 작업 환경의 참조다.
- Google Docs는 이 snapshot과 별개이며 자동 동기화되지 않는다.

현재 기준은 [논문 개요](overpass-plan-ordering-outline.md), [논리 전개](overpass-research-logic.md), [plan 선택·수집 정책](overpass-prefix-plan.md)이다. 2026-09-30 최신 결정. Hermes는 참고 연구이며 채택한 합의 엔진이 아니다.

## 현재 방향

**기반 경로 결정: Native Multimmit을 유지한다.** 기존 tip 추출·extension을 제거하지 않고 plan과의 결합을 검토한다. Historical fixed-cut 변형은 재채택하지 않는다. Native membership finality와 plan에 따른 exact execution order를 안전하게 연결하는 방법은 아직 검증 과제다. 이 결정은 로컬 문서에 기록했으며 Google Docs·코드는 이번에 변경하지 않았다.

**Overpass는 새로운 consensus safety protocol이 아니라 Autobahn-family consensus를 위한 execution-aware ordering extension이다.** Validator들의 intended order를 이용해 speculative execution을 보존하기 유리한 ordering 후보를 선택한다. 이 조율은 별도 plan 승인 단계를 요구하지 않고 기존 cut consensus를 기다리게 하지 않으면서 state-finalization latency를 줄이는 것을 목표로 한다.

핵심은 분산된 intended order를 ordering 후보 선택에 반영하는 것이다. Dissemination·cut consensus와 speculative execution을 겹치고, leader는 **보고들과 공통 prefix 길이 합이 큰 유효 후보**를 전파한다. LCP score와 bounded collection은 이 확장을 구현하는 메커니즘이다. 최종 ordering은 기존 cut에서 확정하며, exact-order binding의 안전한 통합과 성능 이득은 검증 대상이다.

- 같은 기준 cut·canonical parent·view·수집 window의 보고만 사용하고 identity당 하나를 계수한다.
- n=5f+1에서 **보고 4f+1개 또는 고정 local deadline 중 먼저 도달한 때** 계산·필요 시 전파한다.
- 4f+1은 관측 수집 목표이지 동일 plan 지지나 safety/finality quorum이 아니다.
- 새 보고로 deadline을 연장하지 않는다. Deadline에 보고가 적거나 없어도 진행한다.
- Cut은 수집·timer·계산 완료를 기다리지 않고 준비된 최신 후보 또는 유효한 기본 ordering을 사용한다.
- Score(P)=Σ|LCP(P,R_i)|. 중간 조각은 점수로 세지 않으며 현재 후보와 새 후보는 같은 snapshot에서 비교한다.
- 동점이면 incumbent 유지, 의미 있는 개선에서만 재정렬, 무변화 전파 생략으로 churn을 억제한다.
- 예정 순서는 실행 이력·완료 proof가 아니다. Score는 실제 재실행 비용의 proxy다.
- 인증된 문맥과 공통 규칙에서 exact order를 도출하고, 그 input·parent·runtime에 실행을 검증한다. Native leader finality와 해당 입력의 global ordering 완료는 구분한다.
- 선택한 ordering policy는 leader block의 인증 대상에 결속하고 같은 proposal에서 고정한다. 별도 plan 승인 round는 추가하지 않는다.
- State finalization은 exact ordering finality와 동일 input·canonical parent·runtime·결과에 대한 해당 epoch validator f+1명의 유효한 일치 실행 서명이 모두 검증된 상태다. Durable/read readiness는 별도로 측정한다. [채택 조건](overpass-prefix-plan.md#72-policy-binding과-state-finalization의-채택-조건)
- 이전 3f+1 공통 prefix 인증·조정 후 support 수집 경로는 보관한다. 계획에 영구 lock을 부여하지 않는다.

Report/window 형식·bounds·가용성·stale 계산 처리·leader 변경·exact-order 합의 통합과 E2E 이득은 검증 과제다. Producer placement, state-owner sharding, ZK/PAC와 repair lane은 복원하지 않는다.

## 자료 상태

| 자료 | 상태 |
|---|---|
| [연구 개요](overpass-plan-ordering-outline.md) | 현재 source of truth; 8개 논문 section |
| [Plan 결정 기록](overpass-prefix-plan.md) | LCP score, 4f+1-or-deadline, no-wait cut 정책 |
| [논리 전개](overpass-research-logic.md) | 문제 → pipeline → report/score → plan → cut/state |
| [점수 기반 설계 전 보관본](research/archive/2026-09-30-before-scored-plan/INDEX.md) | 3f+1 discovery/adjustment support 모델 |
| [Prefix 설계 전 보관본](research/archive/2026-09-30-before-prefix-convergence/INDEX.md) | 그 이전 개요 |
| [Hermes-advisory 보관본](research/archive/2026-09-29-hermes-advisory/INDEX.md) | Hermes 채택으로 잘못 한정했던 개요 |
| [실행 이력 기반 archive](research/archive/2026-09-29-execution-history-plan/INDEX.md) | 실행 보고 기반 이전 방향 |
| [Binding-plan archive](research/archive/2026-09-29-binding-plan/INDEX.md) | 불변 plan·마지막 plan 대기 모델 |
| [Placement archive](research/archive/2026-09-29-before-plan-ordering/README.md) | 과거 placement 자료 |
| [이전 outline](paper-outline.md) / [영문 manuscript](research/paper/README.md) | 현재 설계 미반영 |
| research/precut_order/ 및 commonware/ | 기존 toy models·fork; 새 설계의 구현·검증 결과 아님 |

이전 positioning 갱신 대상에는 [Google Docs 한국어 리뷰 초안](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit)이 포함됐다. 이후 Native 결합 검토와 지표·비교군 정리는 로컬 문서에만 반영했다. 현재 Google Docs 전체가 로컬 최신본과 같다고 주장하지 않는다. Commonware·영문 manuscript·LaTeX/PDF는 변경하지 않았다.
