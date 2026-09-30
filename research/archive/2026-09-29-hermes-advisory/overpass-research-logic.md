# Overpass: 논리 전개와 주장 경계

> 2026-09-29 · [상세 논문 개요](overpass-plan-ordering-outline.md)의 요약. 아직 설계·평가 계획이다.

## 한 문장

**사전 ordering plan을 조기에 공유하여 consensus와 execution을 겹치고, 실행 방향을 실제 유효 후보와 일관되게 연결하여 재실행과 state-finalization latency를 줄인다.**

원격 실행 이력·진척·완료 주장과 execution proof는 plan의 입력에서 제외한다. 그 사실을 증명·검증하는 후속 protocol을 만들지 않으려는 범위 결정이며, 실행 증명이 원리적으로 불가능하다는 일반 주장은 아니다.

## 왜 이 순서로 설명하는가?

| 단계 | 독자가 납득해야 할 내용 | 다음 질문 |
|---|---|---|
| 문제 | Ordering이 끝나도 application state 준비에는 실행 시간이 남는다 | 실행을 먼저 할 수 없나? |
| 기회 | Blocks는 finality 전에 전파된다 | 그 시간에 실행하면 되지 않나? |
| Pipeline | 수신·sync·consensus와 실행을 겹칠 수 있다 | 예상 순서가 틀리면? |
| 후속 비용 | 다른 local inputs·후보 순서가 speculative work를 무효화한다 | 최종 방향을 일찍 맞출 수 없나? |
| 관찰 | 실행 결과를 몰라도 blocks·tips와 공통 규칙으로 후보 순서를 정할 수 있다 | 그 순서를 미리 공유할 수 없나? |
| Plan | 앞으로 실행할 유효 순서를 예고하고 실제 proposal과 연결한다 | 실제 확정 권한은 누구에게 있나? |
| Finality | Hermes가 prefix를 확정하고 실행 결과를 exact context에서 검증한다 | 추가 비용보다 이득이 큰가? |
| 평가 | 조기 보정·낭비 예방·통신 비용을 분리해 E2E로 검증한다 | 어떤 조건에서 이득이 사라지나? |

## Plan의 입력과 확정 권한

- **입력:** 알려진 exact blocks·tips, 유효 parent와 입력 인증 자료, 공통 ordering rule.
- **Plan:** 앞으로 실행할 후보 순서의 예고. 실행 이력 optimizer나 binding certificate가 아니다.
- **공통 prefix:** Hermes가 실제 votes에서 확정하는 ordering 대상. Plan 전체가 그대로 확정된다고 가정하지 않는다.

구조:

```text
알려진 blocks / tips + 유효 parent + 공통 ordering rule
                         ↓
                 사전 ordering plan 공유
                         ↓
              sync + speculative execution
                         ↓
          실제 proposal·finalized prefix와 검증
```

후보와 나머지는 canonical rule을 따르고, Hermes의 표현·parent·producer ancestry 제약을 만족해야 한다. Plan을 받았어도 입력이 바뀌면 재실행한다. 실행 이력을 제출하지 않는다고 최종 결과 검증까지 없어지는 것은 아니다.

## Plan이 돕는 두 효과

1. **보정 시점 이동:** 필요한 재실행을 finality 이후가 아니라 이전에 처리한다.
2. **불필요한 실행 예방:** 아직 시작하지 않은 작업을 예상 최종 방향에 맞춰 실행한다.

첫 효과는 총 실행량이 그대로여도 가능하다. 두 번째는 plan 안정성과 실제 최종 후보와의 일치가 필요하다. 별도로 측정한다.

## 주장하지 않는 것

- 같은 plan을 공유하면 반드시 재실행이 감소한다.
- Plan 수신이 ordering 또는 state finality다.
- Plan이 기존 vote를 바꾸거나 parent 제약을 무시할 수 있다.
- 모든 노드가 같은 순간에 같은 data·execution view를 갖는다.
- Cut-to-state 간격만 짧아지면 성공이다.
- Advisory이므로 bandwidth·CPU·검열·liveness 비용이 없다.

## 이번 버전의 설계 선택

- 별도 3f+1 binding plan certificate를 두지 않는다.
- 마지막 plan 인증을 기다리고 cut으로 넘어가는 이전 규칙은 사용하지 않는다.
- 준비된 plan을 이용하되 없거나 늦으면 기존 consensus 경로를 진행한다.
- Proposal·vote 이후에는 기존 consensus 규칙이 우선한다.
- Plan의 공개·갱신·candidate binding 규칙과 구체적 Hermes hook은 아직 연구 과제다.
- 실행량·진척은 내부 재사용 검증과 offline 실험 계측에만 사용하며 plan 선택에 피드백하지 않는다.

## 논문에서 앞세울 문장

> Overpass shares advance ordering plans derived from available ordering inputs and a common ordering rule to align speculative execution with valid consensus candidates, aiming to reduce re-execution and end-to-end state-finalization latency without relying on execution-history reports.

## 먼저 확인할 세 가지

1. Hermes의 허용된 후보 선택 범위 안에서 plan을 정상 proposal보다 일찍 공유할 기회가 있는가?
2. 정상 leader 경로와 fallback 경로 중 어디에서 조기 수렴의 이득이 생기는가?
3. Plan 없이 사전 실행하는 비교군보다 planning 비용을 포함한 E2E latency가 개선되는가?

목표는 prefix 합의 자체의 재발명이 아니라, **실행 보고 없이 사전 ordering 예고와 실제 consensus 후보를 연결하는 것이 실질적인 latency 이득을 만드는지** 입증하는 것이다. 단순 early proposal과의 차이도 검증한다.
