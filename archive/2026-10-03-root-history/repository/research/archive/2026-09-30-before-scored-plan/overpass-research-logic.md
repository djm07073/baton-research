# Overpass: 논리 전개와 주장 경계

> 2026-09-30 결정 반영. [연구 개요](overpass-plan-ordering-outline.md) / [상세 결정](overpass-prefix-plan.md). 구현·증명·평가 완료가 아니다.

## 한 문장

**Cut 전에 3f+1이 지지하는 예정 순서의 공통 prefix를 발견하고, 없으면 leader가 조정안을 제안해 공통 방향을 만든다. 실행은 계속하며 최종 cut에 맞춰 결과를 검증한다.**

## 왜 이 구조인가?

| 단계 | 논리 |
|---|---|
| 목적 | Ordering finality 이후 남는 실행 지연을 줄인다 |
| 첫 접근 | Dissemination·cut consensus와 speculative execution을 pipeline화한다 |
| 후속 문제 | 늦은 선행 block이 순서를 바꿔 실행을 무효화한다 |
| Leader-local 반례 | Leader에게만 X가 늦었다면 leader 순서 유지가 다른 노드들의 재실행을 늘릴 수 있다 |
| 관측 공유 | Validators가 같은 기준점에서 앞으로 따를 예정 순서를 보고한다 |
| Discovery | 전체 보고가 아니라 정확한 prefix 하나에 3f+1 지지가 있는지 찾는다 |
| Adjustment | 없으면 leader가 유효 후보를 고정해 제안하고 노드들이 채택·support한다 |
| 실행 | 기존 순서와 달라도 조정하며 support는 재실행 완료를 기다리지 않는다 |
| 확정 | 최종 cut의 exact ordering·parent·runtime에 맞춰 재사용·재실행한다 |
| 평가 | 초기 조정 비용, 이후 invalidation 감소와 통신 비용을 함께 측정한다 |

## 두 경로

```text
Validators: 같은 cut·parent의 예정 순서 보고
                       ↓
Leader: 새 prefix에 3f+1 지지가 있는가?
          ├─ 있음 → 해당 prefix + 근거 보고 전파
          └─ 없음 → 유효한 고정 조정안 제안
                         ↓
              Validators 순서 채택·support
              (재실행 완료는 기다리지 않음)
                         ↓
              동일 prefix에 3f+1 지지 형성
                       ↓
             정상 경로에서 prefix 확장
                       ↓
             기존 cut consensus로 최종 결정

Block 생성·전파·sync·speculative execution은 병렬로 계속
```

빈 prefix나 기존 prefix 그대로는 새 진행이 아니다. Report 수집만으로 q-support를 인정하지 않는다. 공통 중간 조각은 앞선 X·Y의 효과를 제거하지 못하므로 목표에서 제외한다.

## 선택한 quorum과 경계

n=5f+1에서 q=3f+1. 동일 context의 두 q 집합은 f+1 이상 겹치고, 정상 signer가 충돌하는 prefix에 중복 서명하지 않으면 양립 불가능한 두 인증을 만들 수 없다. 이 성질은 다른 rounds/views로 자동 확장되지 않는다.

- Plan은 예정 순서의 지지이지 실행 완료·state root 인증이 아니다.
- 정상 노드는 기존 실행과 다르다는 이유만으로 유효한 조정안을 거부하지 않는다.
- Normal path는 prefix 앞/내부 insertion을 막고 suffix를 확장한다.
- Leader 교체·기반 합의 후보 변경으로 prefix가 바뀔 수 있다. Canonical finality는 cut에서만 얻는다.
- Support가 없을 때 block 생성·실행을 멈추거나 cut을 무조건 기다리게 하지 않는다.
- Discovery와 adjustment의 context 및 증거를 구분하고 서로 다른 round의 표를 합산하지 않는다.

## 작은 cut과의 차이, 숨기지 않을 비용

Plan은 최종 순서를 철회 불가능하게 확정하지 않는다. 기존 finality 절차는 cut에 남는다. 하지만 adjustment 경로에는 추가 통신·지지 수집이 실제로 존재한다. 더 잦은 cut보다 싸거나 빠르다는 것은 이름에서 나오지 않으며 비교 실험이 필요하다.

영구 plan lock을 도입하면 다시 작은 ordering agreement에 가까워지므로 현재 설계와 구분해야 한다. Hermes의 공통 prefix finalization을 그대로 채택한 모델도 아니다.

## 주장과 남은 검증

- H1: 필요한 보정을 cut 이전으로 옮겨 post-cut 잔여 시간을 줄인다.
- H2: 공통 prefix 방향으로 수렴하고 확장하여 이후 late-insertion invalidation을 줄인다.
- 정상 leader·안정된 문맥·가용성·eventual synchrony 아래 정상 4f+1명으로 q를 모을 수 있다. 매 round 성공이나 성능 개선 보장은 아니다.
- Round 전환·leader recovery·미완료 plan과 cut의 경계, Byzantine churn·가용성, exact-order binding을 검증해야 한다.
- 실행 이력·완료 proof·불일치 최소화 optimizer·producer placement는 현재 설계에 넣지 않는다.

## 논문 positioning

> Overpass discovers intended-order prefixes supported by 3f+1 validators and uses leader-guided adjustment when no new supported prefix exists. It coordinates speculative execution alongside dissemination and cut consensus, aiming to reduce late-insertion invalidation without treating plan support as ordering or state finality.
