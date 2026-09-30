> **Historical snapshot — superseded by Baton (2026-09-30).**
> Current research: [Baton paper](baton-paper.md), [implementation specification](baton-implementation-spec.md), and [current handoff](BATON_HANDOFF.md).
> The body below is preserved as research/citation history. Its sum-only selection, plan/advisory descriptions, incumbent preferences and “current/latest/source of truth” claims do not override 2f+1-prefix-first selection or the adopted direction-preserving cut requirement. The four proposed implementation defaults remain unadopted; native integration and performance remain unproved.

# Overpass: 검토 결과를 논문과 다음 검증으로 연결하기

이 문서는 [submission-readiness review](overpass-submission-readiness-review.md)의 25개 검토 항목을 압축한 의사결정 메모다. 새 protocol 명세, 구현 승인, 성능 결과 또는 제출 가능 판정이 아니다. 현재 source of truth는 기존 outline과 prefix-plan이며, 사용자가 마지막으로 정한 세 비교군은 Original / Pre-cut execution / Overpass다.

## 지금 논문에 필요한 것은 세 가지 증거다

| 핵심 주장 | 본문에 필요한 증거 | 현재 확인된 상태 |
|---|---|---|
| Intended-order feedback이 단순 사전 실행보다 유용하다 | 실제 block 도착에서 reports가 생기고, 선택이 final order를 바꾸며, 비용을 포함한 state/E2E latency가 개선됨 | 작은 조건부 성공 사례와 반례만 있음. 현재 Overpass E2E 결과 없음 |
| 선택한 순서를 안전하게 canonical execution에 연결한다 | Exact order의 인증·복구, final input/parent/runtime 검증, 잘못된/stale 후보를 배제하는 논증과 테스트 | Native Multimmit의 chain-local finality를 executable order로 바꾸는 adapter가 미완성 |
| Optional planning이 cut 진행의 필수 대기가 되지 않는다 | Collection·optimizer·전파가 늦어도 fallback 진행; 같은 자원에서 ordering 간섭과 backlog 측정 | 정책은 명시됨. 실제 integration/race/resource 시험 증거 없음 |

이 셋이 채워지지 않은 상태에서 trie, 더 많은 quorum 설명, 새 배치 알고리즘을 추가해도 핵심 빈틈은 닫히지 않는다. 반대로 검토 메모의 모든 수학 예시와 구현 세부를 본문에 넣을 필요도 없다.

## 유지할 8개 섹션에 무엇을 남길 것인가

| 섹션 | 반드시 남길 논리 | 본문에서 줄여도 되는 것 |
|---|---|---|
| Introduction | 문제는 state-finalization latency이며, 핵심은 finality 전 intended-order feedback으로 ordering 후보를 조율하는 것 | 세부 threshold 유도, window message fields, 과거 설계 변화 |
| Background and Motivation | Parallel dissemination의 도착 차이 → pre-cut execution → late-input invalidation. Ordering 확정과 실제 완료 사건 구분 | 합의 기초 전체 강의, 폐기된 state isolation/placement 역사 |
| System Design | Report 생성·window 시작·candidate completion·선택·갱신·cut fallback·exact-order 연결을 하나의 흐름으로 설명 | Trie의 구현 코드, 모든 timeout/event 조합의 장황한 열거 |
| Correctness and Liveness | Planner의 성능 판단과 canonical safety를 분리. 인증된 exact order, parent 검증, freeze/recovery, bounded no-wait의 조건 | 모든 unit-test 사례의 개별 설명. 단, 중요한 예외는 숨기지 않음 |
| Evaluation | 동일 backend·자원·완료 의미의 세 비교군. 개선 원인, 비용, 부하 안정성, 실패 조건 | 과거 다른 모델의 35개 테스트나 local join 시간을 현재 결과로 제시하는 것 |
| Related Work | Optimistic execution의 선행성, Rashnu의 local-order aggregation, Autobahn-family의 실제 경계와 현재 차이 | 비교 목적이 다른 quorum 수를 단순 메시지 수 경쟁으로 나열하는 것 |
| Discussion and Limitations | Intended order는 progress가 아님; LCP와 dependency reuse의 차이; fairness·악성 leader 아래 성능 보장 없음 | 이미 설계·평가에서 다룬 설명을 전부 반복하는 것 |
| Conclusion | 실험에서 입증한 범위만 요약 | 구현 전 성능 수치, 보편적 재실행 최소화·학회 채택 가능성 단정 |

