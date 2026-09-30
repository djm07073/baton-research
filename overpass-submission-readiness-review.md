# Overpass: EuroSys / OSDI submission-readiness review

검토일: 2026-09-30. 현재 score-guided intended-order 설계에 대한 검토 메모다. Protocol 변경이나 실험 성능 결과가 아니다. 전체 연구 goal은 진행 중이다.

**후속 사용자 결정:** Native Multimmit 유지에 더해, ordering policy를 leader block 인증 대상에 결속하여 같은 proposal에서 고정하고, full ordering finality + f+1 exact-context 일치 실행 서명을 state-finalization primary endpoint로 채택했다. Durable/read readiness는 별도 지표다. 아래 과거 검토에서 이 두 선택을 “미정/권고”라고 한 표현은 검토 당시 상태이며, 현재 source of truth는 [prefix-plan §7.2](overpass-prefix-plan.md#72-policy-binding과-state-finalization의-채택-조건)다. 구체적 encoding·extension continuation·recovery와 구현·증명은 여전히 미완료다.

## 1. 판단과 검토 범위

Positioning은 타당하다: Autobahn-family consensus를 위한 execution-aware ordering extension이다. 하지만 좋은 benchmark 수치만으로 완성되지는 않는다. Intended order → 선택한 order → 실제 재사용 → finalization latency의 인과관계, exact-order 합의 통합, bounded overhead를 보여야 한다.

검토한 현재 파일: README.md, overpass-plan-ordering-outline.md, overpass-research-logic.md, overpass-prefix-plan.md. Commonware 새 구현·정식 증명·분산 benchmark 완료를 확인한 것은 아니다. 현재 문서도 이를 미완료로 표시한다.

직전 사용자가 정한 세 주 비교군을 평가 기준으로 삼는다:

1. Original: cut 확정 이후 실행.
2. Pre-cut execution: 실제 수신한 blocks를 기존 ordering rule에 따라 사전 실행하고 final cut과 달라진 부분을 검증·재실행. 별도 leader plan 전파 없음.
3. Overpass: 같은 pre-cut execution에 intended-order 기반 plan 조율 추가.

문서 정합성 문제: 로컬 outline §5.1, prefix-plan §8 및 현재 전달된 AGENTS 지침에는 이전 leader-local/early-proposal 비교가 남아 있다. Google Docs는 직전 요청에 따라 세 비교군으로 수정되었다. 본 검토는 제거된 baseline을 재도입하지 않는다. 기준 문서의 정합성 정리는 별도 필요하다.

## 2. 우선순위

| 우선순위 | 현재 빈틈 | 필요한 증거 / 결정 |
|---|---|---|
| P0 | Intended order가 실제 작업을 얼마나 대표하는가 | 진척 비공개 조건에서 score와 wasted CPU/잔여 시간의 관계, 실패 사례 |
| P0 | Plan을 final cut의 exact order로 바꾸는 함수 미완성 | 입력 집합·ancestry·중복·누락·late block·view change 처리 명세 및 oracle 비교 |
| P0 | No-wait가 추가 전송·검증 대기로 바뀔 수 있음 | order metadata 가용성·크기·fetch·검증 비용 및 cut 경로 자원 격리 |
| P0 | State finalization의 관찰 사건이 선택 사항으로 남음 | local execution 완료 / 결과 인증 / durable apply를 구분하고 primary endpoint 고정 |
| P1 | Plan이 proposal 동결 전에 실제로 도착하는가 | report→선택→전파 timeline, 사용률·fallback률·stale률 |
| P1 | 이전 cut execution이 지연된 상태에서 다음 context가 모호함 | ordering parent와 execution base 구분, backlog·메모리 한도와 진행 규칙 |
| P1 | 성능의 일반성·원인 분리 부족 | 동일 workload·budget의 세 비교군, conflict/RTT/load/arrival-skew sweep |
| P1 | 보고의 Byzantine 왜곡과 report 길이 편향 | bounded horizon·최대 비용·공격/침묵/복구 실험 |

## 3. 새로 확인한 한계: 같은 보고, 반대의 최적 선택

n=6, f=1, 동일 parent와 동일 입력 집합 {A,B,C}를 가정한다. A와 B의 순서가 뒤집히면 이후 계산이 무효화되는 prefix-reuse workload를 사용한다. 다섯 보고를 수집하고 여섯 번째 node는 아직 보고/실행하지 않았다. Byzantine 행동 없이도 성립한다.

```text
R1, R2, R3: P = A → B → C
R4, R5:     Q = B → A → C

Score(P) = 9
Score(Q) = 6
```

동일한 보고가 다음 두 실행 상태와 모두 양립한다. 각 block cost는 1이고 부분 suffix 재사용은 없다고 가정한다.

| Leader에게 보이지 않는 진척 | P 선택 시 무효화 | Q 선택 시 무효화 | 더 적은 무효화 |
|---|---:|---:|---|
| R1–R3는 3개 완료, R4–R5는 0개 완료 | 0 blocks | 9 blocks | P |
| R1–R3는 0개 완료, R4–R5는 3개 완료 | 6 blocks | 0 blocks | Q |

결론: intended orders만 사용하는 결정 함수는 이 두 상태를 구분하지 못하므로 실제 작업 보존의 보편적 최적성을 보장할 수 없다. 모든 blocks가 동일한 비용이어도 발생한다. 실행 비용과 길이를 늘리면 손실 규모도 늘릴 수 있다.

이는 intended-order 설계를 폐기하거나 remote execution proof를 추가해야 한다는 뜻이 아니다. Lightweight heuristic의 한계를 명시하고, 실제 workload에서 왜 이 proxy가 유용한지 검증해야 한다는 뜻이다. Report 이후 진척과 report freshness도 함께 계측한다. 실제 진척은 offline 계측에만 사용한다.

이 예시는 입력된 reports에 대한 정보론적 한계다. 해당 순열들을 정상 report 생성기로 실제 만들 수 있는지는 별개이며, §11에서 이 구분을 추가한다.

위 산술은 Node.js로 직접 확인했다. q=2 결과 확보를 선택한 이상화된 동시 cut/동일 속도 모델에서는 첫 상태가 P=0/Q=3, 둘째 상태가 P=3/Q=0 계산 시간 단위다. 네트워크·검증 비용은 제외했다. 이는 분산 benchmark나 현재 protocol의 latency 측정이 아니다.

### LCP에 줄 수 있는 정확한 이론적 근거

고정된 후보 집합·보고 snapshot에서 모든 보고 순서를 이미 실행했고, block당 비용이 같으며, 첫 불일치 이후 suffix만 재실행한다는 제한된 모델에서는:

```text
Discard(P) = Σ_i (|R_i| − |LCP(P,R_i)|)
           = constant − Score(P)
```

따라서 이 모델 안에서는 score 최대화가 폐기 block 수 최소화와 같다. 실행 진척·비용·dependency-aware reuse가 달라지면 등식이 실제 비용에 적용되지 않는다. 논문은 이 단순 모델을 heuristic의 유도 근거로 사용하고, 실제 환경의 이탈을 평가할 수 있다. 일반적인 실행 최소화 정리로 쓰면 안 된다.

### Byzantine 보고의 제한된 score 분석

동일한 고정 후보 집합 F, 길이 상한 W, snapshot 안의 Byzantine 보고 최대 f개를 가정한다. H는 정직한 보고의 LCP 합, B는 Byzantine 보고의 합이고 0≤B(P)≤fW이다. P*가 H+B의 최대 후보, Q가 H의 최대 후보이면:

```text
H(Q) − H(P*) ≤ B(P*) − B(Q) ≤ fW
```

이는 관측된 정직한 보고에 대한 score regret bound일 뿐이다. 실제 CPU·latency·미보고 노드·fairness의 bound가 아니다. Byzantine 보고로 후보 집합이 바뀌는 counterfactual, bounded-search 누락, hysteresis로 최대 후보를 택하지 않는 정책에는 그대로 적용하지 않는다. 정직한 leader가 해당 고정 집합에서 최대 점수를 계산한다는 조건도 필요하다.

6개의 3-block permutations, 정직한 보고 4개와 악의적 보고 1개의 7,776개 조합을 열거해 이 산술 bound를 확인했다. 위 부등식이 일반 논증이며, 유한 열거는 보조 sanity check다. 이것을 새로운 quorum proof나 protocol safety proof로 포장하지 않는다.

## 4. Plan과 cut 연결: 구현 전에 좁혀야 할 계약

현재 prefix-plan §3·§7은 suffix 추가와 exact-order 인증을 요구하지만, 최종 변환 함수의 모든 경우를 정하지 않는다.

다음 계약을 명시해야 한다:

- Cut이 선택한 정확한 block 집합을 중복·누락 없이 한 번씩 포함한다.
- 기반 protocol이 선택한 lane 경로와 필수 선행 관계를 보존한다.
- Report에는 있었지만 final cut에는 없는 block을 처리한다.
- Plan에는 없지만 final cut에는 있는 block을 처리한다. 필수 predecessor를 단순 suffix로 붙일 수는 없다.
- 같은 tips에 서로 다른 order가 연결되면 서로 다른 consensus subject가 된다.
- 이미 전파한 proposal의 순서를 late plan으로 바꾸지 않는다. 안전한 reproposal 및 view recovery는 기반 consensus의 잠금 규칙을 따른다.

중요한 반례: 초기 x=0에서 speculative plan이 A: x←x+1 다음 B: y←x+1이면 B의 결과는 y=2다. Final cut이 다른 lane의 A를 제외하고 B만 포함한다면 올바른 B 결과는 y=1이다. Plan에서 A를 삭제해 B만 남기는 것과 B의 기존 실행 결과를 재사용하는 것은 다르다.

따라서 ordering projection의 결정성과 execution reuse의 유효성은 각각 확인해야 한다. 필요한 것은 모든 plan이 immutable하다는 새 주장이 아니라, final input 변화가 올바른 invalidation을 유발한다는 명세·시험이다.

## 5. No-wait의 실제 비용: compact cut과 order metadata

Autobahn 원문은 committed lane proposals를 deterministic zipping으로 log에 넣는다. 기존 cut은 lane tips로 많은 blocks를 지칭할 수 있지만, 임의의 선택 순서를 전달하는 가장 단순한 방법은 block references를 열거하는 것이다. Lane 수를 L, 선택 block 수를 B라 하면 tips 중심 표현과 명시적 order 표현의 크기 증가 양상이 달라질 수 있다. 모든 구현의 정확한 byte 복잡도가 같다고 주장하는 것은 아니다.

Hash commitment는 binding을 주지만 order preimage의 가용성·복구·완전성 검사를 대신하지 않는다. Leader에게 plan이 준비되어 있어도 투표할 replicas가 order 정보를 아직 못 받았다면 추가 전송이 cut latency에 노출될 수 있다.

필요한 비교:

- 같은 block 집합에서 원본 cut bytes vs order가 결합된 proposal bytes.
- Order metadata 누락 시 fetch 시간, vote 생성 전 수행하는 검증 작업.
- Report·plan 검증이 consensus event loop·CPU·NIC를 잠식하는지.
- 급증한 backlog와 leader 변경 직후의 ordering/state recovery curve.

권고 설계 방향은 bounded order metadata와 base fallback, report/plan 자원 예산, consensus 작업 우선순위다. 구체 encoding·가용성 경로는 아직 결정하지 않았으며, 새 plan approval certificate를 도입하는 제안이 아니다.

## 6. 시간과 finalization의 측정 정의

Plan이 cut finality보다 먼저 도착했다는 사실만으로 ordering 조율 효과를 입증할 수 없다. 현재 정책은 이미 전파한 proposal을 바꾸지 않으므로 해당 proposal이 동결되기 전에 plan이 준비됐는지도 봐야 한다.

기록할 시점:

- 최초 eligible input / report 생성·수신 / threshold 또는 deadline.
- Optimizer 완료 / leader의 proposal 동결·전파 / validator의 plan 수신.
- Ordering finality / final-context 실행 검증 완료 / 필요한 결과 인증 완료 / durable apply.

Cut-to-state만 줄이고 ordering을 늦추는 결과를 성공으로 세지 않는다. 또한 총 wasted CPU 감소와 result certificate를 구성할 충분한 노드의 완료 시간 감소는 다른 목표다. f+1 인증을 택한다면 동일 subject의 검증된 결과 수집이 끝난 사건을 모든 비교군에서 일관되게 측정하고, 원래 시스템에 없던 인증 비용을 원본의 native latency라고 부르지 않는다.

Ordering은 c+2까지 확정됐지만 execution은 c에서 멈춘 경우, 다음 report의 parent가 ordering parent인지 materialized execution base인지 구분해야 한다. Parent state를 기다리느라 plan 기회가 없어지는지, finalized backlog가 bounded하게 처리되는지는 후속 검토 대상으로 남는다.

## 7. 가장 먼저 실행할 실험과 중단 기준

1. **현상 확인:** Pre-cut execution에서 late predecessor가 실제로 재검증/재실행 CPU와 cut-to-state tail을 늘리는지 계측한다. 독립 거래에서는 order가 달라도 재사용 가능하므로 이를 invalidation으로 과대 계수하지 않는다.
2. **기여 분리:** 동일 application/backend, 동일 도착 workload·cut 정책으로 Original / Pre-cut execution / Overpass를 비교한다. CPU·NIC·committee budget도 고정한다.
3. **원인 확인:** LCP 증가 → 유효한 작업 재사용 증가 → finalization 개선의 연결을 본다. Order-only replay로 입력 집합을 고정한 진단과 실제 distributed run을 구분한다.
4. **비용 확인:** RTT, skew, conflicts, execution cost, load, block/window 크기, 진척 편차에 대한 이득·손실 영역을 찾는다. Cut 빈도 변화는 보조 실험이다.
5. **복구 확인:** 정상 leader, silent report, bounded spam, 서로 다른 plan 전파, view change, stale parent에서 state oracle 및 backlog 회복을 검증한다.

Overpass가 Original보다만 좋고 Pre-cut execution과 같다면 pipeline은 입증했지만 현재 plan의 추가 기여는 입증하지 못했다. Plan 사용률이 낮다면 collection/전파 timing 문제를 먼저 해결한다. Score와 reuse가 약하게 연관되면 보고 정의 또는 heuristic을 다시 검토하되, 원격 실행 proof를 즉시 추가하는 방식으로 범위를 확대하지 않는다.

단순 bank transfer 하나는 출발점이 될 수 있으나, independent / hotspot / multi-key dependent access 및 variable-cost workload를 포함해 조건을 드러내는 것이 좋다. 실험 결과를 낙관적으로 보이게 하기 위해 실패 거래·미완료 요청·재시도를 제외하지 않는다.

## 8. 제출 수준으로 정리할 주장

중심 insight 후보: 최종 ordering에 실행을 일방적으로 맞추는 대신, finality 이전의 분산된 intended order를 ordering 후보 선택으로 되돌려 보내 실행 낭비를 줄인다. 이 조율은 safety certificate가 아니라 선택 가능한 성능 경로다.

논문에는 (a) 기존 pre-cut execution의 낭비 측정, (b) proxy가 맞는 조건과 반례, (c) exact-order cut 통합·복구, (d) 추가 비용까지 포함한 세 비교군의 결과가 필요하다. 본 메모는 그 연구가 완성됐다는 판정이 아니다.

공식 CFP는 두 학회 모두 novelty만 아니라 유의미한 문제, 정확성, 설득력 있는 설계와 평가를 요구한다. OSDI 2027은 새로운 영역에 기존 systems 기법을 적용하는 연구가 기존 systems 연구와 비교하고 새 환경의 과제를 설명할 것을 명시한다. Autobahn에 적용했다는 사실만으로 novelty를 대체하지 않는다.

저자 책임: OSDI 2027은 AI 편집 도구 사용과 원고 전체·대부분의 AI 생성을 구분한다. 이 메모는 검토·분석 보조이며, 저자가 원문·논증·코드·데이터와 최종 원고를 직접 검증하고 목표 학회의 최신 정책을 준수해야 한다.

## 근거

- [현재 plan 명세](overpass-prefix-plan.md): 보고 의미 §2, LCP §3, no-wait §4.2, exact-order §7, 미완료 평가 §8.
- [현재 연구 개요](overpass-plan-ordering-outline.md): System Design, Correctness and Liveness, Evaluation.
- [Autobahn, SOSP 2024](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf): §2 hangover, §5.2.2 deterministic zipping, §5.2.3 lane coverage. 본 검토는 원문에 execution 성능 결함이 입증되어 있다고 주장하지 않는다.
- [EuroSys 2027 CFP](https://2027.eurosys.org/cfp.html): rigorous evaluation, benefits and limitations, novelty/significance/correctness.
- [OSDI 2027 preliminary CFP](https://www.usenix.org/conference/osdi27/call-for-papers): 연구 평가 기준, historical systems work 비교, AI·저자 정책. 향후 갱신 가능.

다음 검토: exact-order adapter의 proposal/vote/recovery 경계를 실제 Commonware 코드와 연결하고, 현재 후보→cut 변환에 필요한 최소 계약을 좁힌다. 구현·protocol 변경 전에 별도 설계안으로 제시한다.

## 9. Commonware 소스 검토: chain-local finality와 executable order

현재 checkout의 `commonware` HEAD는 `534af0ede48affd35b2111522527547b4cc9bf72`이며 미커밋 변경도 있다. 아래는 로컬 소스 검토 결과이지 upstream 전체의 기능 판정이나 Rust 테스트 실행 결과가 아니다. 코드와 외부 문서는 변경하지 않았다.

### 9.1 먼저 필요한 것은 정확한 최종 순서의 delivery

현재 consensus는 lane별 확정 tip 및 leader proof를 제공하지만, application이 소비하는 dense total order와 durable delivery cursor는 제공하지 않는다고 명시한다. 외부 marshal이 proof/history/body를 복구하고 settled/unsettled sweep, 중복 제거, delivery cursor 보존을 수행해야 한다. 따라서 단순히 finality callback에 execution을 연결하는 것만으로 Original baseline도 완성되지 않는다.

- [STATE_MACHINE: 외부 marshal의 책임](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md:56)
- [mod.rs: chain-local finality와 cross-chain placement 구분](commonware/consensus/src/multimmit/mod.rs:210)
- [Activity: delivery authority가 아닌 telemetry](commonware/consensus/src/multimmit/types/activity.rs:1)

이는 Multimmit safety 결함을 발견했다는 주장이 아니다. 현재 구현이 의도적으로 제공하지 않는 application delivery 계약을 Overpass 구현·평가가 채워야 한다는 뜻이다. Diagnostic `Inspection`이나 lossy Reporter 알림을 canonical execution log로 대체하지 않는다.

### 9.2 서로 다른 충분한 vote 집합이 같은 최종 입력 전체를 즉시 드러내지는 않는다

소스의 `PoolExtractor::final_tips`는 n−f 이상 pool에서 chain별 `(3f+1)`번째로 큰 position을 추출한다. Pool은 이후에도 증가할 수 있다. L-QC는 특정 vote transcript를 고정하며, direct pool은 추가 vote로 더 진행할 수 있다. 이미 확정한 chain prefix를 취소하는 것은 아니다.

n=6, f=1, A/B 각각 anchor(position 0)와 새 block(position 1)이 있는 동일 leader proposal, extension 없음인 산술 예시:

| Signer | A position | B position |
|---|---:|---:|
| V1, V2, V3 | 1 | 1 |
| V4, V5 | 0 | 1 |
| V6 | 1 | 1 |

V1–V5 다섯 vote의 4번째 큰 position은 A=0/B=1이다. V6까지 여섯 vote를 보면 A=1/B=1이다. V4를 제외한 다른 다섯 vote만 보아도 A=1/B=1이다. A의 settled flag는 첫 pool에서 false, 다른 두 경우 true다. 나머지 lanes는 변하지 않는다고 놓을 수 있다.

```text
처음 보인 chain-local facts: 새 block B1
더 완전한 chain-local facts: 새 blocks A1, B1

잘못된 단순 adapter:
  첫 facts를 곧바로 [B1]로 canonical apply
  나중 facts를 기본 순서 [A1, B1]로 다시 계산
  → 이미 적용한 global prefix와 불일치
```

반례의 대상은 위 단순 adapter다. 원래 Multimmit의 dense Ord/Emit은 이 문제를 다루기 위한 별도 절차이며, chain-local facts를 임의로 즉시 전역 정렬하는 모델과 다르다. Overpass도 같은 leader의 어느 evidence를 먼저 받았는지에 따라 이미 emit한 순서가 바뀌어서는 안 된다.

위 rank·settled 산술을 JavaScript로 확인했다. 이는 signature 검증, reachable network schedule 또는 Rust protocol의 E2E 검증을 실행한 것이 아니다. 기존 `inbound_lqc_votes_extend_the_arrival_first_pool` 테스트 소스도 5-vote certificate와 6-vote direct pool의 settledness 차이를 명시적으로 검사하지만, 이번 검토에서는 실행하지 않았다.

- [추출 함수](commonware/consensus/src/multimmit/machine/algebra/tips.rs:143)
- [Leader finality의 증가·transcript 규칙](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md:383)
- [기존 테스트](commonware/consensus/src/multimmit/machine/tests/machine.rs:1609)
- [기존 테스트가 dense ordering 증거는 아니라는 설명](commonware/consensus/src/multimmit/docs/PROPERTIES.md:146)

### 9.3 Chosen order를 인증할 seam은 아직 없다

`LeaderBlock`의 encoded fields는 round, parent V-QC, tip-history commitment, chain proposals다. `VoteBody`는 해당 leader digest와 positions/extensions를 인증한다. 현재 leader block에는 Overpass의 chosen cross-chain order가 없다. `history`는 이미 safe-tip history 의미를 가지므로 plan hash 저장소로 전용할 수 없다.

필요한 설계 계약은 단순한 extra hash보다 크다:

1. 같은 proposal에 연결된 exact order 또는 order를 도출할 rule/input commitment가 명확해야 한다.
2. 인증한 order 정보의 preimage를 복구할 수 있어야 한다.
3. Native Multimmit을 유지한다면 partial/late finality facts와 settled/unsettled 처리를 거쳐도 emit한 prefix가 보존되어야 한다.
4. Plan 변경·leader 교체·재시작이 이미 서명·확정한 order를 바꾸지 않아야 한다.

소스의 `ProposalRequest`는 exact block과 parent를 묶고, durable journal은 서명 전파 전에 해당 결정을 보존한다. 새 order 인증도 이 경로와 복구 계약에 들어가야 한다. Mutable planner 메모리에만 남겨서는 안 된다. 단, plan을 hint로 전파하는 모든 단계에 consensus quorum을 추가하자는 뜻은 아니다.

- [LeaderBlock 및 canonical encoding](commonware/consensus/src/multimmit/types/block.rs:561)
- [VoteBody의 subject](commonware/consensus/src/multimmit/types/vote.rs:88)
- [ProposalRequest](commonware/consensus/src/multimmit/machine/durability.rs:446)
- [서명 전파의 durability barrier](commonware/consensus/src/multimmit/machine/durability.rs:1276)

`glue/src/multimmit.rs`의 기존 PoC는 대안이 아니다. `OrderingCut::try_from`은 FinalityFact의 round/blocks만 복사하며 settledness·dense order를 표현하지 않는다. Execution statement 역시 block별 모델이다. 이 reducer를 현재 shared-state, intended-order 설계의 완성된 adapter로 인용하지 않는다. 이는 과거 모델과 현재 요구사항의 불일치이며, 기존 PoC의 의도 전체를 위반한다고 판정한 것은 아니다.

- [Legacy cut projection](commonware/glue/src/multimmit.rs:201)
- [Legacy state-cut join](commonware/glue/src/multimmit.rs:421)

### 9.4 평가의 시간 원점을 더 정밀하게 고정해야 한다

다음 사건을 같은 관찰자에서 구분한다:

```text
chain-local finality 관측
  → 해당 입력의 exact global order가 변경 불가능하게 결정됨
  → 필요한 body를 확보함
  → exact-context execution 결과 검증 / state-finalization endpoint
```

Body 확보는 이 도식보다 먼저 일어날 수도 있고, execution도 다른 단계와 중첩된다. 위는 사건 구분이지 모든 구현의 강제 순차 pipeline이 아니다.

첫 n−f vote 수신을 곧바로 완전한 ordering-finality 시각이라고 쓰면 남아 있는 cross-chain ordering 해소 시간이 execution latency에 섞일 수 있다. 반대로 body가 모두 올 때까지 ordering 시각을 늦추면 sync 비용을 숨긴다. Primary Δstate의 시작은 해당 입력의 **exact order finality**로 정의하고, chain-local→exact-order와 exact-order 이후 body 대기를 별도 보고하는 방향이 타당하다. Endpoint 및 구체 계측 위치는 아직 구현으로 확정되지 않았다.

세 비교군에는 동일한 delivery/recovery 계약을 적용한다. Overpass만 fixed cut으로 바꾸고 Original은 native variable extraction을 사용하면 intended-order planning 외의 변경도 섞인다. 이 경우 별도 인과 분해가 필요하며 세 비교군의 이름만 같게 붙여 해결하지 않는다.

### 9.5 지금 결정해야 할 범위와 최소 검증

권고: 먼저 기반 profile과 executable order 계약을 고정한다. Native Multimmit을 유지하면 Ord/Emit 및 plan 통합의 prefix 보존을 구현·증명해야 한다. Tip 추출·extension을 제거한 fixed-cut profile을 택하면 별도의 agreement/recovery 검증이 필요하다. 이전 fixed-cut 계획은 현재 reference-only이므로 이번 검토에서 자동 채택하지 않는다.

우선 검증할 조건은 (a) 동일 leader의 서로 다른 유효 vote subsets, (b) late vote/extension, (c) partial order에서 뒤늦은 필수 predecessor, (d) order 정보 누락, (e) proposal 전파 후 crash/restart, (f) 다른 plan을 가진 새 leader다. 모든 경우 honest 노드가 emit한 logs는 prefix-compatible하고, 복구 후 누락·중복 state effect 없이 이어져야 한다. 이 검증이 통과하기 전의 성능은 scheduler simulation이나 부분 prototype 결과로 명시한다.

다음 연구 단계는 새로운 quorum을 더하는 것이 아니라 **선택한 기반 profile에서 exact order가 언제 결정되고 무엇이 이를 인증하는지**를 하나의 작은 명세로 만드는 것이다. 이번 검토는 그 결정을 강제로 내리거나 consensus 코드를 수정하지 않았다.

## 10. LCP 합과 state-finalization latency는 다른 목적함수다

§3은 intended order와 실제 진척이 다를 수 있음을 지적했다. 더 강한 한계가 있다: 모든 보고 순서를 이미 완전히 실행했고 비용도 균일하여 LCP가 실제 재사용량을 정확히 나타내더라도, LCP 합 최대화는 필요한 결과들이 가장 빨리 준비되는 순서를 보장하지 않는다. 이는 정직한 실행에서 나타나는 목적함수 차이다.

### 10.1 제한된 모델에서의 정확한 관계

모든 보고가 같은 parent·같은 W개 blocks의 유효 순열이고, 각 block의 계산 비용을 1로 놓는다. 모두 해당 순서를 완료했으며, 첫 불일치 뒤의 state-dependent suffix는 재실행해야 한다. 선택한 P에 대해 validator i가 재사용할 prefix 길이를 ℓ_i(P)라 하면:

```text
Residual_i(P) = W − ℓ_i(P)
TotalResidual(P) = mW − Σ_i ℓ_i(P)

T_q(P) = q번째로 작은 Residual_i(P)
       = W − q번째로 큰 ℓ_i(P)
```

첫 두 식은 m명의 보고자에 대한 총량이다. 마지막 식은 동일 속도·동시 시작·통신 비용 제외 조건에서 q개 결과가 준비되는 계산 시간이다. 따라서 sum objective와 q번째 완료시간 objective는 일반적으로 같지 않다. 실제 protocol의 finality는 추가로 ordering proof, exact-context validation, 인증·전송 등의 조건을 만족해야 한다. T_q는 그 protocol의 전체 latency가 아니라 분석용 계산 성분이다.

### 10.2 진척 차이 없이 발생하는 구체 반례

n=6, f=1이고 다섯 정상 validator가 보고한다. 여섯 번째 validator는 보고하지 않았으며 재사용할 실행도 없다. 실제 Byzantine 행동은 없는 허용 실행이다. 모든 block은 같은 mutable accumulator를 순서에 따라 갱신하므로 prefix 이후의 순서 변경은 재실행을 요구한다. Application failure는 없다고 놓는다.

```text
V1: A B C D E F G
V2: A B C D F G E
V3: A B C D G E F
V4: E F G A B C D
V5: E F G A B C D
```

이는 일곱 producer를 요구하지 않는다. 여섯 producer 중 한 producer의 연속 blocks를 A,D로 두고 B,C,E,F,G를 나머지 다섯 producer에 하나씩 배치하면 된다. 모든 후보가 A<D를 보존하므로 동일 lane ancestry를 위반하지 않는다. 다른 추가 precedence가 없는 경우를 가정한다.

P를 V1–V3 중 어느 하나, Q를 V4/V5의 순서라고 하자. 후보는 실제 report에 존재하므로 bounded reported-candidate 정책 안에 있다.

| 항목 | P: score가 높은 후보 | Q: 다른 유효 후보 |
|---|---:|---:|
| 보고자 LCP 길이, 정렬 | 7,4,4,0,0 | 7,7,0,0,0 |
| LCP 합 | 15 | 14 |
| 보고자 총 재실행 | 20 | 21 |
| 여섯 노드의 남은 계산량, 오름차순 | 0,3,3,7,7,7 | 0,0,7,7,7,7 |
| 두 결과 준비 시간 T₂ | 3 | 0 |
| 세 결과 준비 시간 T₃ | 3 | 7 |
| 모든 결과 준비 시간 T₆ | 7 | 7 |

P의 세 후보가 동점이어도 모두 같은 결론이다. Score는 Q보다 엄격히 높고 총량은 줄지만, 두 결과를 가장 빨리 모으는 데에는 Q가 낫다. 반대로 세 결과를 요구하면 P가 낫다. 어느 endpoint를 택하는지가 이득 판단을 바꾼다.

f+1 결과 인증을 택한다면 이 예시의 q는 2가 된다. 현재 문서에서 그 endpoint가 선택 사항으로 남아 있으므로 여기서 이를 새 기본 정책으로 확정하지 않는다. 또한 report 수집 threshold와 실행 결과 인증 threshold를 연결하거나 plan approval quorum을 추가하지 않는다.

Pre-cut 조정 시간이 충분하면 차이가 가려질 수 있다. 모든 노드에 동일하게 L만큼 계산할 시간이 있다면 post-cut 계산 성분은 max(0,T_q−L)이다. q=2일 때 L=0/1/3이면 P는 3/2/0, Q는 모두 0이다. 실제로는 plan 전달 지연과 속도가 노드마다 다르므로 동일 L 가정도 별도 통제 조건이다.

위 네 후보의 LCP, residual 정렬, T₂/T₃/T₆, A<D 보존 및 L=0/1/3을 JavaScript로 계산·assert했다. 이는 수학적 반례의 sanity check이며 distributed benchmark, 실제 quorum certificate 생성 또는 workload 대표성의 증거가 아니다.

또한 ancestry-valid 순열이라는 사실만으로 현재 미정인 정상 report 생성 규칙에서 그 조합이 도달 가능하다고 입증한 것은 아니다. 이 반례는 scorer의 일반적인 목적함수 한계를 보이며, 실제 honest execution에서의 발생 여부는 §11의 생성 규칙과 event trace로 확인해야 한다.

### 10.3 논문과 평가에서 바꿔야 할 주장

안전한 주장: “LCP 합은 단순 모델에서 총 재실행량을 줄이는 근거가 있는 proxy다. 이것이 state-finalization latency까지 개선하는지는 결과 준비 시각, plan lead time, queueing 및 추가 비용을 포함해 평가한다.”

피해야 할 주장: “더 높은 LCP 합 → 더 적은 재실행 → 반드시 더 빠른 state finalization.” 두 번째 화살표는 위 반례에서도 성립하지 않는다. 낮은 부하에서는 빠른 소수의 준비 시각이, 포화 부하에서는 총 작업량과 queueing이 각각 더 중요할 수 있으므로 부하 구간을 구분한다. 후자의 실제 우세도 실험 없이 단정하지 않는다.

평가에 추가할 최소 계측:

- Node별 final-context execution 완료 시각의 분포. 그중 실제 protocol의 endpoint에 필요한 순서통계량을 명시한다.
- 총 재실행 CPU와 critical nodes의 post-cut 잔여 시간을 별도 보고한다. 전체 평균의 개선으로 인증 완료 latency를 대신하지 않는다.
- Plan 수신→order finality 사이의 node별 lead time 및 실제 이용 가능한 계산 시간.
- 동일 입력 집합의 위 반례 workload와 낮은 부하/포화 부하 비교. 실제 분산 실험과 order-only 진단을 구분한다.
- Offline oracle로 후보별 실제 endpoint를 비교하여 score 선택의 기회손실을 측정할 수 있다. 실행 진척을 production planner에 몰래 전달하지 않는다.

권고는 즉시 sum을 q번째 LCP로 교체하는 것이 아니다. 그러면 거짓 intention과 소수 node 의존의 영향을 별도로 분석해야 하며, 현재 reports는 완료 증거가 아니다. 먼저 실제 finalization endpoint를 고정하고, 현재 score의 총량 이득이 그 endpoint로 연결되는 조건을 측정한다. 현재 세 비교군과 consensus 정책은 변경하지 않는다.

## 11. Report 생성 규칙과 실제로 도달 가능한 disagreement

현재 prefix-plan §2는 report의 문맥·내용을 정하고 §6은 plan에 따른 실행 조정을 설명하지만, 정상 validator의 intended order 생성 함수를 완전히 정하지 않는다. 같은 blocks를 가진 두 정상 node가 왜 A→B와 B→A를 각각 보고하는지 설명하려면 block 수신 시 insert/append, 기존 plan 적용, report snapshot 시점을 정의해야 한다. 이 문제는 wire encoding만의 빈칸이 아니라 논문의 workload·동기부여·효과를 결정하는 설계 항목이다.

### 11.1 Deterministic rule 아래에서 무엇이 달라질 수 있는가

다음 제한된 경우를 먼저 구분한다. 같은 parent에서 block별 고정 total order ≺가 있고, node i가 알고 있는 eligible set S_i를 그 순서로 정렬해 보고한다고 하자.

```text
R_i = sort_≺(S_i)
```

두 reports가 모두 가진 blocks에 대해서는 상대 순서가 동일하다. 증명은 간단하다: 두 block a,b의 순서는 양쪽 모두 같은 비교 a≺b로 정해진다. 따라서 동일한 S_i라면 reports도 같고, block 도착 순서만 달랐다는 이유로 같은 집합의 A→B와 B→A가 나올 수 없다.

주의: 이는 모든 deterministic ordering 함수에 대한 정리가 아니다. 전체 입력 집합이나 바뀌는 graph에 따라 priority를 다시 계산하는 함수는 subset에 대한 상대 순서 보존을 만족하지 않을 수 있다. 그런 함수를 쓰려면 필요한 입력과 변화 규칙을 명시해야 한다. 같은 parent·동일한 전체 함수 입력이면 결과가 같다는 결정성과, 다른 subset에서도 상대 순서가 보존된다는 성질은 다르다.

실제로 가능한 disagreement의 예:

```text
기본 priority: X < A < B

X를 아직 모르는 V1–V4:  A → B
X를 아는 V5:            X → A → B
```

이 경우 두 집단 모두 A<B를 지킨다. 차이는 공통 blocks의 반대 순서가 아니라 앞쪽 입력의 누락이다. 반대로 같은 blocks의 서로 다른 순열을 사용한 기존 score 예시들은 이전에 채택한 plan의 차이, snapshot freshness, 다른 local scheduling 규칙 등의 생성 근거가 추가로 필요하다. 그런 예시가 무조건 잘못됐다는 뜻은 아니다.

고정 total order X,A,B,C의 모든 16개 subsets 쌍, 총 256쌍에서 공통 blocks의 상대 순서가 같은 것을 JavaScript로 확인했다. 일반 근거는 위의 비교 함수 논증이고 유한 열거는 보조 확인이다.

### 11.2 누락 입력 처리에 따라 planner가 실질적으로 달라진다

위 다섯 reports에서 leader가 X,A,B를 모두 유효하게 확보했다고 하자. X는 A의 필수 ancestry가 아니며, X<A는 변경 가능한 기본 priority라고 가정한다.

| Candidate 구성 방식 | 결과 |
|---|---|
| 각 report에 union을 보충하고 기본 rule로 전체 재정렬 | 모든 후보가 X→A→B가 됨 |
| Report의 순서를 prefix로 보존하고 나머지를 유효하게 suffix에 추가 | A→B→X 또는 X→A→B가 됨 |

첫 방식에서는 이 snapshot의 후보 선택이 사라진다. 두 번째 방식에서 score는 A→B→X가 8, X→A→B가 3이다. 이 산술도 계산으로 확인했다. Overpass가 A→B→X를 최종 순서로 제안한다면 기존 priority를 바꾼 것이며, exact order가 cut consensus에 결합되어야 한다. 기존에 결정된 X→A→B를 단순히 빠르게 실행한 것으로 설명하면 안 된다.

이는 현재 positioning인 execution-aware ordering extension과 양립한다. 다만 다음 두 제약을 섞지 않아야 한다:

- 반드시 지킬 제약: 선택된 producer ancestry, 확정한 과거, 기반 합의의 필수 포함·순서 조건.
- 변경 가능한 선호: 아직 확정되지 않은 cross-lane base priority. 정확히 어디까지 바꿀 수 있는지는 기반 profile과 함께 고정해야 한다.

X가 필수 predecessor라면 A→B→X는 높은 점수와 무관하게 무효다. 또한 알고리즘은 leader가 알지 못하는 X를 미리 넣는 것이 아니다. 보고로 reference를 발견하거나 dissemination에서 받은 후, 유효성·가용성 조건을 확인한 입력으로 후보를 만든다.

### 11.3 구현 전에 고정할 작은 계약

정상 report 생성 규칙에는 다음이 필요하다:

1. 공통 parent에서 시작하는 tentative order 전체를 보고하는지, 아직 실행하지 않은 queue만 보고하는지. 후자만 보내면 각 node의 원점이 달라져 현재 LCP 해석이 깨질 수 있다. 원점 일치는 유지해야 하며 실행 완료 여부를 report할 필요는 없다.
2. 첫 plan이 없을 때 block 수신으로 tentative order를 만드는 규칙과, 뒤늦은 predecessor를 알았을 때 갱신하는 규칙.
3. Plan을 적용한 후 새 block을 받았을 때 유지할 순서와 다시 계산할 순서. Finality lock이나 실행 이력 proof를 도입하지 않고도 local scheduling 규칙은 명시할 수 있다.
4. Report 생성 시점을 atomic snapshot으로 정하고 parent·window·plan 변경과 경합할 때 어느 snapshot을 계수하는지.
5. 다른 길이·membership의 reports를 공통 candidate horizon으로 비교하고, 후보를 완성·cut에 투영하는 규칙. 후보 집합이 실제 proposal의 입력과 어떻게 연결되는지도 포함한다.

위는 새 정책의 자동 채택이 아니라 현재 설계가 답해야 할 Interface다. Completion-before-score인지 after-score인지, base priority의 허용 변경 범위 등은 source of truth에 아직 확정하지 않았다.

### 11.4 Evaluation에서 임의 permutation을 실제 네트워크 현상으로 대신하지 않는다

Benchmark reports는 미리 원하는 분포로 뽑는 것만으로 충분하지 않다. 동일한 producer blocks, node별 도착·sync trace, 공통 parent 및 정상 scheduling 규칙에서 reports가 나오게 해야 한다. 인위적인 reports는 scorer stress test로 분리한다.

최소 진단은 다음과 같다:

- Report 차이를 missing-input / 공통 block의 상대 순서 차이 / 이전 plan revision 차이로 구분한다.
- 같은 set·parent·rule로 모든 node를 맞췄을 때 불필요한 차이가 남는지 확인한다.
- 첫 window의 이득과 이후 windows의 이득을 구분한다. 이후 report가 leader plan을 따라 같아지는 것은 조율의 결과일 수 있으나, 그것만으로 실제 실행 재사용을 입증하지는 못한다.
- Plan→report feedback 때문에 LCP가 늘어났는지와 실제 CPU·post-cut 잔여 시간이 줄었는지를 각각 계측한다. 보고 간 수렴을 finality quorum이나 execution completion으로 해석하지 않는다.

권고: 현재 설계를 갈아엎기 전에 작은 event trace 하나에서 **수신→tentative order→report→candidate completion→plan 적용→final cut 검증**을 재현한다. 이 경로가 정해져야 §3·§10의 반례가 실제 실행에서 가능한 경우인지, scorer의 더 넓은 입력 공간에 대한 이론적 경고인지도 구분할 수 있다.

## 12. 직접적인 선행 연구: optimistic delivery와 실행 overlap

이번 추가 검색은 speculative execution의 오래된 계보를 확인하기 위한 targeted review다. 전수조사 또는 novelty 검증 완료가 아니다. 아래는 검색 요약만이 아니라 원문의 관련 절을 확인한 내용이며, 현 설계와의 차이는 본 검토의 해석이다.

### 12.1 추가해야 할 비교 축

| 연구 | 확인한 핵심 내용 | Overpass에서 설명할 차이 |
|---|---|---|
| Pedone·Schiper, Optimistic Atomic Broadcast, DISC 1998 | 네트워크의 spontaneous total order를 이용한 빠른 delivery와 optimistic/conservative 결정 | 우리의 reports는 이미 같은 순서라는 증명이나 optimistic finality 조건이 아니다 |
| Kemme et al., Processing Transactions over Optimistic Atomic Broadcast Protocols, ICDCS 1999 | Tentative delivery에서 실행 시작, definitive order 뒤 commit·필요한 보정; crash-only model | Pipeline 자체가 아니라 reports를 이용한 ordering 후보 선택의 추가 효과가 필요하다 |
| Ports et al., Designing Distributed Systems Using Approximate Synchrony in Data Center Networks, NSDI 2015 (Speculative Paxos) | Mostly-Ordered Multicast를 이용한 사전 실행과 divergent logs의 reconciliation | Network ordering을 전제로 fast commit하는 설계와, 기존 BFT cut에 앞선 optional planning을 구분한다 |

근거: [DISC 1998 원문](https://www.inf.usi.ch/faculty/pedone/Paper/199x/1998DISC.pdf), [ICDCS 1999 원문](https://www.inf.usi.ch/faculty/pedone/Paper/199x/1999ICDCS.pdf), [Speculative Paxos 원문](https://www.cs.princeton.edu/courses/archive/spr17/cos598D/SpeculativePaxos15.pdf), [NSDI 2015 공식 서지](https://www.usenix.org/conference/nsdi15/technical-sessions/presentation/ports). Speculative Paxos의 발표 학회는 SOSP가 아니라 NSDI 2015다.

ICDCS 1999의 §1–§3은 ordering coordination과 transaction execution의 overlap을 명시한다. §3.2는 tentative/definitive order가 달라도 서로 충돌하지 않는 transactions는 보정할 필요가 없음을 설명한다. 따라서 실행 중첩뿐 아니라 dependency-aware 보정도 Overpass의 최초 기여로 제시할 수 없다. 다만 이것이 현재 Overpass의 구체적인 intended-order score와 cut integration까지 이미 제안했다는 뜻은 아니다. [원문 §1–§3](https://www.inf.usi.ch/faculty/pedone/Paper/199x/1999ICDCS.pdf)

Speculative Paxos §4.2.4에서는 reconciliation 동안 새 요청 처리를 멈추고 leader가 logs를 병합한다. 보존해야 할 prefix는 완료된 client operation의 safety와 연결된다. Overpass의 mutable intended-order plan은 그런 실행 log나 committed-prefix 증거가 아니다. 따라서 그 quorum/보존 논증을 현재 score로 옮겨 쓸 수 없다. [원문 §4.2.4](https://www.cs.princeton.edu/courses/archive/spr17/cos598D/SpeculativePaxos15.pdf)

### 12.2 Novelty를 남길 수 있는 정확한 질문

현재 positioning을 다음 질문으로 좁히는 것이 타당하다:

> 병렬 producer dissemination으로 노드마다 다른 tentative inputs를 관측하는 환경에서, finality를 기다리지 않고 수집한 intended-order feedback을 이용해 최종 ordering 후보를 선택하면, 같은 pre-cut execution만 사용하는 경우보다 state-finalization까지의 잔여 작업과 E2E latency를 줄일 수 있는가?

이는 기존 문서의 execution-aware ordering extension을 더 구체화한 연구 질문이지 새 protocol의 자동 채택이 아니다. 차별성을 입증할 대상은 세 가지다:

1. **입력 환경의 과제:** body 도착·sync와 lane prefix 선택이 어긋나는 정도, 그 때문에 실제 발생하는 invalidation. 단순히 blockchain이라는 도메인 이름을 바꾸는 것이 아니다.
2. **조율 메커니즘:** 직접 실행 증명 없이 bounded reports로 후보를 고르는 비용·품질, proposal 동결 이전의 사용 가능성, planner 실패 시 cut fallback.
3. **합의 연결:** 최종 exact order의 인증·복구와 speculative state 검증. 순서 선택 자유를 추가해도 기반 safety/liveness를 보존하는 계약.

이 셋을 하나의 시스템에서 연결하고 측정해야 한다. LCP, 사전 실행, deadline 각각의 최초성이나 모든 선행 protocol보다 나은 fault tolerance를 주장하는 방향은 피한다.

### 12.3 Non-blocking 비교의 공정한 범위

Overpass는 plan을 추가 finality로 사용하지 않는다. 그러므로 다른 protocol의 안전한 fast commit·recovery가 수행하는 일을 제거한 뒤 메시지 수만 비교하여 우월하다고 주장하면 안 된다. 우리의 non-blocking 주장은 **기존 cut consensus가 report 수집·optimizer·plan 승인 때문에 추가로 기다리지 않는다**는 범위에서 검증한다. Application의 입력·parent 대기와 실행 무효화는 여전히 존재한다.

이 비교는 Related Work와 설계 근거에 추가할 내용이지 benchmark baseline을 더 늘리자는 요구가 아니다. Original / Pre-cut execution / Overpass 세 구성을 유지한다. Original 대비 개선은 overlap 효과이고, Overpass의 추가 기여는 Pre-cut execution 대비 비용까지 포함한 개선으로 입증한다. 오래된 논문의 수치를 최신 fork 수치와 직접 대조하지 않는다.

### 12.4 제출 준비에 미치는 결론

문헌 검토상 “consensus와 execution을 overlap한다”만으로는 기여가 약하다. 그러나 현재 intended-order feedback 설계가 무의미하다는 결론도 나오지 않는다. 우선순위는 문구 강화보다 다음 실증 사슬을 채우는 것이다:

```text
실제 입력 도착 편차
  → 정상 report 생성 규칙 아래의 후보 차이
  → feedback이 final order 선택을 실제로 바꿈
  → final-context에서 재사용 가능한 작업 증가 또는 조정 시점 앞당김
  → 추가 통신·계산·ordering 지연을 포함해 state/E2E latency 개선
```

각 화살표를 계측하고 반례 workload에서도 한계를 보여야 한다. Reports가 같아졌거나 LCP score가 커진 사실만으로 마지막 결론을 대신하지 않는다. 논문이 이 연결을 보여주면 단순 pipeline 구현보다 설득력이 커지지만, 학회 채택 가능성은 현재 자료로 판정할 수 없다.

## 13. 같은 context의 오래된 report도 재실행을 증폭할 수 있다

현재 명세는 parent/view/window가 다른 보고를 거부하고, 이미 전파한 proposal을 late plan으로 변경하지 않는다. 그러나 **context가 유효한 것과 intended order가 여전히 최신인 것은 다르다.** 같은 window 안에서 늦은 block을 받고 실행 방향을 바꾼 노드의 이전 report는 여전히 context 검사를 통과할 수 있다. 동일 snapshot에서 incumbent와 후보를 비교해도 그 snapshot 전체가 낡았으면 이 문제는 남는다.

### 13.1 정상 노드만 있는 작은 event trace

§11과 같이 기본 priority는 X<A<B이며 blocks는 서로 다른 lanes에 있고, X<A는 바꿀 수 있는 priority일 뿐 필수 ancestry가 아니라고 놓는다. 각 block은 순서에 민감한 같은 accumulator를 갱신하며 계산 cost는 2 시간 단위다. 기존 local rule은 새 predecessor를 받으면 tentative order에 insert하고 필요한 실행을 보정한다. 이 rule 및 아래 비용은 분석용 가정이지 아직 구현된 기본 설정이 아니다.

n=6/f=1에서 V1–V4는 처음 A,B만 알고 V5는 X,A,B를 안다. V6은 report를 내지 않는다. 같은 parent·view·window이며 모든 노드는 정직하다. Candidate completion은 보고된 prefix를 유지하고 유효한 나머지를 suffix로 추가하는 경우를 사용한다.

| 시각 | 사건 |
|---:|---|
| 0 | V1–V4가 A→B 실행 시작 |
| 1 | V1–V4가 A→B, V5가 X→A→B report 생성 |
| 4 | V1–V4의 A→B 실행 완료 |
| 5 | V1–V4에 X 도착. 기본 rule에 따라 X→A→B로 조정·실행 |
| 8 | Leader가 다섯 report를 확보. A→B→X score=8, X→A→B score=3 |
| 10 | 준비된 A→B→X를 사용해 proposal 동결 |
| 11 | V1–V4의 X→A→B 실행 완료 |
| 12 | V1–V4가 A→B→X plan/해당 proposal 정보를 수신 |
| 15 | 해당 후보의 ordering finality |

계산 예산 및 변경 억제 정책이 이 후보를 수용하고 t=10 이전에 계산이 끝난 경우다. Cut은 collection을 기다리거나 이미 동결한 proposal을 바꾸지 않는다. 비교하는 Pre-cut execution의 ordering도 같은 t=15에 완료된다고 통제한다. 이는 실제 network run에서 두 finality 시각이 같다는 주장이 아니다.

최신 branch만 보존하는 실행기라면 V1–V4는 t=12부터 A→B→X를 다시 실행하여 t=18에 완료한다. Pre-cut execution만 사용했다면 X→A→B가 최종 순서이고 t=11에 계산을 끝내 t=15에 final-context local readiness를 갖는다.

| V1–V4 각각의 결과 | Pre-cut execution | Overpass, 최신 branch만 보존 | Overpass, 이전 A→B checkpoint도 보존 |
|---|---:|---:|---:|
| 계산 완료 시각 | 11 | 18 | 14 |
| 누적 계산량 | 10 | 16 | 12 |
| Ordering finality 시각 | 15 | 15 | 15 |
| Local state readiness 시각 | 15 | 18 | 15 |
| Post-cut 잔여 시간 | 0 | 3 | 0 |

Checkpoint를 보존한 경우에는 A→B의 정확한 parent·input·runtime을 확인해 재사용하고 X만 실행한다고 놓았다. 이 사례의 숫자는 local readiness이며 signature 수집·durable storage를 포함한 전체 state-finalization 측정이 아니다. 고정 비용의 계산·시각 관계를 JavaScript로 assert했으며 protocol 구현이나 E2E benchmark를 실행한 것은 아니다.

이 trace는 두 가지를 분리한다. 과거 의도를 반영하는 조율이 현재 작업을 다시 무효화할 수 있다는 점과, 그 비용이 실행기의 speculative branch 보존 방식에 의존한다는 점이다. 모든 실행기가 반드시 세 blocks를 다시 실행한다고 주장하지 않는다. Reports는 처음 생성될 때 참이었으며 악의적 조작도 필요하지 않다.

### 13.2 설계에 필요한 것은 freshness의 정확한 의미

다음 정보를 offline 계측하면 원인을 구분할 수 있다:

- Sender가 report를 만들 때와 plan을 받을 때의 intended-order 차이.
- 그 사이 도착한 blocks와 바뀐 plan revision, 최초 불일치 위치.
- Plan 때문에 순서를 되돌린 횟수, 이미 버린 branch를 다시 계산한 작업량.
- Parent가 바뀌어 무효인 보고와, parent는 같지만 의도가 바뀐 보고의 비율.

보고가 실제 실행을 완료했다는 증명은 요구하지 않는다. 실제 실행 이력은 benchmark의 offline oracle에만 둔다. 시간 정보도 분석에서는 sender-local event 간 경과를 사용할 수 있으므로 synchronized Unix clock을 도입할 필요가 없다.

### 13.3 개선 옵션과 비용 — 아직 채택하지 않음

1. **Window 안의 더 최신 report를 활용:** identity당 가중치는 계속 하나여야 하며 revision 교체·equivocation·snapshot 동결 규칙과 report rate bound가 필요하다. 최신 보고를 받기 위해 cut을 기다리게 하지 않는다. 기존 first-valid 방향을 바꾸는 결정이므로 자동 적용하지 않는다.
2. **Collection·전파 시간을 짧게 제한:** 오래된 계획을 쓸 가능성을 낮출 수 있지만 coverage가 줄며 최신성 자체를 보장하지 않는다. 현재 τ/horizon/update-rate ablation에 freshness 지표를 붙여 평가할 수 있다.
3. **제한된 speculative checkpoint 재사용:** 반례의 추가 계산을 줄일 수 있으나 메모리·lookup·validation 비용이 생긴다. 같은 backend와 같은 memory budget을 Pre-cut execution과 Overpass 양쪽에 적용해야 한다. Overpass만 더 많은 cache를 쓰고 planning의 이득으로 세지 않는다.

세 옵션을 한꺼번에 채택하라는 권고가 아니다. 먼저 stale-but-valid reports가 자주 생기는지 확인하고, 그때 가장 작은 조정을 택한다. Plan 수신 시 추가 quorum이나 실행 확인 handshake를 붙이는 해법은 현재 non-blocking 설계 범위에 포함하지 않는다.

다음 implementation 검토의 기반 profile(native Multimmit 유지 또는 fixed-cut 변형)은 사용자에게 선택을 요청했다. 이 선택 전에는 어느 profile도 현재 설계로 확정하거나 consensus 코드를 수정하지 않는다. 해당 결정과 무관한 위 freshness·cache 분석은 두 방향 모두에 적용되는 검토 항목이다.

## 14. 기존 benchmark·toy model의 증거 범위 재확인

기존 파일을 새 설계의 성능·안전성 증거로 잘못 인용하지 않도록 소스를 확인했다. 이번에 실행한 것은 아래 Python unit tests뿐이다. Rust benchmark, cloud 배포 및 새 Overpass E2E는 실행하지 않았다.

| 현재 artifact | 소스상 측정/검증 범위 | 현재 논문에서의 허용 범위 |
|---|---|---|
| `glue/benches/multimmit_state_finality.rs` | 5개 lane의 SHA-256 계산 및 local reducer join; preexecuted 경로는 계산·vote 집계가 측정 구간 밖 | 준비된 결과를 결합하는 local microbenchmark. 현재 planning의 latency 개선 결과 아님 |
| `examples/log-multimmit` | 실제 consensus protocol의 commitments/metadata 처리, body-free mock attachment | Network·consensus 운영의 출발점. Application ingress→state E2E 아님 |
| `research/block_views` | 이전 DAG/실행이력 기반 선택과 read-input cache repair의 유한 모델 | Oracle·cache 검증 방식 재사용 후보. 현재 LCP planner의 구현·검증 아님 |
| `research/precut_order/model.py` | 외부 consensus 결정을 가정한 dependency/SCC 모델 | 이전 설계 참고. 현재 intended-order collection/plan finality 증거 아님 |

### 14.1 Rust microbenchmark의 비교 범위

`preexecuted`와 `ready_tracker`는 `bench_function` 전에 구성된다. Baseline은 매 iteration에서 payload hash 실행, tracker 생성, signer 집계 및 state-cut join을 수행하고, proposed 경로는 준비된 tracker에서 join한다. `certify`는 signer ID 네 개를 같은 statement로 reducer에 넣으며 네트워크·독립 replica 실행·signature verification을 수행하는 함수가 아니다.

이는 microbenchmark 자체가 잘못됐다는 뜻은 아니다. 이미 준비된 결과의 소비 비용이라는 좁은 질문에는 맞지만, 준비가 제시간에 끝나는 확률, late predecessors, plan 교환, 재실행, CPU 경합은 측정하지 않는다. 따라서 그 두 숫자의 차이를 현재 Overpass의 E2E speedup이나 intended-order planning의 추가 효과라고 쓸 수 없다.

근거: [준비 구간](commonware/glue/benches/multimmit_state_finality.rs:44), [baseline 측정](commonware/glue/benches/multimmit_state_finality.rs:60), [preexecuted 측정](commonware/glue/benches/multimmit_state_finality.rs:74).

### 14.2 Consensus 예제의 성공과 application 완성은 다르다

`log-multimmit` README는 payload store, marshal, ordered delivery, backfill이 없음을 명시한다. Mock `verify`는 true를 반환하고 `Relay::broadcast`는 payload를 전송하지 않는다. 현재 사용 목적이 consensus 예시이므로 이를 Byzantine-safe application custody나 state readiness 구현으로 확장 해석하지 않는다.

따라서 최소 E2E에는 실제 transaction bytes, input recovery, exact order delivery, 실제 state-changing execution, 재검증 및 정해진 완료 endpoint가 필요하다. 예제의 dashboard에 보이는 L-QC/round latency가 자동으로 application finalization latency가 되는 것은 아니다.

근거: [예제 범위](commonware/examples/log-multimmit/README.md:28), [mock verification](commonware/examples/log-multimmit/src/application/actor.rs:65), [no-op relay](commonware/examples/log-multimmit/src/application/actor.rs:82).

### 14.3 이번에 재실행한 기존 테스트

```text
python3 -B -m unittest discover -s research/block_views -v
Ran 35 tests in 2.051s
OK
exit code: 0
```

위 시간은 unit-test runner 출력이지 protocol latency가 아니다. 기존 결과 문서의 32개 표기와 달리 현재 suite에는 35개가 있다. 과거 문서를 새 실행 기록처럼 덮어쓰지 않는다.

확인한 유용한 속성은 late writer, 제외된 speculative writer, failed transfer의 이전 credit 제거, unchanged reads의 cache reuse, 다른 worker order의 동일 결과, 독립 sequential oracle과의 비교다. `test_properties.py`는 40 seeded cases 및 49개 작은 report 조합을 포함한다. 그러나 `View.executed`를 입력으로 사용하고 `_score`는 예상 repair cost를 계산한다. 현재 intended-order-only LCP 합과 다른 선택 함수다. 모델의 q도 n=6/f=1에서 4이므로 현재 아직 고정되지 않은 endpoint의 증거로 옮기지 않는다.

근거: [View](research/block_views/selection.py:62), [이전 score](research/block_views/selection.py:392), [독립 oracle](research/block_views/test_properties.py:10), [cache 검증 cases](research/block_views/test_selection.py:220). 기존 experiment는 각 block arrival마다 pre-execution을 완료한 뒤 다음 arrival을 처리하고 timing에 unit-work model을 사용한다. 실제 concurrent arrival·report·execution race는 별도 검증해야 한다. [실험 runner](research/block_views/experiment.py:38)

현재 SUT 식별용 SHA-256:

```text
selection.py  b7e8654d51cb7ff297c46fb6f50b36b31157ae49f049867c674c3c2ec88cf0f8
experiment.py 8dd3384bde242bc094c20a2728f514e70fad4303c7f3fd17ffcfb04063ae66a4
```

코드를 수정하거나 기존 tests의 이름만 바꿔 현재 모델을 검증했다고 주장하지 않는다. 재사용할 것은 검증 기법과 독립 oracle이고, reports·선택·timer·consensus의 새 동작은 별도 시험 대상이다.

### 14.4 다음 결과를 내기 위한 최소 통과 조건

1. **세 구성 공통 경로:** Original / Pre-cut execution / Overpass가 같은 application, payload·custody, consensus profile, exact-order delivery와 completion 의미를 사용한다.
2. **동작 확인:** 정상 수신 trace에서 intended reports가 생성되고, score가 선택을 바꾸며, final cut이 선택한 exact order를 인증한다. Synthetic report만 사용하는 시험과 구분한다.
3. **정확성 확인:** 최종 입력을 처음부터 실행한 독립 oracle과 state 및 application outputs가 같고, 재시작 후 중복 state effects가 없다.
4. **누락 없는 비용:** Pre-cut 준비·검증·재실행·reports·plan·body fetch와 apply를 각각 계측한다. Join 밖으로 옮긴 비용을 없어진 비용으로 세지 않는다.
5. **추가 기여 확인:** Pre-cut execution 대비 Overpass의 post-cut와 ingress-to-state 효과를 평가한다. 개선이 없다면 Original 대비 수치로 가리지 않는다.

이 조건은 새 기능을 다 추가하자는 요구가 아니라 논문이 주장하는 경로에 실제 evidence를 연결하기 위한 최소 기준이다. 원형 구현 완료 전에는 local microbenchmark와 toy-model 결과로 명확히 표시한다. 현재 artifact 검토로는 이 다섯 조건이 충족됐다고 확인할 수 없다.

## 15. 독립 작업의 순서 차이를 LCP가 과대평가하는 경우

§10은 prefix 재사용량을 정확히 알아도 합계와 finalization endpoint가 다르다는 문제였다. 여기서는 그보다 앞선 문제를 분리한다. **Dependency-aware 재검증을 사용하면, 실행이 모두 끝나 있고 작업 비용도 같아도 LCP 합과 실제 재실행량의 순위가 반대일 수 있다.** §3의 prefix 뒤 전체 폐기 모델에 대한 등식은 이 실행 방식에 그대로 적용되지 않는다.

### 15.1 입력을 검증하는 cache 모델의 반례

동일 parent에서 x=y=i=j=0이고 네 block은 다음과 같다. 각 block은 transaction 하나를 가진다. 서로 다른 producer의 block으로 두어 아래 순서가 lane ancestry를 위반하지 않게 한다.

```text
A: x := 1
B: y := read(x)
I: i := 1
J: j := 1
```

I와 J는 나머지 작업과 독립적이다. A와 B의 상대 순서만 B의 read와 결과를 바꾼다. n=6, f=1의 window에 다섯 정상 보고가 아래와 같이 들어왔다고 가정한다. 제6 노드는 이 snapshot에 포함되지 않는다. 비교를 단순화하기 위해 보고한 작업은 모두 완료되었다고 두지만, 이를 protocol report의 새 필드나 leader가 아는 정보로 추가하는 것은 아니다.

```text
R1: I → J → A → B
R2: J → I → A → B
R3: A → I → J → B
R4: B → A → I → J
R5: B → A → I → J
```

| 후보 | LCP 합 | R1/R2/R3/R4/R5의 실제 재실행 block 수 | 합계 |
|---|---:|---|---:|
| I → J → A → B | 4 | 0 / 0 / 0 / 1 / 1 | 2 |
| J → I → A → B | 4 | 0 / 0 / 0 / 1 / 1 | 2 |
| A → I → J → B | 4 | 0 / 0 / 0 / 1 / 1 | 2 |
| B → A → I → J | 8 | 1 / 1 / 1 / 0 / 0 | 3 |

Raw score 최대 후보는 마지막 순서다. 하지만 앞선 세 노드는 서로 다른 순서로 실행했어도 A/B에 대해서는 같은 유효 작업을 갖고 있다. 마지막 후보를 고르면 세 노드의 B를 다시 실행해야 한다. 앞선 후보 중 하나를 고르면 R4/R5의 B만 다시 실행하면 된다. 점수 개선 폭 제한이 4보다 크거나 다른 update 제한이 적용되면 변경을 억제할 수 있으므로, 이 표는 raw ranking의 한계이지 모든 설정에서 실제 plan이 변경된다는 주장이 아니다.

두 종류의 후보는 각각 최종 y=1과 y=0을 만든다. 이는 서로 다른 합법적 serial order의 결과다. A/B까지 독립적이거나 모든 후보가 동일한 application 결과를 만든다는 뜻이 아니다. 잘못된 state를 채택하는 safety 반례도 아니다.

### 15.2 확인한 범위와 전제

JavaScript로 네 block의 24개 순열에서 모든 source→target 조합 576개를 검사했다. Source 실행에서 block별 read value와 write effects를 저장하고, target 순서의 parent overlay에서 read value가 같으면 effects를 재적용하며 다르면 해당 block을 실행했다. 모든 조합에서 처음부터 실행한 target 결과와 같았고, A/B의 상대 순서가 바뀐 경우에만 B를 다시 실행했다. 위 표의 score와 repair 수 역시 assert/계산으로 확인했다.

이는 작은 수학적 cache 모델이며 기존 Rust/Python 구현을 시험한 결과가 아니다. Gas, 외부 효과, range read, implicit runtime input은 없는 모델이다. 일반 실행기에서는 그러한 의존성도 검증해야 하며, 이전 전체 state root를 그대로 재사용할 수 있다는 뜻도 아니다. Effects 재적용·root 구성·validation 비용은 재실행 block 수와 별도다.

또한 이 보고 snapshot은 유효 순서들에 대한 목적함수 반례이지, 실제 honest report generator에서의 도달 가능성 증명이 아니다. §11처럼 같은 block 집합을 항상 같은 고정 comparator로 정렬하면 이 다섯 순서가 나오지 않는다. 실제 계획 변경·도착·report 생성 규칙에서 이런 불일치가 생기는 빈도는 trace로 확인해야 한다. Counterexample에 맞춰 report를 직접 만드는 시험을 정상 network benchmark로 제시하지 않는다.

### 15.3 논문에 필요한 보완 — 새 알고리즘 추가보다 먼저

- **주장 범위:** LCP는 application-independent order-prefix proxy다. Dependency-aware 실행기의 실제 invalidation을 최소화한다고 주장하지 않는다. 독립 block의 순서가 달라도 재사용 가능한 점은 한계와 평가에 명시한다.
- **독립 작업 대조군:** 모든 작업이 독립적인 workload에서는 재실행 절약 여지가 거의 없다. 세 비교군에 동일한 cache/validation 정책을 적용하고 Overpass의 추가 통신·계산 비용을 확인한다. 재정렬된 suffix 길이를 실제 wasted execution으로 세지 않는다.
- **혼합 workload:** 소수의 order-sensitive 작업 사이에 독립 작업을 늘려, score가 dependency 보존을 얼마나 잘 설명하는지 본다. Input set·execution cost를 통제한 진단과 실제 arrival 기반 E2E를 구분한다.
- **Offline 진단:** 동일 snapshot의 bounded 후보들을 동일 cache 상태에서 재검증해 score 순위와 repair 순위를 비교한다. Leader에게 remote execution history나 dependency oracle을 제공하지 않는다. 이 진단 결과를 새 온라인 선택 알고리즘으로 오인하지 않는다.
- **비용 분리:** 재실행한 application 작업, read-validation, effects 재적용/root 계산, 계획 변경 비용을 구분한다. Order 일치율·LCP 증가가 실제 실행 절약으로 이어졌는지 확인한다.

현재 score나 report 형식을 즉시 변경하자는 결론은 아니다. 단순한 LCP가 충분히 좋은지부터 위 대조군으로 확인한다. 특정 workload에서만 이득이 나면 그 조건을 논문의 claim으로 제한하는 편이 보편적 재실행 최소화 주장보다 근거가 강하다. Placement·새 execution engine·원격 실행 증명은 이 검토로 복원하지 않는다.

## 16. 점수 계산은 가볍게 할 수 있지만 no-wait는 따로 검증해야 한다

현재 spec은 계산 예산과 cut preemption을 요구하지만, 실제 계산법·상한·scheduler 격리는 아직 정하지 않았다. 이 부분은 새 protocol을 추가하지 않고 구체화할 수 있다. 아래는 구현 권고이며 기존 score나 합의 정책 변경이 아니다.

### 16.1 같은 LCP 점수를 prefix trie로 계산

보고 수를 r, 후보 수를 c, 최대 길이를 W라고 하자. 각 후보와 모든 보고를 직접 대조하면 최악 O(crW)번의 block-reference 비교가 필요하다. 보고 후보와 incumbent를 모두 평가하면 c는 r에 비례할 수 있다.

하지만 공통 prefix를 저장하는 trie의 각 node에 그 prefix를 가진 보고 수를 기록하면 같은 점수를 다음과 같이 계산할 수 있다.

```text
count(S) = S로 시작하는 유효 보고의 수
Score(P) = Σ(d=1..|P|) count(P[1..d])
```

증명은 LCP 길이를 prefix 일치 여부의 합으로 풀고 합산 순서를 바꾸는 것이다.

```text
Σ_i LCP(P,R_i)
  = Σ_i Σ_d 1[R_i의 길이가 d 이상이고 R_i[1..d] = P[1..d]]
  = Σ_d count(P[1..d])
```

따라서 보고 전체 길이 M, 후보 전체 길이 K에 대해 build+score는 O(M+K)개의 trie edge 조회로 계산할 수 있다. Child lookup이 상수 시간이라는 가정이며, hash map에서는 기대 비용이다. 결정적 worst-case가 필요한 구현에서 balanced map을 쓰면 child degree에 따른 log 비용을 포함한다. Memory는 최대 O(M) nodes/edges와 후보·보고 보관 비용이다. 실제 할당량·cache locality·reference hashing 및 DoS 저항성은 별도 측정한다.

이것은 통상적인 prefix 자료구조를 현재 목적함수에 적용한 구현 기법이지 연구 novelty가 아니다. Trie의 prefix 처리 배경: [Sedgewick–Wayne, Algorithms §5.2](https://algs4.cs.princeton.edu/52trie/). 위 count 합 등식은 현재 score에 대한 직접 유도다.

### 16.2 Pseudocode — 유효 snapshot에 대한 계산만

```text
input: context-checked, identity-deduplicated immutable reports R
       bounded valid candidates F, incumbent, fixed horizon W

tree = empty prefix trie
for each report in R:
    node = tree.root
    for each exact block reference in report within W:
        node = get_or_create_child(node, reference)
        node.count += 1

for each candidate P in F, including eligible incumbent:
    node = tree.root
    score[P] = 0
    for each reference in P within W:
        node = child(node, reference)
        if node does not exist: break
        score[P] += node.count

return scores to existing tie-break and update policy
```

Candidate completion/suffix 정책은 계산 전에 고정하며, 같은 prefix node가 존재한다는 이유로 임의 경로를 새 후보로 만들지 않는다. 보고 내용이 같아도 서로 다른 validator이면 각각 count한다. 반대로 같은 identity의 중복 전송은 trie에 넣기 전에 제외한다. Context·서명·refs·ancestry·가용성 검증을 이 자료구조가 대신하지 않는다. Report count나 trie count를 승인 quorum으로 해석하지 않는다.

JavaScript에서 seed `0x5eed2026`의 2,000개 생성 snapshot 및 빈 입력·서로 다른 길이·같은 순서의 다중 보고·미보고 incumbent 등을 포함한 3개 경계 snapshot을 비교했다. 총 **43,229개 candidate score**가 직접 LCP 합과 같았다. 이 검사는 점수 등식의 유한 sanity check이며 현재 Commonware 구현, tie-break/update state machine, 인증 검증 또는 latency 시험이 아니다.

### 16.3 `async`라는 이름만으로는 cut이 비차단이 되지 않는다

빠른 점수 계산도 admission 검증, memory allocation, consensus와 공유한 lock, NIC 전송을 기다리게 만들 수 있다. 또한 async 함수 안의 긴 CPU loop는 같은 executor의 cut-ready 처리를 늦출 수 있다. 따라서 두 층위의 주장을 분리해야 한다.

1. **Protocol-level no-wait:** cut proposal은 report·timer·optimizer 완료를 선행조건으로 삼지 않는다. 이미 검증된 candidate/fallback만 읽는다.
2. **Resource interference:** planning이 CPU·memory·network를 사용하므로 ordering latency 영향이 정확히 0이라는 주장은 하지 않는다. 같은 자원 예산에서 간섭을 측정하고 제한한다.

구현 시 검토할 최소 조건은 bounded input/queue, immutable snapshot, 계산 중 consensus lock 미보유, 계산 결과의 context 재검사, proposal freeze 이후 late result 폐기, consensus 메시지 처리에 대한 scheduling 여유다. 별도 worker를 쓰더라도 같은 총 CPU 예산에 포함한다. Worker 분리나 cooperative yield는 선택 가능한 구현 수단이지 이미 채택·구현된 기능은 아니다.

핵심 시험은 report를 최대로 채우고 optimizer가 진행 중일 때 cut-ready를 발생시키는 것이다. Cut이 optimizer의 종료 event 없이 prepared fallback으로 진행하는지 확인하고, planner-off 대비 ordering p95/p99와 event-queue 지연을 측정한다. Score 연산만 빨라진 microbenchmark로 이 성질을 대신하지 않는다.

이 보완은 기존의 세 비교군을 유지하면서 bounded planning의 구현 근거를 강화한다. 우선순위는 새 score 개발보다 exact-order adapter와 primary completion endpoint 확정이 앞선다. Trie 최적화만으로 §3·§10·§15의 proxy 한계나 finalization latency 문제를 해결했다고 주장할 수 없다.

## 17. Rashnu와의 직접 비교: report 수집 자체는 차별성이 아니다

Rashnu 원문의 §1, §3, §4.1–4.4와 Algorithms 1–3을 확인했다. 현재 outline의 한 줄 설명보다 중요한 겹침이 있다. 아래는 특정 기존 연구와의 비교이며 전체 문헌에 대한 novelty 입증이 아니다.

### 17.1 원문에서 확인한 내용

Rashnu는 transaction 수신 순서와 read/write 의존성으로 local DAG를 만들고, leader가 n−f local reports에서 global graph를 구성한다. Reports를 첨부해 graph를 검증한 뒤 기반 BFT consensus를 수행한다. 목적은 data-dependent order-fairness다. 시간·거래 수 기반 round와 ordering/consensus 분리도 제시한다. Algorithm 3의 실행 단계는 consensus 뒤에 있으며, 본문에는 block 간 독립 실행을 위한 확장도 있다. [Rashnu, PVLDB 17(9), pp.2335–2348, 특히 §4.2–4.3](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)

따라서 “local orders → leader → ordering 후보 → 기존 consensus”만으로는 충분한 새 기여가 아니다. 또 Algorithm 3에는 별도의 global-plan support round 없이 검증 후 기반 consensus로 연결되는 경로가 있으므로, **추가 plan 승인 단계가 없다는 사실만을 독립적인 novelty로 제시하지 않는다.** Rashnu를 단순히 항상 block별 직렬 실행만 하는 모델이라고 설명하는 것도 본문의 확장을 누락한다. [같은 원문 §4.3](https://www.vldb.org/pvldb/vol17/p2335-amiri.pdf)

### 17.2 Overpass가 실제로 증명·측정해야 할 차이

| 비교 축 | 현재 Overpass의 선택 | 필요한 증거 |
|---|---|---|
| 목적 | Fair receive order가 아니라 speculative work 보존과 state-finalization latency | 동일 pre-cut execution 대비 추가 순이득 |
| 보고 의미 | Exact block references의 intended order; 수신 순서 증거·실행 이력 아님 | 실제 report 생성 규칙, context 및 freshness |
| 선택의 역할 | 유효 후보의 LCP score는 heuristic이며 fairness certificate가 아님 | Proxy의 유효 조건·반례 및 score/repair 관계 |
| 진행 조건 | Report 수집 미완료·계산 미완료여도 cut fallback 진행 | 실제 cut-ready race와 resource interference 시험 |
| 실행과 finality | Mutable candidate에서 먼저 실행하고 final cut에 맞춰 검증·보정 | Exact-order adapter, 복구 및 최종 oracle 비교 |

우리 설계에 fairness 보장이 없다는 점은 단순한 성능 우위가 아니라 **제공하는 계약이 다르다는 점**이다. 상대가 제공하는 보장을 제거한 비용 차이만으로 더 좋은 consensus라고 결론내리면 안 된다. 같은 이유로 n=5f+1에서 4f+1=n−f라는 수치의 일치가 두 보고 집계의 의미까지 같게 만들지는 않는다.

### 17.3 예상 reviewer 질문과 정직한 답변 방향

**질문:** “Rashnu처럼 local ordering을 모으되 fairness를 빼고 prefix 점수를 넣은 것 아닌가?”

**답변 방향:** 공통된 구조는 인정한다. 추가로 주장할 대상은 parallel producer dissemination 환경에서 보고를 기다리지 않는 planning을 pre-cut execution과 결합했을 때, late-arrival repair와 finalization까지의 잔여 작업을 실제로 줄이는가이다. 이를 위해 proposal freeze, incomplete inputs, parent 변경, fallback을 함께 처리하는 end-to-end 경로를 구현하고 비용까지 측정해야 한다. 아직 이 결과가 없으므로 강한 차별성이 입증됐다고 답할 수는 없다.

현재 세 비교군 Original / Pre-cut execution / Overpass는 그대로 유지한다. Rashnu 구현을 새 주 비교군으로 자동 추가하지 않는다. 다만 Related Work에서는 local-order aggregation과 ordering/consensus 분리의 선행성을 정확히 인정하고, Discussion에서는 order-fairness를 제공하지 않는 한계를 명시해야 한다.

안전한 positioning 문장 후보:

> Overpass uses intended-order feedback to guide speculative execution before cut finality. Its planning is optional for cut progress: consensus consumes a prepared valid candidate or a fallback without waiting for report collection or optimization. The contribution must be established through safe exact-order integration and measured improvements over otherwise identical pre-cut execution, rather than local-order aggregation alone.

이 문장은 현재 설계 의도를 표현한다. No-wait integration·안전성·성능이 구현 또는 입증 완료됐다는 뜻은 아니다. Google Docs와 protocol source는 이 검토로 변경하지 않았다.

## 18. 실행 낭비 감소와 지속 부하에서의 순이득을 분리한다

현재 evaluation에는 backlog·goodput이 있지만, 성공 판정을 위한 시간·작업량 관계를 더 명확히 할 필요가 있다. **Execution을 cut 앞으로 옮기는 것과 처리해야 할 총 작업량을 줄이는 것은 다르다.** 낮은 부하에서는 idle capacity로 추가 작업을 흡수하며 latency를 줄일 수 있어도, 같은 설정이 높은 부하에서 안정적으로 동작한다는 보장은 없다.

### 18.1 비교할 작업 예산

하나의 병목 자원에서 같은 입력 cohort를 처리하는 비용을 다음처럼 나눈다.

```text
Pre-cut execution: useful execution + repair + validation/apply
Overpass:         useful execution + repair' + validation/apply'
                  + reporting/planning/extra coordination
```

계획이 재실행을 줄였다면 repair'가 작아질 수 있다. 하지만 같은 병목 자원에서 절약한 비용보다 추가 비용이 크면 처리 capacity는 오히려 낮아질 수 있다. 이는 latency가 모든 부하에서 반드시 나빠진다는 정리가 아니다. Pipeline overlap·idle capacity·다른 병목 때문에 개별 요청은 빨라질 수 있다. 반대로 여러 노드의 CPU 합만 비교하면 critical node의 병목을 숨길 수 있으므로 per-node 측정도 필요하다.

### 18.2 작은 service-budget 예시

아래 수치는 모두 인위적인 시간 단위다. 하나의 serial worker, cut 간격 100, 각 cut의 작업은 그 interval 시작에 도착하며 총 100개 cut을 처리한다고 가정한다. Execution 완료와 ordering 완료 중 늦은 때를 이 모델의 readiness로 정의한다. 실제 인증·network·durable apply를 모델링한 것이 아니다.

| 경로 | 유용 작업 | 재실행 | 추가 overhead | cut당 작업 | 100번째 cut의 잔여 지연 | 시각 10,000의 미완료 cut 수 |
|---|---:|---:|---:|---:|---:|---:|
| Pre-cut execution | 80 | 25 | 0 | 105 | 500 | 5 |
| Overpass, 높은 overhead 가정 | 80 | 10 | 20 | 110 | 1,000 | 10 |
| Overpass, 낮은 overhead 가정 | 80 | 10 | 5 | 95 | 0 | 0 |

두 Overpass 행 모두 재실행은 25→10으로 60% 줄었다. 그런데 높은 overhead 행은 서비스 수요가 interval의 capacity보다 더 커서 backlog가 더 빠르게 증가한다. 낮은 overhead 행은 이 단순 모델에서 매 cut 전에 실행을 끝낸다. 이 표는 실제 score가 그러한 repair 절약을 만든다는 증거나 두 overhead 값이 현실적이라는 주장이 아니다.

검산 recurrence:

```text
arrival(k) = 100 * (k - 1)
cut(k) = 100 * k
finish(k) = max(finish(k - 1), arrival(k)) + work_per_cut
ready(k) = max(cut(k), finish(k))
delta(k) = ready(k) - cut(k)
```

JavaScript로 100회 recurrence와 미완료 수를 계산·assert했다. 마지막 cohort의 ingress→ready는 각각 600, 1,100, 100이며 drain 완료 시각은 10,500, 11,000, 10,000이다. 이는 queue-budget sanity check일 뿐 현재 시스템의 성능 결과가 아니다. 실제 speculative repair는 arrival·plan·cut 시점에 따라 발생하므로 discrete-event 구현에서는 작업 release와 취소/재실행을 따로 모델링해야 한다.

### 18.3 실제 실험에서 고정할 최소 규칙

1. **같은 절대 offered load:** 세 비교군에 같은 ingress trace와 총 CPU/NIC budget을 사용한다. 각 시스템의 최대 처리량 대비 같은 비율의 부하만 비교하면 실제 처리량 감소를 가릴 수 있다. Normalized-load 그래프는 보조로 사용한다.
2. **같은 cohort 추적:** 최초 ingress한 요청을 식별해 완료·실패·timeout·미완료를 모두 남긴다. Retry는 최초 ingress clock을 유지하고, speculative 중복 실행을 별도 성공 transaction으로 세지 않는다.
3. **Backlog의 기울기:** 시간에 따른 accepted-but-not-state-ready 요청 수를 기록한다. 짧은 실행에서 완료된 요청의 p99만 낮고 미완료가 계속 증가하면 안정된 latency 개선으로 판정하지 않는다.
4. **Warm-up·측정·drain 구분:** 측정 구간에 들어온 cohort를 정해 drain에서의 완료도 추적한다. Drain까지 끝나지 않은 요청은 검열/미완료로 공개하며 latency 통계에서 조용히 제거하지 않는다. Bounded timeout이 실제로 terminal인지도 명시한다.
5. **Overload와 안정 구간 분리:** 지속 backlog 증가 구간을 정상 steady state처럼 평균내지 않는다. Ordering은 진행되지만 state만 밀리는 상태를 별도 recovery curve로 보고한다.
6. **성능 주장 분리:** 재실행 절약, post-cut 조정 시점의 앞당김, 추가 overhead, ordering latency, ingress→state의 변화를 각각 보여준다. Delta 감소 하나를 capacity 향상이나 E2E 향상으로 바꾸어 말하지 않는다.

새 scheduling 알고리즘이나 primary endpoint를 이 메모에서 결정하지 않는다. 이 검토의 결론은 “재실행 감소”를 중간 지표로 두고, 동일 부하에서 state backlog가 누적되지 않는지까지 확인해야 한다는 것이다. 해당 계측은 앞서 정한 세 비교군에 공통으로 적용한다.

## 19. 결과 인증, 조회 readiness, recovery checkpoint는 다른 계약이다

§6·§10에서 endpoint 선택을 미완료로 남겼다. 이번 소스 확인으로 기존 microbenchmark의 완료 조건을 새 논문의 endpoint로 그대로 가져올 수 없다는 점을 더 구체적으로 확인했다. 주 지표 선택은 사용자에게 질문했으며, 이 메모에서 임의 확정하지 않는다.

### 19.1 현재 코드가 실제로 확인하는 것

- `glue/src/multimmit.rs:240`의 `is_complete()`는 optional execution-certificate 슬롯의 수만 확인한다. Application state가 durable storage에 반영되었거나 query가 새 값을 반환하는지 확인하는 함수가 아니다.
- 같은 파일의 `Application::apply`는 별도 async hook이다. `glue/benches/multimmit_state_finality.rs`의 두 측정 경로는 이 hook을 호출하지 않고 `is_complete()`에서 끝난다.
- `Tracker::new`는 `N5f1::n_minus_two_f`를 사용한다. n=6/f=1의 기존 benchmark는 네 signer ID를 넣는다. 현재 논의의 선택적 f+1 결과 인증을 구현한 benchmark가 아니다.
- Vote 인증·실행 검증은 module 계약상 caller 책임이며 benchmark는 실제 signature/network를 수행하지 않는다. 이 reducer 반환을 원격 observer가 확인한 실행 인증 완료와 같다고 볼 수도 없다.

이는 과거 PoC의 목적을 넘어선 해석을 막는 audit이지, 함수 자체가 잘못됐다는 bug 판정이 아니다. 기존 코드·threshold·storage 정책은 수정하지 않았다.

### 19.2 논문에서 구분할 세 완료 사건

| 사건 | 확인할 사실 | 그 사건만으로 말할 수 없는 것 |
|---|---|---|
| 실행 결과 인증 | Full ordering finality와 정확한 cut/order·canonical parent·runtime에 묶인 결과 서명을 observer가 검증 | 특정 serving node가 state bytes를 보유하거나 조회를 제공함 |
| 지정 node의 state readiness | 해당 node가 최종 state를 검증·반영하고 정한 durable/query 조건을 충족 | 모든 node가 동일 시각에 준비됨 |
| Recovery checkpoint / GC 가능 | 필요한 fault·retention·recovery 계약을 만족해 이전 자료를 안전하게 정리할 수 있음 | 단순 result certificate나 현재 query 성공만으로 자동 성립 |

예를 들어 ordering이 t=100에 확정되고 결과 인증을 t=105에 검증했지만, 지정 node의 state 반영·조회 준비가 t=230이면 두 지연은 각각 5와 130이다. 이는 정의를 설명하는 가상 event timeline이며 실제 측정값이 아니다. 어느 숫자도 다른 숫자를 대신하지 않는다. 서명된 root만 받고 application data를 가져와 검증하는 비용을 측정 밖으로 빼서 사용자 체감 개선이라고 주장하지 않는다.

### 19.3 PBFT를 인용할 때의 정확한 경계

PBFT §4.1은 같은 요청·결과에 대한 서로 다른 replica의 유효한 f+1 replies로 client가 결과를 수용하도록 한다. 반면 §4.3은 n=3f+1 모델의 stable checkpoint에 2f+1 matching checkpoint messages를 사용하고 이를 log GC 및 recovery와 연결한다. [PBFT §4.1–4.3](https://www.usenix.org/legacy/events/osdi99/full_papers/castro/castro_html/node4.html)

따라서 f+1 client-reply 근거를 가져와 모든 state 보관·복구 조건도 충족된다고 확대하면 안 된다. 위 2f+1 checkpoint 수를 현재 n=5f+1 profile에 기계적으로 이식하자는 뜻도 아니다. 원문의 서로 다른 인증이 서로 다른 일을 한다는 점이 참고 사항이다.

Overpass에서 f+1 결과 인증을 택할 경우의 제한된 산술 근거는, 최대 f faulty identities라면 그 집합에 정직한 signer가 하나 이상 있다는 것이다. 이 근거에는 다음 계약이 선행한다: 올바른 epoch membership·signature 검증, 완전히 확정된 정확한 입력 순서, 동일하고 올바른 canonical parent 및 deterministic runtime, 정직한 signer의 직접 실행 또는 정당한 결과 검증. 추측한 plan에 서명했더라도 최종 대상과 정확히 일치하는지 검증하기 전에는 canonical 결과로 수용하지 않는다. 이 인증은 ordering consensus 단계를 대체하지 않는다.

이 산술은 실행 결과의 유효성에 대한 조건부 근거일 뿐, signer의 durable state 보관이나 언제든 data를 받을 수 있다는 retention SLA를 만들지 않는다. Input DA·state transfer·checkpoint retention을 별도로 기술해야 한다. 자료 부족으로 replay가 필요할 수 있는 상황과, 잘못된 결과를 수용하는 safety 문제도 구분한다.

### 19.4 다음 결정을 위한 권고

기존 사용자 의도를 따르는 후보는 **ordering finality + f+1 결과 인증**을 primary endpoint로 명확히 정의하고, 지정 node의 durable/read readiness를 보조 지표로 같이 측정하는 것이다. 하지만 이것은 아직 질문에 대한 답변을 기다리는 권고이며 채택 결정이 아니다.

어느 쪽을 고르든 세 비교군에서 같은 관찰자·동일 subject·동일 완료 의미를 사용하고, ordering finality, certificate verification, apply completion, query readiness를 별도 event로 기록한다. 원본 protocol에 새 certificate 대기를 추가한 baseline을 원본의 native latency라고 이름 붙이지 않는다. 전체 노드의 readiness를 기다리는 새 전역 barrier를 만들 필요도 없다.

## 20. 도착 trace에서 생성한 reports로 이득이 생기는 최소 사례

반례만으로 heuristic을 평가할 수는 없다. §11의 서로 다른 known sets에서 reports가 나오는 경우를 실행·재검증 event까지 연결했다. 이 사례는 현재 방향에 개선 기회가 있음을 보여주는 **조건부 실행 모델**이다. Native Multimmit integration, 인증·네트워크 E2E, workload 대표성 또는 보편적인 개선 증거가 아니다.

### 20.1 조건과 입력

고정 parent x=y=z=0에서 서로 다른 producer의 세 blocks를 사용한다. 각 block에는 transaction 하나가 있고, 아래 비용은 인위적인 serial worker 시간 단위다.

```text
X: x := x + 1       cost 1
A: y := read(x)     cost 3
B: z := read(y)     cost 3
Base priority: X < A < B
```

X<A는 변경 가능한 cross-lane priority이며 필수 ancestry가 아니라고 가정한다. 모든 후보가 필수 포함·선행 조건을 만족해야 한다. 보고는 known blocks를 base priority로 정렬해 만들고, 같은 parent에서 시작하는 전체 tentative order를 담는다. 보고에 execution progress는 없다.

| Node | Block 도착 시각 | t=2의 report |
|---|---|---|
| V1–V4 | A,B는 0; X는 10 | A→B |
| V5, leader | X,A,B 모두 0 | X→A→B |
| V6 | X는 0; A,B는 12 | 이 window에 미수신 |

V1–V5의 reports가 leader에게 t=7까지 도착한다고 놓는다. n=6/f=1의 다섯 보고 목표를 충족하며 deadline은 그보다 뒤다. Leader는 처음부터 X를 알고 있다. 모르는 block을 추측해 제안하거나 누락을 증명하는 모델이 아니다. 도착 시각은 network/DA 합의 전체를 시뮬레이션한 것이 아니라 실행 경로 진단용으로 통제한 입력이다.

Window context가 report 생성 전인 t=2까지 해당 nodes에 알려졌다고 가정했으며, 이를 알리는 메시지·초기화 비용은 별도로 모델링하지 않았다. 따라서 이 trace가 report 수집 시작부터의 실제 network latency를 보여준다고 해석하면 안 된다. §21에서 이 전제의 구현상 빈틈을 다룬다.

이 사례의 candidate completion은 report prefix를 보존하고 나머지 유효 blocks를 suffix에 추가한다. 따라서 후보는 A→B→X와 X→A→B이며 점수는 각각 8과 3이다. §11에서 남겨 둔 completion 정책 중 하나를 이 진단에 사용한 것이지, 연구 source of truth에 이를 새로 확정한 것은 아니다.

Plan은 t=8에 전달되고 proposal은 t=10에 동결되며 ordering은 t=15에 확정된다고 통제한다. 두 실행 비교군 모두 동일한 cut membership {X,A,B}와 finality 시각을 갖는다. Overpass는 A→B→X를, Pre-cut execution은 X→A→B를 최종 인증한다고 가정한다. Update 제한이 점수 5의 개선을 수용한다는 조건도 둔다. Cut을 report 수집 때문에 늦추지 않는다.

### 20.2 실행과 cache 재검증 결과

노드마다 하나의 worker가 block을 실행한다. Target order의 parent overlay에서 이전 read values가 여전히 같으면 effects를 재사용하고, 다르면 해당 block만 다시 실행한다. 검증·effects 재적용 비용은 이 작은 모델에서 0으로 두었으며 실제 benchmark에서는 포함해야 한다.

- V1–V4는 A를 0–3, B를 3–6에 실행한다. Pre-cut 경로는 X가 도착하면 X를 10–11, A/B를 11–17에 실행한다. Overpass는 A/B를 보존하고 X만 10–11에 실행한다.
- V5는 X/A/B를 0–7에 실행한다. Pre-cut 경로에서는 그대로 유효하다. Overpass의 plan을 받고 A/B를 8–14에 보정한다. X의 read x=0은 A/B가 x를 쓰지 않으므로 재사용 가능하다.
- V6는 X를 0–1에 실행하고 A/B가 도착한 12부터 18까지 실행한다. 어느 경로든 이 node는 18에 준비된다.

| 항목 | Pre-cut execution | Overpass |
|---|---|---|
| 각 node의 최종 문맥 실행 준비 시각 | 17,17,17,17,7,18 | 11,11,11,11,14,18 |
| 전체 application 실행 작업량 | 66 | 48 |
| Ordering과 두 결과가 모두 준비되는 시각 | 17 | 15 |
| Ordering과 여섯 결과가 모두 준비되는 시각 | 18 | 18 |

동일한 입력의 useful work는 전체 여섯 node에서 42이다. Pre-cut의 재실행은 24, Overpass의 재실행은 6이다. 이는 application 작업량만의 비교이며 report/optimizer/signature/송수신/storage 비용은 포함하지 않는다. 두 결과 준비 gate는 f+1 endpoint를 채택했을 때 필요한 계산상의 조건일 뿐, certificate 수집·검증 완료 시각은 아니다. 모든 node의 준비를 목표로 하면 이 사례에서는 개선이 없다.

Pre-cut 최종 state는 (x,y,z)=(1,1,1), Overpass는 (1,0,0)이다. 각자의 인증된 serial order로 처음부터 실행한 oracle과 일치한다. 다른 합법적 order의 application 결과가 달라진 것이며, 동일 결과를 만드는 최적화라고 표현하지 않는다. 이 사례에는 실패/abort 거래가 없어서 싼 실패 경로로 latency를 낮춘 것은 아니다.

### 20.3 검증 범위와 다음 활용

JavaScript로 시간순 block 도착·실행 완료·plan 적용을 처리하고 cached read/write effects를 재검증했다. Reports는 t=2의 known sets에서 생성했으며 위 scores, node별 준비 시각, 작업량 및 serial oracle 일치를 확인했다. Consensus messages, cut 선택, 실제 CPU/네트워크, 인증과 durable apply는 시뮬레이션하지 않았다. 따라서 native protocol에서의 도달 가능성까지 입증한 것은 아니다.

다음 단계에서 이 trace를 실제 세 비교군의 regression fixture로 옮기면, 임의 report 순열을 직접 주입하는 대신 **arrival→report→plan→repair→final-context validation** 경로를 시험할 수 있다. 특히 exact-order adapter가 A→B→X를 인증할 수 없다면 이 개선 경로는 구현되지 않은 것이다. Base order X→A→B를 그대로 확정하고 pre-cut에서만 A→B→X를 실행하도록 만드는 것은 이 사례와 다른 실험이다.

이 사례는 heuristic의 가능성을 보여주되 추가 비용보다 절약이 큰지, 정상 network에서 이런 도착 패턴이 얼마나 자주 생기는지는 남겨 둔다. 성공 사례와 §13·§15의 실패 조건을 함께 검증해야 하며, 이 작은 수치를 논문의 실측 성능 결과로 인용하지 않는다.

## 21. Report window를 누가 언제 알려 주는가

현재 source of truth를 검색·확인한 결과, reports는 epoch/view/cut/parent/rule/window에 묶이고 leader의 첫 eligible block 관측에서 window timer가 시작된다. 그러나 remote validators가 그 window ID와 생성 규칙을 언제 배우는지에 대한 메시지/초기화 절차는 찾지 못했다. 이는 기존 구현의 bug 판정이 아니라 wire protocol 및 첫 plan latency의 미정 사항이다. 근거: `overpass-prefix-plan.md` §2·§4.1, outline §3.1·§3.3.

### 21.1 두 가지 구현 경로는 비용과 의미가 다르다

| 경로 | 필요한 규칙 | 비용·주의점 |
|---|---|---|
| Leader가 window를 열며 ID/context를 안내 | Current leader 인증, monotonic window ID, report 응답·중복·마감 처리 | Fresh announcement를 받은 뒤 응답하므로 outbound+return 경로가 collection 시간에 들어감 |
| Window ID/생성 규칙을 사전에 공유하거나 기존 메시지에 piggyback | Validators가 같은 ID를 도출하는 규칙, 후속 window 전환, missed update와 stale report 처리 | 매 window의 별도 안내 RTT를 줄일 수 있지만 미리 공유한 사실과 freshness를 증명·계측해야 함 |

모든 설계에 추가 RTT가 반드시 필요하다는 주장은 아니다. 반대로 현재처럼 window binding만 선언했다고 그 RTT가 없어지는 것도 아니다. Local wall-clock으로 각자 window counter를 증가시키는 방법은 서로 같은 window를 뜻하는지 별도 설명이 필요하다. Unix time 합의나 새 승인 quorum을 넣자는 제안은 아니다.

Window에 묶이지 않은 연속 push reports를 leader가 임의 window에 배정하는 대안은 현재 signed-window 계약과 다르다. 이를 택하면 identity별 latest revision, replay, freshness, snapshot 동결을 다시 정해야 한다. 이번 검토에서 자동 채택하지 않는다.

### 21.2 Collection과 유효한 plan 전달 시간

Fresh announcement 경로에서 validator i의 report 도착은 안내 전송, snapshot 생성, 응답 전송, leader 측 검증의 영향을 받는다. Leader 자신의 report와 remote reports의 경로도 다르다. Threshold 시각은 이 도착 시각들의 필요한 순서통계량이고, deadline은 계속 leader의 고정 t0+τ다. 응답 노드의 timer나 매번 들어오는 report에 맞춰 연장하지 않는다.

```text
leader window 시작
  → validator가 context/ID 수신
  → intended-order snapshot·report 송신
  → leader 수신·검증
  → threshold 또는 deadline → 후보 계산
  → 아직 proposal이 동결되지 않았으면 후보 사용
  → validator에 plan/proposal 도착 → 실행 보정
```

서로 다른 두 시간 조건을 측정한다:

- Leader가 후보를 해당 cut에 사용할 조건: 검증된 후보가 proposal freeze보다 먼저 준비됨.
- Validator가 보정을 cut 전에 숨길 기회: 실제 plan 수신부터 ordering finality까지의 시간과 가용 execution capacity. Plan이 proposal freeze 뒤에 도착했더라도 이미 선택된 동일 순서라면 이 기회가 남을 수 있다.

같은 시각의 freeze/optimizer 완료/threshold event는 구현의 serialization 규칙으로 한 번만 처리해야 한다. 이미 보낸 proposal을 뒤늦은 계산으로 바꾸지 않는다.

### 21.3 짧은 수집 창도 무조건 좋은 것은 아니다

인위적 report 도착 시각을 [0,21,23,25,27,201], threshold를 5, 계산 시간을 2, proposal freeze를 27로 두었다. Leader 자신의 report는 0에 준비된다. 아래는 이 시간표의 산술이며 분산 측정이 아니다.

| τ | Trigger 시각 | 확보 reports | 계산 완료 시각 | Freeze 전에 후보 사용 가능 |
|---|---:|---:|---:|---|
| 40 | 27, threshold | 5 | 명목상 29 | 아니오; cut은 fallback으로 진행 |
| 24 | 24, deadline | 3 | 26 | 예 |
| 10 | 10, deadline | 1 | 12 | 예; 다른 validator의 관측은 없음 |

첫 행에서 cut preemption으로 계산을 시작하지 않거나 취소할 수 있다. 29는 대기를 강제할 경우의 실제 protocol event가 아니라, 해당 snapshot 계산이 끝나더라도 늦는다는 진단값이다. 세 경우의 산술과 strict ready-before-freeze 판정을 JavaScript로 확인했다.

τ=24의 후보가 선택되고 plan 전달에 10이 걸리며 finality가 45라면 node는 36에 plan을 받아 9의 보정 시간을 갖는다. 이 9가 충분한지는 application cost에 달려 있다. τ=10은 더 빨리 준비되지만 분산된 intended-order feedback이 없는 선택이므로, 이를 높은 coverage의 조율 성과로 분류하면 안 된다.

### 21.4 구현·평가에 필요한 최소 추가 항목

1. Window ID를 사전에 알 수 있는지, 안내 메시지가 있는지 먼저 확정한다. First window와 steady-state windows를 분리해 계측한다.
2. Window 시작→remote context 수신→snapshot→report 검증 완료→candidate ready→plan 수신을 모두 추적한다. §20 같은 모델의 보고 전달 시각을 비용 없이 주어진 사실로 E2E benchmark에 옮기지 않는다.
3. Leader가 보내는 window 안내 역시 byte/message/CPU budget에 포함한다. 추가 plan 승인 round가 없다는 표현을 제어 메시지 비용이 없다는 표현으로 확대하지 않는다.
4. Lost announcement, stale ID, view/parent 전환, 종료 window의 delayed report를 시험한다. 모두 report 성능 경로의 문제로 격리하고, cut은 기존 fallback/recovery 조건으로 진행해야 한다.

이 항목은 새로운 연구 기능을 늘리는 것이 아니라 이미 선언한 report context와 fixed deadline을 구현하는 데 필요한 빈칸이다. Threshold·τ 값이나 window 안내 정책을 이번 검토에서 바꾸지 않았다.

## 22. Ordering parent와 execution parent를 혼동하면 planning까지 막힐 수 있다

현재 문서는 report의 `기준 finalized cut·canonical parent`와 결과 검증의 `canonical parent`를 사용하지만, 각각 ordering 식별자인지 실행 입력 state root인지 wire-level 의미를 확정하지 않는다. Report에는 execution progress/state root가 없다고도 명시한다. 실행 backlog가 생긴 경우를 위해 이 구분을 명시해야 한다. 근거: `overpass-prefix-plan.md` §2·§7, outline §3.1·§3.4.

### 22.1 서로 대체할 수 없는 세 값

| 값 | 역할 | 알 수 있다는 사실이 보장하지 않는 것 |
|---|---|---|
| Producer-chain parent block identity | Lane ancestry와 block identity 검증 | Global application의 입력 state가 준비됨 |
| Ordering context의 기준 cut/order identity | 같은 확정 이력 뒤의 intended order를 비교 | 그 이력의 실행 결과 root·state bytes가 이미 있음 |
| Execution input state root와 대응 state | 해당 실행의 실제 입력을 고정하고 재사용/결과를 검증 | 다른 cut·순서·runtime에서 같은 결과를 쓸 수 있음 |

현재 코드도 이름만 보고 같은 값을 넣으면 안 된다. `TransactionBlockHeader.parent`는 producer header의 부모 식별자다. `LeaderBlock.parent`는 `CertificateId`이고, 과거 glue의 `ExecutionStatement.parent_state`는 input state root다. `ExecutionContext.parent()` 역시 producer header parent로 문서화되어 있다. 이는 새 Overpass report 형식의 구현 증거가 아니라, 서로 다른 기존 값을 혼동하지 않기 위한 소스 근거다.

근거: [producer header](commonware/consensus/src/multimmit/types/block.rs:119), [leader block](commonware/consensus/src/multimmit/types/block.rs:563), [execution context](commonware/glue/src/multimmit.rs:65), [execution statement](commonware/glue/src/multimmit.rs:78). 이 코드들은 수정하지 않았다.

### 22.2 이전 실행이 늦는 timeline

가상 시각으로 cut 1 ordering은 10에 확정되고, 그 결과 state는 30에 준비된다고 하자. Cut 2 proposal freeze는 20, ordering finality는 25다. Report 수집·계산이 context 준비 뒤 5만큼 걸린다고 통제한다.

- Report에 cut 1의 결과 root가 필수이고 그 root가 30까지 없다면 후보는 35에야 준비된다. Cut 2에 사용하기에는 늦으므로 fallback이 된다.
- Report가 이미 확정된 cut 1의 ordering identity에 묶일 수 있다면 후보를 15에 준비할 여지가 있다. Execution result나 progress를 보고할 필요는 없다.
- 하지만 cut 2 작업이 cut 1의 아직 계산되지 않은 값에 의존하면 planning이 빨라도 실행은 여전히 그 값을 기다리거나 추측해야 한다. 입력 state를 기다린 뒤 실행 비용이 6이면 완료 시각은 36이다. Planning의 no-wait와 data dependency의 제거는 다른 주장이다.

위는 인위적인 시간의 조건부 예시이며 실제 network·execution 성능이 아니다. 여러 cut을 한꺼번에 speculatively 실행한 올바른 local branch가 이미 있으면 경로가 달라질 수 있다. 여기서 이전 cut의 결과 인증을 반드시 먼저 받아야 다음 cut을 speculative 실행할 수 있다는 새 barrier를 추가하는 것도 아니다.

### 22.3 검토 권고 — context는 분리하고 결과는 정확히 검증

현재 intended-order-only 방향에는 report context를 확정된 ordering 이력의 식별자에 묶고, speculative 실행의 입력 state와 canonical 채택 시의 state 검증을 별도로 정의하는 방식이 자연스럽다. 이는 권고이며 source of truth에 새 message 형식으로 채택하지 않았다. Exact-order adapter가 어떤 ordering 식별자를 제공할 수 있는지도 함께 결정해야 한다.

필요한 조건:

1. 같은 report snapshot의 원점은 같은 확정 ordering 이력이어야 한다. Local execution이 느리다고 각 node가 서로 다른 materialized cut을 원점으로 삼은 reports를 섞지 않는다.
2. 보고 대상의 blocks가 기준 cut 이후 어디에 위치하는지 알려면 ordering 기록이 필요하다. State가 없다는 이유로 이전 확정 blocks를 다시 새 입력처럼 포함하면 안 된다.
3. Runtime이 사용하는 speculative input state는 local cache에서 별도로 식별한다. 나중에 final input·순서·parent가 다르면 의존성 검증과 필요한 재실행을 한다.
4. Execution certificate를 수용할 때는 올바른 canonical input state와 연결됨을 확인한다. 기준 cut ID만 같다고 다른 root에서 실행한 결과를 수용하지 않는다. Producer header parent를 global state parent로 대신 쓰지도 않는다.
5. Ordering이 여러 cut 앞선 경우 reports·cache·미완료 실행의 보관량을 제한한다. 추측 작업을 줄이거나 폐기하는 정책과 canonical execution backlog를 버리는 행동은 구분한다.

예를 들어 cut 1이 x를 0에서 1로 바꾸는데 cut 2의 `y := read(x)`를 오래된 x=0에서 미리 실행하면 y=0이다. 같은 cut 2 ID에 연결했다는 사실만으로 이 결과가 맞아지지 않으며, canonical parent x=1에 대한 read 검증은 실패해야 한다. 작은 값 검산에서도 cached y=0과 올바른 y=1이 달라 재사용 불가였다. 이는 일반 runtime의 검증 구현을 시험한 것은 아니다.

### 22.4 가장 필요한 regression 조건

한 node의 application execution만 늦추어 ordering이 앞서도록 만든다. 다른 context의 reports가 섞이지 않는지, 가능한 경우 planning이 execution root 대기 없이 진행하는지, 오래된 local state에서 만든 결과가 final validation에서 보정되는지 확인한다. 마지막으로 원인을 제거했을 때 accepted backlog를 유실 없이 따라잡는지 본다.

이 테스트의 목적은 모든 dependency를 non-blocking으로 없애는 것이 아니다. **Planning·ordering의 독립 진행과 application state 의존 대기를 분리해서 설명하고 검증하는 것**이다. State sharding이나 새 전역 state-frontier 합의는 도입하지 않는다.

## 23. Native Multimmit의 sweep 변경 여지와 plan 고정 경계

사용자가 Native Multimmit의 tip 추출·extension 유지를 선택한 뒤 원문 §4.2·§6과 checkout의 경계를 대조했다. 직전 turn은 기반 선택을 기록한 진전이었다. 아래 연결 방식은 검토 권고이며 채택된 wire protocol·구현·증명이 아니다.

### 23.1 원문 근거와 novelty 경계

[Multimmit v2 §4.2 및 §6](https://arxiv.org/html/2607.21021v2#S6)은 horizontal ordering 대신 공통 입력에서 결정론적으로 도출하는 다른 sweep을 허용한다. §4.2는 settled chain의 빈 위치는 건너뛰고 unsettled chain의 빈 위치에서는 emission을 멈추는 규칙을 둔다. §6은 sweep 변경의 예로 reputation 기반 순서를 논의한다.

따라서 “Native 유지이면 순서를 전혀 조정할 수 없다”는 우려는 너무 강하다. 반대로 **ordering rule을 바꿀 수 있다는 사실 자체는 Overpass의 novelty가 아니다.** 차별화 후보는 intended-order feedback으로 실행 보존에 유리한 sweep을 미리 선택하고, bounded optional planning의 비용까지 포함해 state-finalization latency를 줄이는 것이다. Reputation/blame을 새로 도입하지는 않는다.

### 23.2 결정론성뿐 아니라 확장 간 일관성이 필요하다

현재 tips에 대해 매번 deterministic하게 새 순서를 계산해도, 다른 tips에서 다른 순서가 나오면 이미 전달한 prefix를 뒤집을 수 있다. 초기 tips A1/B1, 두 chain unsettled인 추상 예시를 보자.

```text
초기 sweep: B1 → A1 → B2 → A2 → ...
초기 emission: B1 → A1       (B2 빈 위치에서 중단)

이후 A tip이 A2로 확장됨
잘못된 재선택: A1 → B1 → A2  (기존 emission과 불일치)

동일 sweep 유지:
  B가 settled이면 B2를 건너뛰고 A2까지 진행
  B가 아직 unsettled이면 B2 위치에서 계속 대기
```

이는 추상 completion 반례이지 Rust 구현의 버그나 실제 vote transcript의 도달 가능성 증명이 아니다.

### 23.3 권고: 인증된 proposal에 고정한 position sweep

알려진 block ID 목록만으로는 아직 모르는 extension의 위치가 정의되지 않는다. 검토할 방향은 **proposal 문맥에 고정한 position sweep + 미명시 위치에 대한 공통 continuation rule**이다.

1. Proposal 전에는 plan을 갱신할 수 있다. Proposal에 사용할 선택은 고정하고 내용 또는 재구성 가능한 입력을 인증 경로에 연결한다. 현재 `LeaderBlock`에는 이 필드가 없으므로 실제 연결은 구현·증명 과제다.
2. Sweep은 기준 tip 이후 상대 위치들을 정렬한다. Chain-local 선행 위치를 보존하고 block이 아직 없는 위치도 slot으로 표현한다.
3. 같은 leader block의 pool이 커져도 sweep은 바꾸지 않는다. Native tips·settledness에 따라 전달 가능한 prefix만 늘린다. 후속 view에서도 과거 인증된 ordering 문맥을 복구해야 한다.
4. Extension은 자기 slot에 들어간다. Plan 밖이라고 제외하거나 local 도착 순서로 삽입하지 않는다. Native 중단·skip·중복 제거와 기존 전달 prefix를 보존한다.
5. 준비된 plan이 없으면 기본 sweep을 선택한다. 누락된 plan 데이터를 가져와야만 proposal을 검증할 수 있게 하면 새 critical-path 대기를 만들 수 있다. Metadata 크기·가용성·복구·검증 비용도 설계해야 한다.

모든 permutation이 안전하다는 결론이 아니다. Coverage, ancestry, 유한 encoding, 공정한 continuation, V-QC/L-QC 간 prefix 관계와 recovery를 만족하는 허용 sweep 집합부터 정의해야 한다. 원문의 sweep 변경 허용을 임의 plan codec의 안전성 증명으로 대신할 수 없다.

### 23.4 유한 검산

In-memory 진단에서 A/B 각 3개 위치의 chain-local 순서를 보존하는 20개 interleaving을 열거했다. 각 tips 0..3, settled flags, settled chain은 더 늘지 않는 completions를 조합하여 **3,920개 조건**에서 고정 sweep emission이 completion 순서의 prefix인지 확인했고 모두 통과했다. Sweep을 바꾼 위 반례에서는 prefix 관계가 깨졌다.

검산 규칙은 `포함 위치 append / settled 빈 위치 skip / unsettled 빈 위치 stop`이다. QC extraction·branch equivocation·view change·network·execution은 포함하지 않았다. BFT 안전성이나 성능 검증으로 보고하지 않는다. Commonware 코드는 변경하지 않았다.

### 23.5 논문과 평가에서 추가로 확인할 것

- **실제 순서 조정 범위:** Intended order 중 native 제약 아래 canonical하게 보존할 수 있는 부분을 구분한다. 자유로운 permutation의 toy 이득을 제한된 sweep 구현의 결과로 쓰지 않는다. Candidate completion 후 실제 적용 순서로 score를 평가한다.
- **재실행 절약 대 emission 대기:** 높은 LCP score의 sweep이 unsettled slot을 앞에 두면 canonical delivery가 늦어질 수 있다. 세 비교군에서 leader finality→ordered delivery→execution validation을 분해한다. 단일 ordering-latency 숫자로 이 손해를 숨기지 않는다.

가장 가까운 검증 과제는 새 quorum이나 fixed-cut 전환이 아니라 **동일한 인증 sweep 아래 서로 다른 vote pool과 후속 view가 compatible prefix를 만드는지** 확인하는 것이다. Primary completion endpoint와 실제 분산 실험은 여전히 미완료다.

### 23.6 유한 검산을 넘어서는 조건부 prefix 보조정리

다음은 §23.3의 권고를 평가하기 위한 수학적 분해다. 새로운 합의 정리나 원문에 없는 안전성 보장의 채택이 아니다. §23.4의 유한 경우 수가 늘어나서 얻는 결론도 아니며, 아래 가정에서 직접 증명하는 성질이다.

고정된 하나의 ordering segment에 대해 다음을 둔다.

- 모든 노드가 동일한 기준 tip vector T와 이미 확정된 과거 순서 H를 사용한다.
- Slot은 `(chain, T 이후 상대 높이)`다. Sweep σ는 각 slot을 정확히 한 번 열거하고 각 chain 내 높이 순서를 보존한다. 각 slot은 유한한 순위에 도달하며, σ는 local pool/도착 순서에 따라 바뀌지 않는다.
- 노드 p는 각 chain에서 F_p까지의 block들을 안전하게 포함할 수 있다는 근거와 settled flags S_p를 가진다.
- 비교할 모든 노드에 공통으로 양립하는 completion G가 있다. 모든 chain에서 F_p ≤ G이며 S_p가 settled이면 해당 chain의 G는 F_p와 같다. 이미 포함하는 slot의 exact block identity도 G의 경로와 같아야 한다. 높이만 같고 hash가 다르면 이 가정을 만족하지 않는다.

`Ordσ(G)`는 σ를 훑으며 G의 tip 이내 slot에 해당하는 block만 남긴 순서다. `Emitσ(F_p,S_p)`는 같은 σ를 훑어 포함 가능한 block을 append하고, settled chain의 빈 slot은 skip하며, 첫 unsettled 빈 slot에서 멈춘다. 모든 chain이 settled이면 유한한 포함 구간을 다 출력하고 끝낼 수 있다.

**보조정리:** 위 가정 아래 `Emitσ(F_p,S_p)`는 `Ordσ(G)`의 prefix다.

증명: Emit이 멈추기 전 방문한 slot을 차례로 본다. (1) F_p 이내 slot이면 G에도 동일 block이 있으므로 양쪽 순서에 동일하게 append된다. (2) Settled chain의 빈 slot이면 G에서도 비어 있으므로 양쪽에서 skip된다. 두 경우 외에는 즉시 멈추므로, Emit이 어떤 G의 선행 block을 빠뜨린 채 그 뒤 block을 출력할 수 없다. 따라서 출력은 prefix다. ∎

**서로 다른 pool에 대한 따름정리:** p와 q가 같은 H·σ 및 공통 completion G에 양립하면 두 emission은 같은 `H || Ordσ(G)`의 prefix이므로 서로 prefix-compatible하다. 두 노드가 동일 vote pool, 동일 finalized tip 길이, 동일 block bodies 또는 동일 실행 진척을 가진다는 가정은 필요 없다. 단, emission identity를 도출하는 데 필요한 인증 자료는 검증되어야 하며 application 실행에는 body/state가 별도로 필요하다.

**과거 prefix 보존:** 후속 view가 위 segment의 올바른 인증 순서를 H의 일부로 상속하고 그 뒤에만 새 segment를 붙인다면 view에 대한 귀납으로 기존 출력은 보존된다. 이 상속 조건 자체는 보조정리가 증명하지 않는다. 이미 확정된 순서를 매번 새 plan으로 재정렬하면 조건을 위반한다.

### 23.7 이 보조정리가 해결하지 않는 실제 통합 의무

| 필요한 가정 | 실제 구현·증명에서 채워야 하는 것 |
|---|---|
| 공통 H와 T | 정확한 anchor certificate·tip history에 대한 재구성, 다른 parent/view의 혼합 배제 |
| 공통 σ | Plan/policy의 인증 subject·encoding·version·recovery; mutable advisory plan을 canonical하게 오인하지 않음 |
| 공통 completion G와 동일 block identities | 서로 다른 L-QC/V-QC·growing pools·equivocating branches에 대한 native 추출 성질과 adapter의 연결 |
| Settled이면 completion에서 더 늘지 않음 | 원래 settledness predicate 유지 및 모든 관련 certificate와의 관계 검증 |
| 후속 view의 H 상속 | Reference-chain 재구성, exact anchor 선택, 이전 emission과 future Ord의 관계 보존 |
| Complete하고 유한 순위인 σ | 잘못된/중복/누락 slot, ancestry 위반과 starvation을 막는 candidate validity·continuation 규칙 |

특히 `공통 completion G가 있다`를 주장하고 그것으로 다시 native safety를 증명하는 순환 논증을 피해야 한다. 기존 quorum/branch 논증에서 이 성질을 독립적으로 확보한 뒤 ordering 보조정리를 적용해야 한다. 코드의 sparse finality event만으로 dense delivery까지 검증됐다고 할 수도 없다. 현재 `docs/PROPERTIES.md`는 recursive Ord/Emit·body retrieval·durable cursor를 외부 marshal의 책임으로 명시한다.

이 결과는 **동일 local view를 증명해야만 실행 pipeline이 가능한 것은 아니다**라는 점을 명확히 한다. 필요한 것은 각자의 speculation이 같다는 보장이 아니라, canonical하게 채택할 순서들의 compatibility와 그 순서에 대한 최종 실행 검증이다. LCP 점수와 보고 4f+1은 이 보조정리의 안전성 가정에 등장하지 않는다. 이들은 성능 후보를 선택하는 정책이다.

진행성·성능은 별도다. 각 slot의 순위가 유한하다는 것만으로 unsettled slot이 빨리 해소되거나 metadata가 제때 복구된다는 보장은 없다. Native의 inclusion·view progression 보장을 adapter가 보존하는지, emission 대기가 실제로 줄어드는지는 여전히 증명·측정해야 한다.

### 23.8 Plan을 leader block에 결속할 때 쓸 수 있는 교집합 논증

현재 checkout에서 `view_quorum()`은 n−f, `designation_quorum()`은 2f+1이다. V-QC는 n−f..n개의 서로 다른 identity에 귀속된 메시지를 포함하지만, 그중 지정 leader block에 투표한 집합은 최소 2f+1이다. 모든 V-QC 참여자가 그 proposal을 지지한다고 해석하지 않는다. `VoteBody::for_leader`는 round와 leader block digest를 subject에 넣고, leader digest는 canonical encoding 전체의 hash다.

소스: [config.rs](commonware/consensus/src/multimmit/config.rs:112), [V-QC 구조 검사](commonware/consensus/src/multimmit/types/certificate.rs:420), [vote subject](commonware/consensus/src/multimmit/types/vote.rs:120), [leader digest](commonware/consensus/src/multimmit/types/block.rs:645). 정직한 노드의 같은 view 중복 투표 금지와 durable reservation은 [Direct vote 및 Invariants](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md)에 명시되어 있다. 이 turn에서는 소스만 확인했으며 Rust 테스트를 실행하지 않았다.

**L-QC가 존재하는 같은 epoch/view에서:** L에 대한 L-QC의 투표자 집합을 A, 다른 V-QC의 지정 proposal L′ 투표자를 B라 하자. n=5f+1이면

```text
|A| ≥ 4f+1, |B| ≥ 2f+1
|A ∩ B| ≥ (4f+1) + (2f+1) − (5f+1) = f+1.
```

최대 f명 Byzantine이므로 교집합에는 정직한 서명자가 있다. 정직한 노드는 같은 view에서 다른 leader block에 중복 투표하지 않으므로, 유효 서명과 collision-resistant digest를 가정하면 L′=L이어야 한다. 이는 이미 존재하는 native threshold의 교집합 설명이지 새 quorum이나 새 voting round가 아니다.

**Plan에 적용하려면:** 서로 다른 plan/policy가 다른 leader digest를 만들도록 canonical encoding에 결속되어야 한다. 그러면 위의 same-leader 결론에서 same-bound-policy를 얻을 수 있다. 인증된 digest 밖의 별도 mutable plan을 수신한 경우에는 이 결론이 적용되지 않는다. 현재 `LeaderBlock::write`는 epoch/view/parent/history/proposals만 기록하므로 plan 결속은 아직 구현되어 있지 않다. 또한 같은 policy여도 tip extraction 결과나 body 보유량이 같다는 결론은 나오지 않는다.

**L-QC 이전에는 이 논증을 사용할 수 없다.** n=6, f=1, Byzantine identity 6이 있는 구조적 예시:

```text
P 지지: {1,2,6}; P의 V-QC: P 지지 3명 + Q 지지 {3,4}
Q 지지: {3,4,6}; Q의 V-QC: Q 지지 3명 + P 지지 {1,2}
```

각 transcript는 5명을 계수하고 지정 proposal에 3명이 투표한다. 두 지정 투표자 집합의 교집합은 Byzantine 6뿐이다. 해당 서명·제안이 각각 유효하다는 전제에서 threshold 구조만으로 이 두 V-QC를 배제할 수 없다. 이는 완전한 runtime 실행 trace의 재현은 아니며 protocol 결함을 뜻하지 않는다. V-QC가 L-QC finality와 다른 증거라는 설명이다.

따라서 proposal 또는 V-QC에 plan이 결속되었다는 이유만으로 speculative 결과를 canonical하게 적용하면 안 된다. 충분한 finality와 native ordered-delivery 조건까지 필요하다. Leader가 바뀌면 정확한 anchor와 그 이력에 결속된 policy를 복구해야 한다. 동일 leader block이어도 여러 V-QC의 vote transcript와 추출 tips가 다를 수 있다는 문제는 §23.6의 prefix 조건 및 native 추출 논증으로 별도로 다룬다.

논문 Correctness에서는 (a) 같은 view의 leader/policy binding, (b) 다른 tip 관측 간 compatible emission, (c) view 간 과거 prefix 상속, (d) exact-order 실행 검증을 분리해 서술하는 것이 적절하다. 이 네 단계를 하나의 “quorum이 있으므로 안전” 주장으로 합치지 않는다.

### 23.9 Prepared plan의 기준점과 실제 proposal parent

Policy binding과 f+1 endpoint 채택 후 proposal 작성 코드를 확인했다. `view.rs::select_anchor`는 보유한 가장 높은 earlier view에서 transcript 크기와 canonical tie-break로 exact parent를 선택한다. Proposal pass는 그 parent를 보관하고 `finish_proposal_request`가 parent ID·tip-history commitment를 block에 넣는다. Leader view나 마지막 finalized cut이 같아도 준비 중이던 plan과 실제 proposal의 원점은 다를 수 있다.

근거: [anchor 선택](commonware/consensus/src/multimmit/machine/view.rs:2734), [proposal pass](commonware/consensus/src/multimmit/machine/view.rs:1293), [exact publication request](commonware/consensus/src/multimmit/machine/durability.rs:448). 이번에는 코드를 변경하거나 Rust 테스트를 실행하지 않았다.

| 기준 | 용도 | 혼동 위험 |
|---|---|---|
| Report의 기준 ordering 이력 | Intended order의 비교 원점 | 실제 proposal이 상속하는 이력과 다른 순서를 점수화 |
| Parent V-QC의 tip vector | Native sweep의 상대 위치 원점 | 동일 slot bytes를 다른 block으로 해석 |
| Chain proposal의 DA anchor | Producer path 제안·검증 | 아직 ordering에 포함해야 할 ancestors 누락 |
| Canonical execution input state | 실행 결과 검증 | 같은 순서라도 잘못된 state에서 실행한 결과 채택 |

예를 들어 Q0의 tips `(A10,B8)`에서 policy `B+1 → A+1`은 `B9 → A11`이다. Actual proposal이 Q1의 tips `(A11,B8)`을 선택하면 같은 slot bytes는 `B9 → A12`가 된다. Epoch/view/window와 서명만 검사하면 점수화한 후보와 실제 적용 후보가 달라질 수 있다. 이는 좌표 변환의 가상 예시이며 실제 native event trace를 재현한 것은 아니다.

또한 parent tip이 A10, chain proposal의 DA anchor가 A12, 제안 suffix가 A13부터라면 native ordering 구간의 A11·A12도 고려해야 한다. 새로 제안한 payload entries만 전체 실행 입력으로 삼으면 안 된다. 이미 전달된 입력의 제거는 인증된 전체 ordering 이력과 native 중복 제거 규칙을 따른다. DA anchor는 global state나 ordered-delivery 완료 증거가 아니다.

**Prepared candidate 사용에 필요한 조건:**

1. Candidate가 완성된 exact ordering 이력·parent·tip origin·rule을 식별한다. 보수적인 첫 검증은 actual parent certificate ID 일치를 요구할 수 있다. 다른 certificate를 동등하게 허용하려면 policy 해석·상속 순서의 동등성을 별도로 정의해야 한다.
2. Native proposal pass가 실제로 고정한 parent와 비교한다. 현재 최신으로 보이는 parent를 이미 진행 중인 pass의 parent로 대신 쓰지 않는다.
3. 불일치 candidate는 해당 proposal에 사용하지 않는다. Actual parent용 유효 candidate가 이미 있으면 사용하고, 없으면 그 parent의 기본 policy로 진행한다. 재계산이나 새 report round를 기다리지 않는다.
4. Background 재구성 시 필수 ancestors·상속 이력을 반영하고 같은 기준·horizon에서 incumbent와 다시 점수화한다. Report의 앞부분을 삭제한 뒤 높은 점수가 나와도 실제 cache 재사용을 증명하지 않는다.
5. Proposal 인증 이후에는 parent·policy를 바꾸지 않는다. Recovery도 최신 parent에서 policy를 다시 계산하는 것이 아니라 인증된 exact 문맥을 복구한다.

이는 native anchor 선택을 늦추거나 옛 anchor를 강제로 유지하자는 제안이 아니다. Report 서식이나 rebasing 최적화의 채택도 아니다. 기존 no-wait·stale-result 배제 조건이 실제 코드의 어느 parent에 적용돼야 하는지를 구체화한 검토다.

검증 사례는 같은 view의 더 큰 transcript V-QC, 더 높은 view의 parent, 계산 중 anchor 변경, 동일 tips지만 다른 certificate 이력, 높은 DA anchor 아래 ancestors, signing 이후 restart다. 계측에는 anchor mismatch fallback 비율과 candidate age를 포함한다. Plan 대부분이 mismatch로 폐기되면 score가 좋아도 실제 latency 기여는 작을 수 있다.

## 24. Extension continuation을 정의하는 작은 policy 후보

이번 검토는 새 consensus나 점수 함수를 추가하지 않는다. 채택된 policy binding을 실제로 표현할 수 있는 한 가지 후보를 제시한다. **아래 prefix-plus-continuation encoding은 아직 정식 채택·구현한 규격이 아니다.** Report는 기존 exact block references를 유지하며, 이것은 proposal에 고정할 ordering policy의 후보 표현이다.

### 24.1 유한 plan 뒤에 기본 slot 순서를 연결

Exact parent Q의 tip vector T를 기준으로 한다. 각 lane의 상대 위치를 `A1,A2,...`로 표기한다. 실제 height는 `T[A].height + offset`이고 block identity는 native가 인증한 경로에서 결정한다.

기본 sweep B는 이 검토 예시에서는 `A1,B1,C1,A2,B2,C2,...`다. 선택한 유한 prefix D는 길이 W 이하이며 같은 lane의 위치는 1부터 빠짐없이 순서대로 포함해야 한다. 예를 들어 `B1,A1,B2`는 유효하지만 `B2,A1`은 B1을 생략하므로 허용하지 않는다.

전체 policy는 다음처럼 정의한다.

```text
σ = D || (기본 sweep B에서 D에 들어간 slot만 제거한 순서)

D: B1 → A1 → B2
B: A1 → B1 → C1 → A2 → B2 → C2 → A3 → B3 → C3 → ...

σ: B1 → A1 → B2 → C1 → A2 → C2 → A3 → B3 → C3 → ...
```

Continuation을 lane별 남은 높이에서 새로 round-robin하는 것은 위 정의와 다르다. 예를 들어 그 다른 방식은 A2 다음에 B3를 C1보다 먼저 둘 수 있다. 구현은 위의 원래 B에서 D를 제거하는 단일 정의를 따라야 하며, 두 해석을 섞지 않는다.

D는 lane ID 목록 `[B,A,B]`로도 표현할 수 있다. 각 lane의 k번째 출현은 그 lane의 상대 위치 k다. 단, exact parent·rule version·기본 lane 순서를 함께 인증해야 한다. 실제 report block IDs를 이 표현으로 바꿀 때는 해당 parent 이후의 branch와 ancestor closure가 일치하는지 먼저 검증한다. 누락된 predecessor를 단순히 잊은 채 renumber하지 않는다.

### 24.2 이 후보가 제공하는 성질

- **중복·누락 없음:** D는 서로 다른 slot이고 tail은 B에서 정확히 D만 제거하므로 모든 slot이 한 번씩 나온다.
- **Lane ancestry:** D의 각 lane 부분은 초기 prefix다. Tail에도 같은 lane의 나머지 위치가 기본 순서대로 남으므로 lane 내 역전이 없다.
- **Extension 위치가 미리 정의됨:** 아직 알려지지 않은 block도 native 경로에서 slot을 얻으면 이미 정의된 σ의 위치를 사용한다. 새 vote·block 도착으로 σ를 다시 정렬하지 않는다.
- **순위 지연의 유한 bound:** B에서 slot x의 순위를 r, D 길이를 w≤W라 하자. x가 D 밖이면 새 순위는 `w + r − |D ∩ B[1..r]| ≤ r+W`다. D 안이면 새 순위는 w 이하이므로 역시 r+W 이하이다. 따라서 어떤 slot도 이 재배치만으로 무한히 뒤로 밀리지 않는다.

마지막 bound는 **slot 순위**에 대한 것이다. Unsettled 빈 slot에서 기다리는 wall-clock 시간, transaction latency, adversarial fairness 또는 execution cost를 제한하지 않는다. 재실행 최소화도 증명하지 않는다. 이전 §23.6의 조건부 emission 보조정리는 같은 σ와 올바른 native 추출 가정이 별도로 충족될 때 적용할 수 있다.

### 24.3 Native emission과의 연결

Slot을 순서에 넣는 것이 해당 block의 존재·membership·실행 성공을 인증하는 것은 아니다. 각 slot에서 native가 포함을 허용하면 append, settled 빈 위치이면 skip, unsettled 빈 위치이면 stop하는 경계를 유지해야 한다. 미지의 extension을 tail에 정의했다고 즉시 실행·확정할 수 있는 것은 아니다.

예컨대 B1이 아직 포함 가능하지 않고 B가 unsettled이면 위 σ는 첫 slot에서 멈춘다. 다른 lane에 실행 가능한 입력이 있어도 높은 LCP 점수만으로 이 대기를 무시할 수 없다. Native consensus 자체는 계속 진행할 수 있지만 ordered delivery와 state finalization은 지연될 수 있다. 따라서 이 후보는 completeness/continuation 문제를 단순화할 뿐 LCP와 latency의 불일치를 해결하지 않는다.

Fallback은 빈 D로 정의할 수 있으므로 기본 sweep과 같아진다. Parent가 바뀐 candidate의 자동 재사용, policy fetch를 consensus 선행조건으로 만드는 것, 새 support round는 필요 조건이 아니다. 이 encoding을 채택한다면 크기 상한·정상화·서명 영역·recovery를 별도로 명세해야 한다.

### 24.4 작은 검산과 다음 판단 기준

3개 lane, W=5에서 길이 0..5의 모든 lane-ID 목록 **364개**를 열거했다. Lane별 높이 8까지의 24개 slot에 대해 중복·누락 없음, lane 순서 보존, 위 순위 지연 bound를 검사했고 **8,736개 slot 검사**가 통과했다. In-memory 유한 모델이며 native QC, branch equivocation, network, execution 또는 benchmark 결과가 아니다. 일반 성질의 근거는 §24.2의 구성과 식이며 이 유한 검사 자체가 증명을 대신하지 않는다.

이 후보를 평가할 때는 보고 순서를 실제로 D로 변환 가능한 비율, ancestor 보충으로 달라진 score, parent mismatch fallback, 앞선 unsettled slot으로 인한 emission 대기를 측정해야 한다. 알려진 block 집합에서 σ를 필터링한 실제 후보에 대해 score를 다시 계산하며, 불가능한 원래 순열의 점수를 그대로 사용하지 않는다. 계산·validity 확인은 bounded하게 하고 준비되지 않으면 기존 no-wait fallback을 유지한다.

장점은 미지의 extension과 유한 plan 사이의 연결을 작은 결정론적 규칙으로 설명할 수 있다는 점이다. 한계는 D를 길게 하면 더 많은 순서를 조정할 수 있지만 metadata·검증 비용·앞선 빈 slot의 영향도 커질 수 있다는 점이다. 이 규칙 자체의 최초성을 주장하지 않으며 연구 기여는 여전히 feedback 기반 선택이 실제 latency에 주는 순효과다.

## 25. f+1 실행 서명의 안전성과 수집 진행성은 다르다

사용자가 f+1 exact-context 실행 서명을 primary endpoint로 채택했으므로, 정상 서명이 실제로 같은 statement에 모이는 조건을 검토했다. 현재 prefix-plan §7.2는 서명 input 범위·parent·runtime·결과의 일치를 요구하지만, 어떤 공통 실행 범위에서 서명을 생성할지는 아직 정하지 않는다. Native vote pool이 커지며 tip/전달 prefix가 증가할 수 있다는 사실과 결합하면 이 빈칸은 liveness·측정 정의에 직접 영향을 준다.

### 25.1 모두 정확하게 실행해도 서로 다른 범위만 서명할 수 있다

n=6, f=1에서 5개 정상 노드가 같은 canonical stream을 실행한다고 하자. Byzantine 1개는 침묵한다. 노드 i가 논리 round r마다 자기 최신 prefix `1..(5r+i)`에만 서명하고 중간 결과에는 서명하지 않는 가상 정책을 둔다.

```text
round 0: V1=1..1, V2=1..2, V3=1..3, V4=1..4, V5=1..5
round 1: V1=1..6, V2=1..7, V3=1..8, V4=1..9, V5=1..10
...
```

모두 deterministic하게 올바른 결과를 계산해도 각 end position은 한 identity만 서명한다. 20 rounds의 작은 집계에서는 유효하다고 가정한 서명 100개, statement 100개, f+1=2를 만족하는 certificate 0개였다. 이는 새 서명 정책의 구조적 반례이며 native message/event trace를 재현한 시험이나 현재 코드의 버그 판정은 아니다. 특정 시점의 일시적 지연뿐 아니라 latest-prefix-only 정책을 계속 유지하면 반복될 수 있음을 보인다.

긴 prefix의 root·서명은 짧은 prefix의 root·서명이 아니다. 서로 다른 범위의 올바른 서명을 모아 f+1이라고 세는 해결책은 허용하지 않는다. 동일 output root가 우연히 나와도 input/order 문맥이 다르면 같은 statement로 합치지 않는다.

### 25.2 인증할 결과와 인증 근거의 identity도 구분해야 한다

같은 exact ordered input을 증명하는 L-QC가 여러 vote transcript로 표현될 수 있다. `Lqc::id`는 encoded certificate의 hash이고, 현재 native 코드는 growing pool과 서로 다른 정확한 transcript를 다룬다. 따라서 단지 QC bytes/ID가 다르다는 이유로 동일 실행 문맥의 서명을 분산시키지 않도록 설계해야 한다. 반대로 certificate가 같은 leader block을 가리킨다는 사실만으로 다른 extracted prefix의 서명을 합쳐서는 안 된다.

근거: [L-QC identity](commonware/consensus/src/multimmit/types/certificate.rs:327), [native finality](commonware/consensus/src/multimmit/docs/STATE_MACHINE.md). Policy가 해석되는 exact proposal parent는 §23.9처럼 계속 보존해야 한다. 여기서 구분하는 것은 그 parent binding을 삭제하는 것이 아니라, **같은 canonical execution statement와 그것을 뒷받침하는 여러 증거 표현**이다. Semantic identity의 정확한 encoding은 미정이다.

### 25.3 수집이 진행되기 위한 최소 설계 조건

1. **공통 실행 단위:** Local pool snapshot이나 scheduler의 임의 batch 경계가 아니라 공통 canonical 순서에서 결정되는 입력 범위로 statement를 식별한다. 가능한 단위는 canonical block 경계 또는 결정론적 실행 구간이다. 어떤 단위를 채택할지는 아직 미정이다.
2. **놓친 서명 경계 처리:** 한 번에 여러 입력을 따라잡아도 필요한 공통 경계의 검증 결과를 서명·제공할 수 있어야 한다. 이를 위해 중간 결과 보관 또는 재실행 정책이 필요하다. Root를 역산해서 대신 만들지는 않는다.
3. **다른 인증자의 완료를 실행 barrier로 만들지 않음:** 다음 speculative 작업을 시작하려고 앞 구간의 f+1 서명 수집을 반드시 기다리게 하지는 않는다. 단, canonical state-finalization 수용 시 parent 연결과 finality 검증은 유지한다.
4. **수집자 장애 처리:** 서명을 단일 collector만 보유하게 하면 collector 장애가 state finality를 막을 수 있다. 재요청·다른 수집자·서명 보관의 경로와 message/CPU budget을 정의해야 한다. f+1이라는 숫자만으로 이 경로가 생기지 않는다.
5. **저부하 종료:** K개 block마다만 서명한다면 마지막 K 미만의 입력이 영원히 남지 않도록 종료/부분 구간 정책을 정의해야 한다. 각 node의 local timer만으로 서로 다른 signing 범위를 만들면 같은 문제가 재발한다.

이 조건은 새 ordering quorum이나 state-frontier 합의를 추가하라는 뜻이 아니다. 이미 채택한 실행 결과 인증이 같은 입력을 가리키며 실제로 수집 가능하도록 하는 조건이다. 실제 서명 batching·aggregation·요청 경로는 별도 설계 대상으로 남긴다.

### 25.4 기존 artifact를 증거로 쓸 수 없는 이유와 평가 항목

기존 `glue/src/multimmit.rs::ExecutionStatement`는 한 producer block과 input/output state·receipt를 다룬다. 새 global ordered-range·runtime 인증의 구현이 아니므로 그 reducer의 certificate 집계만으로 위 문제를 해결했다고 볼 수 없다. 이번에는 코드를 변경하거나 테스트를 실행하지 않았다.

세 비교군에 동일 signing granularity·수집·재시도 정책을 적용하고, execution 완료→statement 준비→f+1 검증 완료를 분리해 측정해야 한다. 필수 사례는 서로 다른 크기의 ordered-delivery batches, 빠른 노드와 catch-up 노드, 동일 order의 서로 다른 QC 증거, collector 실패, Byzantine 서명 거부, 저부하 마지막 구간이다. 같은 범위에 정상 서명 f+1개가 결국 제공된다는 조건 없이 ordering liveness에서 state-finalization liveness를 바로 도출하지 않는다.

### 25.5 실행뿐 아니라 결과 서명의 준비 시점도 latency를 결정한다

Primary endpoint가 f+1 실행 서명 검증을 포함하므로 사전 실행이 끝났다고 post-ordering 잔여 시간이 자동으로 사라지지 않는다. 실행 결과가 준비돼 있어도 서명 생성·전파·수집·검증을 ordering 이후 시작하는 구현에서는 이 비용이 남을 수 있다. 다만 노드별 ordering 관측 시각이 다르므로 모든 실행에 보편적인 1 RTT 하한이 생긴다고 주장하지 않는다.

검토할 최적화는 **정확한 speculative 입력의 실행 statement를 미리 서명·전파하되, canonical 채택은 ordering finality와 문맥 일치 검증까지 보류하는 것**이다. 이는 아직 채택한 서명 스케줄이 아니다. Intended-order reports에 실행 이력이나 proof를 추가하거나 leader score에 실행 진행률을 넣는 모델도 아니다. 보고/선택 경로와 실행 결과 인증 경로는 구분한다.

수용 시 필요한 구분:

| 관측된 상황 | 처리 조건 |
|---|---|
| 같은 후보 입력에 f+1 실행 서명이 있으나 ordering은 미확정 | 결과를 준비 상태로 보관할 수 있으나 canonical하게 채택하지 않음 |
| Ordering 확정, 서명 statement의 exact input·범위·parent·runtime·결과가 모두 일치 | 기존 서명을 활용할 여지가 있음; finality·membership·서명 검증은 유지 |
| 동일 plan 이름이지만 최종 extension이나 순서가 달라짐 | 다른 statement이므로 서명을 합치거나 root를 잘라 재사용하지 않음 |
| Input 순서는 같지만 canonical parent나 실행 환경이 다름 | 재검증·필요한 재실행 후 올바른 statement를 서명 |

서명 subject를 아직 존재하지 않는 최종 L-QC의 raw bytes/hash로만 정의하면 그 증거가 생기기 전에 서명할 수 없다. 반면 정확한 예상 ordered input/range와 실행 문맥을 식별하는 statement를 서명하고, 나중에 확정 evidence와 연결하는 방식은 검토 가능하다. §25.2의 semantic execution subject와 증거 표현 구분이 필요하다. 같은 input hash만으로 충분하다는 뜻이 아니다. Epoch/domain, parent state, runtime 및 결과에 영향을 주는 실행 환경도 고정해야 한다.

정직한 signer는 미래 consensus 결과를 예언하는 것이 아니라 주어진 exact 문맥을 실제로 실행한 결과에 서명한다. 서로 다른 후보 입력의 statement는 서로 다르므로 둘에 서명했다고 consensus equivocation이 되는 것은 아니다. 반대로 동일한 deterministic 실행 문맥에 서로 다른 결과를 서명하는 것은 허용하지 않는다. 실행 statement를 consensus vote로 혼동하거나 state 채택 조건을 완화하지 않는다.

### 25.6 조건부 시간 예시와 공정한 ablation

동일 관측 node에서 ordering evidence가 10, canonical parent 검증이 8에 준비되고 마지막 연결 검사에 1이 걸린다고 하자. 가상 시간이며 실제 성능 수치가 아니다.

| 경로 | 최종 문맥과 일치하는 f+1 서명 준비 | State 수용 | order→state |
|---|---:|---:|---:|
| Ordering 뒤 서명 준비 | 14 | 15 | 5 |
| 미리 준비한 서명이 최종 문맥과 일치 | 9 | 11 | 1 |
| 미리 서명했지만 입력이 달라 보정 필요 | 16 | 17 | 7 |

이 표는 `max(ordering 준비, 올바른 parent 준비, matching 서명 준비) + 마지막 검사`라는 통제된 사건 모델의 산술이다. 실제 CPU 경합·signature verification·fetch·재시도 비용을 제외했으며 항상 개선된다는 결과가 아니다. 틀린 후보 서명에 쓴 비용도 실제 평가에 포함해야 한다.

서명 전파를 overlap하는 최적화를 검토한다면 **Pre-cut execution에도 동일하게 허용**해야 한다. Overpass만 서명을 미리 보내고 baseline은 cut 이후에 보내게 하면 intended-order planning의 추가 기여와 서명 pipeline 효과가 섞인다. Original은 입력 순서 확정 후 실행하는 정의 때문에 실행 서명도 결과 준비 전에는 만들 수 없지만, codec·수집 경로·verifier·완료 의미는 공유한다.

서명 준비 시점은 공통 backend 옵션으로 분리해 on/off ablation을 할 수 있다. 지표에는 최종 입력과 일치한 선행 서명 비율, 무효 후보 서명 bytes/CPU, quorum 수집 지연, aggregation/retry 비용을 포함한다. Byzantine leader의 잦은 plan 갱신으로 서명량이 폭증하지 않도록 생성·전파·보관 예산도 필요하다. Native cut은 결과 서명 준비를 기다리지 않아야 한다.

이 검토는 state finalization의 f+1 기준을 바꾸지 않는다. 완성할 대상은 **ordering과 실행만이 아니라 endpoint에 실제 필요한 작업 중 무엇을 미리 준비할 수 있고, 무엇은 최종 문맥 확인까지 남는가**라는 시간 흐름이다.
