# Baton: Execution-Aware Ordering for Autobahn

> [Google Doc 원문](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) · [동반 문서](baton-implementation-spec.md) · 2026-09-30 수동 동기화. 이후 사용자 결정과 Google Doc의 최신 revision이 이 snapshot에 우선한다.

한국어 리뷰 초안 · 연구 설계 및 평가 계획

이 초안은 구현 전 연구 문서다. Direction 기반 cut이 선택 prefix를 보존해야 한다는 요구와 조건부 논증을 정리하며, native 통합 증명이나 성능 평가가 완료되었다고 주장하지 않는다. 빨간 메모는 미완성 연구 과제를 표시한다. 상세 계약과 미채택 선택은 구현 스펙 문서에 둔다: [Baton — 구현 스펙](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit)

## 초록

Baton은 Autobahn-family consensus를 위한 execution-aware ordering extension이다. 같은 snapshot과 평가를 마친 bounded 후보 집합에서 서로 다른 2f+1명이 전체를 공유하는 가장 긴 유효 nonempty prefix를 우선하고, 없으면 sum-LCP로 유효 후보를 선택한다. 최대 f faulty identities 아래 적어도 f+1 정상 지지자가 남지만, 이는 실행 완료나 native inclusion 증거가 아니다. 핵심 요구는 leader가 선택 prefix를 포함·보존하도록 cut proposal을 구성하고 validator가 이를 검증하여, 같은 canonical 문맥의 최종 실행 순서가 그 prefix로 시작하게 하는 것이다. Report 수집은 4f+1 또는 고정 deadline에서 닫고 cut은 준비를 기다리지 않는다. Proposal별 policy 인증과 Native Multimmit의 tip extraction·extension·recovery를 이 요구에 연결하는 구체 메커니즘과 증명은 미완성이다. State finalization은 irrevocable exact order와 f+1 matching execution signatures를 함께 확인하는 endpoint다. Pre-cut execution 대비 재실행·잔여 작업·E2E 순이득은 검증할 가설이다.

[검증 필요] 2f+1 지지에서 f+1 정상 지지자가 남는 산술적 근거와 실제 성능 향상은 구분한다. Direction 선택의 최초성, exact-order 통합의 safety/liveness, Pre-cut execution 대비 추가 이득은 아직 입증되지 않았다.

## 1 Introduction

빠른 ordering consensus가 곧 application state의 빠른 확정을 의미하지는 않는다. Cut이 포함할 입력을 결정한 뒤 execution을 시작하면, application 계산과 결과 검증이 ordering 이후의 지연으로 남는다. 사용자 관점에서는 transaction이 ordering에 포함되었다는 사실뿐 아니라 잔액·정산 결과 등 application state를 확정적으로 사용할 수 있는 시점이 중요하다. Baton의 목적은 state-finalization latency를 줄이는 것이다. 이를 위해 새로운 consensus safety protocol이나 execution engine 대신, Autobahn-family consensus의 ordering 후보 선택과 speculative execution을 연결하는 execution-aware ordering extension을 제안한다.

첫 번째 접근은 execution pipeline이다. Producer는 block 생성·전파를 계속하고, validator는 block 수신·sync·기반 protocol의 투표와 speculative execution을 병렬로 진행한다. 그러나 모든 validator가 같은 시간에 같은 block을 받는 것은 아니다. 최종 ordering의 predecessor가 뒤늦게 알려지면 이미 실행한 transaction의 관측값이 달라질 수 있고, 재검증과 re-execution이 pipeline의 이득을 상쇄할 수 있다.

이 문제를 leader의 local order만으로 해결하기는 어렵다. Leader에게만 X가 늦게 도착했다면 leader는 A→B→X를 선호하지만 다른 validator들은 이미 X→A→B를 예정했을 수 있다. Leader의 순서를 고집하면 한 노드의 관측을 보존하는 대신 다수 노드의 준비를 무효화할 수 있다. 따라서 조율 대상은 실행 결과의 정확성이나 과거 execution history가 아니라, 여러 validator가 현재 실행하려는 block order이다.

Baton은 분산 intended-order feedback을 cut 구성에 반영한다. 고정 snapshot과 평가를 마친 bounded 후보 집합에서 2f+1 공통-prefix를 우선하고, 없으면 sum-LCP로 fallback한다. 선택된 유효 prefix를 leader의 cut proposal이 포함하고 같은 canonical 문맥의 선두 실행 순서로 보존해야 한다는 요구를 채택했다. Advisory direction은 proposal 전에 수정 가능하지만 인증된 proposal의 policy는 고정한다. Cut no-wait와 prefix 보존을 함께 만족시키는 adoption·availability 조건은 아직 닫히지 않았다. 기여 후보는 이 연결과 native recovery의 안전한 통합이며, 단순 pipeline 대비 순이득은 별도 검증해야 한다.

연구 질문은 다음과 같다. 기존 cut consensus를 기다리게 하거나 별도 direction 승인 단계를 추가하지 않으면서, validator들의 intended order를 ordering 후보 선택에 반영해 speculative execution을 보존하고 state-finalization latency를 줄일 수 있는가?

## 2 Background and Motivation

### 2.1 Autobahn-family ordering과 execution의 경계