본문 구조를 새로 늘리지 않는다. 구현은 System Design의 짧은 구현 설명 및 Evaluation setup에서 실제 변경한 합의 경로·backend·자원·코드 버전을 밝히면 된다. 반드시 독립적인 큰 Implementation 섹션을 만들자는 권고가 아니다.

## 본문 figure에 필요한 네 질문

1. **문제가 실제로 있는가?** Original과 Pre-cut execution의 시간 분해 및 무효화된 실행량. Motivation의 가상 그림과 실제 측정 그림을 명확히 구분한다.
2. **설계가 어디에 개입하는가?** Report/plan 경로와 계속 진행하는 cut 경로를 나란히 놓고 window 안내, proposal freeze, final execution validation을 표시한다.
3. **전체 성능이 좋아지는가?** 같은 절대 offered load에서 세 구성의 state/E2E latency와 미완료 backlog를 함께 본다. 완료된 소수 요청만의 개선은 제외한다.
4. **왜 좋아지거나 나빠지는가?** Plan 사용률·도착 시각, 초기 보정·후속 재실행, 추가 비용을 분해한다. 독립 workload·stale reports·느린 실행의 한계도 보여준다.

아직 데이터가 없으므로 위 항목은 결과 figure의 내용 요구사항일 뿐, 빈 축에 수치를 채워 넣거나 기존 toy 결과를 대체 데이터로 쓰지 않는다.

## 부록·artifact로 보낼 수 있는 것

- 제한된 prefix-suffix 폐기 모델의 score 등식, 유한 sanity checks, 목적함수 반례 전체.
- Trie 계산법과 상세 복잡도, timer/report race의 세부 테스트 목록.
- 메시지 encoding, context/identity 검증의 전체 test vectors와 실행 설정.
- Toy-model 재현 자료. 실제 prototype 결과와 폴더·표기·주장을 분리한다.

핵심 correctness 조건이나 불리한 성능 결과를 부록으로 숨기지는 않는다. 본문에서 한계와 핵심 결과를 설명하고 상세 증거만 이동한다.

## 다음 검증에 앞서 필요한 결정

### 1. 기반 경로 결정 완료: Native Multimmit 유지

2026-09-30 사용자가 Native Multimmit을 선택했다. 기존 tip 추출·extension을 유지하며 plan과의 결합을 검토한다. Historical fixed-cut 변형은 재채택하지 않고 두 구현을 모두 만들지도 않는다.

