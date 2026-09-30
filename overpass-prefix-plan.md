# Overpass: Prefix-Score Planning with Bounded Report Collection

> 2026-09-30 최신 결정. [논문 개요](overpass-plan-ordering-outline.md) / [논리 전개](overpass-research-logic.md).
> 연구 설계이며 구현·안전성 증명·성능 검증 완료가 아니다. 파일명은 기존 링크 호환을 위해 유지한다.

## 1. 결정 요약과 이전 모델 대체

**Positioning: Overpass는 Autobahn-family consensus를 위한 execution-aware ordering extension이며 새로운 consensus safety protocol이 아니다.** Validator들의 intended order를 ordering 후보 선택에 반영하여 speculative execution의 보존 가능성을 높인다. 추가 plan 승인 단계나 cut 대기 없이 state-finalization latency를 줄이는 것이 목표이며, 아래 score·수집 정책은 이를 구현하는 메커니즘이다.

**Leader는 같은 기준 cut·canonical parent의 예정 순서 보고를 비동기로 수집하고, 보고들과 공통 prefix를 가장 많이 보존하는 유효 후보를 실행 plan으로 전파한다. n=5f+1에서 서로 다른 validator의 보고 4f+1개 확보 또는 수집 deadline 중 먼저 도달한 때 계산한다. 최종 결정은 기존 cut consensus에서 내린다.**

이번 결정은 다음을 대체한다.

- 3f+1이 같은 prefix를 지지해야 한다는 필수 조건을 제거한다.
- 공통 prefix가 없으면 조정안에 다시 3f+1 support를 모으던 경로를 제거한다.
- Plan 전파 후 별도 ACK/support quorum을 요구하지 않는다.
- 보고 4f+1개는 동일 plan에 대한 승인이 아니라 관측을 충분히 수집하기 위한 목표다.

Producer 생성·전파, sync·speculative execution과 기존 cut 합의는 계속 진행한다. Cut은 report 수·timer·plan 계산의 완료를 기다리지 않는다.

**추가 채택 결정 (2026-09-30):** 선택한 ordering policy를 leader block의 인증 대상에 결속하고 같은 proposal에서는 고정한다. State finalization은 해당 입력의 완전한 ordering finality와 exact input·canonical parent·runtime·결과에 대한 서로 다른 유효 validator f+1명의 일치 실행 서명이 모두 검증된 상태로 정의한다. Durable/read readiness는 별도 보조 지표다. 이는 설계 채택이며 코드 구현·통합 증명의 완료가 아니다.

## 2. 보고의 문맥과 의미

보고는 epoch, leader view, 기준 finalized cut·canonical parent, rule version, 논리적 수집 window와 exact ordered block references를 묶는다. Validator당 해당 window의 유효 보고 하나만 계수한다. Window를 넘는 보고를 새 보고처럼 중복 계수하거나 다른 parent의 순서를 섞지 않는다.

보고 내용은 “이 순서로 실행할 예정”이지 실행 완료·진척·state root·execution proof가 아니다. Leader 선택에 원격 실행 이력을 요구하지 않는다. 내부 실행 검증과 offline 계측은 유지한다.

유효성 확인에는 identity·서명·문맥·block references·ancestry·필수 선행 제약과 가용성 자료가 포함된다. 서명된 보고만으로 block body의 DA나 application correctness가 보장되지는 않는다. 정확한 encoding과 report recovery는 후속 구현 과제다.

## 3. Prefix-score로 후보 선택

공통 기준점에서 시작하는 bounded horizon W의 보고들을 R_i라 하고, 유효한 보고 후보와 현재 incumbent를 후보 집합에 포함한다. 필수 ancestry가 없거나 parent와 양립하지 않는 후보는 제외한다. 보고에 없는 임의 permutation을 탐색하지 않는 것이 첫 prototype 범위다.

```text
Score(P; R) = sum over distinct validators i of |LCP(P, R_i)|
```

LCP는 처음부터 연속해서 같은 exact blocks가 나오는 길이다. 중간 조각·subsequence는 점수로 세지 않는다. 공통으로 이미 확정된 과거는 비교 구간에서 제외한다.

