# Overpass: 논리 전개와 주장 경계

> 2026-09-29 · [상세 논문 개요](overpass-plan-ordering-outline.md)의 요약. 아직 설계·평가 계획이다.

## 한 문장

**Consensus와 execution을 겹치고, 실행 이력을 참고하는 plan으로 유효한 후보와 실행 방향을 일찍 수렴시켜 state-finalization latency를 줄인다.**

## 왜 이 순서로 설명하는가?

| 단계 | 독자가 납득해야 할 내용 | 다음 질문 |
|---|---|---|
| 문제 | Ordering이 끝나도 application state 준비에는 실행 시간이 남는다 | 실행을 먼저 할 수 없나? |
| 기회 | Blocks는 finality 전에 전파된다 | 그 시간에 실행하면 되지 않나? |
| Pipeline | 수신·sync·consensus와 실행을 겹칠 수 있다 | 예상 순서가 틀리면? |
| 후속 비용 | 다른 local inputs·후보 순서가 speculative work를 무효화한다 | 최종 방향을 일찍 맞출 수 없나? |
| 관찰 | Local views가 달라도 공통 조각·재사용할 작업이 있을 수 있다 | 이를 후보 선택에 활용할 수 없나? |
| Plan | 유효 후보 중 실행 이력과 잘 맞는 방향을 예고한다 | 실제 확정 권한은 누구에게 있나? |
| Finality | Hermes가 prefix를 확정하고 실행 결과를 exact context에서 검증한다 | 추가 비용보다 이득이 큰가? |
| 평가 | 조기 보정·낭비 예방·통신 비용을 분리해 E2E로 검증한다 | 어떤 조건에서 이득이 사라지나? |

## 공통 조각과 공통 prefix의 차이

- **공통 조각:** 여러 local execution에서 같은 순서로 등장하는 일부 blocks. 시작 위치나 입력 state가 같다는 뜻은 아니다.
- **Plan:** 이 관측을 참고하는 후보 선호·실행 예고. 따르지 않았다는 이유만으로 정상 consensus vote를 무효화하지 않는다.
- **공통 prefix:** 기반 consensus가 실제 votes에서 추출하는 확정 대상. Plan이 원하는 조각과 같을 필요는 없다.

사용자가 제시한 개념 예시:

```text
X → [A → B] → Y
Y → [A → B] → X
    [A → B] → X → Y

검토할 방향: [A → B] → canonical(X, Y)
```

공통 조각을 선호하되 나머지는 canonical rule로 정한다. 단, Hermes의 표현·parent·producer ancestry 제약에 맞지 않으면 이 재배열은 사용하지 않는다. 같아 보이는 A→B도 입력이 바뀌었다면 재실행한다. 이 예시를 Hermes가 제공하는 임의 permutation 기능으로 설명하지 않는다.

## Plan이 돕는 두 효과

1. **보정 시점 이동:** 필요한 재실행을 finality 이후가 아니라 이전에 처리한다.
2. **불필요한 실행 예방:** 아직 시작하지 않은 작업을 예상 최종 방향에 맞춰 실행한다.

첫 효과는 총 실행량이 그대로여도 가능하다. 두 번째는 plan 안정성과 실제 최종 후보와의 일치가 필요하다. 별도로 측정한다.

## 주장하지 않는 것

- 공통 조각이 많으면 반드시 재실행이 감소한다.
- Plan 수신·진척 보고가 ordering 또는 state finality다.
- Plan이 기존 vote를 바꾸거나 parent 제약을 무시할 수 있다.
- 모든 노드가 같은 순간에 같은 data·execution view를 갖는다.
- Cut-to-state 간격만 짧아지면 성공이다.
- Advisory이므로 bandwidth·CPU·검열·liveness 비용이 없다.

## 이번 버전의 설계 선택

- 별도 3f+1 binding plan certificate를 두지 않는다.
- 마지막 plan 인증을 기다리고 cut으로 넘어가는 이전 규칙은 사용하지 않는다.
- 준비된 plan을 이용하되 없거나 늦으면 기존 consensus 경로를 진행한다.
- Proposal·vote 이후에는 기존 consensus 규칙이 우선한다.
- Fragment 선택 알고리즘·report budget·구체적 Hermes hook은 아직 연구 과제다.

## 논문에서 앞세울 문장

> Overpass uses execution-aware advisory plans to align valid ordering candidates and speculative execution before ordering finality, aiming to reduce post-finality recovery work and end-to-end state-finalization latency.

## 먼저 확인할 세 가지

1. Hermes의 허용된 후보 선택 범위 안에서 실제로 유용한 plan을 만들 수 있는가?
2. 정상 leader 경로와 fallback 경로 중 어디에서 조기 수렴의 이득이 생기는가?
3. Plan 없이 사전 실행하는 비교군보다 planning 비용을 포함한 E2E latency가 개선되는가?

목표는 prefix 합의 자체의 재발명이 아니라, **ordering 선택과 execution 준비 사이의 정보 교환이 실질적인 latency 이득을 만드는지** 입증하는 것이다.
