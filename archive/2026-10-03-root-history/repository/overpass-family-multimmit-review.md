# Overpass: Autobahn-family 모델과 Multimmit 구현 — 피드백 항목

> **2026-09-28 후속 결정:** 아래는 v13.20에 대한 이전 검토다. 현재는 [fixed certified cut + pipeline + placement 계획](./overpass-fixed-cut-implementation-plan.md)으로 방향을 변경했다. Native tip 추출과 extension voting을 제거하되 5f+1 기반 합의를 재구성하는 계획이며, 현재 코드·LaTeX·PDF·Google Docs에 구현/반영된 상태는 아니다. 아래 M1의 native extraction 의무는 새 fixed-value consensus/durable delivery 의무로 교체될 예정이다.

> 2026-09-27 · v13.20 · 로컬 영문 LaTeX 수정 기록. 이번 갱신은 배치표 scheduling에 한정한다. Google Docs, 기존 proof/PAC SDK와 Commonware 코드는 변경하지 않았다. 구현·실험 완료를 뜻하지 않는다.

## 이번에 확정한 방향

Overpass는 **Autobahn-family consensus 위에서 pipelined execution과 operation-aware producer placement를 결합하여 state-finalization latency를 줄인다.** 일반 모델과 실제 구현을 구분하고, 구현과 주 실험은 **Multimmit**을 기준으로 한다. Family는 논문에서 정의할 설계 범주이며 두 프로토콜의 quorum·cut 추출이 같다는 뜻이 아니다.

- 공통 ordering rule을 block 수신부터 적용하여 speculative execution을 dissemination·consensus와 겹친다.
- 늦은 predecessor와 candidate 변경이 일으키는 재실행을 producer placement로 줄이는 것이 후속 최적화다.
- Multimmit의 native voting, extensions, tip extraction, sweep/anchor/halt 규칙은 유지한다. Cut별 임의 lane 회전을 현재 구현 전제로 가져오지 않는다.
- Canonical adoption은 **native consensus가 확정한 global ordered prefix**와 canonical parent에 맞아야 한다. L-QC 수신이나 chain-local membership finality만으로 대체하지 않는다.
- Cut vote는 body 확보·dependency DAG 완성·execution 완료를 뜻하지 않는다. Sync와 execution은 consensus와 중첩할 수 있다.
- `f+1` matching execution signatures는 최대 `f` Byzantine 아래 정상 직접 실행자가 한 명 이상 있다는 조건부 근거다. Ordering quorum을 대체하지 않는다. 구체적인 signer 자격과 checkpoint 단위는 M2로 남겼다.

## 먼저 피드백이 필요한 설계 결정

### 1. 어떤 실행 구간에 같은 서명을 모을까? — M1/M2

같은 Multimmit proposal의 서로 다른 유효 L-QC라도 확정 범위와 현재 방출한 ordered prefix 길이가 다를 수 있다. `같은 proposal에 투표했음`만으로 같은 결과 서명을 모을 수는 없다.

**필요한 결정:** 모든 노드가 확인 가능한 공통 execution checkpoint 경계. 예를 들어 native ordered stream의 정해진 block-count 경계를 사용할 수 있지만, 범위 식별·parent·마지막 partial interval·recovery까지 명시해야 한다. 이는 제안일 뿐 이번 수정에서 선택하지 않았다. 빈번한 checkpoint의 인증 비용과 큰 checkpoint의 대기 시간을 비교해야 한다.

### 2. 누가 실행 결과에 서명할 수 있을까? — M2

현재는 epoch validator 안의 eligible set을 매개변수로 두었다. 이전 Autobahn `2f+1` voter subset은 이식하지 않았다.

**추천 검토안:** 해당 epoch의 모든 validator 중 정확한 canonical 입력을 직접 실행·검증한 노드가 서명 가능하도록 한다. Late catch-up executor도 참여할 수 있다. 이 정책을 채택한다면 ordering 참여 여부와 무관하게 exact input·parent·runtime·output 일치를 확인해야 한다. `f+1`명만 실행하도록 고정하는 것은 Byzantine withholding 아래 진행 보장이 아니다.

### 3. 확정 전 어떤 candidate 순서로 실행할까? — M1/P1/P2

Native Multimmit의 serialization은 유지하되, 미정 anchor·누락 predecessor·extension을 speculative scheduler가 어떻게 취급할지 구체화해야 한다. 처음부터 최종 prefix를 안다고 주장하지 않는다.