예시:

```text
R1: A → B → C
R2: A → B → D
R3: A → B → E
R4: B → A → X
R5: B → A → Z

Score(A→B→C) = 3+2+2+0+0 = 7
Score(B→A→X) = 0+0+0+3+2 = 5
```

A→B→C / A→B→D / A→B→E는 위 예시에서 동점이다. Incumbent가 동점 후보면 유지하고, 그렇지 않으면 정해진 canonical tie-break로 선택한다. 점수는 예정 순서의 prefix 보존 proxy이며 실제 재실행 비용의 최솟값이나 실행 완료를 보장하지 않는다.

서로 다른 순서에 다수 지지가 있는 경우에도 하나의 후보를 선택할 수 있다. 정확한 같은 prefix에 3f+1이 모였는지는 필수 조건이 아니다.

후보에 없는 준비된 blocks는 유효한 ancestry를 지키며 기본 ordering rule로 suffix에 추가할 수 있다. 계산에 사용한 window·후보 길이·suffix 정책을 고정하여 실험 결과를 재현해야 한다. Candidate window 밖의 선택과 inclusion fairness는 별도 검증 대상이다.

## 4. 언제 모으고 언제 전파하는가?

### 4.1 수집 시작과 전파 trigger

첫 plan은 leader가 아직 plan에 반영하지 않은 실행 가능한 block을 처음 관측한 시점 t0에 수집을 시작한다. Window의 deadline을 t0+τ로 고정한다. 다음 windows도 새로 평가할 작업이 있을 때 시작하며 빈 window를 무한 반복하지 않는다.

```text
수집 시작 t0
    │
    ├─ 동일 문맥의 distinct valid reports 4f+1개 확보
    │       → 현재 보고 snapshot으로 후보 계산
    │
    └─ t0+τ 도달
            → 현재 확보한 보고 snapshot으로 후보 계산

먼저 발생한 trigger 한 번으로 해당 window 종료
       ↓
필요한 경우 plan 전파 (후속 승인 투표 없음)
```

- 새 report/block 도착이 deadline을 연장하거나 timer를 재시작하지 않는다.
- Report threshold와 timer가 동시에 만족돼도 window를 한 번만 닫고 계산한다.
- Deadline에 보고가 적거나 없으면 현재 유효 후보 또는 기본 ordering rule을 사용한다.
- τ는 configurable leader-local duration이다. Unix timestamp를 canonical 순서·finality 조건으로 사용하지 않고 노드 간 clock 동기화를 요구하지 않는다.
- 엄격한 시간·전송 상한을 주장하지 않는다. 계산·검증·event queue 비용도 별도 측정한다.
- τ, horizon W, report/plan bytes와 계산 예산은 고정 가능한 실험 설정이며 수치는 아직 선정하지 않았다.

### 4.2 Cut이 먼저 준비되는 경우

Cut이 정상 경로에서 먼저 제안 가능해지면 수집 완료나 optimizer 완료를 기다리지 않는다. 이미 준비된 최신 유효 후보를 사용하고, 없다면 기반 ordering rule의 유효 fallback을 사용한다.

```text
수집 진행 중 ── cut ready
                   ↓
      준비된 후보 / 기본 rule로 cut 진행
      pending 수집·계산을 기다리지 않음
```

Cut proposal을 전파한 뒤 새 보고나 plan으로 같은 proposal/vote를 변경하지 않는다. 진행 중 계산은 해당 proposal에 대해 stale로 취급한다. 이후 계획에 쓸 경우 새 대상 문맥에서 유효성을 다시 확인하며 다른 cut·parent의 보고를 그대로 섞지 않는다. Finalized parent가 바뀌면 새 문맥으로 보고를 수집한다.

실제 consensus의 후보 유효성·parent·inclusion 규칙이 우선한다. Report count와 local deadline은 canonical validity predicate가 아니다.

## 5. 4f+1 보고의 의미

n=5f+1, 최대 f Byzantine validator identities에서 유효한 서로 다른 보고 4f+1개를 확보하면 정상 보고자는 최소 3f+1명이고 미포함 identity는 최대 f명이다.

