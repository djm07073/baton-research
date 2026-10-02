# Multimmit Execution Extension 논문 개요 연구

> **현재 집필 기준:** 이 문서의 10편 논문 구조 분석은 참고 자료로 유지한다. EPC/ZK/proof 중심의
> 이전 권장 목차는 역사적 초안이며, 실제 논문 개요와 용어는
> [`paper-outline.md`](./paper-outline.md) 및
> [`proof-aware-multimmit-paper.md`](./proof-aware-multimmit-paper.md)를 우선한다.

> 상태: outline and positioning draft  
> 기준일: 2026-08-23  
> Authoritative protocol model: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)  
> 목적: Autobahn/Multimmit의 계보를 설명하고, 상위권 논문 10편의 실제 내용 배치를 비교하여 본 논문의 목차와 주장 배치를 결정한다.

## Current cross-lane positioning update (2026-09-14)

Active cross-lane design은 아래의 historical EPC/CLCC나 asynchronous receipt가 아니라 **finalized-cut-selected conflict-scoped branch proofs**다. Cross-lane fragments를 participant overlays에 즉시 실행하고 동일 prefix에서 `Commit`/`Abort` results를 증명한 뒤, finalized cut의 emitted ordered prefix와 proof-authenticated local prepared bits가 모든 lanes의 branch를 동일하게 선택한다. Static conflict closure 밖의 state updates는 common delta proof로 한 번만 증명하고 selected branch와 disjoint join한다.

직접 비교할 선행연구는 다음과 같다.