다음 검토 대상은 native membership·settled/unsettled 처리·외부 ordered delivery와 plan의 연결이다. 첫 L-QC 관측에서 임의의 전체 실행 순서가 확정되었다고 가정하지 않으며, plan에 없는 extension block도 처리해야 한다. [Plan 정책 §7.1](overpass-prefix-plan.md#71-native-multimmit과의-결합-검토)에 요구사항을 기록했다. 선택은 완료됐지만 adapter 구현·안전성 증명은 미완료다.

Native 결합의 추가 검토 결과는 review §23에 기록했다. 2026-09-30 사용자가 선택한 ordering policy를 leader block의 인증 대상에 결속하고 같은 proposal에서 고정하는 방식을 채택했다. Growing pool에서 policy를 다시 고르지 않는다. 구체적인 position sweep encoding·continuation·recovery와 통합 증명은 여전히 미완료다.

§23.6–23.7은 공통 기준점·고정 sweep·양립 가능한 completion이라는 가정 아래 서로 다른 pool의 emission이 prefix-compatible함을 설명하는 조건부 보조정리와 증명 의무표다. Native QC가 이 가정들을 실제로 보장하고 plan 인증·view 상속이 이를 보존한다는 통합 증명을 대신하지 않는다. 동일 local execution view나 높은 LCP 점수를 safety 전제로 요구하지 않는다.

§23.8은 L-QC의 4f+1과 V-QC designation의 2f+1 사이에 정직한 교집합이 생기는 이유를 코드와 연결했다. 같은 view의 L-QC가 존재하면 지정 leader block이 일치해야 하지만, plan에는 별도 digest 결속이 필요하고 현재 미구현이다. L-QC 이전 V-QC만으로 plan uniqueness나 state finality를 주장할 수 없다.

§23.9는 prepared candidate의 원점을 실제 proposal pass의 exact parent와 비교해야 함을 확인했다. Parent tip의 상대 offset과 chain proposal의 DA anchor를 혼동하면 다른 block을 지정하거나 ancestors를 누락할 수 있다. Mismatch는 stale candidate 배제·유효 fallback으로 처리하고 native anchor 선택을 plan 때문에 지연시키지 않는 검토 방향이다.

§24는 구체적인 continuation 후보 `유효한 유한 prefix D + 기본 sweep에서 D를 제거한 tail`을 검토한다. 중복·누락·lane 역전을 피하고, slot 순위의 추가 지연이 |D| 이하임을 설명한다. Native emission 대기나 latency 개선을 보장하지 않는다. Policy binding 자체는 채택됐지만 이 구체적 encoding은 아직 검토 후보이며 구현하지 않았다.

### 2. Primary completion endpoint 결정 완료

2026-09-30 사용자가 full ordering finality와 f+1 matching execution-result 검증을 primary로, durable/read readiness를 보조 지표로 채택했다. 같은 exact ordered input·canonical parent·runtime·결과에 대한 해당 epoch의 서로 다른 validator 서명을 검증한다. 정직한 서명자는 직접 실행·검증하며 특정 ordering QC 투표자 부분집합에 제한하지 않는다. 상세한 수용 조건은 source of truth의 prefix-plan §7.2에 반영했다.

Endpoint 채택 이후 §25에서 실행 서명의 공통 범위·수집 진행성을 검토했다. 각자 최신 prefix에만 서명하면 정상 노드들이 다른 statement를 계속 만들 수 있으므로, 같은 canonical 실행 구간의 서명을 제공하는 규칙과 collector 복구가 필요하다. f+1 endpoint를 다시 선택하자는 뜻이 아니라 그 endpoint가 실제로 도달 가능하도록 할 후속 명세다.

§25.5–25.6은 결과 서명 준비를 ordering과 겹칠 수 있는 조건을 검토한다. 준비된 서명이 있어도 ordering·exact input·parent·runtime 검증 전에는 state를 채택하지 않는다. 이 최적화를 선택한다면 Pre-cut execution에도 동일하게 제공해 planner의 기여와 혼동하지 않아야 한다. 서명 스케줄은 아직 정식 채택하거나 구현하지 않았다.

### 3. 새 구현·분산 실험으로 범위를 확대할 것인가

현재 요청에 따라 수행한 것은 비판적 검토, read-only 코드 확인, 작은 진단 계산과 로컬 검토 기록이다. Native 경로 선택은 기록했지만 protocol 구현, cloud 배포·비용 지출 및 Google Docs 추가 편집은 수행하지 않았다. 실제 adapter와 세 비교군을 새로 구현하려면 별도 변경 요청과 그 경로에 대한 구현 검토가 필요하다.

Native 경로, policy 인증 위치, primary completion 의미가 선택되어 이전 설계 결정 대기는 해소됐다. 다음 과제는 **policy encoding·extension continuation·view recovery를 구체화하고, 선택한 completion 기준으로 통합을 검증하는 것**이다. 설계 채택을 코드 구현·cloud 실험 승인으로 확대하지 않는다. 실제 integration·latency 증거는 아직 없다.

## 현재 증거의 사용 범위

기존 Python 35개 tests의 통과는 이전 모델의 결과다. Review의 576개 cache 조합, 43,229개 score 비교, service-budget 및 arrival trace는 각각 작은 수학·실행 모델의 확인이다. 이를 현재 BFT protocol의 안전성 증명이나 E2E 성능으로 합산하지 않는다. 이번 재확인에서 Commonware HEAD는 `534af0ede48affd35b2111522527547b4cc9bf72`이고 사용자 작업이 남은 dirty checkout이었다. 변경을 덮어쓰거나 프로세스를 재시작하지 않았다.

총평: 연구 질문과 차별화 방향은 정리되었다. 제출 수준을 판단할 가장 큰 미완료 항목은 이제 표현의 참신함이 아니라 **exact-order integration, 동일한 완료 조건, 실제 추가 순이득의 증거**다. 이 메모는 학회 채택 확률이나 연구 완료를 판정하지 않는다.

## 추가 평가 점검: 같은 거래·같은 결과여도 작업량은 다를 수 있다

현재 outline은 성공률·goodput을 측정하지만, 그것만으로 재실행 절약의 원인이 분리되지는 않는다. Overpass가 final order를 바꾸면 application의 branch 비용도 바뀔 수 있기 때문이다. 다음은 성능 결과가 아니라 검산한 작은 반례다.

```text
초기 state: x=0, y=0
A: x:=1                            작업량 1
B: x=0이면 K 작업, 아니면 1 작업; y:=1

A→B: 총 작업량 2
B→A: 총 작업량 K+1
양쪽 모두 성공 2건, 최종 state (1,1), 재실행 0회
```

K=10/100/1000에서 각각 2 대 11/101/1001을 Python으로 계산·assert했다. 합의·네트워크·실제 runtime 측정이 아니며, 큰 개선 비율을 예상하는 근거가 아니다. 낮은 작업량이 재실행 감소를 뜻하지 않는다는 논리적 반례다. 기존 review §20의 성공 사례는 거래별 비용을 고정했으므로 이 특정 혼동은 통제하지만, 실제 workload까지 일반화하지 못한다.

Outline §5.3에 고정 비용의 dependency workload와 각 run의 실제 final order에 대한 사후 reference replay를 추가했다. Online 세 비교군을 바꾸거나 모든 비교군에 같은 final order를 강제하지 않는다. 구현 시 reference는 canonical parent·runtime·환경을 재현해야 하며, 유효한 speculative 결과의 재사용과 버려진 attempt를 계측으로 구분해야 한다. Serial replay 시간으로 parallel execution latency를 정규화하지 않는다.

다음 결과 판정은 간단하다: **latency 개선과 invalidation 감소가 함께 보이는가?** 하나만 관측되면 그 범위만 주장한다. Reference 데이터나 실행 진척을 online planner에 제공하지 않는다. 이번 추가는 로컬 평가 설계이며 Commonware·Google Docs·실험 결과는 변경하지 않았다.

## Native 선택 이후 문서 일관성 정리

Outline·prefix-plan·research-logic·README·AGENTS에 남아 있던 early-proposal 비교군을 최신 사용자 결정인 Original / Pre-cut execution / Overpass와 구분했다. Pre-cut execution에는 별도 leader plan 전파를 요구하지 않는다. Native의 첫 leader finality와 각 입력의 irrevocable ordering 도출도 구분했고, outline §5.2에 관측 node·completion endpoint·progressive delivery의 계측 조건을 명시했다.

가장 중요한 평가 함정은 ordering 시각이 뒤로 밀려 `order→state`만 짧아지는 경우다. 같은 ingress 0에서 order/state 12/20 대 25/26이면 간격은 8→1이지만 E2E는 20→26으로 악화된다. 설명용 산술 예시이며 실험 결과가 아니다. 이 조건은 새 endpoint를 채택한 것이 아니라, 어떤 endpoint를 선택하더라도 필요한 비교의 일관성 조건이다. 이번 정리는 로컬 문서만 변경했으며 cloud 문서나 Commonware 구현을 변경하지 않았다.