Autobahn은 lane별 dissemination과 cut agreement를 결합한다. Commit된 cut에 대해 새로 선택된 lane proposals를 deterministic zipping으로 log에 배치한다. 이 final log 구성 절차가 cut 이후에 명세되어 있다는 사실은 tentative input으로 사전 실행하는 것이 원천적으로 불가능하다는 뜻이 아니다. 다만 speculation은 최종 선택과 다를 수 있다. Baton은 이 불확실성 아래 실행을 앞당기고 조정 비용을 관리하는 확장이다. [\[1\]](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

Producer lane은 block stream이고 validator는 protocol에 참여하는 identity이다. 한 노드가 두 역할을 함께 수행할 수 있지만 lane을 독립적인 state owner로 가정하지 않는다. 또한 cut에 투표한 replica가 모든 block body를 이미 보유하거나 동일한 local execution view를 갖고 있다고 가정하지 않는다. Replica는 인증된 reference를 통해 실행할 후보를 식별하고 필요한 body를 sync하면서 합의와 계산을 중첩할 수 있다.

Input DA, ordering finality, 검증된 execution result, durable state readiness는 서로 다른 사건이다. DA는 body의 복구 가능성이지 실행 완료의 증거가 아니다. 채택한 state-finalization endpoint는 대상 구간의 irrevocable exact order와 canonical input state 연결, 그리고 동일 input·범위·runtime·결과에 대한 서로 다른 해당 epoch validator f+1명의 실행 서명이 모두 검증된 시점이다. 첫 native leader-finality 관측만으로 모든 extension의 ordering이 끝났다고 보지 않는다. Read-serving node의 fetch·apply·durable 저장은 별도 readiness 지표다.

### 2.2 Pipeline의 이득과 late predecessor 문제

Original (post-cut execution): dissemination → 대상 입력의 irrevocable exact ordering → execution·validation → state finalization

Pre-cut execution: dissemination·cut consensus ∥ 수신한 blocks의 speculative execution → final cut 기준 재검증·재실행 → state finalization

그림 1. Original과 Pre-cut execution의 개념적 비교. Pre-cut execution은 실행을 consensus와 겹치되 별도의 leader direction 전파를 추가하지 않는다. Pipeline 자체는 작업 재사용을 보장하지 않으며 도식의 길이는 측정값이 아니다.

예를 들어 A가 x를 읽고 B가 A의 결과를 사용하는데, 최종 ordering에서 x를 바꾸는 X가 A보다 앞에 들어오면 A와 이에 의존하는 B를 다시 검증해야 한다. X와 무관한 작업까지 무조건 다시 실행할 필요는 없지만, dependency가 길게 연결되면 많은 후속 작업이 영향을 받는다. Application-level failure와 stale-input re-execution은 다른 현상이므로 평가에서도 분리한다.

Leader-local 관측의 비대칭도 중요하다. 공통 base priority가 X<A<B인데 일부 validator만 X를 늦게 받으면 정상 report도 A→B와 X→A→B로 갈릴 수 있다. 목표는 실제로 수신한 입력에 대한 분산 관측을 이용해 재사용에 유리한 유효 후보를 일찍 제시하는 것이다. A→B→X를 후보로 허용하려면 X<A가 변경 가능한 cross-lane 선호여야 한다. X가 A의 필수 ancestry나 이미 확정된 predecessor라면 이 후보는 점수와 무관하게 무효다. Leader-local 예시는 두 순서가 모두 유효한 경우에 한정한다.

### 2.3 공통 prefix를 사용하는 이유와 가설

X→A→B와 Y→A→B에는 A→B라는 공통 조각이 있지만, X와 Y가 다른 입력 state를 만들면 A와 B의 결과도 달라질 수 있다. 따라서 같은 canonical parent에서 처음부터 연속해 일치하는 exact prefix를 사용한다. 공통 중간 조각이나 subsequence는 지지 prefix로 세지 않는다.

2f+1을 선택한 근거는 필요한 정상 지지자의 수다. 동일 prefix 전체를 지지하는 k개 distinct reports 중 faulty identities가 최대 f이면 정상 지지자는 최소 k−f명이다. 결과 인증에 필요한 수와 같은 f+1명의 정상 지지자를 확보하려면 k−f≥f+1, 즉 k≥2f+1이어야 한다. 2f+1은 이 요구를 만족하는 최소 지지 수다. f+1 지지만으로는 최소 한 명의 정상 지지자만 보장된다. 이 산술은 거짓 보고·서명 보류·crash를 합쳐 최대 f identities라는 동일 fault budget에 한정한다.

기대하는 이득은 f+1 정상 validator가 함께 보존할 수 있는 prefix의 길이를 늘리는 것이다. 선택한 길이 k의 prefix가 최종 exact order에도 남고, 해당 validator들이 같은 canonical input state·runtime에서 그 prefix를 이미 실행했으며 dependency 검증과 해당 경계의 checkpoint가 유효하면 그 부분을 재사용할 수 있다. 모두 동일한 W개 block을 실행한 unit-cost·full-suffix-repair 모델에서는 이 정상 지지자 각각의 잔여 작업이 W−k 이하다. 가장 긴 k를 고르는 것은 이 조건부 잔여 작업 상한을 줄인다. Report는 intention이므로 실제 진척·가용성·속도·서명 도착시간까지 이 결론에 포함되지 않으며, prefix 뒤의 tail은 여전히 repair할 수 있다.

Fallback인 sum-LCP에도 제한 모델의 근거가 있다. 고정 snapshot의 m개 report가 같은 W개 block의 순열이고, 모두 같은 parent·runtime에서 이미 실행되었으며, block 비용이 1이고 첫 불일치 뒤 suffix 전체를 다시 실행한다고 하자. ℓᵢ(P)=|LCP(P,Rᵢ)|일 때 총 재실행량은 D(P)=Σᵢ(W−ℓᵢ(P))=mW−Score(P)다. 이 조건에서 후보 집합 내 raw score 최대화는 총 재실행량 최소화와 동치다. 이 등식은 fallback의 제한 모델 관찰이며 2f+1 우선 규칙이나 실제 성능의 최적성 증명이 아니다. Hysteresis가 raw 최대 후보를 선택하지 않으면 그 최적성도 그대로 적용되지 않는다.

H1은 필요한 execution 조정을 finality 이전으로 옮겨 cut 이후의 잔여 작업을 줄일 수 있다는 가설이다. H2는 여러 validator의 예정 순서를 반영하고 불필요한 direction 변경을 억제하면 총 invalidation도 줄일 수 있다는 가설이다. H1이 성립하더라도 H2는 성립하지 않을 수 있다. 총 재실행량은 비슷하지만 더 일찍 수행했기 때문에 post-cut latency만 줄어드는 경우가 있기 때문이다.

[근거 보완 M1] Intended order는 실제 진척이 아니다. 같은 제한 모델에서도 실제 완료 prefix가 eᵢ라면 재사용량은 min(eᵢ,ℓᵢ(P))다. Report에는 eᵢ가 없으므로 같은 snapshot이 반대의 실제 작업 보존 순위와도 양립한다. 실제 비용·dependency-aware reuse·서명 완료시각과의 관계는 §7의 한계이며, re-execution 감소량은 미검증이다.

## 3 System Design

### 3.1 System model과 intended-order report

기반은 Native Multimmit이며 n=5f+1의 고정 validator committee와 최대 f Byzantine identities를 가정한다. 같은 exact input·canonical input state·runtime에서 application execution은 deterministic하다. Native tip extraction·extension을 기반으로 direction-preserving cut을 구성하려 하지만 그 adaptation은 미구현·미증명이다. 원본 Autobahn의 n=3f+1, native voting thresholds, report 수집 목표 4f+1, prefix support 2f+1, 결과 인증 f+1을 서로 대체하지 않는다. [\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md)

Producer는 block 생성·전파를 계속하고 validator는 수신·sync한 입력에 대해 실행하려는 순서를 report한다. Leader는 bounded snapshot으로 direction을 선택하며, 그 prefix를 보존하도록 실제 cut proposal을 구성해야 한다. Validator는 prefix와 policy의 인증, 유효 입력·parent 및 native inclusion 연결을 검증해야 한다. 이 요구는 채택되었지만 해당 검증·ordered-delivery adapter는 아직 없다. Report 전송과 DA acknowledgement는 execution 완료를 요구하지 않는다.

Report는 같은 epoch/view·ordering 이력·canonical parent·rule·window와 exact ordered references에 결속되고 identity당 하나만 센다. 다른 문맥을 섞지 않으며, report는 현재 실행 의도의 관측 입력이다. Result proof나 direction 승인 서명으로 해석하지 않는다.

### 3.2 2f+1 공통 prefix 우선 direction 선택

고정 snapshot R과 bounded 유효 full candidates P를 같은 인증 문맥·frontier·horizon에서 비교한다. 원점은 불변 inherited ordering frontier 뒤의 새 재정렬 가능 segment 시작이다. Prefix p의 support는 그 원점에서 p 전체를 처음부터 정확히 포함하는 distinct original reports의 수다. 위치마다 다른 지지자를 모아 하나의 공통 prefix로 세지 않는다.

고정 admissible 후보 집합의 평가를 완료했을 때 support≥2f+1인 nonempty prefix의 최장 길이를 최대화하는 full candidate를 우선한다. 모든 유효 permutation에 대한 전역 탐색 보장은 아니다. 그런 prefix가 없으면 sum-LCP로, 보고나 준비된 유효 후보가 없으면 actual-parent의 유효 기본 policy로 fallback한다. 평가가 미완료이면 최장 선택을 선언하지 않고 cut no-wait 경로를 따른다. Prefix 밖의 입력을 삭제하지 않는다.

Score(P; R) = Σᵢ |LCP(P, Rᵢ)|

후보는 reported order와 incumbent에서 출발하며 필수 predecessor·ancestry·actual-parent 유효성을 검사한다. 원본 report를 삭제·삽입·renumber해 지지를 만들지 않는다. Candidate completion의 보충분도 원본 support나 LCP에 넣지 않는다. 유효성이 미확인인 후보를 높은 score만으로 채택하지 않는다.

동일 snapshot에서의 prefix 유일성은 닫을 수 있다. Identity당 exact report 하나이고 m=|R|≤4f+1이면, support≥2f+1인 두 prefix는 서로 prefix 관계다. 두 prefix가 갈라지면 하나의 exact report가 양쪽을 지지할 수 없어 지지 집합은 disjoint이고 최소 4f+2명이 필요하므로 모순이다. 따라서 유효 후보 집합에 존재하는 최장 supported prefix p*의 문자열은 유일하다. 남는 candidate tie는 같은 p* 뒤의 tail 선택이다. 이는 m≤4f+1인 report 집합 R 안의 사실이며 다른 snapshot·window·leader의 선택이나 canonical uniqueness/finality를 보장하지 않는다. Native recovery의 n−f..n vote pool은 별개이며 이를 더 큰 R로 대입해 이 유일성을 주장하지 않는다.

R1: A → B → C    R2: A → B → D    R3: A → B → E

R4: B → A → X    R5: B → A → Z

Score(A→B→C) = 3+2+2+0+0 = 7

Score(B→A→X) = 0+0+0+3+2 = 5

예시 1. n=6, f=1이면 2f+1=3이다. 다섯 report 중 R1–R3은 A→B 전체를 공유하지만 B→A의 지지는 두 명뿐이다. 따라서 길이 2의 A→B를 가진 유효 후보 A→B→C, A→B→D, A→B→E가 우선한다. 이 세 후보는 sum-LCP도 7로 같다. 예를 들어 incumbent 우선·canonical tie-break로 하나를 고를 수 있으나, 같은-prefix tail 규칙은 §3.2의 미채택 선택지다. 세 명이 같은 tail C를 승인했다는 뜻은 아니다. 위 sum 점수는 보조 설명이며 이 예시의 일차 선택 근거는 3명의 전체 prefix 지지다.

핵심 요구는 단순히 direction block을 cut에 넣는 데서 끝나지 않는다. 같은 canonical input state·runtime과 불변 frontier 뒤에서 선택 prefix p가 최종 실행 순서 O의 정확한 선두 prefix여야 한다(p ⪯ O). 예를 들어 p=A1→B1이면 둘 다 포함되어도 A1→X→B1은 보존이 아니다. Native extension으로 새 block이 나타날 수 있으므로 이를 삭제하지 않으면서 p 앞·안에 삽입하지 않는 공통 continuation이 필요하다. p가 필수 predecessor를 누락했다면 처음부터 유효 후보가 아니다. 이 invariant를 native membership·extension·view change와 연결하는 방법은 미완성이다.

Incumbent와 새 후보는 같은 snapshot·frontier·horizon에서 비교하고 더 짧은 supported prefix를 높은 sum score로 대체하지 않는다. 동일 최장 prefix 이후 tail의 선호·hysteresis와 update 규칙은 미채택이며 구현 스펙에서 다룬다. 선택 점수의 일반적 성능 최적성은 주장하지 않는다.

### 3.3 4f+1-or-deadline: 언제 direction을 전파하는가

Leader는 새 실행 후보가 생기면 window를 열고 deadline을 고정한다. 유효 distinct reports가 처음 4f+1에 도달하거나 deadline이 먼저 처리될 때 R을 한 번 닫고 초과·후속 reports를 제외한다. 따라서 m=|R|≤4f+1이다. 새 도착은 deadline을 연장하지 않으며 서로 다른 leader의 동일 snapshot을 가정하지 않는다.

고정 R에 2f+1 공통-prefix 우선 규칙과 sum-LCP fallback을 적용한다. Support를 채우려고 window를 연장하거나 추가 ACK를 기다리지 않는다. Deadline에 보고가 2f+1보다 적으면 일차 조건은 성립할 수 없으므로 확보한 보고로 fallback하며, 보고가 없으면 유효 기본 ordering을 사용한다. Cut의 독립적인 no-wait 경로는 유지한다.

Collection 시작 → [4f+1 reports OR local deadline] → 2f+1 prefix 우선 또는 sum-LCP fallback → 필요 시 direction 전파

Cut ready → 준비된 유효 후보 또는 기본 ordering 사용 → 기존 cut consensus

그림 2. Collection과 cut의 독립 경로. Cut은 report 수, deadline, optimizer 완료를 기다리지 않는다. 두 collection trigger가 동시에 발생해도 window는 한 번만 닫는다.

n=5f+1에서 4f+1 distinct reports에는 적어도 3f+1명의 정직한 보고자가 포함되고 빠진 identity는 최대 f명이다. 이는 관측 coverage에 대한 산술적 사실이지 같은 prefix에 대한 지지나 execution 완료를 뜻하지 않는다. Byzantine f명이 침묵하면 strict 4f+1 조건은 정직한 노드 전부를 기다리게 되므로 deadline fallback이 필요하다. Deadline에 더 적은 report로 계산한 경우에는 위 coverage를 주장하지 않는다.

[연구 과제] 고정 deadline은 후보 검증·계산의 완료 상한이 아니다. Bounded reference 목록에도 더 긴 필수 ancestry가 있을 수 있다. 유한 계산·검증 계약과 준비된 actual-parent fallback이 필요하며, 미완료 탐색을 최장-prefix 선택으로 선언하거나 native validity·availability 검사를 생략해서는 안 된다. 새로운 prefix 보존 요구와 no-wait가 양립하는 adoption 조건도 명세해야 한다.

### 3.4 Execution pipeline과 final cut의 연결

Validator는 유효 direction으로 미시작 작업의 scheduling을 조정하고, 진행·완료한 작업은 입력과 dependency를 검증해 재사용하거나 repair한다. Direction 자체는 execution correctness를 인증하지 않는다. 서로 다른 speculative root만으로 Byzantine behavior를 판정하지 않는다.

Proposal 이전의 direction은 수정 가능한 실행 안내다. 실제 proposal은 선택 prefix와 그 해석 policy를 exact parent·ordering frontier에 결속해 고정해야 한다. 늦은 report·optimizer 완료·native vote-pool 증가는 같은 인증 proposal의 policy를 바꾸지 않는다. Report snapshot의 종료와 prefix 보존 대상으로 채택되는 시점은 별개이며, 후자의 조건은 아직 정하지 않았다.

Parent나 ordering frontier가 달라지면 이전 direction을 그대로 재사용할 수 없다. 미완료 inherited segment도 원래 인증 policy로 해석하고 새 방향은 재정렬 가능한 새 segment에만 적용한다. Frontier가 unresolved인 상태에서 report 앞부분을 임의 제거해 유효 후보로 만들지 않는다. Ordering 경계와 canonical input state가 materialize된 시점도 구분한다.

선택 prefix·policy·해석 rule·exact parent를 leader block의 인증 subject에 결속하고 validator가 보존 조건을 검증해야 한다. Authentication만으로 block/policy availability나 native inclusion이 따라오지는 않는다. 2f+1 intention reports는 ordinary payload에 필요한 3f+1 positive position votes 또는 extension carry의 n−f native support를 대신하지 못한다. 이미 준비된 DA-certified anchor로 prefix block을 포함시키는 native 경로는 검토할 연결 후보지만, cross-lane 선두 순서 보존과 recovery까지 증명된 해법은 아니다. [\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md) [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

Fallback은 proposal 인증 전의 선택 규칙이다. 인증 뒤 policy 내용이 누락되었다고 같은 proposal을 기본 policy로 재해석해서는 안 된다. 인증된 내용을 복구하거나 기반 recovery 경로를 따른다. 첫 L-QC 관측을 모든 extension의 최종 위치가 확정된 사건으로 간주하지 않으며, native ordered delivery가 이미 방출한 prefix는 이후 pool 증가로 바꾸지 않는다.

Pinned Commonware에는 ordering policy field가 없고 tip-history commitment만으로 cross-lane order를 복구할 수 없다. Native certificates는 sparse agreement facts를 제공하며 dense ordered delivery, policy 내용·방출 근거와 cursor의 복구는 별도 marshal 의무다. 소스 경계 확인은 Baton의 구현·증명이 아니다. [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

State finalization은 대상 구간의 irrevocable exact order와 canonical input state 연결, 그리고 동일 statement에 대한 서로 다른 해당 epoch validator f+1명의 유효 실행 서명을 모두 검증했을 때 수용한다. 이 endpoint는 채택된 설계다. Leader 서명·V-QC·높은 score만으로 수용하지 않는다. Speculation은 그전에 계속할 수 있지만 canonical 채택에는 두 조건이 모두 필요하다. 결과 인증과 local body fetch·apply·durable 저장 완료는 구분한다. [\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md)

실행 statement는 epoch, canonical 구간과 exact ordered input, 올바른 input state, runtime·환경, 전체 result를 모호함 없이 식별한다. 같은 의미의 실행이라면 QC transcript가 달라도 statement는 같을 수 있고, 범위·input state가 다르면 별개다. Wire encoding은 구현 스펙의 미결정 사항이다.

선택 prefix, irrevocably emitted prefix, 인증된 실행 구간은 구분한다. 선택 prefix 보존은 새 cut 요구이지만 unresolved slot 때문에 아직 전체가 방출되지 않을 수 있다. Reports가 A→B를 공유해도 A→B→C→D의 certificate는 자동 생성되지 않는다. 보존한 실행을 completion에 연결하려면 공통 서명 경계와 해당 중간 결과를 제공할 수 있어야 한다.

정직한 signer는 exact 문맥에서 직접 실행한 결과를 검증한 뒤 서명한다. 다른 node의 receipt나 signature를 복사해 자신의 실행 서명을 발행하지 않는다. Signer를 특정 ordering QC의 투표자 부분집합으로 제한하지 않으며, 늦게 따라온 해당 epoch validator도 참여할 수 있다. Identity 중복은 한 번만 센다. 긴 speculative root나 다른 범위의 서명을 잘라 짧은 구간의 결과로 사용할 수 없다.

[통합 의무] 채택된 상위 요구는 선택 direction prefix를 보존하는 cut 구성·검증, proposal별 authenticated policy 고정, exact-order와 f+1 결과 인증 endpoint다. Availability/adoption 조건, common continuation, actual-parent 및 view recovery 결속은 미완성이다. Prefix commitment 추가만으로 보존이나 native integration safety가 증명되지는 않는다.

## 4 Correctness and Liveness

### 4.1 Safety의 근거와 비근거

Safety의 출발점은 report 수나 score가 아니라 인증된 해석과 irrevocable exact input이다. 다음은 검토 중인 policy 계열의 조건부 prefix 보조정리다. 한 segment에서 공통 이력 H·tip 원점 T·고정 sweep σ를 사용하고, σ가 ancestry를 지키며 모든 slot을 한 번씩 유한 순위에 열거한다고 하자. 추출 결과 F와 settledness S가 동일 block identity의 공통 completion G와 양립하고, settled chain은 G에서 더 늘지 않는다고 가정한다. σ를 따라 포함 block을 출력하고 settled-empty slot은 건너뛰되 unsettled-empty slot에서 멈추는 Emit(F,S)는 Ord(G)의 prefix다.

이유는 출력 전에 방문한 각 slot이 G와 같은 block을 내거나 G에서도 빈 위치이기 때문이다. 미확정 빈 위치를 넘어가지 않으므로 G의 predecessor를 누락한 채 뒤의 block을 출력할 수 없다. 따라서 서로 다른 유효 pool의 출력도 같은 Ord(G)의 prefix로서 양립한다. 단, 공통 completion·settledness 가정은 native extraction/branch 규칙에서 독립적으로 도출해야 한다. 같은 tip 집합마다 결정론적으로 재정렬하는 것만으로 extension 간 prefix 보존이 따라오지는 않는다. [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

Emission에서 확인된 포함 block은 출력하고, 인증 근거로 해당 segment에서 영구히 빈 위치만 건너뛰며, unresolved 위치에서는 멈춰야 한다. Terminal 판단과 block identity를 extension·recovery가 번복하지 않아야 한다. Local 부재나 timeout은 skip 근거가 아니다. 이러한 조건을 실현할 slot·evidence 표현은 구현 스펙에 둔다.

Finalized tip이 같아도 pool별 settledness가 달라질 수 있으므로 tips나 임의 quorum subset만으로 이전 emission을 재현하지 않는다. Terminal 판단의 인증 근거나 검증 가능한 checkpoint가 복구되어야 한다. 원문의 Lemmas 7–8은 native extraction과 공통 sweep을 연결하지만 변경 policy의 common completion이나 선택 prefix 보존을 자동 증명하지 않는다. [\[10\]](https://arxiv.org/pdf/2607.21021v2) [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

동일 snapshot에 대한 deterministic 선택은 재현성을 제공하지만, 서로 다른 snapshot이나 Byzantine leader의 direction이 같은 순서를 만든다는 보장은 아니다. 4f+1은 report 수집 목표, 2f+1은 하나의 전체 prefix에 대한 direction-selection support, f+1은 exact-context 실행 결과의 서명 수다. 이들을 서로 다른 단계의 수로 구분한다. 2f+1 support에는 정상 지지자가 적어도 f+1명 있지만 이는 intended order의 지지이며 실행 완료·ordering vote·finality certificate가 아니다. 별도 direction 승인 quorum을 만들거나 이 support만으로 canonical uniqueness를 증명하지 않는다.

결과 안전성은 별도 조건부 논증이다. 최대 f Byzantine identities, 인증된 epoch membership, 서명 위조 불가, 서명 subject의 모호함 없는 encoding과 사용한 digest의 collision resistance, deterministic execution 및 정직한 직접 실행·검증을 가정하면 f+1 matching signatures에는 정직한 signer가 적어도 한 명 있다. 따라서 그 결과는 서명된 exact 문맥의 결정론적 결과다. 수용자가 구간의 irrevocable order와 canonical input state 연결까지 확인하면 잘못된 canonical 결과는 수용되지 않는다. 동일 exact 문맥의 두 결과 certificate가 다르다면 각각의 정직한 signer가 다른 결정론적 결과를 계산했다는 모순이다. 두 f+1 signer 집합 사이의 교집합은 필요하지 않으며, f+1을 ordering quorum으로 쓰지 않는다.

첫 canonical input state가 정당하고 후속 구간이 검증된 이전 output에 연결되면 결과 안전성을 구간별로 적용한다. 다른 parent에서 계산한 올바른 결과도 canonical 결과로 채택하지 않는다. Cache 재사용은 dependency 검증을 통과해야 하며 speculative effect와 확정 state를 분리한다.

### 4.2 Byzantine behavior

거짓 report와 중복 identity. Byzantine validator는 실행할 의사가 없는 order를 보고하거나 상충 report를 보낼 수 있다. 서명·committee·context·window 검증과 identity당 한 번의 계수로 수 부풀림을 막는다. 최대 f faulty identities 아래 valid 2f+1 support에 f+1 정상 지지자가 포함된다는 bound는 유지되지만, 거짓 보고가 supported-prefix 선택이나 fallback score를 유리하게 조작하여 성능을 악화시킬 수 있다. 서명은 intention의 진실성이나 실행 진척을 증명하지 않는다.

Byzantine leader의 direction equivocation과 선택 편향. Leader가 서로 다른 valid direction을 전파하거나 자신에게 유리한 report만 사용하면 speculative execution이 갈릴 수 있다. Node는 유효성 조건을 검사하고 기존 합의가 확정한 exact order만 canonical하게 채택한다. 이에 따라 잘못된 state 채택을 막는 것과 좋은 latency·공정성을 보장하는 것은 다르다.

잘못된 block과 누락된 body. Report의 서명만으로 body의 무결성·DA·application semantics가 검증된 것은 아니다. Digest·인증·ancestry를 검사하고 필요한 입력은 기존 복구 경로에서 가져온다. 높은 score를 이유로 필수 predecessor를 생략하지 않는다. Producer가 멈춘 경우 기반 합의의 lane progress 규칙을 따르며 해당 producer의 transaction 포함을 무조건 보장하지 않는다.

침묵·지연·report flood. Report가 부족하면 고정 deadline에서 fallback하고 cut은 기다리지 않는다. 메시지 크기·window별 identity 수·계산량을 제한하여 무제한 report로 실행과 합의 자원을 소모하지 않도록 한다. 다만 논리적인 no-wait가 CPU·네트워크 간섭까지 없앤다는 의미는 아니다.

새 leader·recovery node는 local arrival order나 마지막 hint 대신 인증된 exact anchor·segment policy를 복구해야 한다. 새 view의 canonical order는 이전 인증 이력에서 정상 node들이 합법적으로 방출한 모든 prefix를 확장하고, 보존 대상으로 채택한 direction prefix도 유지해야 한다. 자신의 마지막 prefix나 chain-local tips만 보존하는 것은 부족하다. 원문의 Ord 재귀에 각 segment policy와 복구 가능한 emission 근거를 연결하는 Baton 귀납 증명은 미완성이다. [\[10\]](https://arxiv.org/pdf/2607.21021v2) [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

### 4.3 Liveness와 non-blocking의 범위

진행성은 ordering, ordered delivery, 결과 인증을 나누어 본다. 기반 진행성 가정, consensus 작업의 공정한 처리와 fallback 검증의 유한 종료 아래 direction이 준비되기 전 proposal은 기다리지 않고 진행한다. 다만 모든 ready cut이 아직 native adoption 근거가 없는 선택 prefix를 반드시 보존해야 한다면 이를 버리는 fallback과 양립하지 않는다. Prefix를 언제 보장 대상으로 채택할지는 핵심 미해결 계약이다.

둘째, 고정 sweep에서 포함 block의 slot 순위가 유한하고 앞선 모든 slot이 결국 동일 block 또는 정당한 settled-empty로 판명되면 Emit은 그 block까지 전진한다. 앞선 유한개 slot의 확인이 끝나기 때문이다. Finite rank만으로 unresolved slot이 풀리는 것은 아니므로 native 증거의 eventual resolution을 함께 요구한다. 이 논증은 native inclusion 자체나 고정 시간 상한을 보장하지 않는다.

셋째, canonical order·input state·body/runtime 자료가 결국 준비되고, 같은 공통 실행 경계에 대해 적어도 f+1 정상 validator가 직접 실행한 statement를 제공하며, 서명이 재요청·전달·검증될 수 있다면 결과 인증도 결국 완료된다. 각 node가 자기 최신 prefix에만 서명하면 모두 정직해도 범위가 달라 certificate가 모이지 않을 수 있다. Catch-up이 중간 경계를 건너뛰어도 필요한 결과를 보관하거나 재실행해 제공할 수 있어야 하며 단일 collector가 유일한 서명 보관본이어서는 안 된다. 다른 signer의 certificate를 기다린 뒤에만 다음 speculation을 시작하는 새 barrier는 요구하지 않는다. [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

서비스하기로 한 구간의 결과 인증이 결국 완료되려면 matching 서명 또는 직접 재실행·검증할 자료가 결국 접근 가능해야 한다. 현재 state root나 f+1 서명만으로 과거 중간 결과의 재제공·durability가 보장되지는 않는다. 미완료 요청의 의무를 보존할 retention·checkpoint 계약은 필요하지만 무기한 과거 서비스와 bounded storage를 동시에 무조건 약속하지 않는다. 구체 GC 계약과 반례는 구현 스펙에 둔다.

여기서 no-wait는 direction 수집·계산·승인의 완료를 native consensus의 선행조건으로 두지 않는다는 계약이다. 2f+1 supported prefix가 없어도 sum-LCP 또는 유효 기본 ordering으로 진행하며, support를 채우기 위해 cut을 늦추지 않는다. Native availability·settledness·body retrieval·canonical-parent readiness·application dependency 대기는 남는다. 고정 policy의 앞선 unsettled slot x 뒤에 준비된 y가 있어도 x가 해결되기 전에는 y를 canonical prefix로 내보낼 수 없는 경우가 있다. 높은 prefix support가 이 head-of-line blocking이나 자원 간섭을 없애거나 latency 상한을 주지는 않는다.

[통합 의무] Native inclusion과 exact leading-prefix 보존, 인증 이력에 걸친 prefix 확장, dense delivery와 동일 execution statement의 eventual 제공을 실제 경로에서 증명해야 한다. 이 절은 명시한 가정의 귀결이며 완성된 native safety/liveness 증명이나 fault-injection 결과가 아니다.

## 5 Evaluation

### 5.1 비교 구성과 연구 질문

평가는 Original, Pre-cut execution, Baton의 세 구성을 비교한다. Original→Pre-cut execution은 execution pipeline 자체의 효과를, Pre-cut execution→Baton은 intended-order 기반 direction 조율의 추가 효과를 분리한다. 재실행과 cut 이후 잔여 작업을 측정하고, Baton의 report 수집·계산·통신·초기 조정 비용을 포함해 ingress-to-state latency에서도 순이득이 유지되는지 확인한다.

(1) Original: 대상 입력의 irrevocable exact order를 도출한 뒤 application execution을 시작한다. (2) Pre-cut execution: 각 validator가 실제 수신한 blocks를 기존 ordering rule에 따라 사전 실행한다. 늦은 predecessor나 final cut의 입력·순서와 달라진 부분은 재검증·재실행한다. Leader의 별도 사전 direction 전파나 intended-order 수집은 추가하지 않으며, 아직 알려지지 않은 block이나 final cut의 완전한 순서를 미리 안다고 가정하지 않는다. (3) Baton: 동일한 pre-cut execution 기반에 validator들의 intended-order 수집과 2f+1 공통-prefix 우선·sum-LCP fallback direction 선택·전파와 해당 prefix를 보존하는 cut 구성·검증을 추가한다. Leader-local direction 또는 early proposal을 별도 baseline으로 두지 않는다.

동일 committee, consensus profile, application semantics, execution backend와 자원 budget을 사용한다. 새로운 backend 자체의 성능을 Baton의 이득으로 세지 않는다. 채택한 기반은 Native Multimmit이며 tip 추출·extension을 유지한다. Ordering policy 인증·ordered delivery adapter에서 무엇을 유지하거나 변경했는지 명시하고, 미구현 변경이나 기존 toy model 결과를 Baton의 E2E 결과라고 부르지 않는다. 세 주 비교군과 별도로 Baton 내부의 prefix 선택·변경 억제 및 timer-only / strict 4f+1 / 4f+1-or-deadline을 ablation으로 비교한다. Cut 빈도 변화는 Pre-cut execution과 Baton에 적용하는 보조 실험으로 구분한다.

### 5.2 Workload와 측정 지표

핵심 축은 validator RTT와 transaction당 application state operation 수이다. Offered load, conflict density, block 크기, lane 간 도착 불균형, body sync 지연, τ, horizon W 및 개선 폭도 변화시킨다. RTT나 operation 수의 변화가 payload 크기·conflict를 동시에 바꾸는 경우 이를 따로 기록한다. Application 실패와 speculation invalidation을 합쳐 failed transaction 비율 하나로 보고하지 않는다.

Δstate = Tstate-finalization − Tordering-finality

LE2E = Tstate-finalization − Tingress

Ingress-to-state와 cut-to-state의 p50/p95/p99, ordering latency, successful goodput, durable readiness를 보고한다. 각 구간은 같은 관찰자의 clock으로 측정하고 최초 ingress 시각을 retry 때 초기화하지 않는다. Primary completion은 관찰 node가 대상 구간의 ordering evidence, canonical input state 연결, f+1 matching execution signatures를 모두 검증한 시점이다. 세 비교군에 같은 수용 기준을 적용한다. Native leader finality와 입력의 irrevocable ordering 도출 시점은 구분하고, 추가한 결과 인증 대기를 원래 시스템의 native latency라고 부르지 않는다.

Mechanism 지표로 threshold/deadline/cut-preemption 비율, report 수, 수집·계산 시간, direction-to-cut lead time, direction 변경 횟수, 초기 조정과 후속 invalidation의 실행량, CPU·메모리·network bytes를 측정한다. 선택한 supported prefix와 fallback LCP score가 실제 재사용 작업량과 어떤 관계를 갖는지 확인한다. Leader 선택은 intended-order report만 사용하고, 실제 execution history는 offline 분석에만 사용한다.

### 5.3 유리한 경우·불리한 경우와 정확성 검증

Leader에게만 X가 늦는 경우와 다수 validator에게 X가 늦는 경우를 분리한다. 공통 prefix가 긴 경우, report가 크게 갈리는 경우, f명이 침묵하고 정직한 한 노드가 느린 경우, report가 전혀 없는 경우를 포함한다. 점수는 높지만 실행 진척과 무관한 경우도 만들어 heuristic이 잘못 선택하는 범위를 드러낸다.

작은 deterministic harness에서는 동일 점수 tie, duplicate/stale report, threshold와 deadline의 동시 발생, 계속되는 report로 timer 연장을 유도하는 상황, optimizer 도중 cut 도착, leader 교체를 검사한다. 동일한 finalized order·parent·runtime의 sequential oracle과 state root 및 application outputs가 일치해야 한다. 이 시험은 성능 분석을 대규모 공격 연구로 확장하기 위한 것이 아니라 새 경계 조건을 검증하기 위한 것이다.

Open-loop 부하에서 queue 증가와 미완료 요청을 포함하고 독립 반복을 수행한다. Cut을 늦춰 Δstate만 줄이는 결과를 개선으로 보지 않는다. 총 re-execution은 줄지 않았지만 H1의 post-cut 잔여 시간이 줄어든 경우와, H2까지 충족해 총 wasted work도 줄어든 경우를 구분한다.

[실험 필요 E1–E3] 본 절은 평가 계획이며 결과가 없다. 공정한 Original / Pre-cut execution / Baton 구현, Commonware adapter, 자원 설정, τ·W·update 정책, 표본 수와 반복 수를 고정해야 한다. Original 대비 이득만으로 direction 조율의 효용을 주장하지 않는다. Pre-cut execution 대비 재실행·state-finalization latency 및 E2E 순이득이 확인되지 않으면 추가 기여의 주장 범위를 축소해야 한다.

## 6 Related Work

Autobahn은 독립적으로 성장하는 dissemination lanes, certified tips의 cut, consensus와 병렬적인 sync 및 deterministic zipping을 제공한다. 이 기반 구조와 pipeline 일반은 Baton의 새 기여가 아니다. 원 논문의 n=3f+1 모델과 현재 Native Multimmit의 n=5f+1 profile을 구분한다. Baton의 통합 과제는 native tip 추출·extension을 유지한 채 선택된 authenticated policy를 irrevocable exact-order delivery에 연결하는 것이다. [\[1\]](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

Hermes는 prefix consensus를 이용해 prefix 자체를 finalize하는 연구이다. Baton은 Hermes를 채택한 protocol이 아니며, 2f+1 reports가 공유하는 mutable direction prefix에도 별도 finality를 부여하지 않는다. Hermes의 quorum·prefix safety 성질을 Baton의 report 수집이나 direction-selection support에 옮겨 적용하지 않는다. [\[2\]](https://arxiv.org/html/2607.25916v2)

Rashnu는 data-dependent receive order를 local DAG로 보고하고, leader가 n−f 보고로 global graph를 구성하며, replicas가 첨부 보고를 검증한 뒤 BFT consensus를 수행한다. 목적은 data-dependent order-fairness다. 따라서 local-order aggregation, ordering/consensus 분리, 별도 direction 승인 단계가 없다는 사실만으로 차별성을 주장하지 않는다. Baton의 intended order와 exact-block LCP는 fairness certificate가 아니며 Rashnu의 보장을 제공하지 않는다. 입력·목적·검증 계약의 차이가 곧 성능 우위를 뜻하지도 않는다. [\[3\]](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)

SpeedyFair는 optimistic fair ordering(OFO)을 consensus와 분리해 연속 실행하고, 선택된 local-order 입력을 공유하여 leader와 replicas의 order 계산을 병렬화한다. Threshold-signature QC로 fair-order fragment를 consensus에 연결한다. 따라서 ordering 준비를 consensus critical path에서 분리하는 발상 자체도 Baton의 단독 기여가 아니다. Baton의 2f+1 report support는 mutable execution direction의 선택 기준이며 SpeedyFair의 certified fair-order fragment와 계약이 다르다. 본 연구의 intended-order feedback·native extension 통합이라는 목적은 유지하되, 분리 구조나 지지 수만으로 fairness와 성능 우위를 주장하지 않는다. [\[8\]](https://www.ndss-symposium.org/wp-content/uploads/2024-693-paper.pdf)

Bidl은 sequencer의 sequence number로 BFT consensus와 speculative execution을 병렬화하고 합의된 순서와 다르면 재실행한다. 따라서 overlap과 mismatch repair 자체는 Baton의 새 기여가 아니다. Bidl의 order hint는 sequencer가 부여하며, 여기서 검토하는 차이는 여러 validator의 intended order를 최종 ordering policy 선택에 피드백하는 것이다. 또한 Bidl §4.4는 non-deterministic 결과를 별도의 approve/persist 경로로 일치·복구 가능하게 만드는 문제를 다룬다. Baton의 f+1 결과 유일성 논증은 고정된 exact 문맥의 deterministic execution에 한정되며 Bidl의 이 기능을 제공한다고 주장하지 않는다. Feedback의 실익은 안전한 통합과 동일 pre-cut baseline 대비 추가 순이득으로 확인해야 한다. [\[5\]](https://www.cs.hku.hk/~heming/papers/sosp21-bidl.pdf)

PoE(Proof-of-Execution)는 준비 단계 뒤 speculative execution을 수행하고, matching inform responses로 구성한 proof-of-execution과 view-change 절차를 연결하여 client가 수용한 요청이 rollback되지 않게 한다. 따라서 speculation과 실행 응답을 이용한 인증도 선행 연구가 있다. Baton에서는 2f+1이 intention-prefix 선택 기준이고, f+1 실행 서명은 별도로 irrevocable order·canonical input state를 확인한 뒤 결과를 수용하는 근거다. PoE의 실행·복구 certificate와 이 두 수를 동일시하지 않으며, 숫자가 비슷하다는 이유로 안전성 증명을 가져오지 않는다. [\[9\]](https://openproceedings.org/2021/conf/edbt/p111.pdf)

HotStuff-1도 consensus에서 speculation을 사용하는 선행 연구다. Baton의 차별성은 speculation 자체에 두지 않는다. Mutable scheduling direction과 speculative client commitment를 구분하고, 여러 intended-order reports의 feedback이 무엇을 바꾸는지에 한정하여 비교한다. [\[4\]](https://arxiv.org/html/2408.04728v3)

[기여 범위 R1] 현재의 좁은 기여 후보는 parallel dissemination 위의 분산 intended-order feedback, bounded direction 선택, authenticated policy와 native extension·recovery의 안전한 통합이다. 이 문헌 비교는 관련 원문의 targeted comparison이며 최초성의 전수검증이 아니다. 통합 correctness는 조건부 논증을 native 경로에서 닫아야 하고, Pre-cut execution 대비 repair·잔여 작업·state-finalization latency의 순효과는 결과가 없는 가설로 남긴다.

## 7 Discussion and Limitations

LCP는 보수적이고 단순한 proxy다. Dependency-aware 실행은 LCP 밖의 독립 작업도 재사용할 수 있고, block별 비용·report freshness·node별 진척과 처리 속도는 다르다. 따라서 §2.3의 총량 등식은 제한 모델에서만 성립한다. 더구나 모든 report가 완전히 실행되었고 비용·속도가 같아도, q개 결과가 준비되는 이상화한 계산 시간은 Tq(P)=W−q번째로 큰 ℓᵢ(P)다. LCP 합 최대화와 q=f+1번째 완료시각 최소화는 다른 목적이다.

설명용 반례로 W=7, n=6, f=1에서 다섯 보고자의 LCP를 P에 대해 (7,4,4,0,0), Q에 대해 (0,0,0,7,7)로 두고 여섯째 node에는 재사용 작업이 없다고 하자. P의 score는 15로 Q의 14보다 높고 총 잔여 작업도 작지만, 두 결과가 준비되는 계산 성분은 P에서 3, Q에서 0이다. Reports ABCDEFG, ABCDFGE, ABCDGEF, EFGABCD, EFGABCD와 후보 P=ABCDEFG, Q=EFGABCD로 구성할 수 있다. 각 순서가 유효한 독립 block 사례를 가정한 분석적 반례이며 실제 정상 도착 trace의 빈도나 측정 결과가 아니다.

실제 completion에는 ordering evidence와 동일 범위·parent·runtime·result의 f+1 matching signatures 수신·검증이 모두 필요하다. 위 식은 그중 이상화한 계산 성분뿐이다. Sum-LCP의 총량 절약이 f+1번째 완료시각의 최소화를 뜻하지 않는다는 점은 공통-prefix 지지를 따로 고려하는 동기다. 다만 채택한 2f+1 규칙의 이득은 f+1 정상 intention의 공통 기반이다. 이 반례에서도 세 명이 ABCD를 공유하는 P 쪽을 우선하므로, 실제 두 번째 결과의 완료시각을 최소화하는 규칙은 아니다. Remote progress proof를 새로 추가하지 않으며 실제 latency·throughput의 개선 여부는 가설로 남긴다.

2f+1 지지는 f+1 지지보다 정상 지지자 수에 보수적인 조건이다. 같은 snapshot·candidate set에서 지지 수를 높이면 선택 가능한 최장 prefix가 더 짧아지거나 사라질 수 있고, 전체 validator의 sum-LCP가 더 큰 후보를 포기할 수도 있다. 따라서 총 재실행량·자원 효율·throughput의 최적성을 주장하지 않는다. 반면 faulty supporter가 최대 f명 빠져도 f+1 정상 지지자가 남는다는 점이 선택의 이유다. 이들이 실제로 함께 재사용·서명하려면 최종 exact prefix 보존, 실행 진척·checkpoint, 공통 서명 범위와 전달 조건을 별도로 만족해야 한다.

4f+1-or-deadline은 넓은 관측과 빠른 direction 선택 사이의 trade-off다. Threshold를 기다리면 느린 정상 node가 영향을 주고, 짧은 deadline은 적은 관측으로 fallback하게 하거나 불리한 후보를 고르게 할 수 있다. 2f+1 support가 없다는 이유로 deadline이나 cut을 연장하지 않는다. 수집·전파가 늦으면 일반 cut proposal보다 앞서 조율할 시간이 없을 수 있으며, support 충족도 freshness·실행 준비도의 보장은 아니다.

보존 요구가 완성되어도 실행 진척이나 같은 input state에서의 실행을 reports가 증명하지는 않는다. Proposal 이전의 direction 변경, actual-parent 변화와 prefix 밖의 tail에는 repair가 남을 수 있다. 보존 대상으로 채택한 prefix 자체의 누락·중간 삽입은 허용하려는 결과가 아니라 방지할 설계 실패다. 이 요구는 inclusion fairness, MEV 방지 또는 모든 transaction의 bounded inclusion을 보장하지 않는다.

별도 approval round가 없더라도 수집·검증·계산·전파의 CPU와 bandwidth 비용은 존재한다. Consensus 자원을 잠식하면 논리적인 no-wait도 실제 ordering latency를 높일 수 있다. 본 연구는 state-owner sharding, producer placement, ZK proof/PAC, repair lane이나 과거 fixed-cut 모델을 재도입하지 않으며 그 효과를 현재 direction의 성과로 합산하지 않는다.

가장 중요한 남은 문제는 선택 prefix를 포함·보존하는 native proposal 검증과 common continuation을 no-wait·view recovery에 연결하는 것이다. 이 조건이 닫혀야 §2.3의 재사용 bound를 Baton의 정상 경로에 적용할 수 있다. Report/window 표현, tail·hysteresis, policy 전달, 서명 경계와 retention의 구체 선택은 구현 스펙으로 분리했다. 네 기존 선택은 모두 미채택이며 실제 성능은 이후 평가해야 한다.

## 8 Conclusion

Baton은 분산 intended order에서 2f+1 전체-prefix를 우선 선택하고, leader가 그 prefix를 보존하는 cut을 구성·인증하며 validator가 검증하도록 하는 execution-aware ordering extension이다. 2f+1은 f+1 정상 지지자를 확보하는 최소 수지만 native inclusion certificate는 아니다. 4f+1-or-deadline 수집, cut no-wait와 f+1 결과 endpoint를 유지하면서 정확한 prefix 보존을 실현하는 native adaptation·recovery 증명은 남아 있다. Prefix가 보존되고 같은 canonical 문맥에서 실행되었을 때의 잔여 작업 bound가 설계 근거이며, 실제 latency·재실행·E2E 개선은 완료된 결과로 주장하지 않는다.

목표는 작은 finality를 반복해서 만드는 것이 아니라 기존 finality 이전의 시간을 활용하여 state finalization까지 남는 작업을 줄이는 것이다. 재실행 감소와 E2E 이득은 앞으로 검증할 결과이다. Original→Pre-cut execution으로 pipeline의 효과를, Pre-cut execution→Baton으로 intended-order 기반 direction 조율의 추가 효과를 확인하고, 어떤 조건에서 이득이 나타나고 사라지는지 밝히는 것이 연구의 완성 기준이다.

## References

[\[1\]](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf) Autobahn: Seamless high speed BFT. SOSP 2024.

[\[2\]](https://arxiv.org/html/2607.25916v2) Hermes: Low Tail-Latency Via Prefix Consensus. arXiv preprint, v2.

[\[3\]](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf) Rashnu: Data-Dependent Order-Fairness. PVLDB 17, 2024.

[\[4\]](https://arxiv.org/html/2408.04728v3) HotStuff-1: Linear Consensus with One-Phase Speculation. arXiv, v3.

[\[5\]](https://www.cs.hku.hk/~heming/papers/sosp21-bidl.pdf) Bidl: A High-throughput, Low-latency Permissioned Blockchain Framework for Datacenter Networks. SOSP 2021, §§3.2, 4.2–4.4.

[\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md) Overpass design memo. Native Multimmit 및 policy·결과 인증 채택 조건, §§7.1–7.2.

[\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md) Overpass submission-readiness review. 조건부 ordering·recovery와 실행 서명 범위 검토, §§23–25.

[\[8\]](https://www.ndss-symposium.org/wp-content/uploads/2024-693-paper.pdf) SpeedyFair: Separation is Good: A Faster Order-Fairness Byzantine Consensus. NDSS 2024, §§I, IV.

[\[9\]](https://openproceedings.org/2021/conf/edbt/p111.pdf) Proof-of-Execution: Reaching Consensus through Fault-Tolerant Speculation. EDBT 2021, §3.

[\[10\]](https://arxiv.org/pdf/2607.21021v2) Lewis-Pye and O’Grady. Multimmit: Extending Blocks for Faster Finality. arXiv:2607.21021v2, §§4.2, 5.1, 5.3 (Lemmas 7–8, Theorem 1, Corollary 3).

[\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md) Commonware monorepo, pinned commit 534af0ede48affd35b2111522527547b4cc9bf72. Multimmit STATE_MACHINE.md; types/block.rs, vote.rs, history.rs; machine/algebra/tips.rs. Consensus/marshal ownership, re-anchor 및 settledness 경계.