| Work | 가져오는 관점 | 본 연구와의 핵심 차이 |
|---|---|---|
| [Proof-of-Execution](https://arxiv.org/abs/1911.00838) | consensus 전 speculative execution | quorum response proof와 rollback이며 ZK branch/cross-lane selector가 아님 |
| [X-Shard](https://doi.org/10.1109/TPDS.2024.3361180) | optimistic parallel cross-shard sub-transactions | threshold commit 및 conflict withdrawal; cut-selected dual proof paths가 없음 |
| [Prophet](https://arxiv.org/abs/2304.08595) | pre-execution과 read/write 기반 conflict handling | ordering 전에 conflict-free global order를 만들며 bounded branches를 유지하지 않음 |
| [Block-STM](https://arxiv.org/abs/2203.06871) | conflict-directed validation/re-execution | preset single-block order의 incarnations이며 cross-lane atomic proof selection이 없음 |
| [Pilotfish](https://arxiv.org/abs/2401.16292) | global commit order 기반 distributed state execution | worker scheduling/recovery가 중심이며 pre-final commit/abort proofs가 없음 |
| [RollShard](https://doi.org/10.1109/TC.2026.3673996) | proof-verified multi-shard state deltas | one stateless off-chain result를 증명하며 two outcomes를 later cut이 고르지 않음 |
| [SuperNova](https://eprint.iacr.org/2022/1758) | heterogeneous steps를 위한 non-uniform IVC | cryptographic building block일 뿐 branch merge나 cross-lane protocol을 제공하지 않음 |

Preliminary search에서 위 조합과 정확히 같은 design은 확인하지 못했다. 그러나 “first” claim은 systematic literature review 뒤에만 사용한다. 특히 standard linear folding은 fork 뒤 global root가 달라져 non-conflicting suffix proof도 중복하므로, conflict-scoped novelty는 componentized state-delta commitment와 disjoint join proof가 실제로 구현·평가될 때만 성립한다.

## 0. 먼저 내리는 결론

본 논문은 **새 합의 프로토콜 전체**를 제안하는 논문으로 쓰기보다, Multimmit의 ordering finality와
application state finality 사이에 빠져 있는 실행 계층을 정의하는 **execution-finality systems paper**로
쓰는 편이 가장 정확하다.

권장 서술 순서는 다음과 같다.

```text
문제와 측정 가능한 execution gap
  → Autobahn/Multimmit에서 상속하는 것
  → 시스템 모델과 application contract
  → 전체 protocol timeline
  → lane-local proof-certified execution
  → cross-lane completeness와 atomic cut
  → Multimmit cut 통합
  → safety/liveness 분석
  → Commonware 구현
  → contribution별 실험과 ablation
  → 한계와 선행연구
```

핵심 작성 원칙은 네 가지다.

1. `State-Isolated Lane`, `Execution Proof Certificate`, `Cross-Lane Completeness Certificate`를
   서로 독립된 세 프로토콜처럼 쓰지 않는다. 하나의 실행 확정 경로를 이루는 세 구성 요소다.
2. “비동기 proof”나 “state isolation” 자체를 최초라고 주장하지 않는다. 새 주장은 이 증거들을
   Multimmit의 proposal-relative cut에 결합하는 규칙, post-cut full re-execution 제거, 그리고
   proof-independent N-lane completeness를 함께 정의한 데 둔다.
3. CLCC는 실행 정당성을 증명하지 않는다. 전체 fragment bundle의 joint availability와
   completeness를 증명하고, 실행 정당성은 participant lane의 일반 block proof/EPC가 담당한다.
4. 실험은 논문의 세 contribution과 일대일로 대응해야 한다. mock proof만으로는 프로토콜
   배관 검증은 가능하지만 상위권 venue의 성능 주장을 뒷받침할 수 없다.

---

## 1. 연구 방법과 코퍼스

### 1.1 “탑 저널”의 해석

분산 시스템과 시스템 보안은 저널보다 SOSP, EuroSys, NSDI, CCS, IEEE S&P, NDSS 같은
동료심사 학회가 대표 출판 venue인 분야다. 따라서 이 문서에서 “상위권 논문”은 다음을 포함한다.

- 최상위 시스템/분산시스템 학회
- 최상위 보안 학회 중 BFT·블록체인 시스템 논문
- PVLDB 및 IEEE Transactions on Computers와 같은 저널급 venue

Multimmit은 아직 본 논문이 직접 확장할 최신 기반 원고이므로 별도로 분석하며, 10편의
동료심사 구조 비교 숫자에는 넣지 않는다.

### 1.2 비교 기준

각 논문에 대해 다음을 비교했다.

- 실제 main-section 순서
- background, model, overview, protocol, proof, implementation, evaluation의 위치
- introduction에서 문제·insight·contribution을 전개하는 방식
- 우리가 채택하거나 피해야 할 내용 배치

소절과 appendix는 필요한 경우에만 참고하고, 아래 표의 순서는 PDF의 main heading을 정규화한 것이다.

---

## 2. 상위권 논문 10편의 개요와 내용 배치

### 2.1 한눈에 보는 비교

| # | 논문 / venue | 실제 본문 순서의 요약 | 배치상 특징 | 우리 논문에 적용할 점 |
|---:|---|---|---|---|
| 1 | [Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf), SOSP 2024 | Introduction → Partial Synchrony → Overview → Model → Protocol → Evaluation → Related Work → Conclusion | 먼저 기존 partial-synchrony의 실전 문제를 독립 절로 세운 뒤 설계를 제시한다. | Multimmit 설명 전에 “ordering은 빨라졌지만 state finality는 무엇을 기다리는가”를 timeline과 측정으로 보여준다. |
| 2 | [Narwhal and Tusk](https://sonnino.com/papers/narwhal-and-tusk.pdf), EuroSys 2022 | Introduction → Overview → Narwhal Core → Practical System → Tusk → Implementation → Evaluation → Related Work & Limitations → Conclusion | dissemination과 consensus를 분해하고 각 층의 효용을 별도로 평가한다. | Multimmit의 ordering layer와 우리가 추가하는 execution-finality layer의 책임을 명시적으로 분리한다. |
| 3 | [HotStuff](https://malkhi.com/files/HotStuff-PODC2019.pdf), PODC 2019 | Introduction → Related Work → Model → Basic HotStuff → Chained HotStuff → Implementation | 작은 기본 프로토콜을 먼저 증명하고, 실제 chained 형태로 확장한다. correctness는 protocol 절 안에 밀착 배치한다. | 먼저 local-only 경로를 정의한 뒤 N-lane 경로와 cut 통합으로 확장하는 서술 방식은 유용하다. 다만 systems paper이므로 평가를 뒤로 미루지 않는다. |
| 4 | [Bullshark](https://sonnino.com/papers/bullshark.pdf), CCS 2022 | Introduction → Preliminaries → DAG Construction → Protocol → Partial-Synchrony Variant → Garbage Collection → Proofs → Implementation → Evaluation → Related Work → Discussion | data structure, protocol, proof를 분리하고 구현·평가 전에 correctness를 완료한다. | certificate와 cut extraction algorithm을 먼저 닫은 후 Commonware 구현을 설명한다. 운영상 backlog/GC도 discussion에 남기지 말고 설계 절에서 다룬다. |
| 5 | [Mysticeti](https://arxiv.org/pdf/2310.14821), NDSS 2025 | Introduction → Overview → Mysticeti-C → Fast Path → Security → Implementation → Evaluation → Production → Related Work → Conclusion | 두 경로를 overview에서 먼저 통합하고, 보안 분석 뒤 구현·평가·production evidence를 둔다. | local path와 cross-lane path를 하나의 lifecycle로 먼저 보여주고 각각 상세화한다. 가능하면 Commonware testnet의 장기 운용 결과를 별도 소절로 둔다. |
| 6 | [Sui Lutris](https://docs.sui.io/paper/sui-lutris.pdf), CCS 2024 | Introduction → Overview → System → Long-Term Stability → Implementation → Evaluation → Related & Future Work → Conclusion | threat model, system model, properties, protocol overview를 모두 Overview 안에서 먼저 고정한다. object/ownership 모델과 fast/shared 경로를 연결한다. | lane ownership과 application cross-state predicate를 프로토콜 상세 전에 정의한다. hot shared state와 reconfiguration을 한계로 숨기지 않는다. |
| 7 | [OmniLedger](https://eprint.iacr.org/2017/406.pdf), IEEE S&P 2018 | Introduction → Background → System Overview → Security Design → Performance Refinements → Security Analysis → Implementation → Evaluation → Related Work → Limitations/Future Work → Conclusion | security core와 성능 refinement를 분리해 “최적화가 안전성을 바꾸지 않음”을 보인다. | 최소 안전 프로토콜과 asynchronous proof pipeline 최적화를 구분한다. proof batching/folding이 추가되면 optimization으로 분리한다. |
| 8 | [Chainspace](https://arxiv.org/pdf/1708.03778), NDSS 2018 | Introduction → System Overview → Application Interface → System Design → Security/Correctness → Applications → Implementation/Evaluation → Limitations → Related Work → Conclusion | application contract를 시스템 내부 프로토콜보다 먼저 정의하고 cross-shard commit을 설명한다. | `validate_cross_bundle`, ownership, read/write/version 규칙을 application interface로 독립시킨다. CLCC와 application validity를 섞지 않는다. |
| 9 | [RapidChain](https://eprint.iacr.org/2018/460.pdf), CCS 2018 | Introduction → Background/Related Work → Model & Problem → Protocol → Evaluation → Security/Performance Analysis → Conclusion | 큰 문제를 여러 설계 부품으로 쪼개고 표로 기존 시스템과 비교한다. formal analysis가 평가 뒤에 온다. | 비교표와 end-to-end scalability 평가는 채택하되, 우리 correctness 분석은 평가보다 앞에 두는 편이 낫다. |
| 10 | [Arete](https://www.vldb.org/pvldb/vol18/p2198-zhang.pdf), PVLDB 2025 | Introduction → Preliminaries → Scalable-Sharding Insight → Protocol → COE Architecture → Analysis → Evaluation → Related Work → Conclusion | 먼저 size-security dilemma와 정량 insight를 세운 뒤 protocol과 execution architecture를 분리한다. | “Multimmit ordering capacity가 execution에서 사라지는 조건”을 정량화하고, protocol rule과 execution architecture를 구분한다. |

### 2.2 논문별 더 구체적인 관찰

#### 1) Autobahn: 문제 현상을 먼저 이름 붙인다

Autobahn은 곧바로 protocol pseudocode로 들어가지 않는다. partial synchrony가 실제 시스템에서
남기는 `hangover`를 정의하고, 기존 leader BFT와 DAG 접근이 각각 왜 만족스럽지 않은지를
정리한 뒤 lanes와 cuts를 소개한다.

우리 논문도 다음 현상을 먼저 이름 붙여야 한다.

> **execution-finality gap**: transaction membership/order가 결정된 시점과, application state가
> 재실행 또는 증거 검증을 거쳐 확정되는 시점 사이의 간격.

이 용어를 쓰려면 baseline Multimmit에서 실제로 발생하는 wait/re-execution 경로를 구현하거나
명확한 reference execution model로 정의해야 한다.

#### 2) Narwhal/Tusk: 층을 분해한 뒤 end-to-end로 다시 합친다

Narwhal은 data dissemination을 mempool로 분리하고, 그 위에서 consensus가 digest를 다루게 한다.
그 후 Narwhal 단독 성능과 consensus 결합 성능을 모두 평가한다. 이는 우리에게 다음 평가 원칙을 준다.

- proof generation의 microbenchmark만 제시하지 않는다.
- certificate formation의 microbenchmark만 제시하지 않는다.
- transaction 수신부터 cut-based state finality까지 end-to-end latency를 반드시 측정한다.

#### 3) HotStuff: 기본형과 실제형을 분리한다

HotStuff의 `Basic → Chained` 배치는 proof를 이해하기 쉬운 최소형에서 시작해 pipelined implementation으로
확장한다. 우리 논문에서는 다음 순서가 대응한다.

```text
single-lane operation
  → State-Isolated Lane + EPC
  → N-lane operation
  → CLCC + participant EPCs
  → Multimmit L-QC cut에 통합
```

#### 4) Bullshark: proof와 operation을 멀리 떼지 않는다

Bullshark는 protocol 직후 garbage collection과 proofs를 둔다. 형식적 safety 근거를 끝까지 미룬 뒤
평가에서 처음 언급하지 않는다. 우리도 각 certificate 정의 바로 옆에 quorum 교집합과 custody
의미를 설명하고, 전체 정리와 증명은 Analysis 절로 모은다.

#### 5) Mysticeti: 두 경로를 하나의 overview에서 먼저 보여준다

Mysticeti는 consensus path와 fast path를 상세 절에서 분리하지만, Overview에서 공통 모델과 둘의
관계를 먼저 보여준다. 우리도 SIL/EPC와 CLCC를 세 개의 상자로만 그리면 안 된다. 한 operation이
수신되어 participant blocks, proof pipeline, certificate reports, cut apply로 이동하는 전체 그림을
먼저 제시해야 한다.

#### 6) Sui Lutris: object model은 protocol보다 앞선다

Sui Lutris는 object ownership에 따라 consensusless path와 consensus path를 구분한다. 우리 설계는
Sui와 같지 않지만, lane이 무엇을 소유하고 어떤 operation이 cross-lane이 되는지는 protocol 실행
전에 결정되어야 한다. 따라서 state/object contract는 background가 아니라 system model의 핵심이다.

#### 7) OmniLedger: 안전한 core와 성능 최적화를 분리한다

proof를 비동기 생성하는 것은 safety rule이 아니라 pipeline optimization이기도 하다. 최소 안전 규칙은
“cut apply 전에 필요한 EPC/CLCC가 존재한다”이고, block production과 proof generation을 겹치는 것은
이를 빠르게 만족시키는 구현이다. 두 주장을 분리해야 proof lag 상황의 liveness를 정직하게 설명할 수 있다.

#### 8) Chainspace: application interface를 명시한다

Cross-lane operation의 application-level predicate를 “앱이 알아서 한다”고만 쓰면 protocol specification이
불완전해 보인다. interface의 입력, 결정성, 실패 결과, version rule은 논문이 정의하고, 구체적인 business
logic만 application에 위임해야 한다.

#### 9) RapidChain: contribution별 실험을 표로 닫는다

RapidChain은 여러 설계 부품을 하나의 scalability 주장으로 합치되 기존 시스템과 정량 비교한다.
우리도 세 구성 요소를 모두 켠 결과 하나만 제시하면 안 된다. 각각을 제거한 ablation이 필요하다.

#### 10) Arete: architecture의 필요성을 숫자로 먼저 보인다

Arete는 protocol 설계 전에 size-security dilemma를 정량화한다. 우리 논문의 동기 역시 다음 식 또는
timeline으로 먼저 보여주는 편이 강하다.

```text
state-finality latency
  = ordering/cut latency
  + max(required proof readiness, cross-lane completeness)
  + cut apply cost
```

baseline이 post-cut re-execution을 한다면 비교식은 다음과 같다.

```text
baseline = cut latency + post-cut execution/synchronization
ours     = max(cut latency, pre-cut async execution/proving/readiness) + apply
```

두 번째 식은 proof가 cut 전에 준비되는 workload에서만 유리하므로, proof lag 분포를 평가해야 한다.

### 2.3 10편에서 반복되는 배치 패턴

| 반복 패턴 | 관찰 | 본 논문의 결정 |
|---|---|---|
| protocol 전에 model/assumption을 둠 | 10/10 | `n=5f+1`, Byzantine bound, partial synchrony, proof assumptions, lane ownership, application obligations를 먼저 고정한다. |
| overview를 상세 protocol 전에 둠 | 명시적 Overview가 6편, 나머지도 introduction/preliminaries에서 유사 역할 | 1페이지 안에 local/cross-lane lifecycle과 certificate 역할을 보여준다. |
| 포괄적 Related Work를 뒤에 둠 | 8/10; HotStuff와 RapidChain만 앞쪽 | Autobahn/Multimmit의 상속 설명만 초반에 두고, novelty 비교는 후반 Related Work에서 한다. |
| 별도 security/correctness 분석 | 6편이 독립 절, 나머지는 protocol 또는 appendix에 포함 | protocol 다음에 Safety and Liveness 절을 둔다. |
| implementation 뒤 evaluation | 5편이 명시적으로 이 순서, 2편은 합친 절 | Commonware 구조와 측정 지점을 먼저 설명한 뒤 결과를 제시한다. |
| limitation/discussion을 명시 | 5편이 별도 또는 Related/Future에 포함 | proof lag, shared hot object, app predicate, proof takeover, storage 비용을 독립 Discussion에 둔다. |

### 2.4 Step 2의 결론

우리 논문은 **Autobahn의 문제-현상 중심 도입**, **Narwhal의 layer decomposition**,
**Mysticeti/Sui의 overview-first 설명**, **Bullshark/OmniLedger의 protocol-before-proof-before-evaluation**,
**Chainspace의 application interface**, **Arete의 정량적 motivation**을 결합하는 것이 가장 적합하다.

반대로 피해야 할 배치는 다음과 같다.

- introduction 직후 certificate 세 종류를 나열하고 왜 필요한지 나중에 설명하는 구성
- Autobahn과 Multimmit 전체를 장황하게 재서술하여 본 논문의 문제를 늦게 제시하는 구성
- proof system 구현 없이 proof latency 개선을 핵심 성능 결론으로 쓰는 구성
- CLCC를 validity proof처럼 표현하는 구성
- formal property와 evaluation claim이 서로 연결되지 않는 구성

---

## 3. Autobahn에서 Multimmit까지: 초반 Background에 들어갈 내용

### 3.1 Autobahn이 담당하는 것

Autobahn은 각 replica가 독립적인 data lane을 확장하고, lane tip들의 vector인 `cut`을 BFT consensus로
commit한다. lane 안의 hash chain은 tip 하나로 그 이전 history를 참조하게 하며, 데이터 전파와
ordering agreement를 병렬화한다.

Autobahn의 기본 프로파일은 `n=3f+1`이고, lane car의 Proof of Availability는 `f+1` votes다.
Consensus commit에는 `2f+1` 규모 quorum이 사용된다. 이 certificate는 application execution proof가
아니라 data possession/availability를 위한 것이다.

본 논문에서 Autobahn은 다음 두 아이디어의 출발점으로 설명한다.

- independently growing producer lanes
- a compact cut that commits multiple lane histories together

### 3.2 Multimmit이 변경한 것

[Multimmit v3](https://arxiv.org/html/2607.21021v3)은 Autobahn 스타일의 multi-producer chains를
Minimmit 계열의 `n≥5f+1` single-round finality와 결합한다.

- 각 producer는 transaction-block chain을 독립적으로 확장한다.
- transaction blocks는 직접 consensus 투표 대상이 아니다.
- leader blocks는 transaction data를 담지 않고 chain tips와 이전 QC를 참조한다.
- DA certificate는 `n-2f=3f+1` shares로 형성된다.
- producer는 certificate 형성을 기다리지 않고 제한된 깊이까지 다음 blocks를 pipeline할 수 있다.
- proposal-relative votes는 voter가 각 chain에서 실제로 보유한 위치를 보고한다.
- L-QC는 `n-f=4f+1` view votes로 leader block을 finalise한다.
- per-chain extraction은 withheld data의 피해가 다른 producer chains 전체로 번지는 것을 줄인다.

Multimmit의 논문 구조도 본 논문에서 짧게 참고한다.

```text
Introduction
→ Setup
→ Intuition
   (Minimmit, chain layer, uncertified tips, proposal-relative voting, extensions)
→ Formal Specification
→ Verification
→ Optimisations
→ Experiments
→ Related Work
→ Final Comments
```

이는 consensus paper로서는 적합하지만, 우리 논문은 execution systems paper이므로 `Intuition`을
길게 반복하기보다 `Background & Motivation`에서 필요한 부분만 상속하고 구현·평가를 더 크게 둔다.

### 3.3 Multimmit이 직접 정의하지 않는 실행 문제

Multimmit은 transaction blocks의 availability, membership finality, ordering extraction을 주로 다룬다.
다음 application execution contract는 별도로 필요하다.

- 어떤 state를 어느 lane이 소유하는가?
- block을 언제 실행하고 어떤 result commitment를 만드는가?
- cut 이후 모든 validator가 full re-execution하지 않고 결과를 채택할 수 있는 조건은 무엇인가?
- 하나의 operation이 N lanes를 건드릴 때 모든 fragment가 존재함을 어떻게 확인하는가?
- proof correctness, cross-lane completeness, application validity를 각각 누가 담당하는가?

본 논문의 위치는 이 gap이다.

### 3.4 본 논문의 확장 지점

```text
Multimmit chain block dissemination
        │
        ├─ lane-local speculative execution ── async block proof ── EPC
        │
        └─ cross-lane manifest/fragments ────────────────────────── CLCC
                                                                  │
Multimmit proposal-relative cut + participant placement + EPC + CLCC + app predicate
                                                                  │
                                                        atomic state apply
```

EPC와 CLCC는 기존 Multimmit DA certificate 또는 L-QC와 같은 의미가 아니다.

| 객체 | threshold (`n=5f+1`) | 핵심 의미 |
|---|---:|---|
| Multimmit DA certificate | `n-2f=3f+1` | transaction block availability와 chain-position uniqueness |
| EPC | `n-2f=3f+1` | block execution proof/effects를 검증하고 보관한 quorum |
| CLCC | `n-2f=3f+1` | 동일 cross-operation의 전체 participant fragments/manifest를 보유한 quorum |
| Multimmit L-QC | `n-f=4f+1` | leader block/cut finality |

---

## 4. 권장 논문 목차

### 가제

**Execution-Relative Multimmit: Proof-Certified State Finality with Cross-Lane Completeness**

대안:

- **Extending Multimmit to State Finality**
- **Proof-Certified Execution Cuts for Multi-Producer Blockchains**
- **From Ordering Cuts to State Cuts: Asynchronous Execution for Multimmit**

`ZK`는 구체 proof system과 측정이 확정되기 전에는 제목에 넣지 않는다.

### Abstract

다섯 문단이 아니라 하나의 밀도 높은 문단으로 다음 다섯 요소를 순서대로 넣는다.

1. Multimmit의 multi-producer ordering이 주는 장점
2. execution/state-finality gap과 N-lane completeness 문제
3. SIL, EPC, CLCC를 결합한 해결책
4. safety/atomicity 및 conditional liveness 결과
5. Commonware prototype의 핵심 정량 결과

결과 숫자가 나오기 전까지 “significantly”, “near-linear”, “negligible” 같은 표현을 쓰지 않는다.

### 1. Introduction

배치할 내용:

- multi-producer ordering throughput이 application state finality로 자동 이전되지 않는 문제
- baseline timeline: receive → disseminate/order → cut → re-execute/synchronize → apply
- 제안 timeline: receive → execute/prove in pipeline → certificate readiness → cut → verify/apply
- A/B/C lanes를 건드리는 operation의 partial-fragment 문제
- 핵심 insight: execution validity와 cross-lane completeness는 서로 다른 evidence다.
- 정확히 제한한 contribution 3개

권장 contribution 문장:

1. **State-isolated proof-certified execution.** Producer-chain blocks를 lane-local state transition에
   결합하고, async proof와 EPC가 준비된 prefix를 post-cut full re-execution 없이 apply한다.
2. **Proof-independent cross-lane completeness.** N-lane operation의 joint manifest에 대한 CLCC를
   proof pipeline과 병렬로 형성하고, participant EPC와 함께 cut에서 all-or-none 결정을 한다.
3. **Multimmit integration and analysis.** `n=5f+1` proposal-relative cut에 두 evidence를 결합하는
   deterministic eligibility/apply rule을 정의하고 safety, atomicity, conditional liveness를 분석한다.

### 2. Background and Motivation

#### 2.1 Autobahn

- lanes, cars, availability proof, cut
- data dissemination과 ordering의 분리

#### 2.2 Multimmit

- transaction chains와 leader blocks
- DA certificate, proposal-relative voting, V-QC/L-QC
- `3f+1` 및 `4f+1` thresholds

#### 2.3 The Execution-Finality Gap

- Multimmit이 확정하는 것과 application state가 추가로 필요로 하는 것
- post-cut re-execution baseline
- proof lag가 있을 때 ordering은 계속되지만 state frontier가 늦어질 수 있음을 명시

#### 2.4 Motivating Cross-Lane Example

- `X={X_A,X_B,X_C}`
- 한 fragment 누락, 서로 다른 manifest, proof lag를 구분
- CLCC가 해결하는 문제와 해결하지 않는 문제

### 3. System Model and Problem Definition

#### 3.1 Participants and Network

- validators `n=5f+1`, Byzantine validators `≤f`
- partial synchrony와 cryptographic assumptions
- producer와 validator가 동일한 단순형 및 분리 가능한 일반형

#### 3.2 State and Lane Model

- lane ownership, state root, deterministic transitions
- producer chain ID와 execution lane ID의 구분
- object/version 또는 coarse state partition의 최소 contract

#### 3.3 Proof Model

- completeness, soundness, verification cost
- statement binding: epoch, lane, block, parent, pre-root, payload/effects, post-root, version
- proof generation failure는 Byzantine fault 또는 operational fault로 취급하는 정책

#### 3.4 Cross-Lane Application Interface

최소 interface:

```text
participants(operation) -> ordered lane set
fragment(operation, lane) -> lane-local transaction
manifest(operation) -> joint commitment
validate_cross_bundle(manifest, fragments, pre_versions, effects) -> accept | abort
apply_cross_effects(accepted_bundle) -> deterministic state updates
```

#### 3.5 Goals and Non-Goals

Goals:

- state convergence
- no partial cross-lane apply
- no post-cut full re-execution when evidence is ready
- continued block production during proof lag

Non-goals:

- off-chain orderbook matching fairness
- arbitrary shared-state scalability
- proving that an application chose an economically fair transaction order
- unconditional state-finality liveness when proof producers never produce a proof

### 4. Protocol Overview

한 페이지의 end-to-end 그림과 transaction lifecycle을 둔다.

#### 4.1 Evidence Separation

| 질문 | 담당 증거 |
|---|---|
| block bytes가 존재하는가? | Multimmit DA certificate |
| lane execution result가 올바른가? | block proof + EPC |
| cross-lane fragments가 모두 동일 bundle로 존재하는가? | CLCC |
| 이 bundle을 application이 허용하는가? | application predicate |
| 어느 결과가 canonical cut에 들어가는가? | Multimmit L-QC |

#### 4.2 Local Operation Timeline

#### 4.3 Cross-Lane Operation Timeline

#### 4.4 Cut Eligibility Overview

### 5. State-Isolated Lane Execution

#### 5.1 Lane State and Block Transition

#### 5.2 Speculative Execution Before Cut

#### 5.3 Asynchronous Proof Pipeline

block `h`를 생산한 뒤 `h+1...` 생산과 proof generation을 겹친다. proof가 늦어도 ordering block
production은 멈추지 않지만, proof-certified state frontier는 늦어질 수 있다.

#### 5.4 Effects Commitment and Apply

`apply`는 transaction logic 재실행이 아니라 이미 증명된 exact effects를 deterministic하게 반영한다.

#### 5.5 Proof Lag and Backpressure

- maximum speculative depth
- proof queue bound
- missing/invalid proof policy
- witness/effects retrievability 및 alternate prover 가능성

### 6. Execution Proof Certificate

#### 6.1 EPC Statement and Vote Rule

#### 6.2 Quorum Formation

`3f+1` votes는 최대 `f` Byzantine일 때 최소 `2f+1` honest verifier/custodian을 포함한다.

#### 6.3 Uniqueness and Custody

서로 충돌하는 두 `3f+1` certificate는 최소 `f+1` voters가 겹친다. honest validator가 동일
`(epoch,lane,height/pre-root)`에서 하나의 statement에만 vote한다는 규칙이 필요하다.

#### 6.4 Relationship to DA Certificates

동일 transport를 재사용할 수 있어도 vote semantics와 signed statement는 분리한다.

### 7. Cross-Lane Completeness

#### 7.1 Joint Manifest and Fragments

```text
operation_id,
attempt_id,
anchor_cut,
ordered participant lanes,
per-lane fragment commitments,
declared access/version metadata,
expiry,
application version
```

#### 7.2 CLCC Handshake

- validator는 모든 declared fragments를 받은 뒤 하나의 joint digest에 한 번 vote한다.
- proof completion을 기다리지 않는다.
- `3f+1` votes로 CLCC를 형성한다.

#### 7.3 Participant Lane Execution

각 fragment는 participant lane의 일반 transaction으로 block에 들어간다. 별도 cross-lane proof를
만들지 않고 해당 lane block의 일반 proof에 포함한다.

#### 7.4 Application Validation

completeness를 확인한 뒤에만 application predicate가 versions, conservation, margin, authorization 등
업무 규칙을 평가한다.

#### 7.5 Abort and Expiry

canonical state에 아직 apply하지 않은 결과는 `rollback`보다 `discard/abort`로 표현한다. 다만
후속 local transaction이 speculative cross-effect를 소비할 수 있다면 단순 discard가 불가능하므로,
첫 구현은 cross-effect를 non-consumable overlay로 유지하거나 dependency를 명시해야 한다.

### 8. Integration with Multimmit Cuts

#### 8.1 Ordering Frontier vs State Frontier

- ordering frontier는 Multimmit이 계속 전진시킨다.
- state frontier는 필요한 EPC/CLCC가 준비된 결과만 포함한다.
- 두 frontier를 혼동하지 않는다.

#### 8.2 Deterministic Eligibility Predicate

cross-lane operation `X`의 최소 조건:

```text
canonical_placement(X)
∧ CLCC(X)
∧ ∀ lane ∈ participants(X): EPC(block_containing(fragment(X,lane)))
∧ version_conflict_free(X)
∧ application_accepts(X)
```

#### 8.3 Cut Construction and L-QC

cut voter가 동일 evidence set과 deterministic rule로 결과를 계산할 수 있어야 한다. L-QC는
`4f+1`이고, 확정된 cross-lane operation은 모든 participant lanes에 all-or-none으로 apply한다.

#### 8.4 Recovery Paths

- missing fragment
- conflicting manifest
- missing/invalid proof
- expired operation
- producer equivocation
- state mapping/reconfiguration epoch change

### 9. Safety and Liveness Analysis

#### 9.1 Lane State Consistency

#### 9.2 EPC Uniqueness and Execution Soundness

#### 9.3 CLCC Joint-Manifest Uniqueness

#### 9.4 Cross-Lane Atomicity

#### 9.5 Deterministic State Convergence

#### 9.6 Conditional Liveness

정직한 participant가 fragments를 전파하고 필요한 proofs가 결국 생성·가용해지며 application
predicate가 accept하는 경우에 state finality가 발생한다고 쓴다. proof가 영구 누락돼도 ordering
progress가 계속된다는 것과 해당 state dependency가 finalise된다는 것은 별개다.

#### 9.7 Complexity

- certificate bytes
- votes per operation/block
- proof verification cost
- cross-lane fanout `m`
- effect/witness custody storage

### 10. Commonware Implementation

#### 10.1 Architecture

- Multimmit fork/control plane
- lane executor
- proof worker queue
- certificate collector
- cut evaluator
- state apply engine

#### 10.2 Application Traits

논문에 노출할 최소 trait은 Section 3.4의 contract와 일치시킨다.

#### 10.3 Prototype Stages

1. mock proof를 사용한 end-to-end control-plane 및 5-lane test
2. deterministic effects와 adversarial fragment/certificate tests
3. 실제 proof backend를 연결한 latency/throughput evaluation

Step 1은 correctness harness이고 논문 최종 성능 결과가 아니다.

### 11. Evaluation

#### 11.1 Research Questions

| RQ | 질문 | 대응 contribution |
|---|---|---|
| RQ1 | post-cut re-execution을 제거하면 state-finality latency가 얼마나 줄어드는가? | SIL + EPC |
| RQ2 | proof generation이 block production과 얼마나 겹치며 어느 lag에서 이점이 사라지는가? | async proof pipeline |
| RQ3 | lanes/validators 증가 시 throughput, network, verification cost는 어떻게 변하는가? | Multimmit integration |
| RQ4 | cross-lane 비율과 participant fanout이 CLCC latency/throughput에 미치는 영향은 무엇인가? | CLCC |
| RQ5 | missing fragment, invalid proof, Byzantine withholding이 ordering 및 state frontier에 미치는 영향은 무엇인가? | recovery/safety |
| RQ6 | certificate/effect custody의 storage와 bandwidth 비용은 얼마인가? | EPC/CLCC practicality |

#### 11.2 Baselines and Ablations

최소 비교군:

1. Multimmit ordering + post-cut validator re-execution
2. state-isolated pre-execution, EPC 없음
3. SIL + EPC, local-only workload
4. SIL + EPC + CLCC, mixed local/cross-lane workload
5. full design에서 proof latency, CLCC, custody를 각각 delay/disable한 ablation

가능하면 re-execution slow path 또는 2PC-style cross-shard baseline을 추가한다.

#### 11.3 Workloads

- 5 lanes 기본 시나리오
- 1, 5, 10, 20+ lanes scale-out
- local/cross-lane 비율 변화
- cross-lane fanout 2, 3, 5, 10
- uniform state access와 hot-object skew
- proof service time distribution과 injected backlog

#### 11.4 Metrics

- transaction receipt → membership/order finality
- transaction receipt → state finality
- proof ready → next eligible cut
- throughput, p50/p95/p99 latency
- proof queue length, speculative depth
- bytes per block/certificate/cut
- CPU, memory, storage, network
- abort/expiry rate와 affected state scope

#### 11.5 Fault Experiments

- producer withholds one fragment
- validator votes on conflicting manifest attempt
- proof arrives late or is invalid
- proof/effects custodian crashes
- one slow participant lane
- reconfiguration or lane mapping epoch boundary

### 12. Discussion and Limitations

반드시 명시할 내용:

- async proof generation은 proof cost를 없애지 않고 critical path와 겹친다.
- proof가 계속 늦으면 state finality가 lag하며 bounded queue/backpressure가 필요하다.
- CLCC는 correctness proof가 아니다.
- `3f+1` custody는 proof producibility를 자동 보장하지 않는다. witness가 producer에게만 있으면
  alternate proving이 불가능할 수 있다.
- cross-lane application predicate의 경제적 정당성은 application 책임이다.
- 모든 operation이 하나의 hot shared object를 건드리면 lane parallelism의 효용이 감소한다.
- monolithic lane root 아래에서 abort된 speculative effect를 후속 transaction이 소비했다면 suffix
  재실행 또는 overlay/dependency 구조가 필요하다.
- off-chain CLOB matching order/fairness는 범위 밖이다.

### 13. Related Work

다섯 묶음으로 정리한다.

1. multi-proposer dissemination and ordering: Autobahn, Multimmit, Narwhal/Tusk, Bullshark, Mysticeti
2. state/object isolation: Sui Lutris, Chainspace, object-based execution systems
3. sharded and cross-shard transactions: OmniLedger/Atomix, RapidChain, Byzcuit, Cerberus, Arete
4. verifiable asynchronous execution: Hyli, RollShard, Mina scan state, Kaspa vProgs, Flow/Sei asynchronous execution
5. recursive/folded proofs and proof availability: 실제 backend가 정해진 경우에만 상세화

Related Work의 비교축은 “proof를 쓰는가”가 아니라 다음 네 가지여야 한다.

- ordering finality와 state finality를 분리하는가?
- proof가 block production critical path에 있는가?
- cross-lane completeness를 proof validity와 분리하는가?
- canonical cut에서 all-or-none apply를 어떻게 결정하는가?

### 14. Conclusion

새 기여를 다시 과장하기보다, 다음 세 결과만 요약한다.

- Multimmit producer chains를 state-isolated execution lanes로 해석하는 execution contract
- asynchronous block proof/EPC로 post-cut full re-execution을 제거하는 state-finality path
- proof-independent CLCC와 participant proofs를 cut에서 결합하는 N-lane atomic finalization

---

## 5. 주장·정리·실험의 연결표

| Introduction의 주장 | Protocol 위치 | Formal property | Evaluation evidence |
|---|---|---|---|
| cut 뒤 full re-execution을 제거한다 | Sections 5, 6, 8 | execution soundness, deterministic apply | RQ1 latency/CPU |
| proof generation을 block production과 겹친다 | Section 5.3 | safety independent of proof timing, conditional liveness | RQ2 lag sweep |
| N-lane partial-fragment apply를 막는다 | Sections 7, 8 | CLCC uniqueness, cross-lane atomicity | RQ4/RQ5 |
| Byzantine non-participant/slow proof가 ordering 자체를 막지 않는다 | Section 8.1 | ordering/state frontier separation | RQ5 fault injection |
| design이 scale-out 이점을 유지한다 | Sections 5, 8 | complexity bounds | RQ3 lane/validator scaling |

이 표의 어느 칸도 채우지 못하는 주장은 introduction contribution에서 제거한다.

---

## 6. 필요한 그림과 표

### Figure 1 — Baseline vs Proposed Timeline

baseline post-cut execution과 proposed async execution/proof overlap을 같은 시간축에 둔다.

### Figure 2 — Protocol Lineage

```text
Autobahn lanes/cuts
        ↓
Multimmit producer chains + proposal-relative finality
        ↓
State-Isolated Lanes + EPC + CLCC + state apply
```

### Figure 3 — End-to-End Architecture

producer, validators, proof workers, certificate collectors, Multimmit leader/cut, state apply를 표시한다.

### Figure 4 — Three-Lane Operation

`X_A`, `X_B`, `X_C`의 block inclusion, CLCC handshake, independent block proofs, cut-time all-or-none
결정을 보여준다.

### Table 1 — Evidence and Thresholds

DA certificate, EPC, CLCC, V-QC/L-QC의 statement, signer rule, threshold, guarantee를 비교한다.

### Table 2 — Prior Work Comparison

ordering/state finality separation, async proof, cross-state completeness, re-execution, atomic apply를 비교한다.

### Table 3 — Threats and Recovery

withholding, equivocation, proof lag, invalid proof, version conflict, reconfiguration별 detection과 outcome을 적는다.

---

## 7. 출판 전략에 대한 잠정 결론

현재 서사의 자연스러운 1차 형태는 **EuroSys/NSDI 계열 systems paper**다. 다음 조건이 필요하다.

- 실제 Commonware/Multimmit fork 또는 충실한 구현
- WAN 또는 다중 region 실험
- proof lag와 cross-lane fanout을 포함한 end-to-end evaluation
- baseline/ablation과 장기 backlog 실험

CCS/IEEE S&P/NDSS 계열을 목표로 하려면 certificate/cut safety가 단순 quorum 조합을 넘어서야 한다.
공격 모델, fork binding, proof/effects custody, witness takeover, reconfiguration까지 형식화하고 새로운
adversarial result를 보여줄 필요가 있다.

IEEE Transactions on Computers나 PVLDB형 장문은 protocol, proof, implementation, workload analysis를
더 넓게 담을 수 있지만, 최초 투고 전에 systems contribution이 단순한 기존 기술 조합으로 보이지
않도록 cut algorithm과 formal property를 더 날카롭게 만들어야 한다.

---

## 8. 다음 작성 단계

1. Figure 1의 baseline을 실제 Multimmit execution reference model로 확정한다.
2. EPC와 CLCC의 signed statement 및 honest one-vote rule을 byte-level schema로 확정한다.
3. cross-lane overlay/dependency 정책을 첫 구현 범위에서 하나 선택한다.
4. Section 8의 deterministic cut algorithm을 pseudocode로 작성한다.
5. Section 9의 theorem statements와 proof sketches를 먼저 작성한다.
6. 그 정리와 일치하는 Commonware E2E test 및 evaluation matrix를 작성한다.
7. 이후 Introduction과 Abstract를 작성한다.

논문 본문을 먼저 길게 쓰기보다 4–6단계를 먼저 닫아야 contribution과 novelty가 흔들리지 않는다.