그러나 서로 다른 보고들의 순서는 다를 수 있다. Leader가 선택한 plan에 4f+1이 동의했거나 동일하게 실행했다고 해석하면 안 된다. 이 수를 ordering finality·execution certification·plan non-equivocation의 quorum으로 사용하지 않는다.

Byzantine f명이 침묵하면 strict 4f+1 수집은 정상 4f+1명 모두를 기다린다. 그래서 deadline fallback을 둔다. Deadline으로 더 적은 보고를 사용했을 때는 4f+1 수집의 관측 coverage를 주장하지 않는다. 정상 보고자 수가 많아도 보고의 freshness나 latency 개선을 보장하지 않는다.

## 6. 후보 변경과 실행

- 같은 문맥의 현재 보고 snapshot으로 incumbent와 새 후보를 함께 평가한다. 이전 window 원점수와 직접 비교하지 않는다.
- 동점이면 incumbent를 유지한다. 동점 해소 rule은 deterministic하게 고정한다.
- 기존 순서 변경은 충분한 점수 개선이 있을 때만 허용하여 churn을 억제한다. 개선 폭·최소 갱신 간격은 tuning 항목이다.
- 기존 순서를 유지하는 suffix 확장, 실제 재정렬, 변화 없음의 경우를 구별한다. 변화가 없으면 재전파를 생략한다.
- Nodes는 수신 plan의 parent·refs·revision을 확인하고 미실행 작업을 scheduling한다. 완료·진행 작업은 입력 의존성을 검증하고 필요한 부분만 재실행한다.
- Plan에 동의하는 추가 support/ACK를 모으지 않는다. 이후 정기 보고는 관측 갱신이지 plan 인증이 아니다.
- Leader의 미래 후보가 유지된다는 보장은 없다. Byzantine leader·view change·기반 합의 제약으로 순서가 바뀌면 보정한다.

## 7. Canonicality와 Byzantine 경계

Plan은 바뀔 수 있는 실행 후보다. Canonical exact order는 인증된 문맥과 공통 규칙으로 유일하게 도출되어야 한다. 선택한 order 또는 이를 결정하는 plan/policy 입력을 인증하는 adapter는 아직 미완료다. Tips만 인증한 뒤 임의 순서를 덧붙일 수 없다. Native Multimmit의 첫 leader-finality 관측을 모든 관련 block의 global ordering 완료로 간주하지 않는다.

최종 결과는 exact finalized input·canonical parent·runtime에서 검증한다. 높은 점수, 많은 보고, leader 서명은 실행 결과의 정확성을 대체하지 않는다. 긴 speculative state root를 짧은 prefix 결과로 잘라 쓰지 않는다.

Byzantine 보고·선택 편향·equivocation은 성능을 악화시킬 수 있다. Identity 계수·window binding·bounded input·유효 ordering 검사·기존 합의 recovery로 영향을 다루되, 이 heuristic으로 Byzantine leader 아래 좋은 성능을 보장하지 않는다. 서로 다른 보고 집합을 받은 leaders가 같은 후보를 계산한다고 주장하지 않는다.

같은 입력 snapshot·후보 집합·rule로 선택을 재현할 수 있는 것과 모든 노드의 관측이 동일하다는 것은 다르다. 보고 최적성 검증을 cut critical path에 강제하는 설계도 현재 도입하지 않는다.

### 7.1 Native Multimmit과의 결합 검토

2026-09-30 사용자 결정: **Native Multimmit의 tip 추출·extension을 유지한다.** 과거 fixed-cut 구현 계획의 제거 방향은 재채택하지 않는다. 다음은 결합의 요구사항이며 구현된 protocol이나 안전성 증명이 아니다.

