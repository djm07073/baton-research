# Baton: Execution-Aware Ordering for Autobahn

Baton은 Autobahn-family consensus에서 분산 intended order를 cut 구성에 반영해 speculative execution을 보존하고 state-finalization latency를 줄이려는 연구다. 저장소 이름 `overpass-research`와 과거 Overpass 자료의 이름·URL은 유지한다.

## 현재 문서와 기준

2026-09-30 Google Docs의 최신 연구 내용을 수동 동기화했다. **구현, native 통합 증명, E2E 성능 결과는 없다.** 논문 설명과 상세 구현 계약을 분리하며 과학적으로 필수인 prefix 보존 조건은 논문에도 남긴다.

| 목적 | 저장소 문서 | 편집 원문 |
|---|---|---|
| 문제·메커니즘·조건부 논증·향후 평가·한계 | [Baton 논문 초안](baton-paper.md), 기존 8개 절 | [Google Doc](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) |
| Context·snapshot·frontier·candidate completion·slot/recovery·서명·retention·미채택 선택 | [Baton 구현 스펙](baton-implementation-spec.md) | [Google Doc](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) |
| 이어받기·미완성 증명·동기화와 검증 범위 | [BATON_HANDOFF.md](BATON_HANDOFF.md) | — |

최신 사용자 결정과 Google Docs가 개념상의 기준이다. Markdown은 이번 revision의 검증된 counterpart이며 자동 양방향 동기화하지 않는다. 새 편집 전 양쪽 변경을 확인한다. [AGENTS.md](AGENTS.md)는 현재 작업 지침이다. 과거 문서의 “current/latest/source of truth”는 아래 역사적 snapshot 내부의 표현이다.

## 채택한 요구와 미완성 연결

- 기반은 Native Multimmit, `n=5f+1`이다. Tip extraction·extension을 보존하며 direction-preserving cut에 연결하는 구체 adaptation은 미구현·미증명이다.
- 같은 문맥의 bounded 유효 full candidates를 평가한 뒤, `2f+1` distinct original reports가 **전체를 연속으로 지지하는 최장 유효 nonempty prefix**를 우선한다. 없으면 sum-LCP, reports/준비된 유효 후보가 없으면 actual-parent의 유효 기본 policy를 사용한다. 모든 permutation에 대한 전역 최장을 주장하지 않는다.
- Report snapshot은 첫 `4f+1` admission 또는 고정 deadline에서 한 번 닫는다. `m≤4f+1`이며 초과·후속 reports는 제외한다. Cut은 report·timer·optimizer 완료를 기다리지 않는다.
- **Leader가 선택 유효 prefix를 포함하고 정확한 선두 실행 순서로 보존하는 cut proposal을 구성하고 validator가 검증해야 한다.** 같은 canonical input state·runtime과 불변 frontier 뒤에서 `p ⪯ O`가 요구된다. Membership만 일치하거나 중간에 다른 block이 끼는 것으로는 충분하지 않다.
- 선택 prefix·policy는 실제 proposal parent와 인증 subject에 결속해 proposal 안에서 고정한다. Proposal 전 advisory direction 수정과 인증 뒤 재해석은 구분한다.
- Report support는 intention이다. 실행 완료·native inclusion certificate가 아니며 실제 재사용은 같은 canonical 문맥의 실행·dependency 검증·checkpoint 조건에 의존한다.
- Primary completion은 대상 구간의 irrevocable exact order와 동일 input/range·canonical input state·runtime·result에 대한 해당 epoch의 distinct validators `f+1` matching execution signatures를 모두 검증한 사건이다. Durable/read readiness는 별도다.

Prefix를 보장 대상으로 채택하는 availability/adoption 조건, exact cross-lane continuation, terminal-state 근거와 view recovery, no-wait와의 양립은 아직 닫히지 않았다. 이미 준비된 DA-certified anchors는 inclusion 연결 후보이며 완성된 해법이 아니다. **Per-block signing, incumbent-first tail, inline policy, finite-prefix permutation은 모두 권고/대안이며 미채택이다.**

## 소스와 검증 경계

Pinned Commonware: [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72). Finalized proposal position은 `3f+1`번째로 **큰** position이다. Certified anchor의 ancestor는 낮은 position만으로 제외할 수 없다. 구체 조건·분석적 transcript·소스 링크는 [구현 스펙 §5](baton-implementation-spec.md#5-proposal-결속과-exact-prefix-보존)에 둔다.

이번 동기화는 문서만 변경했다. Native source 실행, protocol 구현, toy 테스트 재실행, compilation, benchmark를 수행하지 않았다. 기존 toy/LaTeX 자료를 Baton의 검증 결과로 취급하지 않는다.

## 보존한 연구 이력

- [과거 outline](overpass-plan-ordering-outline.md), [design memo](overpass-prefix-plan.md), [research logic](overpass-research-logic.md): sum-only/plan 시기의 snapshot. 현재 선택·보존 요구를 대신하지 않는다.
- [Submission-readiness review](overpass-submission-readiness-review.md), [당시 next decisions](overpass-review-next-decisions.md): 조건부 논증·반례와 당시 미정 항목을 보존한 인용 자료다.
- [Draft PR1: native 검증 명세와 E2E 계획](https://github.com/djm07073/overpass-research/pull/1): P/Q/P+ fixture, unresolved-slot negative mutation, endpoint/E2E gates는 유용한 검증 방향이다. 최신 selected-prefix 보존 gate와 연결해야 하며 이 동기화는 PR을 merge/close하지 않는다.
- [점수 기반 설계 전 archive](research/archive/2026-09-30-before-scored-plan/INDEX.md), [prefix 설계 전 archive](research/archive/2026-09-30-before-prefix-convergence/INDEX.md), [Hermes-advisory archive](research/archive/2026-09-29-hermes-advisory/INDEX.md), [실행 이력 archive](research/archive/2026-09-29-execution-history-plan/INDEX.md), [binding-plan archive](research/archive/2026-09-29-binding-plan/INDEX.md), [placement archive](research/archive/2026-09-29-before-plan-ordering/README.md).
- [이전 session handoff](SESSION_HANDOFF.md), [이전 paper outline](paper-outline.md), [영문 manuscript/LaTeX](research/paper/README.md), 기존 toy models와 외부 checkout 참조는 과거 작업의 이력이다. 외부 Commonware checkout은 이 저장소에 포함되지 않는다.
- 동기화 전 README/AGENTS의 원본은 [기준 commit `80e09a82`](https://github.com/djm07073/overpass-research/tree/80e09a82d9c717d6c5eed47189b87bfe7ce81f19)에 보존된다.
