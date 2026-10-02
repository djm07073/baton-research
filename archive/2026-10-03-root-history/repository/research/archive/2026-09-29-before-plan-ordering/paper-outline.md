# Paper Outline: Overpass: Pipelined Execution and Producer Placement for Low-Latency State Finalization in Autobahn-Family Consensus

## 최신 설계 변경 — 2026-09-28 (본문 반영 전)

[Fixed-cut 구현 계획](./overpass-fixed-cut-implementation-plan.md)에 새 reasoning과 module/그림을 기록했다. `n=5f+1`을 유지하고 certified cut 자체를 `4f+1`로 확정하며, native proposal-relative tip 추출과 extension voting은 제거하는 방향이다. 기존 Voter/Actor에 실행·배치 module을 독립 연결한다. 아래 v13.20의 “native 유지”는 이전 결정이며 영문 본문/PDF는 아직 그 버전이다.

논리 전개는 **E2E state-finalization 목표 → fixed candidate cut과 사전 execution pipeline → late predecessor/재실행 비용 → operation-aware producer placement → exact-context result certification/apply**다. DA 인증 대기와 execution을 중첩해 얻는 이득은 가설이며 ordering 지연 자체를 무가치하다고 쓰지 않는다. Extension 제거 시 inclusion 보장을 재검토한다. Fixed-value parent/view-change 안전성을 tip 추출 삭제만으로 계승했다고 주장하지 않는다.

평가는 Native Multimmit + post-order execution / Fixed-cut + post-cut execution / Fixed-cut + Pipeline / Fixed-cut + Pipeline + Placement로 나눠 합의 변경·pipeline·placement 효과를 분리한다. 아래 보관 개요의 safety/quorum·baseline 서술은 다음 manuscript 갱신에서 함께 수정해야 한다.

---

> 상태: v13.20 — v13.19 family/Multimmit 모델 유지; c+1 배치표 활성화와 canonical 중복 제거 반영. 아래 보관 이력은 현재 규칙을 대체하지 않음  
> 갱신일: 2026-09-27  
> 최신 영문 설계: [Pipelined Ordering and State Finalization](./research/paper/sections/03-design.tex)  
> 평가 backend 구현 참고: [blockstm-execution-model.md](./blockstm-execution-model.md)  
> 최신 배치 설계: [Producer Placement](./research/paper/sections/04-placement.tex); [이전 soft-routing 기록](./state-affinity-placement.md)과 구분  
> 구현 상태: 설계 기록과 개요이며 아직 consensus E2E로 구현·검증되지 않음  
> 이전 개요: [v12 cut-tail/proof 모델 보관본](./paper-outline-v12-cut-tail.md)

## v13.20 배치표 scheduling 결정 — 2026-09-27

이 절은 아래 v13.19의 배치표 전환 관련 서술을 갱신한다. Optimizer·실행 인증 threshold·native ordering 규칙은 이번 편집에서 바꾸지 않는다.

1. **선택과 활성화:** background에서 준비한 map 또는 KEEP을 cut c에서 선택한다. 새 map은 cut c+1의 finality를 확인하고 map을 확보한 producer가 이후 만드는 블록부터 사용한다. Unix time이나 로컬 L-QC 수신 횟수가 아니다.
2. **계속 생성:** block 생성·전파·ordering을 멈추거나 모든 old work가 소진되기를 기다리지 않는다. 기존 블록의 bytes와 map version은 유지하며, 이후 cut에 old/new-map 블록이 함께 들어갈 수 있다. 모든 노드가 같은 wall-clock 순간에 전환한다는 뜻은 아니다.
3. **중복 포함 허용:** canonical inclusion이 확인되지 않은 tx는 새 map으로 다시 전달할 수 있다. 옛 producer 블록에도 같은 tx가 있을 수 있으므로 cross-block 중복 포함 자체는 금지하지 않는다. 같은 블록 내부 중복은 admission에서 거부한다.
4. **한 번만 실행 입력으로 채택:** routing envelope·map version·producer와 무관한 stable tx ID를 유지한다. Canonical block order에서 admission-valid 첫 occurrence만 남기고 이전 canonical history에서 소비된 ID도 제외한다. 먼저 수신·먼저 speculative execution한 노드가 winner를 정하는 것이 아니다.
5. **실패와 재실행:** 첫 canonical occurrence가 application 실패여도 같은 ID를 소비한다. 뒤의 복사본은 재시도·fee·event를 추가하지 않는다. 살아남는 occurrence가 달라지면 제외된 speculative effects를 제거하고 영향을 받은 tx들을 재검증·필요 시 재실행한다. STM을 호출하면 입력 집합 변경까지 자동 해결된다는 주장은 하지 않는다.
6. **남은 의무:** native cut identifier와 map metadata binding, old-map block의 권한·유효기간·retirement, deduplication history의 복구·보관, faulty producer 재배정은 여전히 M1/M3/D4/P3 검증 대상이다. Map tag만으로 전환 전 블록과 전환 후 악의적으로 만든 stale-map 블록을 구분할 수 없다.

논문 §4.3과 Figure 3의 scheduling 그림, §3.2 재사용, §5 correctness, Evaluation·한계·review companion에 반영한다. 최종 ingress-to-certified-state latency가 핵심 지표이며, dynamic transition을 구현할 경우 중복 전송·speculation·복구 비용도 포함한다. 별도 대규모 fault benchmark를 추가하지 않는다. 이 기록은 구현 또는 검증 완료가 아니며 Google Docs는 변경하지 않았다.

## v13.19 구조와 범위 — family 모델은 유지, scheduling은 위 v13.20으로 갱신

**핵심 주장:** Overpass는 Autobahn-family consensus 위에서 pipelined execution과 operation-aware producer placement를 결합하여 state-finalization latency를 줄인다. Multimmit은 실제 구현과 세 primary benchmark의 기반이다. Family 명칭은 이 논문의 설계 범주이며 모든 quorum·cut 추출을 같게 취급하지 않는다.

1. **Introduction:** ordering 이후 노출되는 실행 지연 → dissemination/consensus와 실행 중첩 → late predecessor가 이득을 상쇄할 수 있음 → producer placement로 완화.
2. **Background and Motivation:** Autobahn의 certified cut과 Multimmit의 L-QC-derived prefix를 각각 설명한다. Membership finality, global ordered delivery, execution certification, durable readiness를 구분한다.
3. **Pipelined Ordering and State Finalization:** 공통 contract와 Multimmit native ordering을 설명한다. 기존 voting·extensions·sweep/anchor/halt는 유지하고 speculative execution의 검증·재사용을 연결한다. Canonical adoption은 exact emitted prefix·parent·runtime의 matching result를 요구한다.
4. **Reducing Re-execution through Producer Placement:** 기존 deterministic Multilevel grouping과 whole-tx producer assignment를 유지한다. 후보는 background에서 준비하되 native consensus가 metadata·activation을 묶어야 한다. 이번 수정은 optimizer 수식을 바꾸지 않는다.
5. **Correctness and Liveness:** 결과 유일성과 f+1 honest-witness 조건, 안전한 재사용, Byzantine behavior 및 조건부 진행을 구분한다. Cut vote가 같은 body·DAG·완료 결과를 보장한다고 주장하지 않는다.
6. **Evaluation:** 같은 Multimmit native profile과 application backend에서 Original / Pipeline / Pipeline + Placement. Native ordering을 유지한 same-order control, RTT × state operations, retry CPU·queueing·ingress-to-state latency를 측정한다.
7. **Related Work / Discussion / Conclusion:** ordering과 execution/placement의 기존 연구, 통합의 한계와 아직 검증되지 않은 성능을 명시한다.

### 이번에 추가한 빨간 검토 항목

- **M1 / P1:** native global ordered-prefix extraction/adapter와 논문–fork 버전 일치. Chain-local membership finality를 실행 순서 확정으로 오인하지 않는다.
- **M2:** common execution checkpoint와 eligible signer policy. 이전 Q(F) subset은 이식하지 않는다. f+1 threshold의 조건부 안전성은 유지되지만 서로 다른 prefix 길이의 서명을 합칠 수는 없다.
- **M3:** q_map > f의 실제 profile threshold, placement metadata binding, uncertified proposal/extension admission 검사와 native cut identifier. 활성화는 위 v13.20의 c+1 규칙을 따른다.
- **D4 / P3, E1 / E2:** online handoff·failed-producer reassignment와 실제 latency 이득은 여전히 미결이다.

[피드백용 한국어 정리](./overpass-family-multimmit-review.md)에 선택할 정책과 검증 항목을 분리했다. 기존 proof/PAC SDK·Commonware 코드·Google Docs는 변경하지 않았다.

## v13.18 구조와 범위 — 보관 기록

아래의 Q(F), n=3f+1 reference, 2f+1 sidecar 및 lane 회전 관련 규칙은 당시 설계이며 위 v13.19 Multimmit profile에 그대로 적용하지 않는다. 이력의 “현재/최신” 표현도 당시 시점으로 읽는다.

**2026-09-26 설명 보충:** [Cut vote, execution plan, Sync overlap 노트](./cut-vote-execution-view-note.md)를 Background와 pipeline 설명에 참조한다. 같은 cut 제안은 같은 실행 대상 prefix를 지정하며, 동일 누적 경계·ordering rule 아래 같은 block-level 계획을 정할 수 있다. Body와 state가 준비되는 대로 실행을 시작해 Sync·cut consensus와 겹치되, 모든 voter의 데이터 보유·transaction-level DAG·실행 완료 일치를 가정하지 않는다. 제안 변경과 exact-finalized-context 검증 의무는 유지한다. 이는 아래 draft의 signer 정책이나 기존 proof SDK를 바꾸는 갱신이 아니다.

권위 있는 현재 본문은 [영문 LaTeX draft](./research/paper/main.tex)다. 최상위 목표는 **tx ingress부터 certified state finalization까지의 E2E latency**이며, cut-to-state는 주로 최적화하는 세부 구간이다. Ingress는 배치·admission 전 최초 관측 시각이고 재전송으로 초기화하지 않는다. Durable read readiness는 별도 종료점이다.

**이번 편집:** OSDI 분량 확인용 USENIX 10pt 2단 형식을 사용한다. Sidecar는 준비→cut 선택→지연 활성화로 압축하고 Algorithm 1과의 중복을 제거했다. 비잔틴 대응은 입력·candidate/map 변경·결과 인증·가용성의 네 범주로 묶으며 핵심 정족수 논증은 본문에 둔다. Evaluation은 질문→설정/비교군 표→예정 결과 패널로 재구성했다. 실제 결과용 약 4페이지를 목표로 하며, 현재 계획 뒤에 결과를 단순 추가하지 않는다. 제출 학회 확정이나 구현·측정 완료를 뜻하지 않는다.

1. **Introduction:** E2E 목표 → 같은 cut의 ordering/execution pipeline → 재실행 비용 → 선언 기반 배치·grouping의 역할.
2. **Background and Motivation:** Autobahn의 DA·cut·실행 경계, cut 이후 노출되는 작업과 pre-cut 실행 기회. E2E와 cut-to-state 지표를 분리한다.
3. **Pipelined Ordering and State Finalization**
   - 3.1 Common Ordering and the Execution Pipeline
   - 3.2 Declared Accesses and Safe Reuse
   - 3.3 Transferring and Applying Certified Results
4. **Reducing Re-execution through Producer Placement**
   - 4.1 When Re-execution Consumes the Latency Gain: 늦은 선행 writer 예시, 정확한 복구와 낮은 복구 비용의 차이.
   - 4.2 Deterministic Grouping and Whole-Transaction Assignment: 공통 과거 확정 이력, operation-pair sensitivity, 실제 whole-tx 경로를 반영한 dependency/load/churn proxy, 매 갱신 기회의 deterministic hierarchy 재구성과 coarse-to-fine refinement.
   - 4.3 Placement Sidecar and Cut-Controlled Activation: 백그라운드 계산·검증·보관 인증, leader의 후보/KEEP 제안, 기존 전체 cut 선택, k+2 확정 뒤 적용과 미해결 handoff.
5. **Correctness and Liveness:** exact-context 인증과 설치, 배치 위반 거부, 잘못된 map·중복·검열·old certified block의 경계.
6. **Evaluation:** Original / Pipeline / Pipeline + Placement. 같은 admission 아래 grouped/ungrouped를 비교하고 hard/soft enforcement는 별도 비교한다. 과거 window로 계산해 다음 미관측 window에서 검증한다.
7. **Related Work:** Autobahn, 실행/인증·state transfer, Shard Scheduler와 TxAllo의 verifiable history-based allocation. State migration과 whole-tx producer 배치를 구분한다.
8. **Discussion and Limitations:** proxy의 한계, hot producer·계산/검증 비용, 미래 workload 변화, dynamic map activation·중복·faulty owner 재배정.
9. **Conclusion:** E2E 순이득을 기준으로 pipeline과 후속 최적화를 연결한다. 미측정 성능이나 완성되지 않은 진행성은 주장하지 않는다.