**필요한 검증:** 서로 다른 도착 순서/누락/extension에서 이미 수행한 작업 중 무엇을 재사용하고 무엇을 무효화하는지, 최종 sequential oracle과 결과가 같은지. 전체 body sync나 실행 완료를 ordering vote의 선행조건으로 추가하지 않는다.

### 4. 배치표를 native consensus에 어떻게 연결할까? — M3/D4/P3

Map/KEEP·history·activation metadata가 consensus의 서명/복구 문맥에 묶여야 한다. PoA 이전 검사만으로 충분하다고 쓰지 않고, uncertified block에 대한 proposal-relative/extension endorsement 경로도 확인해야 한다.

**확정한 scheduling:** cut c에서 map을 선택하고 cut c+1이 확정되면 새 블록부터 사용한다. 생성·전파·ordering은 멈추지 않고 기존 블록은 원래 map version 그대로 남는다. Old/new-map 블록이 뒤의 cut에 함께 포함될 수 있으며, 아직 canonical inclusion을 확인하지 못한 tx는 새 map으로 재전달할 수 있다.

**중복 정책 변경:** cross-block 중복을 금지하지 않는다. Routing 정보와 무관한 stable tx ID로 canonical order의 admission-valid 첫 occurrence만 실행 입력에 남기고, 이전 history에서 소비한 ID도 제외한다. 첫 attempt가 실패해도 같은 ID의 뒤 복사본은 재실행·fee·event를 만들지 않는다. Speculation에서 사용한 occurrence가 달라지면 해당 effects와 의존 결과를 재검증·필요 시 재실행한다. 다른 signed tx의 동일 nonce 문제는 application replay 규칙으로 처리한다.

**남은 의무:** `q_map > f`의 구체적 값과 native consensus cut 식별·metadata binding, old-map applicability/retirement, consumed-ID history 복구, faulty producer 재배정이다. 단순 map tag는 전환 전 블록과 전환 후 악의적인 stale-map 생산을 구분하지 못한다. c+1은 Unix time이나 로컬 L-QC 수신 횟수가 아니며 모든 노드의 동시 전환·map 수신을 보장하지 않는다. Fixed-map 실험과 온라인 전환 검증을 구분한다.

### 5. 실제 latency 이득이 남을까? — E1/E2

Multimmit 자체의 ordering이 짧으면 실행을 숨길 시간도 짧아질 수 있다. Placement가 historical dependency 점수를 줄여도 queueing·map 검증·서명 대기 때문에 E2E latency가 악화될 수 있다.

**실험:** 동일 Multimmit 버전·ordering·application backend로 Original / Pipeline / Pipeline + Placement를 비교한다. Membership finality, global ordered delivery, result certification, node-local readiness를 따로 측정한다. RTT × state operation count, 늦은 predecessor, workload skew에 따른 post-order residual work와 ingress-to-state p50/p99를 함께 본다. Ethereum trace simulation만으로 실행 latency 향상을 확정하지 않는다.

### 6. 논문과 구현 버전이 일치할까? — M1/D1

근거 논문은 Multimmit arXiv v5, 로컬 fork 기준은 `534af0ed`다. 둘이 같은 규칙을 구현한다고 아직 확인하지 않았다. 구현 시작 전 commit을 고정하고 vote/extraction/emission 차이를 audit해야 한다. 현재 로컬 배치 목적함수도 별도 Google Docs 수정본과 자동 동기화되어 있지 않으며, 이번 수정은 배치 알고리즘 자체를 바꾸지 않았다.

## 현재 논문 흐름

1. Introduction: 빠른 ordering과 별개로 남는 state-finalization latency; pipeline + placement 제안.
2. Background: Autobahn/Multimmit의 공통 구조와 차이, ordering·execution·read readiness 구분.
3. Core design: family contract → Multimmit 적용 → speculative execution → exact-prefix 결과 인증·state transfer.
4. Producer placement: 늦은 predecessor로 인한 재실행 비용 → operation-aware grouping/배치 → 안전한 활성화 의무.
5. Correctness/Liveness: 입력 유일성, 재사용 검증, 조건부 `f+1` 논증, Byzantine 경계.
6. Evaluation: 세 Multimmit 비교군과 같은 ordering/resource 통제; 개선 결과는 아직 없음.
7. Related Work, Discussion, Conclusion: 기여 경계와 해결되지 않은 조건.

근거: [Multimmit v5](https://arxiv.org/abs/2607.21021v5), [Autobahn](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf). 이 노트는 새 safety proof나 측정 결과가 아니다.