- **Membership는 native 경로가 결정한다.** Plan에 없는 block도 native extension으로 포함될 수 있다. Plan에 있다는 이유만으로 포함을 확정하거나, 없다는 이유로 native inclusion을 누락시켜서는 안 된다.
- **Plan은 speculative 실행 후보다.** Native finalized input과 다르면 의존성을 검증하고 필요한 실행을 보정한다. 최종 입력에서 block을 빼는 것만으로 기존 실행 결과를 그대로 재사용할 수 있다고 가정하지 않는다.
- **최종 실행 순서는 별도로 명확히 연결해야 한다.** 현재 checkout의 `LeaderBlock`에는 plan/order field가 없고 consensus는 chain-local tips와 인증 자료를 제공한다. Dense global ordering·body retrieval·durable delivery는 외부 marshal의 구현 책임으로 남아 있다. 따라서 기존 L-QC만으로 임의의 leader plan까지 인증되었다고 주장하지 않는다.
- **Vote pool의 증가와 settled/unsettled 처리를 보존한다.** 첫 leader-finality 관측을 더 이상 변하지 않는 전체 실행 block 집합으로 간주하지 않는다. 새 tip·extension을 반영하되 이미 canonical하게 전달한 실행 prefix는 바꾸지 않아야 한다.
- **채택한 연결 방식:** 선택한 ordering policy를 leader block의 인증 대상에 결속한다. 같은 proposal에서 policy를 변경하지 않고, native delivery 제약 안에서 exact order를 결정론적으로 도출한다. 구체적 encoding·미명시 extension 위치·leader 변경 시 복구는 후속 명세·증명 과제다. 단순히 commitment field를 추가하면 해결된다고 보지 않는다.
- **No-wait 경계:** Report 수집·plan 계산 완료를 native consensus 진행의 선행조건으로 만들지 않는다. 이것은 native availability·settledness·application dependency 대기까지 없앤다는 뜻은 아니다.

예를 들어 plan이 `A1 → B1`인데 native extraction 결과에 `A2`도 포함되면, `A2`를 버리거나 임의로 앞/뒤에 붙이지 않는다. Producer ancestry와 native delivery 제약을 만족하는 공통 규칙으로 위치를 정해야 한다. 어느 위치를 허용할지와 그 선택을 인증하는 방법이 adapter의 검증 과제다.

코드 근거: [STATE_MACHINE.md](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md)의 ownership boundary와 Leader finality, [PoolExtractor](commonware/consensus/src/multimmit/machine/algebra/tips.rs), [LeaderBlock](commonware/consensus/src/multimmit/types/block.rs). 이는 현재 checkout의 구현 경계 확인이며 upstream 전체 구현 상태나 native protocol의 결함을 주장하는 것이 아니다. 이번에는 Commonware 코드를 변경하지 않았다.

### 7.2 Policy binding과 state finalization의 채택 조건

**Policy의 수명:** Advisory plan은 proposal 전에 변경 가능하다. 실제 proposal에는 준비된 유효 policy 또는 기본 fallback을 선택하여 인증한다. 이후 같은 proposal의 policy는 고정하며 늦은 보고·growing vote pool로 교체하지 않는다. 다음 view의 별도 proposal은 기반 recovery 규칙을 따라야 하며 이미 확정·전달된 순서를 바꾸지 않는다. Policy를 결속하는 것은 별도 plan 승인 quorum이나 과거의 영구 plan-lock 모델을 도입하는 것이 아니다.

**인증 범위:** Policy 내용 또는 재구성 가능한 commitment와 해석 규칙이 leader block의 인증 subject에 포함되어야 한다. 서로 다른 policy가 같은 인증 subject로 해석되는 것을 허용하지 않는다. Policy의 유효성·가용성·크기 상한·extension continuation·복구 방식은 구현 전에 정의할 의무로 남긴다. V-QC 또는 leader 서명만으로 state를 finalize하지 않는다.

**State-finalization 수용 조건:**

1. 대상 입력 범위의 exact order가 native finality와 ordered-delivery 규칙에 의해 irrevocable하게 정해져 있어야 한다. 첫 L-QC 수신만으로 모든 extension의 위치가 정해졌다고 가정하지 않는다.
2. 서로 다른 해당 epoch validator f+1명의 서명이 같은 statement에 대해 유효해야 한다. Statement는 replay domain/epoch, exact ordered input 및 범위, 올바른 canonical input state, runtime, output result를 모호함 없이 식별해야 한다. 구체적 wire schema는 미정이다.
3. 정직한 서명자는 그 문맥에서 직접 실행한 결과를 검증한 뒤 서명한다. 다른 노드의 서명이나 receipt를 복사해서 자신의 실행 서명을 발행하지 않는다. Speculative cache를 사용하면 최종 문맥과의 일치 및 dependency validation이 필요하다.
4. 서명자를 특정 ordering QC의 투표자 부분집합으로 제한하지 않는다. 늦게 따라온 해당 epoch validator도 정확한 입력을 실행·검증하면 참여할 수 있다. 같은 identity의 중복 서명은 한 번만 센다.

