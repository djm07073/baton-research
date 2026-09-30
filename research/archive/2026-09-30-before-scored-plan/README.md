# Overpass: Advance Ordering Plans for State Finalization

현재 기준은 [논문 개요](overpass-plan-ordering-outline.md), [논리 전개](overpass-research-logic.md), [공통 prefix와 조정 경로](overpass-prefix-plan.md)다. 2026-09-30 결정 반영. **Hermes는 참고 연구이며 채택한 기본 합의 엔진이 아니다.**

## 현재 방향

Autobahn-family parallel dissemination·cut consensus와 speculative execution을 겹친다. n=5f+1에서 같은 cut·canonical parent에 대해 validator들이 보고한 **예정 순서의 처음부터 일치하는 가장 긴 prefix**를 3f+1 지지로 찾는다. 지지가 없으면 leader가 유효한 조정안을 제안하여 노드들이 순서를 채택하고 support를 보내게 한다.

- 보고 3f+1개 도착과 동일 prefix에 대한 3f+1 지지는 다르다.
- 공통 중간 조각이나 불일치 최소화 optimizer가 아니라 **공통 prefix 발견 + leader-guided adjustment**다.
- 예정 순서는 실행 이력·실행 완료·execution proof가 아니다. Support도 실행 완료를 기다리지 않는다.
- 조정 round 중 후보는 고정하고 새 blocks는 다음 확장에 반영한다.
- 정상 경로에서는 채택 prefix를 확장해 late insertion을 억제한다. Leader 교체·후보 변경을 넘는 불변성이나 별도 plan finality는 주장하지 않는다.
- 생성·전파·실행은 계속하며, 미완료 plan을 cut의 무조건적인 대기 조건으로 두지 않는다.
- 최종 cut·선택된 exact order·canonical parent·runtime에 실행을 검증한다. Plan quorum과 cut finality·실행 인증은 별개다.
- 동일 context 중복 서명 방지 아래 q=3f+1의 교집합 논증을 사용한다. 다른 rounds/views의 서명을 섞지 않는다.

Round 전환·leader recovery·늦은 support·cut 경계·가용성·E2E 이득은 검증 과제다. 새 quorum의 선정이 완성된 consensus 증명을 뜻하지 않는다. Producer placement, state-owner sharding, ZK/PAC와 repair lane은 복원하지 않는다.

## 자료 상태

| 자료 | 상태 |
|---|---|
| [연구 개요](overpass-plan-ordering-outline.md) | 현재 source of truth; 8개 논문 section |
| [Prefix plan 결정](overpass-prefix-plan.md) | 두 경로·3f+1 의미·예시·검증 의무 |
| [논리 전개](overpass-research-logic.md) | 문제 → pipeline → prefix 발견/조정 → cut → state |
| [이번 변경 전 보관본](research/archive/2026-09-30-before-prefix-convergence/INDEX.md) | 직전 문서 원본 |
| [Hermes-advisory 보관본](research/archive/2026-09-29-hermes-advisory/INDEX.md) | Hermes 채택으로 잘못 한정했던 개요 |
| [실행 이력 기반 archive](research/archive/2026-09-29-execution-history-plan/INDEX.md) | 실행 보고 기반 이전 방향 |
| [Binding-plan archive](research/archive/2026-09-29-binding-plan/INDEX.md) | 과거 불변 plan·마지막 plan 대기 모델 |
| [Placement archive](research/archive/2026-09-29-before-plan-ordering/README.md) | 과거 placement·분석 자료 |
| [이전 outline](paper-outline.md) / [영문 manuscript](research/paper/README.md) | Reference-only; 현재 설계 미반영 |
| research/precut_order/ 및 commonware/ | 기존 toy models·fork; 새 설계 구현·검증 결과 아님 |

이번 갱신은 로컬 문서에 한정한다. Commonware·LaTeX/PDF·Google Docs는 변경하지 않았다.