**별도 보조 문서:** [placement-supplement.tex](./research/paper/placement-supplement.tex)의 Appendix A에 hierarchy affinity·matching, 출력 encoding·bound 목록·인증서 필드와 connectivity/routing-cost 반례를 둔다. Appendix B는 state transfer·저장·복구 세부사항이다. Multilevel 근거, J=15→12 예시, 실제 목적함수·알고리즘, 인증과 crash-safe apply의 핵심 조건은 본문에 남긴다. 보조 문서 없이도 본문 논리가 성립해야 한다. 삭제했던 Evaluation fault-injection·unit-test 상세 절차는 복원하지 않는다. 본문·review companion의 빨간 메모 30개는 원문 그대로 유지한다.

### 실행 서명자와 cut-finality 증거

- 결과 인증에 첨부된 전체 cut-finality 증거 F로 2f+1명의 Q(F)를 정한다. 일반 경로는 CommitQC의 Confirm signer이며 Prepare quorum이 아니다. Native fast path는 먼저 3f+1 Prepare 전체로 finality를 검증한다. 유효 증거에 2f+1명을 넘는 voter가 있으면 고정 epoch 순서의 첫 2f+1명을 택한다.
- 동일 exact cut·parent·runtime·결과에 대한 직접 실행 signer 집합 E(C)에서 `|E(C) ∩ Q(F)| ≥ f+1`을 요구한다. 같은 epoch에 속했다는 이유만으로 Q(F) 밖 서명을 계수하지 않는다. Cut 투표 자체는 실행 완료 증거가 아니다.
- 같은 cut의 서로 다른 유효 F는 서로 다른 Q(F)를 가질 수 있다. 수신자는 첨부된 F로 모든 계수된 signer의 자격을 확인하며 first-seen Q를 강제하거나 signer 집합에 별도 합의하지 않는다. 실행 서명은 F 직렬화가 아니라 exact execution context에 묶어 cut 전 준비를 허용한다.
- Q(F) 내 충분한 정상 노드가 직접 실행·검증·보관을 마치고 서명을 제공해야 한다. 더 빠른 실행자가 Q(F) 밖에 있으면 인증이 늦어질 수 있다. 이 자격 제한은 기존 ordering threshold를 바꾸거나 추가 ordering round를 요구하지 않는다.

### 이번 배치 제안에서 확정한 서술

- 그룹은 placement metadata이며 state ownership이나 실행 barrier가 아니다. 여러 그룹에 걸친 tx도 전체를 하나의 producer에 배치한다.
- Read/read는 pairwise dependency 점수가 0이지만 read의 routing weight는 1이다. Writer와의 관계를 유지해야 한다. 조건부 try 연산은 무조건 호환으로 취급하지 않는다.
- 매 configured update opportunity에 새 공통 finalized-history window로 Multilevel hierarchy를 재구성한다. 모든 original scope의 incumbent 위치를 유지한 채 관련 scope를 coarse bundle로 묶고, bundle→producer 후보의 실제 whole-tx 배치·load·M0 대비 이동 비용을 평가한다. Uncoarsening 뒤 작은 bundle·singleton으로 refinement하여 기존 그룹도 나눌 수 있다.
- 최근 window에 없는 기존 scope도 원래 위치를 유지하며 임의 삭제·default hash 재배치를 하지 않는다. Split 자체는 producer 권한·state·기존 tx를 바꾸지 않으며 residence나 M0 대비 churn 기준도 초기화하지 않는다. 개선이 없으면 원래 map에 대한 KEEP이고, singleton metadata를 새 map으로 활성화하지 않는다.
- Split 후 확장된 scope 수·working metadata·candidate 탐색도 제한한다. Grouping은 매번 재계산할 수 있지만 매번 새 map이 활성화되는 것은 아니며, 불리한 hierarchy와 local optimum·계산 예산·residence로 유리한 변경을 놓칠 수 있다. Scope eviction과 온라인 handoff는 별도 미해결이다.
- 점수는 separated sensitive pairs + historical load concentration + 원래 map 대비 변경 비용이다. 입력 크기·group size·load·변경량·step budget, canonical tie-break와 checked integer arithmetic을 고정한다.
- 배치를 강제하려면 DA ACK 전에 authorized map/context와 tx별 producer를 검사한다. 최대 f Byzantine 아래 위반 블록은 f+1 서명을 만들 수 없다. 기존 DA가 이 검사를 자동 제공하는 것은 아니다.
- Sidecar의 2f+1 검증·보관 signer가 계산을 재현한다. Leader는 준비된 인증 후보 또는 KEEP을 제안하고, cut voter는 인증·authorized context를 확인한다. 계산·history fetch를 정상 cut 투표 경로에서 반복하지 않는다. Full cut k가 배치표와 적용 일정을 함께 확정하고 k+2 확정 뒤 새 구간을 시작한다. 준비가 안 된 후보를 기다리지 않으며 이미 확정된 활성화 일정은 후속 KEEP으로 취소하지 않는다.
- **D4/P3:** 적용할 map을 임의 선택하지 못하게 하는 권한 바인딩, old certified block 처리, pending tx 재배정, strict duplicate exclusion과 faulty producer 탈출은 아직 완성된 프로토콜이 아니다. Fixed-map profile을 먼저 평가하고 이 경계를 빨간 메모로 유지한다.
- 과거 v3 soft-routing의 자유로운 fanout을 hard-placement의 liveness 근거로 가져오지 않는다. [기존 모델](./state-affinity-placement.md)과 Commonware fork는 이번 문서 변경으로 구현이 바뀐 것이 아니다.

### Entity별 Byzantine 검토에서 추가한 경계

- **공통 fault budget:** producer/leader/DA voter/executor/collector를 겸한 노드는 하나의 validator identity다. 역할마다 f개를 독립 허용하지 않는다. Client·relay는 악성이어도 validator 투표권을 얻지 않는다.
- **Leader/planner:** history anchor·seed·버전·계수·tie-break를 prescribed configuration과 대조한다. Cut의 signed proposal·lock·view change·recovery가 map 또는 KEEP, prior-map digest와 적용 문맥을 함께 묶어야 한다. Tips만 서명한 인증서에 map을 붙이는 것으로는 부족하며 실제 adapter 연결은 D4다.
- **Map 은닉·KEEP 반복:** sidecar signer는 전체 입력·map을 검증·보관하기 전 서명하지 않는다. Cut voter는 유효한 준비 인증으로 선택을 검증할 수 있지만 block admission 전에는 map을 확보해야 한다. Local map 대체는 금지하고 KEEP 반복의 adaptation 지연·활성화 이후 복구·자원 격리는 D3/D4 조건으로 구분한다.
- **Producer/relay 중단:** ACK는 포함 증거가 아니다. 다른 lane의 ordering은 진행돼도 독점 배치된 tx는 영구 대기할 수 있다. Leader 교체가 producer 권한 이전을 자동 제공하지 않으며 D4/P3의 handoff가 필요하다.
- **Client 조작:** 과대 접근 선언·tx variant/ID 탐색·서로 다른 유효 거래로 과거 통계를 오염시키는 공격은 결정적 검증을 통과할 수 있다. Split-and-rebuild로 과거 그룹을 나눌 수 있게 했지만 지속적인 이력 오염이나 residence·이동 비용까지 없어지는 것은 아니다. 성능·공정성 보장으로 과장하지 않는다.
- **DA/실행 signer:** 올바른 admission 검사 아래 잘못된 producer 배치는 f+1에 도달할 수 없다. 실행 결과는 message domain·epoch membership·Q(F) 내부 자격·exact cut·parent history·outputs를 검사하며 같은 root만으로 같은 이력/결과라고 보지 않는다. DA는 fork 방지나 application 성공 증거가 아니다.
- **Collector/data/read server:** collector 한 명의 은닉으로 전체 수집이 멈추지 않도록 endorsement discovery가 필요하며 D2/P3로 남긴다. Delta 변조는 commitment·staging 검사로 거부한다. 정상 제공자와 영구 단절되면 readiness는 보장하지 않는다. 임의 RPC 답변이나 최신 상태라는 주장은 state certificate만으로 인증되지 않는다.

### 구조 선택의 근거