최대 f Byzantine, 인증된 membership, 서명 위조 불가 및 deterministic execution 아래 f+1 일치 서명에는 정상 서명자가 적어도 하나 있다. 따라서 이미 확정된 동일 입력의 잘못된 결과만으로 이 조건을 만족할 수 없다는 논거를 사용한다. f+1은 ordering을 결정하거나 native consensus quorum을 대체하지 않는다. 틀린 parent/runtime에 대한 서명은 개수가 충분해도 수용하지 않는다.

이 정의는 사전 실행을 금지하거나 cut 이후에 새 ordering round를 추가하지 않는다. 다만 speculative 결과를 canonical하게 채택하려면 위 조건을 모두 만족해야 한다. 실행 서명의 생성·전파 시점, 인증 aggregation, checkpoint/보관·복구는 후속 설계 과제다.

**측정:** 지정한 관측 node가 ordering evidence와 f+1 일치 실행 서명을 모두 검증하고 canonical parent 연결을 확인한 시점을 primary completion event로 사용한다. 세 비교군에 같은 수용·서명 기준을 적용한다. State bytes의 local apply·durable persistence·read readiness는 별도로 기록하며, 결과 인증만으로 이들이 완료됐다고 주장하지 않는다.

## 8. 평가와 다음 작업

주 비교군은 **Original / Pre-cut execution / Overpass**다. Original은 해당 입력의 irrevocable execution order 도출 후 실행한다. Pre-cut execution은 받은 blocks를 기본 rule로 사전 실행·보정하며 별도 leader plan 전파가 없다. Overpass는 여기에 intended-order 기반 planning을 더한다.

Prefix-score 선택만/변경 억제 포함, timer-only/strict 4f+1/hybrid는 ablation으로 둔다. Frequent cuts는 별도 민감도 실험이다. Early proposal은 주 비교군이 아니며 Pre-cut execution과 동일시하지 않는다.

지표:

- Native leader finality와 해당 입력의 irrevocable ordering 도출을 별도 기록한다. 첫 L-QC를 모든 입력의 ordering 완료 시각으로 쓰지 않는다. Completion endpoint와 local timestamp 기준은 outline §5.2를 따른다.
- Ingress-to-state와 cut-to-state p50/p95/p99, ordering latency, durable readiness, successful goodput·backlog.
- Threshold/deadline/cut-preemption 비율, 수집 시간·report 수·계산 시간·plan-to-cut lead time.
- Initial adjustment와 후속 invalidation의 재실행량, 실제 reuse·CPU·메모리·report/plan bytes.
- Leader에게만 X가 늦는 경우, 침묵하는 f명과 느린 정상 노드, report 없음, timer 재시작 공격, 동일 snapshot 동점·계산 중 cut 도착.
- Stale parent·보고 중복·위조 refs·leader 변경·성능 조작을 검증한다.

실행 이력은 offline 평가에만 사용한다. Report 점수가 실제 절약 실행량을 설명하는지 확인해야 한다. 작은 cut과의 차이는 별도의 plan 결정 quorum이 없다는 점이지만 비용 우위나 novelty는 측정·문헌 비교 대상이다.

남은 의무는 report/window 형식, 후보 집합·bounds·tie-break·변경 억제 파라미터, stale 계산 취소, 가용성·복구, exact-order cut adapter의 safety/liveness다. 이전 positioning 갱신 뒤 추가된 Native 결합 검토와 지표·비교군 정리는 로컬 문서에만 반영했다. Google Docs·코드·영문 manuscript·LaTeX/PDF의 최신 동기화를 주장하지 않는다.
