# Overpass: 첫 native 검증 명세와 E2E 실험 계획

> 2026-09-30. **문서 단계의 검증 계획**이며 구현·테스트 통과·성능 결과가 아니다.
> 기준: [outline](overpass-plan-ordering-outline.md), [policy §7](overpass-prefix-plan.md#7-canonicality와-byzantine-경계), [research logic](overpass-research-logic.md), [review §§23–25](overpass-submission-readiness-review.md#23-native-multimmit의-sweep-변경-여지와-plan-고정-경계).
> 이번 변경은 별도 branch의 문서화만 포함한다. Commonware 구현, 테스트 실행, 배포·비용 지출은 별도 작업 승인 후 진행한다.

## 1. 먼저 확인할 것

먼저 짧은 invariant를 고정한다: **서로 다른 유효 vote pool과 늦은 extension을 받아도, 이미 확정 전달한 exact block 순서는 뒤집히지 않는다.** 그다음 production extractor를 쓰는 작은 반증용 regression을 만들고, 통과한 연결 위에 실행·인증과 E2E를 붙인다. 전체 재작성부터 시작하지 않는다.

여기서 exact-order adapter는 Native가 내놓는 tips·finality 근거를 **되돌릴 수 없는 전역 block 전달 순서**로 연결하는 부분이다. `PoolExtractor`만으로는 그 순서와 durable cursor가 구현되지 않는다. EuroSys/OSDI를 위한 다음 증거는 이 연결의 correctness → 같은 endpoint의 실행·인증 → planner의 추가 E2E 이득 순서다. 제출 가능성이나 개선 폭을 미리 정하지 않는다.

- Native Multimmit의 tip extraction·extension·settledness와 recovery를 유지한다.
- Selected policy는 leader block의 인증 subject에 결속하고 proposal 안에서 고정한다. 늦은 report나 growing pool로 바꾸지 않는다.
- Cut은 report 수집·timer·optimizer 완료를 기다리지 않는다. 준비된 유효 candidate가 없으면 actual proposal parent의 base policy로 진행한다.
- State finalization은 **irrevocable exact order + 같은 input/range·canonical input state·runtime·result의 서로 다른 epoch validator `f+1` matching execution signatures**를 관측자가 검증한 사건이다. Durable apply/read readiness는 별도다.
- Review §24의 finite prefix `D` + base-sweep continuation은 **시험할 후보 표현**이다. 이 계획이 wire encoding이나 선행 실행 서명 스케줄을 채택하지 않는다.

LCP proxy와 `f+1` endpoint의 목적함수 차이는 [review §10](overpass-submission-readiness-review.md#10-lcp-합과-state-finalization-latency는-다른-목적함수다), dependency-aware reuse는 [§15](overpass-submission-readiness-review.md#15-독립-작업의-순서-차이를-lcp가-과대평가하는-경우), 부하·cost confounds는 [§18](overpass-submission-readiness-review.md#18-실행-낭비-감소와-지속-부하에서의-순이득을-분리한다) 및 [outline §5.3](overpass-plan-ordering-outline.md#53-순서-변경-효과와-재실행-절약의-원인-분리)을 따른다. 기존 반례를 다시 증명하는 것이 첫 artifact의 목적은 아니다.

## 2. 첫 artifact: native transcript-driven, policy-bound Emit regression

### 2.1 기존 증거와의 차이

Review §23.6은 공통 completion `G`가 있다는 **가정 아래**의 prefix lemma다. 새 regression은 서로 다른 **유효 native vote transcripts를 production `PoolExtractor`에 입력**하고, 추출한 exact tips·settledness를 고정 policy의 `Emit`에 연결한다. 기대하는 completion을 먼저 넣어 얻은 출력은 이 gate의 통과 증거가 아니다.

검토 기준은 Commonware [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72)다. 이 commit은 원래 dirty checkout의 미커밋 변경을 포함하지 않는다.

- [`PROPERTIES.md`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/PROPERTIES.md)의 P-TIPS-1과 `cross_certificate_safe_and_final_tips_match_reference`를 출발점으로 삼는다.
- 해당 deterministic test matrix의 transcript 생성·branch 제약을 재사용/확장하되 production extractor를 별도 toy extractor로 대체하지 않는다. 이는 exported generator API가 아니다. [Seed `0x5afe_e17e`의 기존 matrix](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/tests/algebra.rs#L935-L993)는 n=6,7,11,12와 pool size n−f…n을 다룬다. 기존 helper는 n chains·chain당 2 proposal payloads를 쓰므로 아래 2-chain fixture에 맞게 조정해야 한다.
- 같은 ledger의 “External ordering is out of scope”에 따라 recursive `Ord/Emit`, body retrieval, duplicate removal, durable delivery cursor는 외부 marshal의 새 검증 범위다.
- 기준 commit의 `LeaderBlock`에는 ordering-policy field가 없다. Extractor-only regression과 **실제 인증·복구 경로까지 연결한 adapter regression**의 통과 상태를 따로 기록한다.

### 2.2 최소 fixture와 기대 결과

아래 표는 소스 규칙으로 검산한 **예상값**이다. 실제 테스트 실행 결과가 아니다.

```text
n=6, f=1, 동일 epoch/view, 동일 leader block L, 동일 exact parent Q0
parent tips: A0, B0
leader proposed tips: A1, B1
v1,v2,v3,v4,v6: 같은 B1→B2 extension을 보유한 유효 vote
v5: extension 없는 유효 vote
P = {v1,v2,v3,v4,v5}
Q = {v1,v2,v3,v4,v6}
P+ = P ∪ {v6}

시험 policy: D=[B,B,A] → B1,B2,A1
σ = D || (base sweep에서 D의 slot만 제거)
```

**Source-level fixture 검산:** 6 participants와 2 chains(A=0, B=1), pipeline depth·extension bound 각각 1 이상을 사용한다. v1…v6는 Participant index 0…5다. Leader의 각 chain proposal은 `Anchor::Tip(A0/B0)`에서 payload 하나를 제안한다. **모든 vote의 positions는 [1,1]**이고, v5도 novote가 아닌 extension 없는 ordinary vote다. Extension의 원소는 payload commitment이며 B2 header는 같은 epoch·chain B·height 2·parent digest B1에서 재구성한다. 단순 임의 block digest를 extension에 넣지 않는다. [Config](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/config.rs#L22-L79), [vote shape](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/vote.rs#L119-L228), [header reconstruction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/path.rs#L220-L288).

Final proposal rank는 `3f+1=4`, final extension support는 `n−f=5`다. [Production extraction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L101-L189)의 settledness `beyond + unseen ≤ f`에서 P의 B는 `4+1>1`, Q의 B는 `0+1≤1`, P+의 B는 `0+0≤1`이다. 이는 **소스 대조에 의한 예상값**이며 cryptographic admission·availability·runtime 도달 가능성을 실행 검증한 것이 아니다.

| 관측 transcript | 예상 native final tips | 핵심 settledness | 예상 Emit |
|---|---|---|---|
| P | A1, B1 | [A=true, B=false]; B2 unresolved | `[B1]`; B2에서 stop, A1 보류 |
| Q | A1, B2 | [true,true] | `[B1,B2,A1]`까지 전달 |
| P+ | A1, B2 | [true,true] | 기존 `[B1]` 뒤 `[B2,A1]`만 append |

`D`는 membership를 늘리지 않는다. 모든 slot은 exact parent 기준으로 해석하고, A/B 표기는 높이뿐 아니라 native가 인증한 **동일 block identity·ancestry**를 뜻한다. 다른 lane·history가 있다면 실제 config와 parent에 명시하고 이미 전달된 prefix/중복 제거에 포함한다.

**Certificate 구분:** P/Q는 각각 exact-five-vote L-QC가 될 수 있다. P+는 six-vote sticky pool이며 L-QC로 만들지 않는다. L-QC는 정확히 n−f votes를 요구한다. 허용된 larger V-QC와 혼동하지 않는다. 특히 P의 all-vote V-QC는 safe-extension threshold `2f+1=3`으로 이미 B2를 반환할 수 있으나 P의 **final** tip은 B1이다. [L-QC cardinality](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/certificate.rs#L331-L364), [safe/final extraction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L280-L421).

이 fixture의 B2 threshold·settledness가 production 결과와 다르면 기대값을 강제로 맞추지 않는다. Legal fixture를 고치거나 미해결 조건과 counterexample을 남기고 adapter gate를 중단한다.

### 2.3 Assertions, negative control, 일반화

1. P/Q/P+를 같은 immutable vote records에서 만든다. Distinct identity·signature subject·positions·extension ancestry·길이 bounds를 실제 admission/verification 경로에서 확인한다. 잘못된 transcript를 extractor에 직접 넣은 결과는 legal-protocol evidence에서 제외한다.
2. Production incremental `PoolExtractor`와 `FinalTips::from_pool`의 blocks·positions·settledness를 비교하고, exact-five인 P/Q는 `FinalTips::from_lqc`와도 대조한 뒤 `Emit`을 확인한다. Proposal positions는 Q에서도 [1,1]이며 B2 extension height와 혼동하지 않는다. P와 Q는 길이가 달라도 exact emitted block stream이 prefix-compatible해야 한다.
3. P→P+ 및 vote arrival permutation·중복 delivery에서 emission은 append-only이며 block occurrence가 중복 전달되지 않아야 한다. Policy·parent·rule은 바뀌지 않는다.
4. **Negative mutation:** “unsettled 빈 slot도 skip”하도록 바꾸면 P가 `[B1,A1]`, Q가 `[B1,B2,A1]`를 내므로 prefix oracle이 반드시 실패해야 한다. Native transcript를 무효로 만들어 실패시키는 mutation이 아니다.
5. Existing cross-certificate test의 transcript 생성 matrix를 확장해 legal P/Q 쌍, growing pools, compatible extension branches, settled empty slots, V-QC/L-QC 관계를 검사한다. Unsupported branch combination은 generator의 전제로 배제하고 이유를 기록한다.
6. Signature된 policy bytes/commitment·rule version·actual parent 변경은 reject한다. Proposal freeze 뒤 stale optimizer result와 restart가 policy를 재선택하지 않아야 한다.
7. 후속 view는 인증된 history를 복구하고 기존 emitted prefix를 상속한다. Missing history/policy/body에서는 필요한 범위만 대기하고 authority를 추측하지 않는다. Crash/replay 시 durable cursor가 중복·누락·재정렬을 만들지 않아야 한다.

기존 test의 후속 실행 위치는 Commonware repo root이며, 승인 후 `just test -p commonware-consensus multimmit::machine::algebra::tests::cross_certificate_safe_and_final_tips_match_reference`로 baseline을 확인한다. 새 adapter test의 정확한 target은 구현 위치 결정 후 기록한다. **이번 문서 작업에서 이 명령을 실행하지 않았다.**

최소 fixture 통과는 finite regression evidence다. 모든 legal certificate에 대한 통합 증명이나 view-change/recovery 검증을 대신하지 않는다. Review §23.7의 각 가정을 어느 production invariant/증명/테스트가 충족하는지 traceability 표로 남긴다.

### 2.4 No-wait와 HOL을 구분할 관측

P에서 A1이 이미 포함 가능해도 앞선 B2가 unresolved이면 ordered delivery는 멈춘다. **No-wait cut은 ordered-delivery head-of-line(HOL) 대기 제거를 뜻하지 않는다.** Consensus의 cut/view 진행, body readiness, native settledness, application parent 대기를 각각 기록한다.

Report 없음·optimizer 지연·계산 중 cut-ready·parent mismatch에서 cut fallback을 확인한다. 같은 CPU/NIC budget에서 planner 부하가 cut scheduling을 간접 지연하는지도 측정한다. “async”나 lock-free 호출만으로 no-wait 성능을 인정하지 않는다.

## 3. E2E를 시작하기 전 endpoint 검증

[Review §25](overpass-submission-readiness-review.md#25-f1-실행-서명의-안전성과-수집-진행성은-다르다)에 따라 공통 signing range, semantic statement identity, retention/retry, collector recovery, 저부하 마지막 구간을 먼저 명세한다. 각자의 latest prefix에만 서명하는 방식은 matching `f+1`을 보장하지 않는다.

- 다른 delivery batch 크기·catch-up 속도와 다른 QC representation에서도 같은 canonical statement의 서명이 모이는지 확인한다.
- Duplicate signer, wrong epoch/domain, 다른 range/order/parent/runtime/result는 합치지 않는다. 같은 leader block이라는 이유만으로 다른 extracted prefix의 서명을 합치지 않는다.
- Honest signer는 exact context에서 직접 실행·검증한다. 긴 prefix root를 잘라 쓰거나 다른 certificate를 echo하지 않는다.
- Collector crash, Byzantine signature withholding, body 지연, view change 후 matching statement의 복구·최종 수집을 검사한다. Crash/침묵/Byzantine은 **합쳐서 f 이내**인 liveness schedule과 그 밖의 fail-closed stress를 구분한다.
- Pre-order result-signature 전파를 시험한다면 Pre-cut과 Overpass에 같은 옵션으로 제공한다. Canonical 채택은 full ordering과 exact-context 검증 이후다.

## 4. 세 비교군의 공통 실험 계약

| 구성 | 차이 |
|---|---|
| Original | 해당 입력의 irrevocable order 이후 실행 시작 |
| Pre-cut execution | 실제 받은 blocks를 base rule로 사전 실행·검증/repair; 별도 leader plan broadcast 없음 |
| Overpass | 같은 Pre-cut 경로 + intended-order reports·bounded score selection·plan 전파 |

Consensus version/profile, deterministic executor와 cache/validation, signature codec·수집 정책, validator 배치, 총 CPU/memory/NIC budget, block/transaction 크기, cut 설정, ingress cohort와 **절대 offered load**를 동일하게 한다. Runtime/OS/build/seed/config를 보존한다. Frequent cuts는 별도 sensitivity이며 주 baseline으로 바꾸지 않는다.

### 4.1 최소 workload·failure matrix

- Fixed-cost dependency workload: conflict와 arrival skew를 분리해 실제 validation·repair를 측정한다. Leader만 늦음, 다수만 늦음, 균등 도착을 포함한다.
- Independent workload와 dependency/independent 혼합: LCP 변화가 실제 reuse를 대표하지 않는 경우와 순수 planning overhead를 드러낸다.
- Order-dependent application cost workload: 각 run의 canonical input·parent·runtime·final order를 사후 reference replay한다. 유효 작업량 차이와 discarded speculative attempts를 분리한다.
- Load sweep: 공통 저부하부터 포화·overload까지. RTT/지터, execution cost, lane imbalance, τ/horizon/update budget을 기록한다. Pilot으로 범위를 정하고 confirmatory run 전에 고정한다.
- Failure: no reports, f 이내 report/signature silence, slow honest node, duplicate/stale report, timer/threshold race, optimizer stall, parent mismatch, view change, collector/node restart, missing body/history. Fault recovery 후 backlog drain과 인증 재개까지 관측한다.

Reports는 실제 block arrivals와 명시한 intended-order 생성 규칙에서 나온다. Window 안내 비용을 포함한다. 임의 report permutations, offline oracle·remote execution progress를 online planner의 입력으로 주지 않는다.

### 4.2 기록할 사건과 지표

관측 node의 monotonic clock으로 동일 transaction의 canonical occurrence/block을 추적한다. Ingress가 별도 client clock이면 그 clock에서 response까지 따로 측정하고 서로 다른 node의 timestamp를 그대로 빼지 않는다.

- 사건: ingress → first leader finality / input별 irrevocable ordering → body·canonical parent 준비 → execution validation → statement 준비 → matching `f+1` 검증 → durable apply/read readiness. 겹치는 단계는 직렬 합산하지 않는다.
- Primary: ingress→state p50/p95/p99, successful goodput, 시간별 backlog·기울기·drain, 실패/timeout/미완료 cohort.
- 진단: input별 order→state, leader-finality→ordered-delivery, unresolved-slot HOL과 data/parent 대기. 첫 L-QC를 모든 extension 입력의 ordering 시각으로 쓰지 않는다.
- 실제 작업: retained valid execution, discarded attempts·CPU/operations, repair, read validation, effects apply/root 생성, signing/verification/aggregation/retry.
- Planner 비용: report/window/plan bytes·CPU·queueing, peak memory, snapshot 크기, τ/W/update 설정, plan 사용/late/stale/fallback·parent mismatch 비율, plan-to-cut lead time, score와 실제 reuse의 관계. Per-node 병목과 전체 합을 함께 보고한다.
- Failure recovery: fault onset·healing/restart부터 ordering·state certification 재개 및 backlog drain까지, 중복/누락과 retained-state 상한. Durable/read readiness는 primary와 별도 그래프다.

Warm-up·measurement·drain을 분리하고 측정 cohort의 retries는 최초 ingress를 유지한다. 미완료 요청을 latency 표에서 조용히 제거하지 않는다. Paired seeds/arrival schedules와 반복 실험으로 run-level 불확실성을 보고하고, tail 표본·관측 시간·censoring을 공개한다. Pilot 후 반복 수/기간·분석법을 고정하며 유리한 결과가 나올 때까지 실행하지 않는다.

## 5. Stop / go gates와 결과물

| Gate | Go에 필요한 증거 | Stop 또는 주장 축소 조건 |
|---|---|---|
| G0: 명세 | Legal fixture, policy/authentication seam, bounds·recovery·signing 범위의 미정 항목과 담당 구현 위치 명시; 별도 구현 승인 | Encoding 후보를 채택 완료로 취급하거나 production 경로가 불명확 |
| G1: native adapter | 실제 extractor P/Q/P+ + negative mutation, generator regression, authenticated freeze·view/recovery·cursor 검사와 §23.7 proof obligations 검토 | Prefix 불일치, 잘못된 identity/parent, 누락/중복, unresolved skip, 무인증 policy 수용 중 하나라도 발생 |
| G2: endpoint | Reference execution 결과 일치; 같은 canonical statement의 matching f+1·실패 복구; 세 구성의 동일 verifier | 서로 다른 범위 서명 합산, 인증 없는 completion, 미해결 collector/low-load 진행성 |
| G3: no-wait | Report/optimizer 미완료 상태의 fallback; deadline 불변·단일 trigger; 자원 경쟁 계측 | Plan 때문에 cut이 명시적으로 기다림, unbounded queue/state 또는 freeze 위반 |
| G4: E2E claim | Pre-cut 대비 비용 포함 ingress→state 개선을 재현; 동일 load에서 goodput/backlog와 불확실성을 함께 제시 | Order→state만 개선, 미완료 누락, backlog 증가를 숨김, 비용/endpoint 불일치 |
| G5: mechanism claim | 실제 valid reuse·discarded work와 final-order reference의 작업량 차이로 개선 원인 설명 | E2E만 좋아지면 그 관측만 주장; repair 감소만 있으면 latency 목표 달성 주장 보류 |

Gate는 특정 배수나 임의 “몇 % 개선” 목표가 아니다. 효과가 특정 workload에서만 나타나면 그 조건으로 claim을 제한하고 무효/악화 구간도 공개한다. G1/G2 실패 시 성능 수집보다 correctness를 먼저 해결한다. No-wait 구조를 만족해도 HOL·resource contention으로 E2E가 나빠질 수 있다.

별도 구현 작업의 deliverables:
1. Commit-pinned regression, legal serialized transcripts, seeds·failing traces, expected/actual assertions와 mutation 결과
2. Policy/authentication/recovery 및 statement schema와 proof-obligation 추적표
3. 세 구성의 실행 설정·raw event/cost logs·reference replay·분석 절차, 완료/실패/미완료를 포함한 결과
4. 통과·실패·미실행을 구분한 validation report. 기존 toy counts와 새 native/E2E 증거를 합산하지 않음

## 6. 선행 연구와 claim의 최소 경계

[Bidl (SOSP 2021)](https://www.cs.hku.hk/~heming/papers/sosp21-bidl.pdf)은 sequencer가 준 순서에서 consensus와 speculative execution을 겹친다. [Rashnu (PVLDB 2024)](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)는 local ordering을 모아 data-dependent order-fairness를 다룬다. Overlap 또는 local-order aggregation 자체를 novelty로 주장하지 않는다. 상세 비교는 [review §§12,17](overpass-submission-readiness-review.md#17-rashnu와의-직접-비교-report-수집-자체는-차별성이-아니다)에 두고, 이번 검증은 **Native의 안전한 exact-order 연결 + 동일 Pre-cut 대비 optional feedback의 비용 포함 순이득**에 집중한다.