**Multilevel 선택 근거:** tx의 plurality routing은 작은 scope 이동에 경로가 바뀌지 않는 구간이 있다. Strict-improvement greedy가 중간 이동을 거부할 때 coarse bundle의 공동 이동이 다른 경로를 탐색하고, fine refinement는 과도한 결합을 다시 나눈다. [KaHyPar / JEA 2022](https://arxiv.org/abs/2106.08696)와 [deterministic parallel hypergraph partitioning / ACDA 2025](https://arxiv.org/abs/2504.12013v2)는 구조와 결정성의 선행 근거이지 우리 목적함수·latency의 우월성 증명이 아니다. 본문에 1~2 scope 이동은 J=16/17로 나빠지지만 3-scope 공동 이동은 J=15에서 12로 개선되는 정규화 예를 넣고, 기존 greedy를 비교군으로 남긴다. 실제 배치 평가는 original scope의 표 수·whole-tx 경로·tx load를 보존하며 native hyperedge cut 점수로 대체하지 않는다.

**Sidecar 그림:** [placement-sidecar.tex](./research/paper/figures/placement-sidecar.tex)는 공통 확정 이력 → 계산 → 검증·보관 → 2f+1 인증 → leader 제안과, full cut k 선택 → k+1 준비 → k+2 확정 후 새 배치 구간을 구분한다. 늦은 노드는 임의 구 map 대신 복구해야 하며, 두 cut 대기가 old certified block·pending tx를 소진한다는 주장은 하지 않는다. 별도 ingress coordinator나 독립 side-finality 엔진은 도입하지 않는다.

기본 설계 뒤 남는 비용을 제시하고 그 비용을 줄이는 확장을 설명하는 구성을 따른다. Autobahn은 §5.4에서 sequential slot의 대기를 설명한 뒤 parallel multi-slot agreement를, §5.5에서 추가 최적화를 설명한다. Anthemius는 Architecture 다음 Block Construction으로, TxAllo는 Design Challenges 다음 알고리즘으로 전개한다. 독립 절 여부는 보편적 형식 규칙이 아니라 설명량에 따른 선택이며, 현재 draft에서는 grouping·검증·변경의 설명량 때문에 Section 4를 분리한다.

[Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf), [Anthemius](https://fc25.ifca.ai/preproceedings/115.pdf), [TxAllo](https://arxiv.org/pdf/2212.11584).

---

## v13.12 상세 작성 메모 — 아래는 이전 구조의 보관 기록

아래의 기존 §3.3/§3.4, soft placement·fanout, cut-to-state를 최상위 목표로 둔 서술은 **2026-09-23 현재 draft의 제안으로 적용하지 않는다.** Cut 투표자 밖 실행 signer를 허용한 설명과 §5.5의 상세 fault-injection 계획도 과거 기록이며 최신 규칙·평가 범위가 아니다. 아래 보관 본문은 수정하지 않는다. 최신 절 번호·역할·서명자 자격·미해결 의무는 위 v13.18 구조와 영문 본문을 따른다.

이 개요는 최근 논의를 반영한 새로운 논문 방향이다. 기존 proof-aware protocol/SDK의 state isolation, validity proof 및 PAC 설계를 그대로 설명하는 문서가 아니다. 기존 fork 구현을 이 방향으로 이행한 것으로 간주하지 않는다.

이번 v13.12 변경은 §4에 Byzantine behavior를 사례별로 설명하고, §5.5에 n=4, f=1의 작은 검증 harness와 제한된 late-predecessor 실험을 추가한다. DA 인증, ordering finality와 실행 결과 인증이 서로 다른 사실을 보장함을 구분하며 공격 아래의 무조건적인 latency 보장을 주장하지 않는다. 기존 **state finalization 지연 감소라는 목표 → 공통 ordering의 사전 적용과 실행 pipeline·exact-cut 인증 → 재실행 비용에 의한 이득 상쇄·역전 가능성 → 선언된 state 접근·operation에 따른 producer 배치**의 흐름은 유지한다. STM은 벤치마크 backend이며 설계 축이나 기여가 아니다. 정족수는 순수 Autobahn의 n=3f+1 reference model이며, Multimmit n=5f+1 모델과 통합하지 않는다. 기존 protocol/SDK와 fork는 수정하지 않는다.

## 논리 전개와 연구 질문

**핵심 과제와 최종 목적은 ordering cut이 확정된 뒤 application state가 최종 확정되기까지의 latency를 줄이는 것이다.** 빠른 ordering만으로는 state가 확정되지 않으며, cut 이후에 실행을 시작하는 직렬 경로에서는 실행·결과 인증 비용이 그대로 남는다. STM 활용이나 새로운 실행엔진 개발 자체가 해결할 문제가 아니다.

**첫 번째 해결 방법은 공통 ordering rule의 사전 적용과 실행 파이프라인화다.** 같은 cut의 DA·ordering과 execution·결과 인증 준비를 겹친다. Finalized cut과 canonical parent가 정해지면 최종 입력·순서와 양립하는 계산만 재사용하고 필요한 부분을 보정하여 cut 이후 남는 작업을 줄인다. 이는 특정 실행기 내부 알고리즘이 아니라 합의와 실행을 연결하는 설계다.

**그 방법에서 생기는 후속 과제는 재실행 비용이 원래 줄이려던 latency를 다시 늘릴 수 있다는 것이다.** 다중 producer의 늦은 선행 block과 candidate 변경이 기존 실행을 반복 무효화하면 정확성을 복구하더라도 잔여 실행량과 자원 경합이 커진다. 그 비용은 pipeline의 latency 이득을 상쇄하거나, workload에 따라 cut 이후 실행하는 baseline보다 더 느리게 만들 수도 있다. 이는 특정 실행기의 결함이나 항상 발생하는 현상이 아니라 검증할 성능 위험이다.

**이를 해결하기 위해 transaction에 명시된 state 접근·operation과 공통 ordering rule을 이용한 producer 배치를 추가한다.** 서명된 보수적 선언과 runtime 접근 범위 강제는 이 설계의 입력이다. 순서에 민감한 관련 입력이 서로 다른 시점에 도착해 불필요한 재실행을 일으킬 기회를 줄이는 것이 설계 가설이다. 선언은 접근할 state를 알려줄 뿐 실제 값이나 성공 여부를 미리 알려주지 않으며 재실행을 없애지도 않는다. 배치의 목표는 특정 실행기를 최적화하는 것 자체가 아니라, 재실행 비용으로 잃을 수 있는 state-finalization latency 이득을 보존·확대하는 것이다. 재실행 감소가 queueing 비용을 포함한 최종 latency 감소로 이어지는지는 실험으로 확인한다.

벤치마크에서는 STM(Software Transactional Memory) 계열의 Block-STM + Aggregators V2를 동일 실행 backend로 사용할 계획이다. 이는 평가의 통제 변수이자 구현 선택이며 pipeline의 필수 전제나 논문의 기여가 아니다. 새로운 STM·VM을 제안하지 않으며, 모든 실행기에 수정 없이 적용되거나 항상 성능이 좋아진다는 주장도 하지 않는다.

이 latency 목표를 위한 **합의 엔진의 변경**은 공통 serialization rule, 그 규칙의 사전 적용과 실행 연결, state·operation 기반 producer 배치 및 exact-cut 결과 인증의 결합을 뜻한다. 기존 Autobahn의 BFT cut 합의·Prepare/Confirm·view-change 안전성 핵심을 새로운 투표 알고리즘으로 교체한다는 뜻은 아니다. 실행 계층에는 최종 확정 문맥에 대한 올바른 결과와 안전한 speculative 결과 재사용을 요구한다. 선택한 backend에 연결하는 adapter의 정확성은 별도로 검증하며, backend의 concurrency-control 알고리즘이나 VM·aggregator 의미를 기여로 제안하지 않는다.

여기서 cut 확정은 ordering 합의의 결과이며, 그 뒤의 순서 구성은 선택된 입력에 결정적 실행 규칙을 적용하는 과정이다. 별도의 ordering 합의가 한 번 더 있다는 뜻이 아니다. 또한 이전 cut의 실행과 다음 cut의 합의를 겹치는 throughput pipeline만을 뜻하지 않는다. **동일 cut에 대한 합의와 실행 준비를 중첩해 그 cut의 state finalization을 앞당기는 것**이 핵심이다.

```text
비교할 직렬 경로:
  cut 확정 -> 실행 순서 구성 -> 실행 -> 결과 인증 -> state finality

제안 경로:
  cut 합의 진행과 순서 구성·사전 실행·결과 인증 준비를 중첩
  -> cut 확정 -> 필요한 보정·잔여 인증 -> state finality

실행이 늦은 노드:
  ordering finality + f+1 일치 실행 결과 인증 확인
  -> 인증된 state 변경 데이터 fetch -> 문맥·데이터 검증
  -> exact parent에 apply -> root 확인·durable publish -> read readiness
```

회전형 라운드로빈, conflict DAG, read-validation recovery와 f+1 matching signatures는 이 목적을 구현하는 수단이다. 사전 실행은 speculative이며 cut·parent·결과 인증 조건을 갖추기 전에는 canonical state가 아니다. State 데이터의 durable apply와 read readiness는 별도로 측정한다.

1. **핵심 과제:** 빠른 ordering 뒤에도 남는 cut-to-state-finalization latency를 줄인다.
2. **첫 번째 해결 방법:** 공통 ordering rule을 사전 적용하고, 같은 cut의 DA·ordering과 execution을 중첩한다.
3. **확정 방식:** n=3f+1에서 기존 2f+1 기반 전체 cut 확정 절차를 유지하며, exact cut·parent·runtime의 결과에 대한 f+1 일치 서명으로 state 결과를 인증한다.
4. **정확성 경계:** 최종 입력·순서·parent에서 유효한 결과만 재사용하며, 관측이나 의존성이 달라지면 무효화·재검증·필요한 재실행을 수행한다. 이는 실행기 선택과 무관한 요구 조건이다.
5. **후속 문제:** speculative 결과의 재실행 비용이 pipeline의 이득을 상쇄하거나 state finalization latency를 오히려 늘릴 수 있다.
6. **추가 해결 방법:** signed state·operation 선언과 이미 도입한 ordering rule을 함께 이용해 producer에 배치한다. 재실행을 줄여 원래의 latency 목표를 달성하려는 설계이며, 새 ordering policy를 추가하거나 state ownership을 분할하는 것이 아니다.
7. **결과 공유:** 실행 결과 인증에 참여하지 못했거나 뒤처진 노드는 인증된 delta를 받아 검증·적용한다. Application transaction 재실행은 필수가 아니며, 데이터 복구가 불가능할 때 사용할 fallback이다. Result certification과 read-serving readiness는 구분한다.

앞부분에서 강조할 세 숫자의 의미는 다음과 같다.

| 구성 | 의미 |
|---|---|
| n=3f+1 | 최대 f Byzantine 아래의 reference validator 구성 |
| 2f+1 기반 ordering finality | 일반 경로의 Prepare 2f+1 **및 Confirm 2f+1**을 거친 CommitQC. Fast path는 n=3f+1 Prepare |
| f+1 matching execution signatures | 동일한 exact cut·canonical parent·규칙·전체 결과에 최소 한 정상 검증자의 서명이 있음을 보장 |

이는 `2f+1 Prepare + f+1 execution`으로 Confirm을 대체하거나, ordering quorum을 f+1로 낮추는 주장이 아니다. Ordering과 result certification은 서로 다른 사실을 인증한다. 실행 서명자는 cut 투표자 집합에 한정할 필요는 없지만, 같은 epoch의 validator이고 전체 결과를 실제 실행·검증해야 한다. 같은 cut이 확정되어도 모든 투표자가 이미 같은 block bodies나 완료된 실행을 가지고 있는 것은 아니다. [Autobahn §5.2](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf), [PBFT §4](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/01/p398-castro-bft-tocs.pdf)

핵심 논증은 다음과 같다. 전체 ordering finality와 canonical parent가 실행 입력 I를 고정하고, 결정적 실행은 유일한 결과 R*=Exec(I)를 정한다. (I,R)에 대한 f+1 일치 서명에는 정상 실행자가 최소 한 명 있으므로 R=R*다. 다른 노드는 이 인증이 묶은 변경 데이터를 적용할 수 있다. **사전 ordering rule은 f+1이라는 임계값을 새로 가능하게 하는 것이 아니라, 인증할 결과의 계산을 cut 이전으로 옮기는 수단**이다. Result transfer 자체 역시 독립적인 최초성 주장이 아니라 pipeline의 결과를 늦은 노드가 활용하는 경로다.

연구 질문:

> Autobahn 계열 합의에서 cut 확정 이후 state finalization까지의 latency를 어떻게 줄일 수 있는가? 공통 ordering rule과 실행 pipeline으로 실행을 앞당기되, 그 이득이 재실행 비용으로 상쇄되지 않도록 선언된 state 접근·operation에 따른 producer 배치를 어떻게 설계할 것인가?

기여 후보는 (a) **cut-to-state-finalization latency를 줄이기 위한 ordering/execution pipeline**: 공통 ordering의 사전 적용·실행·exact-cut 결과 인증을 연결하는 합의 엔진 설계, (b) **재실행으로 latency 이득이 상쇄되는 문제를 줄이는 operation 기반 producer 배치**: 선언된 state 접근·operation과 ordering priority를 결합하는 후속 설계, (c) 같은 실행 backend 아래 정확성을 보존하면서 latency 이득과 재실행·queueing·전송 비용을 규명하는 평가다. 인증된 state 전달·적용은 늦은 노드가 결과를 사용하는 경로다. Block-STM·Aggregators V2는 평가 구현에 사용할 backend일 뿐 별도 기여가 아니다. Round robin, DAG, speculative execution, f+1 matching signatures, access declaration이나 authenticated state transfer 각각을 새로운 발명으로 주장하지 않는다.

## 1. Introduction

### 1.1 문제: 빠른 ordering만으로 application state가 준비되지는 않는다

- Autobahn의 강점인 병렬 전파와 빠른 cut 확정을 먼저 설명한다.
- Cut 확정 뒤에 실행 순서 구성·execution·결과 확인을 시작하는 직렬 경로에서는 그 비용이 state finalization의 critical path에 남는다는 문제를 제기한다.
- 논문의 목적은 **cut-to-state-finalization latency 감소**다. 공통 ordering과 execution pipeline, 이를 보완하는 선언 기반 producer 배치가 제안 설계다. STM은 구현 환경에서 사용할 실행 backend로만 다룬다.
- 상태 동기화와 durable apply는 인증된 결과를 사용자가 실제로 읽기까지 남는 추가 지연으로 구분한다.
- 기존 연구가 execution을 전혀 다루지 않았다는 주장은 하지 않는다. 특정 backend 선택보다 latency 문제와 이를 줄이는 합의·실행 연결을 먼저 설명한다.
- 부하 증가 시 cut-to-state gap이 커지는지는 실험으로 보여줄 가설이다. 측정 전 사실처럼 단정하지 않는다.

### 1.2 첫 번째 해결 방법: ordering/execution pipeline

- 기존에도 deterministic zipping이 있다는 점을 인정한다. 기여는 결정론 자체가 아니라 **공통 ordering의 사전 적용과 DA·ordering·execution의 중첩**, 그리고 그 구조에 맞는 producer 배치에 둔다. Reference RR rule은 native zip과 순서가 달라질 수 있으므로 규칙 변경과 적용 시점 변경을 구분한다.
- 공통 RR 순위로 수신한 blocks의 기준 순서를 구성해 같은 cut의 전파·합의와 실행을 겹친다. Leader는 cut 포함 대상을 제안하지만 임의의 실행 스케줄을 제안하지 않는다.
- n=3f+1 구성, 기존 2f+1 기반 전체 ordering 확정 절차, f+1 일치 실행 결과 서명의 역할을 앞에서 제시한다.
- 실행과 조건부 결과 서명을 먼저 준비하고, exact finalized cut 및 canonical parent와 일치할 때만 state-final로 채택한다.
- 같은 확정 입력의 결과는 유일하고 f+1에는 정상 실행자가 최소 한 명 있다는 논증을 소개한다. Cut에 투표한 2f+1 모두가 이미 같은 실행을 끝냈다는 주장이 아니다.
- 모든 노드의 재실행 완료를 기다리지 않는다. 인증에 참여하지 못한 노드는 인증된 state 변경 데이터를 받아 검증·적용할 수 있다. 노드별 apply와 read readiness는 여전히 별도다.
- 공통 ordering은 pre-cut 입력의 완전성을 보장하지 않는다. 검증·복구가 필요한 speculative pipeline임을 함께 밝힌다.

### 1.3 사전 실행의 후속 비용과 선언 기반 배치

- 최종 입력·순서·parent와 일치하지 않는 speculative 결과는 그대로 채택할 수 없다. 안전한 재사용과 필요한 재실행은 실행 계층에 대한 요구 조건이며 특정 backend의 내부 구현을 핵심 설계로 소개하지 않는다.
- Multi-producer 입력을 cut 전에 실행하면 late predecessor 등의 영향으로 재실행이 반복될 수 있다. 재실행 비용이 커지면 원래 줄이려던 state-finalization latency가 오히려 늘어날 수 있다. 이는 Autobahn이나 특정 실행기의 결함이 아니라 제안한 방법에서 발생할 수 있는 후속 문제다.
- 이를 해결하기 위해 선언된 state·operation과 공통 ordering rule을 결합한 producer 배치를 추가한다. 재실행 수 감소 자체가 아니라 최종 latency 이득을 보존·확대하는지 평가한다.
- 평가 순서도 Original → Pipeline → Pipeline + Placement로 맞춘다. 수치는 검증 전 가설이며 ordering을 늦춰 cut-to-state gap만 줄이는 결과는 개선으로 보지 않는다.

**배치 의도:** 문제 → 핵심 pipeline·결과 인증 → 안전한 재사용 조건 → 남는 비용 → 선언 기반 배치 최적화 순서다. 접근 선언은 핵심 설계 입력이지만 latency 문제를 대신하는 동기는 아니며, 실행 backend 선택은 Evaluation에서 설명한다.

## 2. Background and Motivation

### 2.1 Autobahn의 cut과 application execution 경계

- Data lanes, certified tips, leader의 cut 제안, 전체 Prepare/Confirm 및 fast path를 설명한다.
- 정상 경로 n=3f+1, Prepare 2f+1, Confirm 2f+1과 별도의 execution signatures를 구분한다.
- 기존 committed cut 이후 deterministic zip 및 data recovery 경계를 설명한다.
- Parallel slots에서 raw cuts가 non-monotonic할 수 있으므로 누적 처리 경계와 새 occurrences를 정의해야 함을 짚는다.
- Multimmit은 관련 확장 및 가능한 artifact 선택지로만 소개한다. n=5f+1의 tip 추출을 현재 Autobahn 기준 모델에 섞지 않는다.

### 2.2 측정할 문제: post-cut execution과 state readiness

- Cut 이후 실행·결과 인증을 시작하는 baseline에서 노출되는 시간을 분해한다. 부하·state 변경 횟수에 따라 backlog가 커지는지는 실험으로 확인한다.
- 결과가 인증되어도 데이터 전송과 durable apply가 끝나지 않으면 사용자가 읽을 수 없다. Certified state finalization과 read readiness를 별도 지표로 정의한다.
- Ordering DA는 transaction input의 가용성이지 실행 이후 생성된 delta의 가용성은 아니다. 뒤처진 노드가 모든 finalized backlog를 재실행하는 비용과, 인증된 변경 데이터를 받아 적용하는 비용을 구분한다.
- 같은 balance/nonce를 서로 다른 producer lanes의 tx가 건드릴 수 있음을 설명한다. Producer chain은 state ownership shard가 아니다.

### 2.3 관찰: cut 전에 이미 블록 데이터가 전파된다

- 블록 수신과 cut 확정 사이의 시간을 실행에 활용할 수 있다는 기회를 제시한다.
- 공통 rule은 도착 순서와 무관한 기준 순서를 제공하지만, 어떤 blocks가 최종 포함되는지까지 미리 확정하지는 않는다.
- 이 단계에서는 speculative 실행과 최종 검증이 필요하다는 경계만 설명한다. 결과 무효화·재실행 비용과 선언 기반 배치의 구체적 동기는 §3.2 이후에 전개한다.

**배치 의도:** post-cut latency 문제와 pre-cut 실행 기회를 먼저 납득시킨다. 재실행 감소를 논문의 최초 문제나 독립된 핵심 목표로 앞세우지 않는다.

## 3. System Design

### 3.1 Common ordering and execution pipeline

**최소 system model:** 고정 위원회 n=3f+1, 최대 f Byzantine, 인증된 메시지와 결정적 application을 가정한다. Validator는 합의·실행 검증 참여자이고 producer lane은 블록 생성 chain이다. 한 노드가 두 역할을 수행할 수 있지만 lane을 state owner로 정의하지 않는다. 접근 선언과 안전한 재사용은 §3.2에서, 이 선언을 이용한 placement는 §3.4에서 설명한다.

**합의 엔진과 실행 계층의 책임 경계:** 기존 cut 합의는 어떤 입력이 canonical한지 결정한다. 제안하는 합의 계층은 공통 순서의 사전 구성·producer 배치·실행 시작 시점과 exact-cut 인증 연결을 담당한다. 실행 계층은 주어진 문맥의 결정적 application semantics를 계산하고, 후보 변경 뒤 결과가 유효한지 검증하거나 다시 실행한다. Adapter는 후보 문맥과 결과의 재사용 경계를 연결한다. 특정 병렬화·concurrency-control 알고리즘은 요구하지 않으며, 실행 correctness를 ordering vote 자체가 대신 검증하지 않는다.

**공통 순서:**

- 고정 lane 목록을 slot index에 따라 회전한다. Relative block height를 먼저, 해당 slot의 lane priority를 다음으로 비교한다. Block 내부 tx 순서는 고정한다.
- Relative height의 anchor는 이미 ordering된 누적 lane boundary다. 실행 완료 높이가 아니며, parallel slots의 중복 occurrences는 canonical history에서 제거한다.
- Leader는 기존 절차에 따라 cut 포함 대상을 제안한다. 별도의 leader-selected execution policy는 없지만 leader의 합의 역할이 사라지는 것은 아니다.
- 같은 exact cut·누적 경계·parent·rule에서 같은 기준 block order와 serial semantics를 얻는다. 같은 local 수신 집합이나 완료 시점까지 보장하지 않는다.
- 기존 native zip을 제안한 serialization rule로 바꾸는 semantic change를 명시한다. 단순히 Autobahn의 기존 순서를 더 일찍 계산했을 뿐이라고 주장하지 않는다.

**네 lane 그림:** [편집 가능한 TikZ 그림](./research/paper/figures/uneven-lane-order.tex)을 영어 본문 §3.1에 넣는다. 예시의 설정된 lane 목록은 `[D,C,B,A]`이며 초기 회전의 **방문 순서 D → C → B → A**를 표시한다. 누적 ordering 경계 A100/B20/C7/D40 이후 cut이 A103/B21/C9/D44를 선택하면, 상대 높이별로 읽은 순서는 `D41 → C8 → B21 → A101 → D42 → C9 → A102 → D43 → A103 → D44`다. 빈칸은 확정 cut의 미선택 위치이지 선택됐으나 body가 미수신된 block이 아니며, 화살표는 기준 순서이지 실행 barrier가 아니다. 숫자 rank의 비교 방향이나 기존 회전 함수를 변경하는 그림이 아니다.

**중첩할 작업:**

1. 자신의 block 생성·전파.
2. 다른 block 수신·검증·DA/ordering vote.
3. 수신한 block을 공통 순서에 insert/append하고 후보 실행 문맥 갱신.
4. 준비된 tx 실행·재검증·필요한 재실행과 조건부 결과 서명 준비.

작업 사이의 데이터 의존성은 유지하되, 실행 완료를 DA/ordering vote나 다음 block 생성의 선행조건으로 만들지 않는다. 아직 수신하지 못한 모든 lane을 기다리는 전역 barrier도 두지 않는다. Candidate cut이 오면 그 exact set의 준비를 앞당기지만, cut 이전의 overlay는 canonical state가 아니다.

**Ordering finality와 실행 결과 인증:**

- 일반 경로는 2f+1 Prepare와 2f+1 Confirm으로 CommitQC를 만들며, native fast path는 n=3f+1 Prepare를 사용한다. 실행 서명은 어느 합의 단계도 대체하지 않는다.
- 전체 결과를 직접 실행·검증한 validator가 domain/chain/epoch/slot, exact cut 및 ordered input digest, 누적 경계, canonical parent의 인증된 문맥, scheduling/runtime version, materialized state와 status/events/fee 및 delta commitments를 서명한다. 원본 signer와 전체 signed subject를 유지해 다른 chain·cut·parent의 결과가 섞이지 않도록 한다.
- f+1 일치 서명에는 정상 signer가 최소 하나 있으므로, 같은 결정적 입력의 결과를 인증할 수 있다. Quorum intersection으로 새로운 순서를 선택하는 논증이 아니다.
- 논증 순서는 **입력 확정 → 올바른 결과의 유일성 → f+1 중 정상 signer 존재 → 결과 인증**이다. 정상 노드들의 내부 worker schedule·재실행 횟수는 달라도 된다. Cut 투표 그 자체는 실행 완료 증거가 아니다.
- 실행과 서명은 cut 전에 조건부로 준비할 수 있다. **해당 subject와 정확히 일치하는 전체 ordering finality와 canonical parent 연속성을 확인한 이후에만** state-final로 채택한다. 후보가 바뀌면 다른 subject이며 서명을 전용하지 않는다.
- 정의: `StateFinal(C) = ValidOrderingFinality(C) AND CanonicalParentMatches(C) AND MatchingExecutedResultSignatures(C) >= f+1`. 서명된 결과의 delayed 값은 모두 구체화되어 있어야 한다.
- f+1 결과가 아직 없으면 필요한 실행·서명 수집이 cut 이후에 남는다. 항상 cut과 동시에 state-final이 된다는 보장은 없다. f+1명을 고정 실행 위원회로 지정하고 나머지는 무조건 대기시키는 모델이 아니며, withholding을 고려해 충분한 정상 노드가 실행·서명할 수 있어야 한다.
- 실행 signer는 signed commitment와 일치하는 구체화된 delta·transaction outputs를 서명 전에 durable하게 보관하고 복구 요청에 제공한다. 단순 root 서명이나 기존 input DA만으로 post-state data custody가 따라온다고 가정하지 않는다. 상세 retention/fetch 조건은 §3.5에서 설명한다.
- 결과 인증에 참여하지 못한 노드는 §3.5의 검증·apply 경로를 따른다. 인증서와 데이터를 전달받아 적용했다는 이유만으로 같은 결과의 새로운 **직접 실행 서명**을 만들지는 않는다. 원본 f+1 실행 서명은 그대로 전달할 수 있다.

**연결 문장:** 이 구조는 실행을 앞당길 기회를 제공한다. 다음으로, 미확정 입력을 실행하면서도 최종 cut과 같은 결과를 얻는 방법을 설명한다.

### 3.2 Declared accesses and safe reuse

**선언된 실행·배치 입력:**

- Tx는 signed conservative state/object 접근 범위와 지원되는 operation 종류를 담는다. Nonce·fee 등 공통 implicit 접근을 고정 schema로 보강한다. 배치 정보를 얻기 위한 별도 사전 실행은 요구하지 않는다.
- 일반 read/write와 application이 지원하는 지연 갱신·정확한 읽기·조건 의존성을 요약한다. 연구 메모의 R/W/Defer는 이 요약이지 새로운 VM instruction set이 아니다. 선택한 평가 backend의 aggregator/snapshot 대응은 §5.1에서 설명한다.
- 실제 scope/mode가 선언 안에 있는지 runtime이 접근 수행 전에 강제한다. 선언은 접근 권한, 성공 여부, 실제 분기·값 또는 무충돌의 증거가 아니다. Sui식 명시 입력에서 영감을 받되 완전한 flat storage-access list를 Sui의 보장으로 인용하지 않는다.

**결과 재사용·무효화 조건:**

- 이 절은 실행기 내부 알고리즘 대신 §3.1 pipeline이 결과를 재사용하거나 무효화하는 조건을 정의한다. 순차 실행기·DAG scheduler·STM 등 어떤 구현이든 최종 cut의 결정적 순차 의미와 같은 결과를 제공해야 한다.
- Block이 ordering 단위지만 실행 결과의 보관·검증·재실행 단위는 tx로 둘 수 있다. Block-level conflict 요약을 전체 block 완료 barrier로 강제하지 않는다.
- 결과는 transaction occurrence·프로그램 및 runtime version·candidate 입력과 순서·parent 문맥에 묶는다. Candidate 변경만으로 모든 계산을 무조건 버리지는 않되, 변경된 문맥에서 해당 결과가 유효하다는 검증 없이 재사용하지 않는다.
- 결과에 영향을 준 실제 읽기·조건 판단·관측 위치가 최종 선행 effects와 양립해야 한다. 선언된 접근 범위만 같다는 이유로 결과가 같다고 판단하지 않는다. 지원되는 지연 갱신이 있다면 조건·snapshot 의미를 보존하고 인증 전에 출력과 state를 구체화한다.
- 늦은 선행 writer의 삽입, 기존 predecessor의 cut 제외, parent 변경으로 관측이 달라지면 해당 tx 결과를 무효화하고 필요한 재실행을 수행한다. 영향받을 수 있는 후속 tx는 재검증하고 독립적이거나 유효성이 확인된 결과는 유지한다.
- 인증 대상은 state root만이 아니라 status/events/fee 및 실패 tx의 effects까지 포함한 전체 결과다. 구현상의 retry 횟수가 canonical gas나 application 결과를 바꾸지 않아야 한다.
- 이전 candidate의 늦은 작업 완료가 새 문맥의 결과로 publish되거나 이미 설치한 state를 덮어쓰지 못하게 한다. Stable occurrence·generation 등 구체적 구현은 §5.1에서 선택한 backend adapter에 대해 검증한다.
- 재사용 검증이 불확실하거나 자원 한도를 넘으면 해당 작업을 최종 cut 기준으로 다시 실행한다. 안전한 검증·복구는 기본 pipeline의 필수 구성이지 §3.4 placement를 켰을 때만 제공하는 기능이 아니다.

**연결 문장:** 최종 입력에 맞게 결과를 복구하면 정확성을 지킬 수 있다. 그러나 복구가 정확하다는 사실과 복구 비용이 작다는 사실은 다르다.

### 3.3 Remaining cost: re-execution under multi-producer arrivals

- 제안한 pre-cut pipeline에서는 여러 lane의 blocks가 서로 다른 시점에 도착한다. 공통 rank가 있어도 아직 없는 선행 writer의 효과는 알 수 없다.
- 예: 기준 순서는 writer X → reader Y지만 Y의 block이 먼저 도착한다. Y가 이전 값을 읽고 실행한 뒤 X가 들어오면 Y의 관측을 검증하고 필요하면 재실행한다. 무관한 Z의 결과는 유지할 수 있다.
- 여러 writer가 늦게 들어오거나 후보에서 제외되면 같은 reader가 반복 무효화될 수 있다. 알려진 dependency 대기는 도움이 되지만 아직 수신하지 않은 predecessor까지 해결하지 않는다.
- 선언된 read/write 범위와 지원되는 지연 갱신이 있어도 정확한 읽기·상하한 조건 변화·overwrite 경계는 남는다. 모든 shared-state 접근을 무충돌 합산으로 치환할 수 없다.
- 이 비용은 Autobahn 자체의 안전성 문제나 기존 post-cut 실행의 필연적 오류가 아니다. **다중 producer 입력의 pre-cut 실행으로 latency를 줄일 때 발생할 수 있는 후속 비용**이다.
- 가설: 연관 입력의 분산과 도착 불일치로 재실행이 커지면 cut 이후 잔여 작업과 총 CPU가 늘어 pipeline의 이득이 감소하거나 역전된다. RTT·충돌률·late writer 실험으로 검증하며, 재실행으로 state-finalization latency가 오히려 늘어나는 조건도 보고한다.

**연결 문장:** 복구 알고리즘을 더 복잡하게 만들기 전에, 같은 공통 ordering rule을 producer 배치에도 활용해 불필요한 무효화의 발생 기회를 줄인다.

### 3.4 Ordering-aware state and operation placement

**배치 입력:** §3.2의 signed state 접근·operation 선언과 고정 schema를 그대로 사용한다. 배치만을 위한 추가 사전 실행이나 별도 접근 의미를 도입하지 않는다. 선언 기반 순서 민감성은 후보 producer 선택에 쓰이며 실행 결과의 유효성을 대신 증명하지 않는다.

**공통 ordering을 활용한 producer 선택:**

- State affinity와 operation에 따른 순서 민감성을 함께 반영한다. 여러 state를 건드려도 **whole tx 하나**를 producer에 배치하며 state ownership이나 cross-lane fragments를 도입하지 않는다.
- 기존 §3.1의 priority를 재사용한다. 새 leader scheduling policy가 아니다. 논리 state 위치는 고정하고 선호 physical producer를 slot별 priority와 같은 순열로 회전한다.
- 배치 목표 q는 연속 finalized prefix h의 다음 slot이다. 아직 정해지지 않은 candidate cut·anchor·실행 결과·로컬 mempool 부하를 후보 순위 입력으로 쓰지 않는다. q와 실제 포함 k는 다를 수 있다.
- `aggregate(A), aggregate(B), W(C)`와 `aggregate(A), R(C), R/W(E)`를 예로 들어, 단순 shared key 수가 아니라 C의 순서 민감성을 고려할 동기를 설명한다. 실제 후보 순위는 [배치 spec](./state-affinity-placement.md)의 scope 위치·점수·tie-break를 따른다. 모든 multi-key tx가 같은 producer를 고른다고 보장하지 않는다.
- 관련 tx의 조기 동시 확보와 알려진 선행 writer/조건 의존성의 scheduling을 연결한다. 실행 backend의 자체 의존성 대기와 추가 선언 기반 선행 작업 대기를 구분한다. 후자의 효과는 배치와 별도로 ablate한다.

**전달과 한계:**

- 미포함을 결정한 producer는 다음 후보로 전달한다. 원본을 보관한 sender/relay는 H finalized cuts 뒤 모든 후보에 재전파한다. 새 quorum은 없으며 ACK·새 attempt가 pending age를 초기화하지 않는다.
- Soft preference이므로 권장 lane과 달라도 기존 유효 block을 거부하지 않는다. 이미 생성된 block은 옮기거나 수정하지 않고, 중복은 canonical replay/status/fee 규칙으로 처리한다.
- 같은 lane·같은 block·재실행 0회는 보장하지 않는다. Rotation 자체는 같은-slot colocation/conflict 수를 개선하지 않으며 physical 역할만 바꾼다. Hot lane, multi-key tie, queueing과 cut 경계 효과를 평가한다.
- 메커니즘 가설은 **관련 입력의 도착 불일치와 불필요한 추측 실행 감소**다. 재실행 CPU 감소와 state-finality latency 감소를 각각 측정하며 일반적인 성능 보장으로 표현하지 않는다.

### 3.5 Certified state transfer and installation

**누가 무엇을 전달하는가:** 실행을 마친 validator들이 **같은 cut 전체의 결과**를 인증한다. 이는 f+1개의 서로 다른 block 결과나 lane-local root를 모아 합치는 과정이 아니다. 실행이 늦거나 인증에 참여하지 못한 validator/node는 결과와 state 변경 데이터를 받아 사용할 수 있다. Producer lane은 데이터 생성 chain이며 state를 apply하는 주체는 node다. 영구적인 실행자/수신자 계급을 만들지 않으며 다음 cut에서는 역할이 달라질 수 있다.

**인증과 함께 전달할 내용:**

- 전체 ordering finality evidence와 canonical parent까지의 검증 가능한 연결.
- Signed execution subject, f+1 distinct validator signatures, final state root, deterministic transaction outputs commitment.
- Canonically encoded materialized state delta 및 status/events/fee 등 결과 데이터. Writes/deletions·처리 위치와 필요한 metadata를 포함하며, signer별 내부 delayed ID나 물리 DB 배치는 포함하지 않는다.
- Delta/output commitment는 전달 데이터의 전체 내용·범위를 묶는다. Chunk 전송은 digest/commitment로 검증하고 전체 검증이 끝나기 전에는 partial state를 노출하지 않는다. 별도의 application validity proof나 PAC를 도입하지 않는다.

**수신·적용 절차:**

1. 해당 chain/epoch의 validator set으로 ordering finality와 exact subject에 대한 f+1 일치 서명을 확인한다. Canonical parent의 결과 인증은 검증된 genesis/checkpoint까지 연결되어야 한다.
2. Signer들에게 digest로 delta/output을 요청한다. 다른 peer의 캐시도 같은 commitment와 일치하면 사용할 수 있다. f+1개 데이터 사본을 모두 받을 필요는 없고, 인증된 전체 데이터 한 벌을 확보하면 된다.
3. 자신의 durable state root와 처리 cut/누적 경계가 signed parent 문맥과 정확히 일치하는지 확인한다. 뒤처졌다면 빠진 certified updates를 순서대로 적용한다. 검증 가능한 checkpoint로 대체할 수도 있지만 임의 parent 위에 delta를 적용하거나 parent 인증 없이 건너뛰지 않는다.
4. 데이터의 commitment와 encoding/범위를 검사하고 별도 staging state에 delta를 적용한다. 새로운 root가 서명된 post-state root와 일치하는지 확인한다. 이는 application tx 재실행이 아니라 인증된 writes 적용과 해시·무결성 검증이다.
5. 검증이 끝난 state·outputs·적용 위치를 crash-safe하게 함께 publish한다. 같은 cut의 중복 수신은 no-op이며 fee나 events를 다시 적용하지 않는다. 성공 후에만 해당 cut의 read readiness를 노출한다.
6. 진행 중이던 speculative 결과는 새 canonical parent와 대조한다. 이미 적용한 cut의 늦은 실행 완료가 state를 다시 덮어쓰지 못하게 하고, 후속 cut 캐시는 새 parent에서 재검증한다.

**가용성과 fallback:**

- 실행 signer는 서명한 데이터를 보관·제공한다. 이를 통해 최대 f Byzantine 아래 최소 한 정상 데이터 보유자가 존재한다는 조건부 복구 근거를 얻는다. 인증서가 데이터를 즉시 전달하거나 무한히 보관해 주는 것은 아니다.
- Retention을 finalized-cut 기준으로 명시하고, 데이터 삭제 전에는 대체 certified checkpoint와 복구 자료의 가용성을 확보해야 한다. 고정 retention window 밖의 무제한 catch-up이나 Byzantine bound 밖의 추가 데이터 손실을 보장하지 않는다. 구체적인 checkpoint/GC 정책은 구현·평가에서 명시한다.
- 수신자는 여러 signer/peer에게 재요청하며, 누락·오염 데이터만으로 canonical state를 변경하지 않는다. Eventual synchrony, fair serving, retention 및 충분한 transfer/apply 용량 아래 catch-up을 주장한다. 데이터가 복구되지 않으면 authenticated inputs와 parent를 확보해 직접 실행하는 fallback을 사용할 수 있다.
- Fetch·apply 완료를 ordering vote나 모든 노드가 기다리는 global barrier로 만들지 않는다. 다만 parent 미준비로 dependent execution은 기다릴 수 있고, 실제 read readiness는 signature finality보다 늦을 수 있다.

**직관적 예시:** n=4, f=1에서 H1·H2·Z가 cut 확정에 참여하고, H1·H3가 같은 결과를 실행·검증해 서명한다. H2는 실행을 끝내지 못했더라도 두 서명을 확인하고 H1 또는 H3에서 delta를 받아 적용한다. H3가 cut 투표 집합 밖에 있어도 exact context의 정상 실행 서명이면 사용 가능하며, H2의 application 재실행 완료는 결과 인증의 선행조건이 아니다.

**배치 의도:** 핵심 pipeline·결과 인증 → 안전한 재사용·무효화 조건 → 남는 재실행 비용 → 선언 기반 ordering-aware 배치 → 실제 사용 가능 상태 순으로 읽히게 한다. 특정 실행 backend나 별도 SDK hook을 System Design의 독립 설계 축으로 두지 않는다.

## 4. Correctness and Liveness

### 4.1 Correctness argument and progress conditions

본문은 먼저 아래 세 명제를 연결해 §3.1과 §3.5가 성립하는 이유를 증명한다.

1. **결과 유일성:** 전체 ordering finality, canonical parent와 누적 처리 경계, 결정적 ordering/runtime에서 실행 입력 I와 올바른 결과 R*=Exec(I)가 유일하다. 정상 노드의 최종 결과가 같다는 성질이지 모든 cut 투표자의 동시 실행 완료를 의미하지 않는다.
2. **실행 결과 인증:** 같은 (I,R)에 대한 f+1 distinct 실행 서명에는 정상 직접 실행자가 최소 하나 있으므로 R=R*다. 같은 I에 서로 다른 결과의 유효한 인증서가 존재할 수 없으며, 이 결론은 실행 인증서끼리의 quorum intersection을 필요로 하지 않는다.
3. **재실행 없는 설치:** 이미 검증된 parent state에 인증된 canonical delta를 적용하면 직접 실행과 같은 post-state를 얻는다. 전체 delta/output commitment, parent 처리 위치, post-root 및 atomic publish를 검사하므로 수신 노드의 application 재실행은 필요 없다. Genesis/검증된 checkpoint를 기저로 연속된 cuts에 귀납 적용한다.

이를 뒷받침하는 세부 성질과 진행 조건은 다음과 같다.

- **DAG determinism and acyclicity:** exact input/context와 strict rank에서 같은 cycle-free graph를 얻음.
- **Serial equivalence:** reference rank와 내부 tx 순서 아래 모든 실제 읽기·delta 조건·snapshot을 검증하여 순차 실행과 state/status/events/gas가 동등함.
- **Safe reuse:** 같은 프로그램과 검증된 관측의 결과만 재사용하고 stale descendants를 재검증함. 재검증과 실제 재실행은 구분함.
- **Deferred-effect correctness:** 실패·제외 tx의 효과 제거, overwrite 경계, 중간 범위 검사와 snapshot 위치를 보존함. 로컬 retry 횟수는 canonical gas나 실패 결과를 바꾸지 않음.
- **Certified result correctness:** 확정된 단일 입력에 대해 f+1 matching signatures에 정상 검증자가 포함됨. Quorum intersection으로 별도 ordering을 정한다는 증명이 아님.
- **Safe installation:** 다른 parent·누적 처리 위치, 누락/오염된 delta, 중복 cut과 stale worker completion을 거부하거나 idempotent 처리함. Crash 도중 partial state를 ready로 공개하지 않음. State root가 같아도 cut 처리 위치가 다르면 같은 parent로 취급하지 않음.
- **No premature canonicality:** 미확정 cut, 다른 parent 또는 다른 runtime의 결과를 적용하지 않음.
- **Placement independence for a fixed cut:** 배치 artifact 누락·불일치와 무관하게 같은 exact cut의 순차 의미를 보존함. 배치가 달라져 다른 cut/order를 만들었을 때까지 결과가 같다는 주장은 하지 않음.
- **Declared-access containment:** 실제 scope/mode가 signed 및 protocol-derived 범위 안에 있음. Runtime 접근 위반의 후보 결과와 최종 실패를 구분하고, lane 전달로 선언을 변경하지 않음.
- **Routing determinism and scope:** 같은 tx/config/q에서 후보 순위가 같고 공통 순열로 회전함. 이것은 실제 포함 k·block contents 일치나 state 순서 공정성을 보장하지 않음. Cut-count fallback의 전달 기회와 실제 inclusion liveness의 용량·fair admission 전제를 구분함.
- **Conditional liveness:** eventual synchrony, 충분한 정상 실행자와 fair scheduling을 전제로 결과 인증이 진행됨. f+1 서명자의 durable 보관·제공, retention 내 재요청, recoverable checkpoint와 충분한 네트워크/저장장치 용량 아래 늦은 노드가 따라잡음. 인증의 안전성과 데이터 복구의 진행 조건을 구분함.

다른 local roots가 보인다는 사실만으로 Byzantine이라고 판단하지 않는다. Context가 다른 speculative results는 정상적으로 다를 수 있다.

### 4.2 Byzantine behavior: case-by-case boundaries

**인증이 보장하는 사실부터 구분한다.** n=3f+1, 최대 f Byzantine에서 f+1 DA 서명은 적어도 한 정상 보관자와 그 signer가 실제 검사한 dissemination predicate의 충족을 보장한다. Application execution의 정확성이나 같은 lane position의 non-equivocation까지 보장하지 않는다. Autobahn은 서로 충돌하는 availability-certified forks가 생길 수 있음을 다루며, 전체 ordering 절차가 각 lane position에서 최대 하나의 proposal만 commit하도록 한다. 따라서 DA 인증만 보고 실행 결과를 canonical하게 설치해서는 안 된다. [Autobahn Appendix A.4](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)

현재 모델은 기존 전체 Autobahn ordering finality와 **exact context에 대한 f+1 distinct 직접 실행 서명**을 함께 요구한다. 아래는 새 합의 단계나 punishment 체계의 제안이 아니라, 입력·실행·배치·결과 전달의 경계에서 정상 노드가 무엇을 거부하고 무엇을 복구해야 하는지에 대한 설명이다.

1. **잘못된 block bytes 또는 hash·형식 불일치.** 정상 노드는 producer 서명·digest·허용 encoding과 inherited dissemination predicate를 검사한 뒤 해당 입력을 사용하고 서명한다. Body가 인증된 digest와 다르면 거부하고 같은 digest의 데이터를 정상 DA 보관자에게 요청한다. 검사하지 않은 application 성공까지 DA 서명이 보증한다고 해석하지 않는다. 거부된 입력으로부터 만든 speculative 결과는 채택하지 않으며, malformed input의 처리량 제한과 자원 예산은 별도 필요하다.
2. **동일 position의 fork와 지연된 predecessor.** Byzantine producer가 다른 정상 노드에 다른 certified 후보를 보여줄 수 있다. 노드별 speculative view는 달라도 되며 전체 ordering finality가 선택한 exact 입력만 canonical 후보가 된다. 선택되지 않은 branch·새로 삽입된 선행 write에 의존한 결과를 재검증하고 필요한 tx를 재실행한다. 늦은 과거 generation의 완료는 새 결과에 publish하지 않는다. 공통 순서 규칙과 DA 인증이 이런 재실행 비용이나 adversarial delay를 없애는 것은 아니다.
3. **거짓 접근 선언 또는 operation 종류 위장.** 선언은 signed scheduling 입력이지 실행 정당성의 증거가 아니다. Runtime은 실제 read/write/지원 연산을 수행하기 전에 scope와 mode 포함 여부를 검사한다. 범위를 벗어난 접근을 허용한 뒤 복구하는 대신 접근을 차단하고, 확정 입력에서 정해진 실패·fee 규칙에 따른 결과를 만든다. 해당 tx의 임시 application effects는 누출하지 않는다. 보수적 과대 선언은 안전성을 깨지 않아도 배치와 병렬성을 악화시킬 수 있으며 admission·resource 한계 안에서 다룬다.
4. **거짓 결과, 위조·중복·재사용 서명 또는 잘못된 문맥의 인증서.** 서명 검증과 distinct signer 집계에 더해 chain/epoch/slot, exact cut·input, 누적 처리 위치, canonical parent, runtime/order version과 전체 output·delta commitment를 함께 확인한다. 다른 후보에서 정당했던 서명을 재사용하거나 같은 서명자를 중복 계수하지 않는다. 최대 f 악성 signer만으로는 f+1의 일치하는 잘못된 결과 인증을 만들 수 없다. 이는 정상 직접 실행자의 검증이 올바르다는 전제 아래의 결과이며, 공통 runtime bug나 BFT bound 초과까지 막는다는 뜻은 아니다. 온전한 ordering finality가 없는 사전 인증은 조건부 결과로 남는다.
5. **권장 producer의 검열·전달 거부·거짓 ACK.** Soft placement는 포함 보장이 아니다. 원본을 유지한 정상 sender/relay는 첫 전달 기준의 pending age를 유지하고 H finalized cuts 뒤 모든 producer에 fanout한다. ACK·새 attempt·다른 producer 전달은 이 age를 초기화하지 않는다. 따라서 한 악성 producer의 협조에 전파를 영구 의존하지 않지만, H는 재전파 조건이지 inclusion deadline이 아니다. 실제 포함에는 ordering 진행, 정상 sender/relay, 충분한 용량과 fair admission이 필요하다.
6. **Delta/output의 변조·누락·은닉.** 수신자는 원본 f+1 서명과 commitment에 맞는 전체 데이터를 확보하고 exact parent 위 staging apply·post-root 검증을 마친 뒤에만 durable readiness를 공개한다. 변조·불완전 데이터는 거부하며 다른 signer/peer에게 재요청한다. 정상 직접 실행 signer가 서명 전 데이터를 durable하게 저장하고 retention 동안 제공한다는 조건이 적어도 한 정상 복구 경로를 준다. 미응답은 readiness를 늦출 수 있지만 잘못된 state를 설치할 이유가 되지 않는다. 복구가 불가능하면 인증된 입력·parent의 직접 실행 fallback을 사용하며 무제한 보관이나 즉시 복구를 보장하지 않는다.

**안전성과 성능의 분리:** 정상 노드는 악성 입력·결과를 그대로 확정하지 않아야 하지만, 지연·fork·과대 선언은 wasted execution과 queueing을 늘릴 수 있다. Eventual synchrony와 fair scheduling·serving, 보관·용량 전제 아래의 진행을 설명하고, 모든 Byzantine 스케줄에서 낮거나 일정한 cut-to-state latency를 보장한다고 쓰지 않는다. 이를 구현에서 확인할 최소 계획은 §5.5에 둔다.

## 5. Evaluation

**평가할 주장:** 공통 ordering과 실행 pipeline이 cut-to-state-finalization latency를 얼마나 줄이며, 재실행 비용으로 그 이득이 사라지거나 역전되는 조건은 무엇인가? 선언된 state·operation에 따른 producer 배치가 그 비용을 줄여 최종 latency를 개선하는가? 동일 실행 backend·공통 adapter 경로 아래 변경 요소를 분리한다. 실행기 간 성능 비교가 아니며, 재실행 수만 줄고 queueing으로 최종 latency가 늘었다면 목표를 달성했다고 주장하지 않는다.

### 5.1 Prototype, execution backend and fair baselines

- 실제 구현한 consensus/adapter, commit, validator 구성과 실행 semantics를 명시한다. 초기 formal 구성은 n=4/7/10 등을 고려한다.
- 기존 Commonware legacy EC 코드나 synthetic view-selection 실험을 새 모델의 E2E로 인용하지 않는다.

**실행 backend 선택과 검증 계획:**

- 벤치마크 application의 실행 backend로 **Block-STM + Aggregators V2**를 사용할 계획이다. 이는 §3의 프로토콜을 평가하기 위한 구현 선택이지 제안하는 새 실행엔진이나 pipeline의 필수 전제가 아니다. 아직 port나 E2E 실행이 완료되었다는 뜻이 아니며 실제 구현 commit·지원 API와 설정을 고정해 보고한다. [Block-STM](https://arxiv.org/abs/2203.06871), [AIP-47](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md)
- Block ordering을 유지하되 실행·캐시·재실행은 tx 단위로 한다. 일반 read/write의 다중 버전 관측·검증과 backend 자체의 ESTIMATE 대기를 사용한다. 추가 선언 기반 선행 작업 대기와 same-block packing은 별도 정책으로 구분한다.
- 지원되는 aggregator 변경량, try_add/try_sub 조건 관측, delayed field와 output-only snapshot을 구분한다. 같은 aggregator를 갱신했다는 이유만으로 일반 RMW 충돌을 만들지는 않지만 정확한 읽기나 조건 판단이 바뀌면 재실행한다. 임의 연산을 무충돌 defer로 분류하지 않는다.
- 정확한 값이 계산·분기에 사용되는 경우와 출력에만 placeholder로 남을 수 있는 경우를 구분한다. 조건은 유지되고 출력 값만 달라졌다면 지원되는 snapshot을 재구체화하며 인증 전에 모두 materialize한다.
- 검증 실패 시 해당 tx 처음부터 재실행하고 후속 tx를 재검증한다. 유효한 결과는 유지하며 전체 suffix의 무조건 재실행이나 명령어 중간 재개로 설명하지 않는다.
- Block-STM의 preset-order 전제와 가변 pre-cut block 집합·순서·parent 사이에는 adapter가 필요하다. Generation, stable occurrence와 exact-order cache-import 검증을 구현·검증하며, 기존 Aptos 실행기를 호출하면 이 연결까지 자동 해결된다고 주장하지 않는다.
- Ordinary reads, delta 조건의 참/거짓 이력, snapshot 위치, status/events/gas와 실패 tx effects를 최종 문맥에서 검증한다. 이전 generation의 늦은 완료는 새 결과에 publish하지 않는다. 선택한 backend와 adapter를 순차 실행 oracle과 비교해 §3.2의 조건을 충족하는지 시험한다.

**세 가지 주 비교군:**

| 비교군 | 구성 | 답할 질문 |
|---|---|---|
| Original | 기존 ordering/native serialization을 유지하고 cut 이후 동일 application 실행 | 기존 post-cut 경로의 latency는 얼마인가? |
| Pipeline | 공통 ordering rule + pre-cut 실행·검증·재사용 + exact-cut 결과 인증·state 전달/적용; state-aware routing 없음 | 핵심 pipeline으로 cut 이후 잔여 작업과 늦은 노드의 재실행을 얼마나 줄이는가? |
| Pipeline + Placement | Pipeline과 같은 실행기·인증·state 전달/적용 + 선언된 state·operation·cut priority 기반 producer 배치 | 배치가 추가로 재실행과 state-finality latency를 얼마나 줄이는가? |

- 주 비교에서는 **동일한 Block-STM + Aggregators V2 backend와 application/fee 의미·지원 operation**을 사용할 계획이다. Original에 이를 연결하는 것은 공정한 실행 비용 비교를 위한 실험 구성이지 upstream consensus가 원래 이 실행기를 제공한다는 뜻이 아니다. Native artifact의 원래 실행 성능은 별도로 표기한다.
- Pipeline에도 충돌 검출·재검증·tx 재실행과 exact-cut 검증이 있다. 이를 빼거나 무조건 전체 replay만 강제해 약한 비교군을 만들지 않는다. Full replay는 보조 민감도 실험으로만 둔다.
- Pipeline → Pipeline + Placement의 주 비교에서는 producer routing만 바꾼다. 두 경로에 동일한 선언 payload·검증과 실행 설정을 유지하고, 선언 도입 자체의 추가 bytes·검증 비용은 별도 실험으로 보고한다. 선언 기반 predecessor waiting과 same-block packing은 양쪽에 같은 설정을 적용하며, 추가 정책의 효과는 별도 ablation으로 분리한다.
- Original의 native zip과 제안 RR serialization은 순서가 다를 수 있다. 세 주 비교군은 **시스템 전체 효과**를 보여주고, 같은 exact blocks·order·parent에서 post-cut/pre-cut 실행을 비교하는 통제 실험으로 pipeline 자체의 효과를 분리한다. 배치 E2E가 block 구성·cut·성공률을 바꾸면 이를 함께 보고한다.
- 인증 latency를 비교할 때는 같은 `전체 ordering finality + canonical parent + f+1 matching result signatures` 완료 조건을 적용한다. 기존 시스템에 없는 결과 서명 경로를 추가했다면 별도 계측이라고 명시하고, 직접 실행 결과·native 응답 latency도 함께 제시한다.
- CPU/worker·메모리·대역폭·offered load와 scheduling budget을 맞춘다. 투기 실행이 ordering의 CPU와 네트워크를 잠식하는 비용도 포함한다.
- Pipeline 두 비교군은 같은 fetch/apply·signer 보관 정책을 사용한다. Original의 native catch-up 경로를 명시하고, **같은 인증 결과·parent·수신 노드 자원에서 직접 replay 대 certified delta 적용**을 별도로 비교한다. Post-cut에도 동일 결과 전달 경로를 연결하는 통제 실험으로 pipeline 효과와 state transfer 효과를 분리한다. Delta 생성·encoding·durable 보관·서명·전송·hash/DB apply 비용을 모두 포함한다.

**보조 실험과 ablation:** ordering-only ceiling, 같은 순서의 post-cut/pre-cut 실행, plain/deferred Block-STM, 고정/회전 lane 순서, predicate 재사용과 snapshot 구체화, delta fetch/replay, speculation budget을 분리한다. 배치는 tx-ID hash·고정 physical affinity·cut별 회전 affinity를 비교하며 tie-break와 알려진 predecessor 대기를 명시한다. Aggregators·waiting·packing의 이득을 placement만의 이득으로 합산하지 않는다.

### 5.2 Workloads and faults

아래 fault 항목은 검증할 기능·경계의 목록이다. 모든 fault와 workload 축의 전조합 benchmark를 요구하지 않으며, 최초 검증 범위는 §5.5의 작은 targeted harness로 제한한다. 추가 crash·retention·부하 사례는 해당 기능을 구현한 뒤 독립 regression으로 확장한다.

- Bank-like shared accounts와 nonce, multi-account atomic updates, hot keys. Account를 lane에 귀속시키지 않는다.
- Offered load, execution cost, block size, conflict density, lane imbalance, worker 수와 네트워크 지연을 변화시킨다.
- Late tip/body, excluded speculative predecessor, same-height fork, view change, delayed parent state를 넣는다.
- False result, wrong subject, replayed/duplicate signatures, Byzantine signature withholding과 replay-amplification load를 시험한다.
- 느린 실행 노드, 몇 cuts 뒤처진 재시작 노드, Byzantine 데이터 미응답, chunk 누락·변조, 잘못된 parent/처리 위치, 중복 전송, apply 중 crash, retention 경계와 checkpoint 복구를 시험한다. Root는 같지만 처리 cut이 다른 no-op 구간도 포함한다.
- Application failure와 stale-result recovery를 별도 계측한다. 두 개를 모두 failed transaction으로 합치지 않는다.
- Deferred 비율, exact-read 빈도, 공통 fee payer, overflow/underflow 경계 근접도와 cut churn을 변화시킨다. False→true 조건, abort delta 제거, snapshot 이동 및 stale completion을 안전성 사례에 포함한다.
- Packing 크기·대기시간·선언의 과대 정도·용량·hot-key 편중을 바꾼다. 다른 mempool에서도 후보 순위 일치, producer 전달/침묵, 잘못된 epoch/config 메시지 거부, 중복 재전송·nonce 역전과 접근 위반도 평가한다. Membership reconfiguration은 초기 실험 범위 밖이다.

### 5.3 Metrics and claims

- Cut -> local verified execution result, cut -> transferable result certification, cut -> durable read readiness의 p50/p95/p99.
- 결과 인증에 참여한 노드와 fetch/apply로 따라잡은 노드의 readiness를 따로 보고한다. 수신자의 signature verification·데이터 확보·delta 검사·root 계산·durable apply 시간, catch-up cut 수와 실패/재요청 횟수를 계측한다. 재실행을 생략했어도 이러한 비용을 0으로 세지 않는다.
- Input -> state-ready end-to-end latency, ordering throughput/latency와 state-ready goodput.
- Reused work, rerun work, recovery CPU, critical path, memory와 result/delta traffic.
- 전체 시도한 application 실행 수·완료한 실행자 수와, 인증 후 불필요한 실행을 중단하고 데이터를 적용한 노드 수를 기록한다. Signer의 delta 생성·보관 비용, retention bytes, serving 대역폭과 수신자의 CPU/DB writes를 함께 보고한다.
- Predicate 검증·snapshot 재구체화·최종 materialization과 state-root 계산을 따로 계측한다. Logical deferred updates와 실제 DB writes를 구분한다.
- 실행 서명이 cut 전에 준비된 비율, cut 기준 state lag, lane별 대기와 처리량.
- 배치 비용·queue wait·실제 same-block packing률을 측정하고, late predecessor·cut 제외·parent 변경·알려진 writer보다 이른 실행·defer 조건 변화별 retry를 분리한다. Cut 내부/경계, target q와 inclusion k의 차이, Pass/fanout 비용을 기록한다. 배치로 ordering 순서·성공률이 달라지면 함께 보고한다.
- Wrong result acceptance와 잘못된 canonical apply는 모든 안전성 실험에서 0이어야 함.

같은 serialization rule에서 pre/post-cut 실행을 비교해 overlap 효과를 분리한다. RR 회전이 application 성공률을 바꾸면 별도로 보고한다. 목표는 항상 빨라진다는 주장이 아니라 어느 조건에서 cut 이후 residual work가 줄어드는지 규명하는 것이다.

파이프라인이 cut 이전으로 옮긴 작업량과 cut 이후 남은 작업량을 분리하고, 보정·서명·통신 비용까지 포함한 순효과를 평가한다. Cut 확정 자체를 늦춰 간격만 줄이는 결과는 개선으로 보지 않으며, input-to-state latency와 ordering latency를 함께 보고한다.

### 5.4 RTT × application operation count

**2026-09-19 실험 결정:** validator 간 RTT와 application operation 수, 즉 state 변경 횟수를 두 핵심 축으로 삼는다. 네트워크 시간이 길어 실행을 숨길 여유가 생기는 구간과, 실행량이 커져 cut 이후에도 작업이 남는 구간을 함께 관찰한다. 이는 검증할 가설이며 RTT가 클수록 E2E latency도 개선된다는 주장은 아니다.

| 축 | 정의 | 예비 sweep 값 — pilot 후 조정 |
|---|---|---|
| Validator RTT | validator 쌍 사이에서 실제 관측한 왕복 지연 | 1, 10, 50, 100, 200 ms |
| Application operations | 성공한 transaction 하나가 정본 실행에서 수행하는 논리적 state 갱신 횟수 `k` | 1, 4, 16, 64회/tx |

- 사용자 합의 사항은 두 축이며 위 수치는 초기 실험 제안이다. 먼저 homogeneous RTT matrix로 측정하고, heterogeneous WAN 지연은 별도 실험으로 분리한다.
- `k`는 CPU instruction, transaction 수, gas, DB 물리 쓰기 횟수나 Merkle-tree node 갱신 수가 아니다. 첫 synthetic workload에서는 서로 다른 `k`개 key에 같은 종류의 결정적 갱신을 한 번씩 수행해 logical updates와 unique written keys를 일치시킨다. Bank 송금의 debit/credit은 business-state 기준으로 두 갱신이다.
- Nonce/fee 등 고정 bookkeeping writes는 별도 기록하고 동일하게 유지한다. 실제 logical read/write 수, unique keys, state-change bytes와 실행 시간도 기록한다. 같은 key의 반복 쓰기나 no-op 쓰기를 `k` 증가로 사용하지 않는다.
- RTT 설정이 총 목표 지연인지 추가 지연인지 명시한다. 대칭 링크의 양 방향에 각각 편도 지연 `d`를 추가하면 추가 RTT는 약 `2d`임을 구분하고, 실제 관측 RTT의 median/p95도 저장한다. Bandwidth, packet loss, jitter와 client/fullnode 링크 조건은 RTT sweep 동안 고정한다.
- Block당 tx 수, cut 제안 정책, validator/lane 수, CPU/worker 수, state 크기·cache 조건과 값 크기를 통제한다. 입력 payload bytes는 가능한 한 고정하고, 접근 key 수 증가로 payload가 커지는 실험은 그 bytes를 명시해 전송 비용과 실행 비용을 혼동하지 않는다.
- `k`와 **거래 간 충돌률은 별도 변수**다. 연산 종류와 read/write 비율을 고정하고 key 배치를 제어해, 가능한 한 같은 충돌 관계를 유지하면서 갱신량을 늘린다. 실제 transaction/block conflict density와 DAG critical path를 함께 보고한다. 처음에는 낮은 충돌로 두 축의 효과를 분리한 뒤 고정된 hot-key 조건에서 반복한다.

**비교 방법:** 각 조합에서 Original / Pipeline / Pipeline + Placement 세 주 비교군을 측정한다. 추가로 동일한 RR-DAG semantics에서 post-cut/pre-cut을 비교해 overlap 효과를 분리한다. 인증 latency를 비교하는 모든 경로에는 동일한 `finalized cut + canonical parent + f+1 matching execution signatures` 완료 조건을 사용한다. 별도로 직접 실행한 노드의 결과 확인 시간도 보고하며, 기존 시스템에 없던 인증 대기를 강제로 붙인 값을 기존 시스템의 원래 latency라고 부르지 않는다.

각 `(RTT, k)` 조합에서 같은 offered TPS로 방법들을 비교한다. 낮은 부하와 포화 근처를 구분하고, capacity sweep은 별도로 수행한다. 방법별 서로 다른 부하를 같은 latency 비교에 섞지 않는다. Open-loop 도착률, queue growth와 미완료 요청 수를 기록하고, 과부하에서 완료된 요청만으로 latency를 요약하지 않는다. 여러 독립 반복과 seed를 사용하고, warm-up·측정 시간·반복 수를 결과와 함께 공개한다.

**필수 결과:**

- Cut → state finalization과 제출 → state finalization의 p50/p95/p99. State finalization은 같은 관찰 노드가 cut·parent·`f+1` 인증을 모두 확인한 최초 시점으로 계측한다. 인증이 먼저 준비됐어도 cut 이전 시간을 finality로 세지 않는다.
- Cut → durable state readiness 및 제출 → 사용자 결과 확인 시간은 별도 보고한다. 서로 다른 노드의 동기화되지 않은 clock을 직접 빼지 않는다.
- 직접 실행 노드와 certified update 수신 노드를 구분하고, 느린 노드의 parent catch-up·fetch·apply 시간을 포함한다. 결과 인증 시점을 모든 노드의 read readiness로 대체하지 않는다.
- 성공한 canonical tx/s와 유효 state updates/s를 함께 보고한다. 이 workload에서 모든 성공 tx가 `k`회 갱신하면 updates/s = successful tx/s × `k`다. Speculative retries, 버린 결과와 실패 tx의 미적용 writes는 유효 처리량에 넣지 않는다.
- 실제 실행·state-root 계산·입력 재검증·재실행·서명 수집·durable apply 시간, cut 이전 완료된 계산 비율, 총 시도한 갱신 수와 유효 갱신 수를 분리한다.

**그림 배치:** RTT를 x축, `k`를 곡선/패널로 둔 latency 그래프; `k`를 x축으로 한 실행·복구 비용 그래프; `(RTT, k)`별 baseline 대비 latency 개선 heatmap을 계획한다. 개선율만 제시하지 않고 절대 latency와 ordering latency도 함께 표시한다. RTT가 커져 cut-to-state gap만 작아졌지만 E2E가 느려진 경우는 명확히 구분한다.

이 절은 벤치마크 계획이며 구현 또는 실험 완료 기록이 아니다. State 변경 횟수는 workload knob이고 Computing Gas나 새 protocol admission rule을 도입하지 않는다.

### 5.5 Targeted Byzantine fault-injection plan

**범위:** 대부분의 사례는 n=4, f=1의 소규모 deterministic harness에서 정상 노드 3개와 한 faulty 역할을 두고 하나씩 주입한다. Certified fork 사례만 n=7, f=2로 구성한다. 악성 producer 이외의 악성 voter 한 명이 두 branch에 서명하고, 서로 다른 정상 voter 두 명씩이 각 branch에 서명하면 각각 f+1=3 인증을 얻는다. 이 구성은 producer의 self-vote를 계수한다는 가정 없이 가능하다. Consensus adapter의 실제 메시지 경로를 연결할 계획이며 단순 mock으로 finality를 부여한 시험을 Autobahn E2E라고 부르지 않는다. 동일 exact finalized cut·parent·runtime에 대한 순차 실행 oracle로 state root, status/events/fee와 canonical delta를 비교한다. 이 절은 구현·실험 계획이며 아직 결과가 없다.

| Targeted case | 주입할 행동 | 확인할 최소 조건 |
|---|---|---|
| 입력 무결성 | 인증된 digest와 다른 body 또는 malformed encoding | 입력 거부·정상 보관자로부터 재요청; 잘못된 canonical effect 없음 |
| Fork·late predecessor | 동일 producer position의 두 후보를 분리 전파하고, 선행 writer를 늦게 공개 | DA 인증을 non-equivocation으로 오인하지 않음; 선택된 cut 기준 재검증·필요한 재실행 뒤 oracle과 일치 |
| 접근 선언 위반 | 실제 write를 read로 선언하거나 접근 key를 누락 | 범위 밖 접근 전에 차단; 정해진 실패·fee 결과와 일치; 임시 effects 누출 없음 |
| 실행 인증 공격 | 거짓 root 한 표, 중복 signer, 변조 서명, 다른 cut/parent/epoch의 서명 재사용 | f+1 distinct exact-context 직접 실행 서명 및 전체 ordering finality 없이는 채택하지 않음 |
| 배치 검열 | 첫 producer가 보관/전달을 거부하고 ACK만 반복 | 원래 age 유지; H finalized cuts에서 fanout; 정상 admission이 주어진 실행에서 진행하며 deadline 보장은 주장하지 않음 |
| 결과 데이터 공격 | 악성 signer가 delta를 은닉하거나 변조 chunk 제공 | 정상 보관자에게 복구 요청; commitment·parent·post-root 검증 전 readiness 없음; 한 번만 atomic install |

**한 가지 제한된 latency 사례:** 한 선행 writer와 그 값을 읽는 후행 tx, 무관한 tx로 구성한 짧은 workload를 사용한다. 고정된 유한 delay로 writer의 delivery를 늦춘 뒤 공개하고 같은 blocks·order·parent에서 post-cut 실행과 pre-cut pipeline을 비교한다. Delay 값·release 시점·load·resource budget을 공개하고 cut-to-result certification, cut-to-durable readiness, 제출-to-result, 재실행 수·CPU 및 ordering latency를 측정한다. 단일 bounded scenario의 관측을 임의의 Byzantine 스케줄에 대한 latency 상한이나 placement의 일반적 우월성으로 확대하지 않는다.

**완료 기준:** 각 사례의 모든 정상 노드가 같은 확정 문맥에서 oracle과 같은 결과를 설치하고, 위조 인증·잘못된 state 채택이 0이어야 한다. 제한된 네트워크 지연과 정상 보관·admission·scheduling을 제공한 실행에서 복구가 완료되는지 별도로 확인한다. 이 test evidence는 §4의 증명을 대체하지 않으며, 작은 fault suite를 대규모 공격 성능 평가로 포장하지 않는다.

## 6. Related Work

- **Ordering:** [Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf), Multimmit 및 DAG-based BFT와 cut/실행 경계를 비교한다.
- **Execution/result certification:** [PBFT](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/01/p398-castro-bft-tocs.pdf)의 matching replies와 tentative execution을 직접 비교한다. f+1 자체는 새 기여가 아니다.
- **Authenticated state transfer:** 같은 [PBFT §6.2.2](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/01/p398-castro-bft-tocs.pdf)의 인증된 root와 받아온 state 검증을 비교한다. 본 모델의 cut별 materialized delta 전달·실행 signature binding·retention은 별도로 정의하며, state를 받아 재실행 없이 복구하는 개념 자체를 새 기여로 주장하지 않는다.
- **Latency overlap:** [Zaptos](https://arxiv.org/abs/2501.10612)는 execution/consensus overlap 관련 연구로 짧게 위치시킨다. 본 연구의 필수 직접 benchmark나 주된 비교 대상으로 삼지 않는다.
- **평가에 사용하는 실행 기술:** [Block-STM](https://arxiv.org/abs/2203.06871)과 [AIP-47 Aggregators V2](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md)는 평가 backend의 근거로 간략히 인용한다. Preset-order 실행과 가변 pre-cut 입력의 연결 의무를 구분하고, delta·predicate 재사용·snapshot을 본 논문의 기여로 주장하지 않는다. [SIP-58](https://github.com/sui-foundation/sips/blob/main/sips/sip-58.md)의 reservation 기반 scheduling은 다른 지불 능력 관리 방식으로 구분한다.
- **Declared inputs:** [Sui의 transaction 입력 모델](https://sdk.mystenlabs.com/sui/transactions/reference)을 명시 object의 참고점으로 사용한다. 우리의 conservative state·operation 배치 metadata 및 runtime containment와 동일한 모델이라고 주장하지 않는다.
- **Scale-out execution:** [Pilotfish](https://arxiv.org/abs/2401.16292)와 worker scheduling을 비교하되, 본 모델을 곧바로 inter-validator execution sharding이라고 부르지 않는다.
- **Conflict-aware allocation:** [TxAllo](https://arxiv.org/abs/2212.11584)의 부하 고려 배치, [Strife](https://homes.cs.washington.edu/~suciu/guna-sigmod-2020-pdfa.pdf)의 RW clustering을 참고한다. State sharding·global batch barrier를 도입하지 않는 producer routing이라는 차이를 설명하고, [Prophet](https://arxiv.org/abs/2304.08595)의 ordering 기반 conflict-free 보장을 그대로 인용하지 않는다.

독립 Related Work 절은 유지한다. System Design에서는 해당 선택의 가장 가까운 근거만 짧게 인용한다. 이번 모델은 state ownership sharding이 아니므로 cross-shard atomic commit 논문을 핵심 novelty 비교 대상으로 앞세우지 않는다.

## 7. Discussion and Limitations

- 고정 순위를 회전시켜도 complete local view나 pre-cut 실행 완료가 보장되지 않음.
- 회전 및 cut exclusion 때문에 recovery가 늘어날 수 있음.
- 정확한 값 읽기·조건 변화가 연결된 hot keys의 본질적 의존성. Tx 단위 재실행도 최악에는 전체 suffix로 전파될 수 있음.
- Deferred update가 payer 자금 예약·잔액 부족 문제를 자동 해결하지 않음. Snapshot 구체화·predicate 검증 비용과 상태 크기·재시도 상한이 필요함.
- f+1 Byzantine-trust-based certification과 validity proof의 차이; 공통 application bug는 범위 밖.
- 인증된 root와 실제 state availability/readiness의 차이, retention 및 checkpoint 비용.
- f+1 인증에는 정상 제공자가 한 명뿐일 수 있어 serving 집중과 대역폭 병목이 생길 수 있음. 실행 생략은 전송·hash·DB apply 비용 생략이 아니며, 무제한 과거 데이터 보존이나 추가 장애 모델을 보장하지 않음.
- 모든 노드가 다른 실행자를 기다리는 정책은 진행을 멈출 수 있음. 충분한 정상 노드의 직접 실행이 필요하며, 새 실행 quorum이나 고정 f+1 실행 committee를 제안하는 것은 아님.
- Ordering이 계속돼도 execution throughput 부족이나 parent 의존으로 state backlog가 증가할 수 있음.
- Deterministic lane rotation은 MEV 방지나 경제적 공정성 보장이 아님.
- 선언 기반 후보 순위는 실제 포함 producer·같은 block·전역 부하 균형을 보장하지 않음. Hot lane·과대 선언·queueing·전달 비용·state/tx-id grinding과 달라지는 canonical order를 평가해야 함.
- State와 priority를 같은 순열로 회전하면 논리적 우선순위 위치는 고정됨. 물리 producer 교대와 state 간 공정성은 다르며, 회전 자체의 retry 감소를 주장하지 않음. Cut 경계 이월·fallback이 오히려 재사용을 줄일 수 있음.
- Dynamic membership, arbitrary runtime-discovered EVM access, adaptive leader scheduling은 초기 범위 밖.

## 8. Conclusion

- **State finalization latency 감소**라는 핵심 과제에 답한다. 공통 ordering과 실행 pipeline으로 실행을 앞당긴 효과, 재실행이 그 이득을 소모하는 조건, 선언된 state·operation 기반 producer 배치가 그 비용을 줄여 최종 latency를 개선한 효과를 순서대로 정리한다. 특정 실행 backend의 도입을 연구 성과로 바꾸지 않는다.
- Original → Pipeline의 이득을 먼저, Pipeline → Pipeline + Placement의 추가 이득을 다음으로 정리한다. 재실행 감소는 주 목적을 지원하는 최적화이며 단독 목표로 바꾸지 않는다.
- Ordering finality, 실행 결과 인증, serving readiness를 분리해 요약한다.
- Shared-state pre-execution을 공통 RR-DAG 규칙과 연결하고, selected cut에 맞지 않는 계산만 복구하는 설계를 정리한다.
- 기존 cut 합의와 f+1 execution endorsement의 역할을 다시 구분한다.
- 실행을 마친 노드의 결과 인증과, 늦은 노드의 인증된 변경 데이터 적용을 연결한다. 전체 노드 재실행 완료를 요구하지 않되 node-local readiness와 데이터 복구 조건은 분리한다.
- 실험으로 확인한 이득·실패 조건만 결론에 적는다.

## 그림과 본문 배치 계획

1. **Introduction / Motivation:** block 전파 -> cut 합의 -> 실행 -> 결과 인증 -> apply/readiness에서 드러나는 지연.
2. **System Design §3.1:** 같은 cut의 DA/ordering과 speculative 실행·결과 인증 준비의 중첩. n=3f+1 구성, 기존 전체 ordering finality와 별도 f+1 실행 서명의 결합을 표시한다. Cut 투표자 전체의 실행 완료와 혼동하지 않는다.
3. **System Design §3.2–3.3:** 늦은 writer 삽입 -> reader 관측 무효화 -> 해당 tx 재실행·후속 재검증. 독립 tx의 재사용과 반복 무효화 비용을 함께 보인다.
4. **System Design §3.4:** 동일 workload의 분산 배치와 state·operation 배치를 비교한다. 공통 priority와 state 선호 producer의 회전, multi-key tx, q≠k를 작은 예로 설명한다. 결과는 검증할 가설로 표시한다.
5. **System Design §3.5:** 실행자들의 동일 결과 서명 → 늦은 노드의 인증·delta fetch → parent/데이터 검증 → atomic apply·root 확인 → read-ready 경로. f+1 서명과 데이터 한 벌, parent가 이미 준비된 경우와 여러 cuts 뒤처진 경우를 구분한다.
6. **Evaluation:** Original / Pipeline / Pipeline + Placement의 latency 분해와 재실행·CPU·대기 trade-off. 동일 순서 통제 실험과 replay 대 fetch/apply는 별도 패널로 둔다.

이 파일은 논문 구조와 작성 지침이지 제출용 완성 본문이나 검증된 실험 결과가 아니다.
