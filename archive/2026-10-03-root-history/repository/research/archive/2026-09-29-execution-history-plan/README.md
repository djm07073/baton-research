# Overpass: Execution-Aware Planning for State Finalization

현재 기준은 [논문 개요](overpass-plan-ordering-outline.md)와 [논리 전개 요약](overpass-research-logic.md)이다. 2026-09-29 Hermes 문헌 검토와 사용자 논의를 반영했다.

## 현재 방향

Dissemination·ordering consensus와 speculative execution을 중첩한다. 실행 이력의 공통 순서 조각과 진척을 참고하는 advisory plan으로 유효 후보와 실행을 조기에 수렴시켜 state-finalization latency를 줄이고자 한다.

- Plan은 별도의 순서 합의나 execution certificate가 아니다.
- Hermes가 실제 ordering prefix를 확정한다. Plan은 기존 parent·proposal·vote 규칙을 우회하지 않는다.
- 공통 조각을 선호하고 나머지는 canonical rule을 따르되, Hermes에서 유효하게 표현할 수 있는 후보에 한정한다.
- Plan 수집·완료를 production·execution·consensus의 대기 조건으로 두지 않는다.
- 결과는 실제 finalized prefix·parent·runtime에서 재검증한다.
- 보정을 finality 이전으로 옮기는 효과와 총 재실행량 감소를 별도로 평가한다.

Fragment 선택 정책, 실제 통합 hook, liveness·inclusion 영향과 E2E 성능은 미검증이다. Hermes는 초기 reference protocol이며 Commonware fork에 이미 구현되었다고 가정하지 않는다.

## 자료 상태

| 자료 | 상태 |
|---|---|
| [연구 개요](overpass-plan-ordering-outline.md) | 현재 source of truth; 8개 논문 section과 검증 과제 |
| [논리 전개](overpass-research-logic.md) | 문제 → pipeline → 불일치 → plan → Hermes finality → 평가 |
| [Binding-plan archive](research/archive/2026-09-29-binding-plan/INDEX.md) | 이전 별도 quorum·마지막 plan 완료 대기·fixed-cut 모델 |
| [Placement archive](research/archive/2026-09-29-before-plan-ordering/README.md) | 이전 producer placement·문서·분석 코드 |
| [이전 탐색](overpass-progressive-ordering.md) / [이전 outline](paper-outline.md) | Reference-only |
| [영문 manuscript](research/paper/README.md) | 기존 LaTeX/PDF; 현재 설계 미반영 |
| [Placement 코드](research/placement/README.md) | 보존; 현재 설계에 포함하지 않음 |
| research/precut_order/ | 이전 toy models; Hermes 통합 검증이 아님 |
| commonware/ | 기존 fork; 새 planning 설계 미구현 |

파일·코드는 삭제하지 않고 이력을 보존한다. 이번 갱신은 로컬 문서에 한정되며 Commonware·LaTeX/PDF·Google Docs는 변경하지 않았다.
