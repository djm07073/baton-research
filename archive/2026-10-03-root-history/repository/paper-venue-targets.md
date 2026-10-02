# Multimmit Execution Extension 투고 venue 후보

> 기준일: 2026-08-23  
> 관련 문서: [paper-outline-research.md](./paper-outline-research.md), [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 결론

현재 연구의 권장 target hierarchy는 다음과 같다.

1. **Stretch target:** SOSP 또는 OSDI
2. **가장 자연스러운 systems target:** EuroSys 또는 NSDI
3. **security framing을 강화한 대안:** NDSS, CCS, IEEE S&P
4. **formal-algorithm framing 대안:** PODC 또는 DISC
5. **장문 journal target:** IEEE Transactions on Computers, TPDS, TOCS
6. **blockchain-specific target:** Financial Cryptography

Autobahn이 SOSP 2024 논문이라는 이유만으로 우리도 SOSP 스타일을 그대로 따라야 하는 것은 아니다.
Autobahn은 Multimmit의 한 기능 확장이 아니라, partial synchrony의 실전 문제를 `seamlessness`라는
일반 문제로 정의하고 새로운 BFT architecture와 폭넓은 평가를 제시했다. 우리 논문도 SOSP를
목표로 한다면 “Multimmit에 세 certificate를 추가했다”가 아니라 다음과 같이 일반화해야 한다.

> Multi-producer ledgers에서 ordering finality와 state finality가 분리될 때, asynchronous execution
> evidence와 cross-state completeness를 canonical cut에 결합하는 일반 execution-finality architecture.

## 2. 후보별 적합도

| Venue | 현재 적합도 | 선호하는 논문 형태 | 우리에게 필요한 것 | 판단 |
|---|---:|---|---|---|
| **SOSP** | 중간 | 새로운 일반 systems principle, 설계·구현·분석·대규모 평가가 모두 강한 논문 | Multimmit 종속 표현을 넘어선 일반화, 명확한 새 abstraction, 완성도 높은 Commonware system, WAN/fault evaluation | 가장 좋은 stretch target이지만 현재 상태로는 incremental-extension 판정 위험이 큼 |
| **OSDI** | 중간–높음 | 독창적인 systems design과 강한 implementation/evaluation | 실제 end-to-end prototype, 운영 가능한 proof pipeline, state recovery/backpressure, 비교 시스템 | SOSP보다 implementation 중심으로 밀기 좋음 |
| **NSDI** | 높음 | networked/distributed systems의 설계 원리, 구현, 실증 평가 | validators/lanes 규모 변화, WAN 배포, bandwidth/custody, Byzantine withholding 실험 | 현재 연구와 매우 잘 맞음. 단, networking/system contribution이 전면에 있어야 함 |
| **EuroSys** | 높음 | 넓은 computer systems 문제, 설득력 있는 architecture, 엄밀한 평가와 limitations | Commonware 구현, baseline/ablation, proof-lag와 cross-lane workload 실험 | 현재 설계의 가장 자연스러운 1차 systems venue |
| **ACM CCS** | 중간 | 명확한 security problem, 새로운 공격/방어, formal 또는 empirical security evidence | CLCC/EPC 없을 때의 구체 공격, fork binding, custody/witness attacks, security theorem | 성능 최적화가 중심이면 약함 |
| **IEEE S&P** | 중간 | security/privacy에 대한 분명한 새 기여 | proof/certificate security를 핵심으로 재구성하고 강한 adversarial evaluation과 formalization | 단순 execution acceleration은 scope risk |
| **NDSS** | 중간–높음 | network/distributed systems security와 실용적 구현 | Byzantine withholding/equivocation, cross-lane partial execution attacks, prototype | security attack story가 생기면 좋은 후보 |
| **PODC / DISC** | 중간 | distributed algorithm의 새 원리, 정리, lower bound/complexity | deterministic cut algorithm, quorum proof, safety/liveness 및 가능하면 impossibility/lower-bound result | 구현보다 형식적 기여를 전면에 둘 때 적합 |
| **DSN** | 높음 | dependability, fault containment, recovery, resilient distributed systems | proof lag/backlog, failure recovery, custody loss, reconfiguration 실험 | 안정성·복구를 강조하면 매우 실용적인 후보 |
| **Financial Cryptography** | 높음 | blockchain protocols, ZK, consensus, cross-chain/DeFi의 명확한 기여 | blockchain 선행연구 대비 novelty와 protocol analysis | 분야 적합도는 높지만 SOSP/NSDI와 평판 축은 다름 |
| **IEEE Transactions on Computers** | 높음 | 이론·시스템·성능을 함께 담은 완결된 장문 | protocol, proof, implementation, broad evaluation | 현재 주제의 가장 자연스러운 journal 후보. RollShard도 이 venue에 게재됨 |
| **IEEE TPDS** | 높음 | parallel/distributed algorithms, software, architecture, scalability evaluation | lane parallelism, synchronization cost, scale-out 분석 | execution parallelism을 중심으로 쓰면 적합 |
| **IEEE TDSC** | 중간–높음 | dependable/secure protocols, attacks, verification, experimental fault evaluation | certificate security와 recovery를 중심에 배치 | security/dependability 버전에 적합 |
| **ACM TOCS** | 중간–높음 | 깊이 있는 computer systems design·implementation·evaluation | 일반화된 architecture와 완성도 높은 system artifact | 좋은 archival target이나 높은 시스템 완성도가 필요 |
| **PVLDB** | 낮음–중간 | transaction processing/data systems에 대한 새 abstraction과 workload evidence | concurrency control, object transaction semantics, serializability를 핵심으로 재구성 | 현재 consensus/execution 서사 그대로는 부적합 |

## 3. SOSP를 목표로 할 때 필요한 변화

### 3.1 제목과 문제를 Multimmit 밖으로 일반화

약한 framing:

```text
Adding execution proofs and cross-lane certificates to Multimmit
```

강한 framing:

```text
Decoupling ordering and state finality in multi-producer ledgers
```

Multimmit은 implementation vehicle 및 protocol instantiation으로 내리고, 본문이 답하는 질문은
다른 multi-proposer protocols에도 적용되게 해야 한다.

### 3.2 하나의 새 abstraction이 필요

현재 세 요소는 합리적이지만 각각은 알려진 아이디어와 가깝다. SOSP 수준에서는 이들을 묶는
하나의 기억 가능한 abstraction이 필요하다. 후보는 다음과 같다.

- **evidence-relative state cut**
- **dual-frontier finality:** ordering frontier와 state frontier
- **proof/completeness-separated execution finality**

certificate 이름 세 개보다 이 상위 abstraction을 논문의 중심으로 둔다.

### 3.3 강한 general result

최소한 다음 중 하나가 필요하다.

- 어떤 evidence 조합이 post-order re-execution 없이 안전한 state apply를 허용하는지에 대한
  necessary/sufficient conditions
- scalar lane prefix만으로는 cross-state proof lag를 국소화할 수 없다는 limitation/impossibility result
- deterministic maximal eligible cut algorithm과 compatibility theorem
- proof lag 아래 ordering progress와 state convergence의 bounded relationship

### 3.4 완전한 system evidence

- Commonware/Multimmit end-to-end implementation
- mock이 아닌 실제 proof backend 또는 여러 proof-cost profile을 정당화하는 구현
- geo-distributed/WAN 배포
- lane 수, validators 수, proof lag, cross-lane 비율, fanout, hot state를 변화시킨 평가
- Byzantine fragment/proof withholding, crash recovery, backlog/GC 실험
- Multimmit+re-execution, 2PC/slow path 및 주요 ablation과 비교

## 4. Venue별 권장 논문 스타일

### SOSP/OSDI 스타일

```text
general problem
→ surprising systems insight
→ architecture
→ end-to-end implementation
→ rigorous evaluation
→ broader lessons
```

프로토콜 세부사항보다 “왜 기존 systems architecture가 실행 단계에서 병렬성을 잃는가”를 먼저
보여준다. formal proof는 핵심 정리만 본문에 두고 세부는 appendix로 보낼 수 있다.

### NSDI/EuroSys 스타일

```text
distributed bottleneck
→ layer decomposition
→ protocol/architecture
→ implementation
→ WAN, scaling, failure evaluation
```

현재 준비한 개요와 가장 가깝다. latency breakdown, network/custody overhead, slow lane 및 Byzantine
withholding이 특히 중요하다.

### CCS/S&P/NDSS 스타일

```text
adversarial failure or attack
→ security model
→ protocol
→ formal security
→ attack/fault experiments
```

“더 빠르다”보다 “기존 proof-late/cross-lane execution은 이 공격을 막지 못하며, 우리 evidence
separation이 이를 막는다”가 중심이어야 한다.

### PODC/DISC 스타일

```text
formal problem
→ model
→ algorithm
→ theorem/lower bound
→ complexity
→ optional implementation
```

Commonware는 validation artifact가 되고 핵심 기여는 cut algorithm과 증명이 된다.

### IEEE TC/TPDS journal 스타일

```text
complete background and taxonomy
→ formal model
→ full protocol
→ correctness proofs
→ implementation
→ broad evaluation and sensitivity analysis
→ limitations
```

학회보다 긴 관련연구, 여러 workload, parameter sensitivity, recovery/reconfiguration을 담기 좋다.

## 5. 현재 공개된 가까운 일정

현재 날짜 기준 공식 CFP에서 확인되는 일정이다.

| Venue | 일정 | 현실성 |
|---|---|---|
| NSDI 2027 fall | abstract 2026-09-10, paper 2026-09-17 | 완성된 구현·초안이 없다면 매우 촉박함 |
| EuroSys 2027 fall | abstract 2026-09-17, paper 2026-09-24 | 역시 현재 단계에는 촉박함 |
| Financial Cryptography 2027 | paper 2026-09-17 | protocol paper가 거의 완성돼 있을 때만 가능 |
| IEEE S&P 2027 second cycle | abstract 2026-11-10, paper 2026-11-17 | security framing과 formal proof를 빠르게 닫을 때 가능 |
| OSDI 2027 | abstract 2026-12-01, paper 2026-12-08 | 공격적인 일정. 9–10월 내 prototype/evaluation 시작 필요 |
| SOSP 2026 | 2026-04-01 마감 완료 | 다음 공식 cycle을 기다려야 함 |
| IEEE TC / TPDS / TDSC / TOCS | 일반적으로 rolling submission | 완성도를 우선할 수 있음 |

NDSS 2027 fall 마감은 2026-08-19로 이미 지났다. 다음 cycle/연도를 고려해야 한다.

## 6. 권장 투고 전략

### 전략 A — Top systems 우선

1. SOSP 수준을 논문 품질 기준으로 설정한다.
2. 2026년에는 protocol specification, theorem, Commonware prototype을 완성한다.
3. OSDI 2027 readiness를 2026년 10월에 평가한다.
4. 준비가 부족하면 성급하게 제출하지 않고 다음 SOSP/NSDI/EuroSys cycle을 목표로 한다.

### 전략 B — Conference 후 journal 확장

1. EuroSys/NSDI/FC/DSN 중 framing에 맞는 학회 버전을 제출한다.
2. 이후 recovery, reconfiguration, proof backend, 더 큰 evaluation을 추가한다.
3. IEEE TC/TPDS에 substantial extension으로 제출한다.

IEEE TC는 이미 출판된 conference paper의 확장판도 받지만, 공식 안내상 최소 40%의 새로운
기술·과학적 내용을 요구하므로 처음부터 conference/journal 경계를 설계해야 한다.

## 7. 최종 추천

현재 상태의 추천 순위는 다음과 같다.

```text
논문 품질의 north star: SOSP
가장 자연스러운 실제 1차 target: EuroSys 또는 NSDI
구현 중심의 강한 대안: OSDI
보안 기여가 강해질 경우: NDSS
장문 journal로 바로 갈 경우: IEEE Transactions on Computers
```

따라서 “Autobahn이 SOSP이므로 우리도 SOSP”가 아니라, **Autobahn처럼 일반적인 systems problem을
정의할 수 있으면 SOSP**, Multimmit execution architecture와 실증이 중심이면 **EuroSys/NSDI**가
더 정확한 판단이다.

## 8. 2027년 9월 투고 로드맵

목표를 **2027년 9월 full-paper submission**으로 둔다. 2028년 conference의 CFP와 정확한 마감은
아직 공개되지 않았으므로, 내부 마감은 venue와 독립적으로 2027년 8월 말로 설정한다. 현재 공식적으로
NSDI 2028 행사는 2028년 5월 9–11일로 예정되어 있으나 submission deadline은 아직 발표되지 않았다.

| 기간 | 핵심 작업 | 종료 조건 |
|---|---|---|
| 2026.08–09 | protocol/spec freeze | SIL/EPC/CLCC schema, threat model, deterministic cut predicate, non-goals 확정 |
| 2026.10–12 | Commonware control-plane PoC | 5 lanes E2E, mock proof, local/cross-lane apply, failure tests 통과 |
| 2027.01–02 | real proof pipeline | 실제 proof backend 1종, async queue/backpressure, proof/EPC latency 측정 |
| 2027.03–04 | adversarial and recovery design | missing fragment/proof, equivocation, expiry, crash recovery, overlay/dependency 정책 구현 |
| 2027.05–06 | full evaluation | WAN testbed, scale-out, baselines, ablations, proof-lag/fanout/hot-state experiments 완료 |
| 2027.07 | full paper draft | introduction부터 conclusion까지 모든 표·그림·정리·결과 포함 |
| 2027.08 | internal review and artifact | 외부 연구자 리뷰, claim audit, 재현 스크립트, 익명 artifact 완성 |
| 2027.09 | submission | 당시 열린 NSDI/EuroSys/SOSP 계열 CFP 중 fit이 가장 높은 venue에 제출 |

### 필수 gate

- **G1 — 2026-09-30:** protocol ambiguity가 없어야 한다.
- **G2 — 2026-12-31:** mock proof라도 5-lane E2E가 실제 cut까지 실행되어야 한다.
- **G3 — 2027-02-28:** 실제 proof latency와 block interval의 관계를 측정해야 한다.
- **G4 — 2027-04-30:** Byzantine/failure 시나리오와 recovery semantics가 닫혀야 한다.
- **G5 — 2027-06-30:** 논문의 모든 핵심 숫자가 고정되어야 한다.
- **G6 — 2027-07-31:** 완전한 첫 원고가 있어야 한다.
- **G7 — 2027-08-31:** reviewer-ready paper와 artifact가 있어야 한다.

### Venue 결정 시점

2027년 5–6월에 다음 기준으로 최종 venue를 선택한다.

- general abstraction과 fundamental result가 강함 → SOSP/OSDI 계열
- system implementation과 WAN evaluation이 가장 강함 → NSDI/EuroSys
- 새로운 adversarial result와 security proof가 강함 → NDSS/CCS/S&P
- formal cut algorithm과 theorem이 주 기여 → PODC/DISC
- 결과가 광범위하지만 conference page limit에 맞지 않음 → IEEE TC/TPDS

9월에 맞추기 위해 결과를 줄이는 것이 아니라, **6월까지 연구 결과를 닫고 7–8월을 논문 품질과
artifact에 온전히 사용하는 것**을 일정의 핵심 원칙으로 둔다.
