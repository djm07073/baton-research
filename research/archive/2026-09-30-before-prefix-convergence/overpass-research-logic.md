# Overpass: 논리 전개와 주장 경계

> 2026-09-29 사용자 정정 반영. [상세 개요](overpass-plan-ordering-outline.md). 설계·평가 계획이며 구현·증명 완료가 아니다.

## 한 문장

**Cut 전에 사전 ordering plan으로 실행 순서를 조율하고, 수용된 plan과 tips를 최종 cut의 순서 결정에 함께 반영하여 재실행과 state-finalization latency를 줄인다.**

Hermes를 기본 합의 엔진으로 채택한 것이 아니다. Plan을 실행 hint로만 취급하고 Hermes가 별도로 순서를 결정한다는 직전 설명을 정정한다.

## 논리 전개

| 단계 | 핵심 내용 | 다음 질문 |
|---|---|---|
| 문제 | Ordering finality 이후에도 실행·state 준비 시간이 남는다 | 실행을 앞당길 수 없나? |
| Pipeline | Block 생성·전파·수신·합의와 실행을 겹친다 | 늦은 선행 block이 들어오면? |
| 후속 비용 | 예정 순서가 달라져 speculative work가 무효화될 수 있다 | 순서를 미리 조율할 수 없나? |
| Plan | Leader가 알려진 ordering 입력에서 사전 순서를 제안한다 | 무엇을 수용하고 보존할 것인가? |
| Cut 연결 | 수용된 plan과 tips로 최종 순서를 결정하고 나머지는 canonical rule로 정렬한다 | 상충·누락·늦은 plan은? |
| State finalization | 확정된 exact 입력에서 실행을 재검증·재사용·재실행한다 | 추가 비용보다 이득이 큰가? |
| 평가 | 조기 보정·낭비 예방·합의 비용을 분리해 E2E 순이득을 측정한다 | 어떤 조건에서 효과가 사라지는가? |

## 역할과 흐름

```text
Producer: block 생성·전파 ──────────────────────────── 계속
                         │ 알려진 blocks / tips
                         v
Leader: 사전 ordering plan 제안 → 검증·수용 절차 [설계 필요]
                         │                  │
                         v                  v
Replica: sync·사전 실행·조정          수용된 plans + tips
                         │                  │
                         │          최종 순서 구성·cut 합의
                         │                  │
                         └──────────> exact-context 검증
                                      재사용 / 재실행
                                            ↓
                                    state finalization
```

- Plan 입력: 알려진 exact blocks/tips, ancestry, 유효 parent, 입력 가용성 자료와 공통 ordering rule.
- 원격 실행 이력·완료 보고·execution proof는 입력에서 제외한다. 내부 실행 검증과 offline 계측은 유지한다.
- Plan 제안, protocol상 plan 수용, 최종 cut 확정은 서로 다른 사건이다. 단순 수신으로 보존 권한이 생기지 않는다.
- Plan은 최종 순서에 영향을 준다. 수용 조건과 보존 범위가 정해지기 전에는 insertion 금지나 재실행 제거를 보장했다고 주장하지 않는다.
- Plan만으로 canonical state를 채택하지 않는다. 최종 cut·parent·runtime과 일치하는 실행 결과가 필요하다.

## Hermes와의 구분

Hermes는 서로 다른 투표에서 공통 prefix를 추출해 ordering을 확정하는 참고 연구다. 우리는 cut 전에 순서를 조율하고 그 합의를 cut에 연결하여 speculative invalidation을 줄이려 한다. Hermes의 quorum이나 proposal 표현을 우리 설계 규칙으로 가져오지 않는다.

## 다음 설계에서 결정할 것

1. Plan 수용 조건과 quorum, 상충 plan 중복 투표 방지, plan 간 확장·중첩 규칙.
2. 상대 순서 보존인지, 사이 또는 앞의 insertion도 금지하는지 등 정확한 보존 범위.
3. Cut이 고려해야 하는 plan의 종료 경계와 늦게 도착·인증되는 plan의 처리.
4. Leader 교체 시 수용 이력 복구와 이미 생긴 보존 의무 유지.
5. 수용된 plans·tips·ancestry·기본 ordering rule에서 하나의 유효 순서를 구성하는 규칙.

Leader가 현재 plan 구간을 닫고 cut으로 넘어가는 방향은 유지하되, leader의 일방적 선언이나 local clock만으로 경계가 합의된다고 가정하지 않는다. 미완료 plan을 무조건 기다려야 하는 설계도 확정하지 않는다.

## 효과와 주장 경계

- H1: 필요한 보정을 finality 이전으로 옮겨 post-cut 잔여 시간을 줄인다.
- H2: 수용된 순서의 보존으로 잘못된 speculative execution 자체를 줄인다.
- 두 효과는 별도 검증 대상이다. 같은 순서라도 parent·앞선 입력이 달라지면 결과 재사용이 안 될 수 있다.
- Production·실행의 지속과 cut consensus의 liveness는 다르다. Plan 단계가 숨은 barrier가 되지 않는지 검증해야 한다.
- 이전 3f+1 plan certificate, Hermes의 4f+1 규칙, 실행 서명 threshold를 혼합해 안전성을 주장하지 않는다.
- Producer placement, state-owner sharding, ZK/PAC, receipt bridge와 repair lane은 복원하지 않는다.

## 논문 positioning

> Overpass proposes advance ordering plans that coordinate speculative execution during block dissemination and are incorporated with producer tips into final cut ordering. It aims to reduce speculative-work invalidation and state-finalization latency; plan acceptance, preservation, and recovery rules remain protocol design and verification obligations.

Plan 없는 speculation, 단순 early proposal, 더 잦은 cut과 비교한다. 목표는 Hermes를 실행에 붙이는 것이 아니라, **사전 순서 조율과 최종 cut의 연결이 추가 비용을 넘는 이득을 만드는지** 입증하는 것이다.
