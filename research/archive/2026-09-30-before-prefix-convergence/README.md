# Overpass: Advance Ordering Plans for State Finalization

현재 기준은 [논문 개요](overpass-plan-ordering-outline.md)와 [논리 전개](overpass-research-logic.md)이다. 2026-09-29 사용자 정정: **Hermes를 채택한 설계가 아니다.**

## 현재 방향

Autobahn-family의 parallel dissemination과 cut consensus를 배경으로 사전 ordering plan과 speculative execution을 병렬로 진행한다. Cut에서는 **수용된 plan과 tips를 함께 사용해 최종 순서를 결정**하여 늦은 block 삽입에 따른 재실행과 state-finalization latency를 줄이고자 한다.

- Leader는 알려진 blocks/tips, 유효 parent와 ordering rule을 바탕으로 plan을 제안한다.
- 실행 이력·진척·완료 보고나 execution proof를 plan의 입력으로 사용하지 않는다.
- Plan은 단순 실행 hint로 한정하지 않는다. 수용 조건과 최종 cut의 보존 의무는 합의 설계의 일부다.
- Plan이 다루지 않는 나머지 blocks는 공통 canonical ordering rule을 따른다. Plan과 기본 순서의 deterministic 결합 규칙을 정의해야 한다.
- Block 생성·전파와 speculative execution은 계속 진행한다. Cut까지 non-blocking으로 보장하려면 미완료 plan의 종료·복구 규칙이 필요하다.
- 최종 cut·canonical parent·runtime에 실행을 재검증하고 필요한 부분을 재실행한다.
- Hermes는 참고 연구다. Hermes의 quorum·fixed interleaving·finalization 규칙을 자동 적용하지 않는다.

Plan 수용 quorum, 상충 plan 투표 방지, cut 종료 경계, 늦은 plan, leader 교체 시 보존과 E2E 성능은 미검증이다. 이전 3f+1 plan 인증이나 무조건적인 마지막 plan 완료 대기를 확정 규칙으로 복원하지 않는다.

## 자료 상태

| 자료 | 상태 |
|---|---|
| [연구 개요](overpass-plan-ordering-outline.md) | 현재 source of truth; 8개 논문 section과 검증 과제 |
| [논리 전개](overpass-research-logic.md) | 문제 → pipeline → plan 수용 → plan+tips로 cut → 평가 |
| [Hermes-advisory 정정 전 보관본](research/archive/2026-09-29-hermes-advisory/INDEX.md) | Hermes 채택·단순 hint로 잘못 한정한 개요 |
| [실행 이력 기반 archive](research/archive/2026-09-29-execution-history-plan/INDEX.md) | 실행 보고·공통 실행 조각을 이용하던 이전 개요 |
| [Binding-plan archive](research/archive/2026-09-29-binding-plan/INDEX.md) | 이전 quorum·마지막 plan 대기 모델; 자동 복원하지 않음 |
| [Placement archive](research/archive/2026-09-29-before-plan-ordering/README.md) | 이전 producer placement·분석 자료 |
| [이전 outline](paper-outline.md) / [영문 manuscript](research/paper/README.md) | Reference-only; 현재 설계 미반영 |
| research/precut_order/ 및 commonware/ | 기존 toy models·fork; 새 설계 구현·검증 결과 아님 |

이번 갱신은 로컬 문서에 한정한다. Commonware·LaTeX/PDF·Google Docs는 변경하지 않았다.
