# Overpass: Plan-Assisted Pipelined Execution

현재 연구 기준은 [새 연구 개요](overpass-plan-ordering-outline.md)다. 2026-09-29 요청에 따라 이전 자료는 참고로만 사용하고 개요를 새로 작성했다.

## 현재 방향

Block dissemination·cut consensus와 speculative execution을 중첩하여 state-finalization latency를 줄인다. 연속적인 plan으로 이미 실행한 prefix 앞의 late insertion을 제한한다.

- Base ordering을 round-robin 하나로 한정하지 않는다.
- Leader가 plan을 제안·인증하지만 production·execution은 plan 완료를 기다리지 않는다.
- Cut을 시작할 때 진행 중인 마지막 plan을 마무리하고 새 plan 제안을 멈춘다.
- 마지막 plan chain과 tips·최종 순서를 함께 묶어 cut을 확정한다.
- Local work는 필요하면 재검증·재실행한다. Speculative state는 canonical state가 아니다.

마지막 plan의 인증 실패, cut/plan voting fence와 leader recovery는 아직 증명·구체화할 과제다. 설계 기록을 구현 완료나 성능 보장으로 해석하지 않는다.

## 문서와 구현 상태

| 자료 | 상태 |
|---|---|
| [새 개요](overpass-plan-ordering-outline.md) | 현재 연구 방향·논문 구성·검증 과제 |
| [Archive](research/archive/2026-09-29-before-plan-ordering/README.md) | 이전 outline·producer placement·module 계획 snapshot |
| [이전 progressive-ordering 탐색](overpass-progressive-ordering.md) | 참고용; RR 한정과 cut 역할 등은 새 개요로 대체 |
| [이전 paper outline](paper-outline.md) | 보관; placement 중심 설계 |
| [영문 manuscript](research/paper/README.md) | 기존 LaTeX/PDF 보관; 새 개요 미반영 |
| [Placement 분석](research/placement/README.md) | 보관; 새 연구의 구성 요소가 아님 |
| research/precut_order/ | 일부 ordering·재사용 toy models; 새 BFT protocol 검증이 아님 |
| commonware/ | 기존 fork; 새 plan/cut protocol 미구현 |

기존 파일은 링크·빌드·연구 이력을 보존하기 위해 원래 경로에도 남겼다. 이전 README 전체는 archive에 보존했다. Google Docs와 외부 서비스는 이번 정리에서 변경하지 않았다.
