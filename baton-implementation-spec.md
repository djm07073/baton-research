# Baton — 구현 스펙

> [Google Doc 원문](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) · [동반 문서](baton-paper.md) · 2026-09-30 수동 동기화. 이후 사용자 결정과 Google Doc의 최신 revision이 이 snapshot에 우선한다.

논문 초안의 구현 계약과 미결정 선택을 분리한 작업 문서. 구현 완료 또는 완성된 프로토콜 증명을 뜻하지 않는다.

연결된 논문 초안: [Baton: Execution-Aware Ordering for Autobahn](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit)

## 1 범위와 현재 요구

현재 기준은 연결된 Google Doc과 사용자의 최신 설계 요구다. 저장소 문서는 더 오래된 documentary snapshot이며 자동 동기화하지 않는다. 이 문서는 기존 초안의 구체 계약을 보관한다. 아래에서 원문의 § 번호를 인용한 경우 연결된 논문 초안의 논증을 가리킨다.

고정된 방향은 Native Multimmit 기반, n=5f+1, 2f+1 전체-prefix 우선·sum-LCP fallback, 4f+1-or-fixed-deadline, cut no-wait, proposal별 authenticated policy 고정, irrevocable exact order와 동일 문맥의 f+1 실행 서명 endpoint다. Report는 intention이며 execution progress proof가 아니다.

새로 채택한 상위 요구는 leader가 선택한 유효 direction prefix를 포함하고 보존하도록 cut proposal을 구성하며 validator가 그 보존 조건을 검증하는 것이다. 같은 canonical input state·runtime과 불변 ordering frontier 뒤에서 선택 prefix p가 최종 실행 순서 O의 선두 연속 prefix여야 한다(p ⪯ O). 각 block의 membership만 맞아도 중간에 다른 block이 끼면 이 요구를 충족하지 않는다. 구체 native adaptation과 증명은 미완성이다.

이 요구는 native inclusion과 무관하게 순서 hint만 적용하면 충분하다는 이전 연결 가정을 강화한다. Native tip 추출·extension을 기반으로 삼되, 어떤 availability/adoption 및 proposal validity 조건으로 보존을 보장할지는 정하지 않았다. 미가용·무효 block을 강제로 포함하거나 과거 direction approval/3f+1 plan-lock을 되살리지 않는다.

## 2 Report 문맥과 admission

Report는 epoch, leader view, 기준 finalized cut, canonical parent의 식별자, ordering-rule version, collection window, exact ordered block references와 sender signature를 포함한다. Identity당 같은 window의 유효 보고 하나만 계수하고, 다른 cut·parent·view의 보고는 섞지 않는다. Report는 “이 순서로 실행할 예정”이라는 관측 입력일 뿐 state root, execution proof 또는 선택될 direction에 대한 승인 서명이 아니다.

초기 prototype은 동일 window에서 처음 수용한 유효 report를 고정하는 정책을 사용할 수 있다. 이후 상충 report를 중복 계수하지 않으며 메시지 크기와 처리량을 제한한다. Signed report가 body availability를 대신하지 않으므로 block references의 문맥과 기반 dissemination의 가용성 근거도 검사한다. 서로 다른 leader가 같은 report snapshot을 보유한다는 가정은 하지 않는다.

[명세 선택 D1] Report encoding·크기 한도·상충 report 처리와 recovery를 고정해야 한다. Validator가 실제 수신한 blocks와 기존 direction에서 intended order를 만드는 규칙, signed window ID를 알게 되는 경로도 명세해야 한다. Leader-local timer만으로 remote validator에게 window가 알려지지는 않는다. First-valid 수용, 인증된 window 안내, 사전 공유·piggyback 중 구체적 조합은 아직 채택하지 않는다.

같은 인증 문맥의 고정 report snapshot을 R, bounded 후보 집합의 유효 full candidate order를 P라 한다. Epoch/view·ordering 이력·parent·rule·window를 섞지 않고 identity당 원본 report 하나만 센다. 비교 원점은 대상 proposal에서 바꿀 수 없는 inherited ordering frontier 뒤의 새 재정렬 가능 segment 시작이다. 이미 고정된 과거는 제외하며 최대 W개 block의 horizon에서 비교한다. Prefix p의 support는 이 동일 원점에서 p 전체를 처음부터 정확히 포함하는 distinct original reports의 수다. 서로 다른 위치를 서로 다른 보고 집합이 지지하는 것만으로 공통 prefix를 만들지 않는다.

## 3 Snapshot 종료와 no-wait

Leader가 아직 direction에 반영되지 않은 실행 가능한 block을 관측한 t₀에 window를 열고 deadline을 t₀+τ로 고정한다. 검증된 distinct report를 snapshot에 넣는 admission event와 deadline event를 leader-local로 직렬화한다. 유효 report 수가 처음 4f+1에 도달하는 event 또는 deadline 중 먼저 처리된 event에서 R을 한 번 고정하며, 닫힌 뒤의 report나 동시에 검증된 초과분은 그 R에 넣지 않는다. 따라서 R의 크기는 최대 4f+1이다. 검증 완료·admission 순서와 동시 event의 tie 처리는 명시하고 기록해야 하며, 서로 다른 leader가 같은 snapshot을 갖는다는 뜻은 아니다.

고정 R에 2f+1 공통-prefix 우선 규칙과 sum-LCP fallback을 적용한다. Support를 채우려고 window를 연장하거나 추가 ACK를 기다리지 않는다. Deadline에 보고가 2f+1보다 적으면 일차 조건은 성립할 수 없으므로 확보한 보고로 fallback하며, 보고가 없으면 유효 기본 ordering을 사용한다. Cut의 독립적인 no-wait 경로는 유지한다.

새 report나 block이 도착해도 timer를 재시작하거나 deadline을 연장하지 않는다. Deadline에 report가 없으면 유효한 기본 ordering을 사용한다. Cut이 먼저 준비되면 기존과 같이 준비된 유효 후보 또는 기본 ordering으로 진행한다. 다음 window도 새로 평가할 작업이 있을 때만 시작한다. τ는 leader-local duration이므로 Unix timestamp를 canonical ordering 기준으로 쓰거나 node들의 clock을 동기화할 필요가 없다.

n=5f+1에서 4f+1 distinct reports에는 적어도 3f+1명의 정직한 보고자가 포함되고 빠진 identity는 최대 f명이다. 이는 관측 coverage에 대한 산술적 사실이지 같은 prefix에 대한 지지나 execution 완료를 뜻하지 않는다. Byzantine f명이 침묵하면 strict 4f+1 조건은 정직한 노드 전부를 기다리게 되므로 deadline fallback이 필요하다. Deadline에 더 적은 report로 계산한 경우에는 위 coverage를 주장하지 않는다.

[검증 과제 D3] Local deadline은 검증·계산·전파 완료시간의 상한이 아니다. W개 reference만 받아도 frontier에서 먼 lane tip의 필수 ancestry는 W보다 길 수 있어, 후보 수·report 길이만으로 completion 비용이 bounded하다고 결론낼 수 없다. 권고하는 종료 계약은 snapshot의 후보 입력·사용 가능한 인증 자료를 고정하고 후보 생성·closure 확장·검증·optimizer에 유한 작업 예산과 yield/cancel 지점을 두는 것이다. 예산 안에 검증하지 못한 후보는 무효로 판정하지 않는다. 고정 비교 집합의 평가가 미완료이면 그 집합의 최장-prefix 선택을 완료했다고 선언하지 않고 새 direction 계산을 보류하며, cut은 이미 준비된 actual-parent 후보 또는 유효 기본 policy로 진행한다. 이후 비교 집합의 결정론적 한도·admission·예산은 명세할 선택으로 남긴다. 자료를 기다리려고 deadline/cut을 연장하지 않고 native proposal의 필수 validity·availability 검사를 생략하지 않는다. Invalid report가 first-valid identity 자리를 선점하지 않도록 하며 event queue·flood·stale 계산의 간섭도 검증해야 한다.

Snapshot 종료는 report 수집을 닫는 사건이다. Prefix의 보장 대상으로 채택되는 시점과 동일시하지 않는다. 보존 조건이 준비되기 전 cut이 ready이면 새 direction을 기다리지 않는 fallback 계약이 있다. 이미 보존 대상으로 채택한 prefix를 인증 뒤 기본 policy로 바꾸거나 버려서는 안 된다. 보고 기반 선택부터 보존 채택까지의 정확한 상태 전이와 준비되지 않은 prefix의 처리 방식은 새 요구를 만족하도록 명세해야 한다.

## 4 후보 검증과 direction 선택

고정 admissible 후보 집합의 평가를 완료했을 때, 각 유효 full candidate P에서 support≥2f+1인 nonempty prefix의 최장 길이를 구하고 그 길이가 집합 전체에서 최대인 후보를 우선한다. 모든 유효 permutation에 대한 전역 탐색 보장은 아니다. 평가가 미완료이면 최장 선택을 선언하지 않고 §3.3의 준비된 policy·기본 rule로 cut을 진행한다. 선택되는 것은 그 prefix를 가진 유효 full candidate order이며 prefix 밖의 input을 삭제한다는 뜻이 아니다. 그런 prefix가 어느 유효 후보에도 없으면 아래의 기존 sum-LCP로 fallback한다. Report가 없으면 유효한 기본 ordering을 사용한다.

Score(P; R) = Σᵢ |LCP(P, Rᵢ)|

첫 prototype의 bounded 후보 집합은 reported order와 incumbent에서 출발하며 모든 permutation을 탐색하지 않는다. 각 full candidate의 입력 범위·필수 predecessor closure·ancestry·actual-parent 유효성을 먼저 검사한다. 원본 report는 서명된 비교 원점·순서를 유지한다. Block digest와 lane/position의 대응, 길이 한도 및 native 중복 제거 규칙에 어긋나는 반복 reference를 검사하며, leader가 삭제·삽입·renumber한 목록을 원본 support로 세지 않는다. Candidate completion은 report를 바꾸지 않고 끝 이후 보충분도 support나 LCP에 포함하지 않는다. X→A→B에서 X를 제거해 A→B 지지를 만들 수 없으며, inherited frontier 이전 이력의 정당한 제외와 이후 임의 filtering을 구분한다. 유효성을 확인한 full candidate가 하나도 준비되지 않으면 report가 존재해도 actual-parent의 유효 기본 policy로 진행한다. 이는 2f+1 조건을 낮추거나 invalid candidate를 허용하는 fallback이 아니다.

동일 snapshot에서의 prefix 유일성은 닫을 수 있다. Identity당 exact report 하나이고 m=|R|≤4f+1이면, support≥2f+1인 두 prefix는 서로 prefix 관계다. 두 prefix가 갈라지면 하나의 exact report가 양쪽을 지지할 수 없어 지지 집합은 disjoint이고 최소 4f+2명이 필요하므로 모순이다. 따라서 유효 후보 집합에 존재하는 최장 supported prefix p*의 문자열은 유일하다. 남는 candidate tie는 같은 p* 뒤의 tail 선택이다. 이는 m≤4f+1인 report 집합 R 안의 사실이며 다른 snapshot·window·leader의 선택이나 canonical uniqueness/finality를 보장하지 않는다. Native recovery의 n−f..n vote pool은 별개이며 이를 더 큰 R로 대입해 이 유일성을 주장하지 않는다.

원본 support는 signed report의 전체 연속 prefix에 대해서만 센다. Candidate completion으로 새 support를 만들지 않는다. 이미 고정된 segment의 해석은 바꿀 수 없으며 selected prefix도 필수 ancestry와 actual parent에 대해 유효해야 한다.

Incumbent와 새 후보는 같은 최신 snapshot·frontier·horizon으로 비교한다. 서로 다른 window의 raw score를 직접 비교하지 않는다. 최장 supported prefix p*를 더 짧은 prefix나 높은 sum score로 바꾸지 않는다는 일차 우선순위는 유지한다. 같은 p*를 가진 full candidate들의 tail 선택은 두 구체화가 가능하다. 안 A는 유효 incumbent를 먼저 유지하고 나머지를 canonical rule로 정하여 churn을 우선 억제한다. 안 B는 이 tier 안에서 sum-LCP를 먼저 비교하고 동점에 incumbent·canonical rule을 적용하여 추가 prefix 총량을 고려한다. 어느 안과 hysteresis 적용 순서도 새로 채택한 것은 아니다. Supported prefix가 없는 fallback에서는 기존 sum-score 동점 유지·개선 폭 원칙을 사용한다. Suffix 확장·재정렬·무변화를 구분하고 update frequency를 제한한다.

[명세 선택 D2] 일차 기준인 2f+1 최장 supported prefix와 sum-LCP fallback은 채택되었다. 동일 p* 이후 tail의 안 A/안 B 및 hysteresis, candidate 입력 범위·completion, horizon W·한도·update 간격은 구체 선택이 남아 있다. 후보 보완으로 support를 만들어내지 않는 불변식은 두 안 모두 지켜야 한다. 어느 경로도 실제 CPU cost·총 작업량·f+1 완료시간의 일반적 최적성을 주장하지 않는다.

## 5 Proposal 결속과 exact prefix 보존

Direction을 수신한 validator는 leader/view, parent, references, revision의 유효성을 확인한 뒤 아직 시작하지 않은 작업의 scheduling을 조정한다. 이미 진행하거나 완료한 작업은 관측한 입력과 dependency를 검증하여 재사용하거나 필요한 부분만 다시 실행한다. Direction 자체가 execution correctness를 인증하지 않으며, 서로 다른 speculative root가 나왔다는 이유만으로 Byzantine behavior라고 판단하지 않는다.

Direction은 proposal 이전의 수정 가능한 실행 안내이고, authenticated ordering policy는 특정 proposal의 고정된 해석 규칙이다. Window 종료 때 report snapshot·후보 집합·horizon을 고정한다. 계산 결과는 원래 epoch/view·ordering 이력·실제 proposal parent·tip 원점·rule에 여전히 부합할 때만 준비된 후보가 된다. Cut이 먼저 준비되면 해당 proposal pass가 선택한 exact parent에 맞는 후보 또는 기본 policy를 한 번 선택한다. 늦은 report·optimizer 완료·vote-pool 증가는 인증된 같은 proposal의 policy를 바꾸지 않는다. 동시 event도 논리적으로 직렬화하여 한 번만 선택한다.

Parent 일치는 단순 version 확인이 아니다. Tips (A10,B8)에서 B+1→A+1은 B9→A11이지만 실제 parent가 (A11,B8)이면 B9→A12다. 맞는 후보가 없으면 actual-parent 기본 policy로 진행하며 이전 anchor를 강제로 유지하지 않는다. §3.2의 comparison frontier는 바꿀 수 없는 inherited segment와 새 direction으로 재정렬 가능한 segment를 나누는 ordering 경계다. Actual parent가 이미 이 구분을 포함한다면 이는 기존 문맥 규칙의 명확화다. 미완료 inherited segment는 원래 policy로 계속 해석하고 새 점수로 재선택하지 않는다. 경계 자체가 unresolved이면 report의 앞부분을 임의 삭제하거나 재anchor해 유효 후보인 것처럼 사용하지 않는다. 이 ordering frontier와 canonical execution input state의 materialization 여부는 별개다.

Native Multimmit의 tip 추출·extension과 settled/unsettled 처리를 유지하면서 exact order를 연결한다. 선택한 policy 내용 또는 재구성 가능한 commitment, 해석 rule과 exact parent·원점을 leader block의 인증 subject에 결속해야 한다. 다른 의미의 policy가 같은 subject로 검증되어서는 안 된다. Tips-only certificate 뒤에 leader가 임의 순서를 덧붙이는 것은 허용하지 않는다. Policy binding은 availability를 보장하지 않으므로 검증자와 recovery node가 같은 내용을 복구할 수 있어야 한다. Score 최적성이나 report count는 canonical validity의 필수 조건으로 추가하지 않는다. [\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md)

Fallback은 proposal 인증 전의 선택 규칙이다. 인증 뒤 policy 내용이 누락되었다고 같은 proposal을 기본 policy로 재해석해서는 안 된다. 인증된 내용을 복구하거나 기반 recovery 경로를 따른다. 첫 L-QC 관측을 모든 extension의 최종 위치가 확정된 사건으로 간주하지 않으며, native ordered delivery가 이미 방출한 prefix는 이후 pool 증가로 바꾸지 않는다.

Pinned Commonware에서는 LeaderBlock의 round·exact parent·tip history·chain proposals가 canonical digest에 들어가고 vote는 그 digest에 결속된다. Ordering policy field는 아직 없으며 TipRecord는 이전 commitment와 safe tips만 담는다. 따라서 tip-history opening만으로 Baton의 cross-lane policy를 복구할 수 없다. 같은 tips의 A→B와 B→A는 다른 순서이고 state 결과도 달라질 수 있다. Covering L-QC를 통한 re-anchor는 parent history를 가져오지 않고 agreement를 재개하는 경로이며 과거 dense order의 복원은 아니다. 인증된 policy·원점·rule, emission 근거와 durable cursor를 복구할 archive 또는 검증 가능한 checkpoint는 external marshal의 별도 의무다. Reporter는 lossy hint이고 Automaton::verify는 producer payload/parent의 validity·availability fence다. 어느 쪽도 이 ordering 이력의 durable handoff가 아니다. 이는 소스 경계 확인이며 새 Baton recovery의 구현·증명이 아니다. [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

Native extraction·extension으로 direction에 없던 block도 포함될 수 있다. 추가 block을 삭제하지 않으면서 채택한 exact prefix 앞·안에 끼우지 않는 completion이 필요하다. Known prefix 목록만으로 이후 native 입력을 임의 앞뒤에 붙이지 않는다. D+base-sweep은 검토 후보이며 채택된 continuation이 아니다. 보호 대상으로 채택되기 전 advisory 방향의 수정, actual-parent 불일치, 선택 prefix 밖의 tail은 repair가 남을 수 있다. 채택한 prefix 자체의 누락·삽입은 정상 경로의 허용된 결과가 아니라 막아야 할 설계 실패다.

2f+1 report support가 실제 B 지식을 뜻한다고 가정하면 n=5f+1에서 B를 모르는 node는 최대 3f명이다. 하지만 보고하지 않은 node, 낮은 position으로 투표한 node, vote pool 밖의 node는 서로 다르다. Byzantine 보고자 최대 f명을 빼면 확인된 정상 지지자는 f+1명이며, n−f pool에서 그중 최대 f명이 빠질 수 있다. 이 산술만으로 3f+1 positive position votes를 확보하지 못한다.

Native finalized proposal position은 (3f+1)번째로 큰 position이다. B가 ordinary proposal payload(position j≥1)라면 pool 안의 position≥j vote가 3f+1개 이상이어야 finalized position이 j 이상이다. Native extension carry는 별도로 finalized position이 proposed tip과 같고 동일 branch의 extension에 n−f support가 있어야 한다. Safe V-QC의 f+1 position rank·2f+1 extension carry와 구분한다. [\[12\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143) [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

분석적 transcript 사례의 전제는 f=1,n=6,d≥1, 유효한 authenticated parent의 chain tip/base G, 그 다음 유효 block B, 그리고 완성된 DA certificate 없이 locally verified/DA-voted B를 intention candidate에 허용하는 것이다. h1·h2는 B와 parent를 검증하고 local DA-vote한다. b도 B를 report하지만 Byzantine이다. 다른 정상 h3–h5는 아직 B에 DA-vote하지 않았다. Scheduled leader h1은 G를 anchor로 B를 payload position 1에 넣고, 다른 chains는 유효한 공통 anchor에 둔다. 단 하나의 유효 proposal과 정상 parent/history를 가정하고 h2의 view vote만 지연한다. h1·b·h3·h4·h5가 같은 proposal에 positions [1,0,0,0,0], empty extensions로 투표하면 n−f=5 pool의 네 번째로 큰 position은 0이다. Proposal validity는 이 local DA history 차이를 금지하지 않는다. [\[13\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978) [\[14\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L2601)

이 사례에서 B를 모르는 정상 node는 3명뿐이다. 네 개의 낮은 vote 중 하나는 알고도 낮게 투표한 b이며, B를 지지하는 정상 h2는 pool 밖이다. Finalized tip은 G이고 proposed tip B에 미달하므로 unsettled이며 Emit은 미확정 위치에서 멈춘다. B가 영구 제외되거나 뒤의 block을 임의 방출한다는 반례는 아니다. 완성된 Baton의 후보 validity가 DA certificate를 요구한다면 이 uncertified B 사례는 admissible하지 않을 수 있다. 소스 규칙에 대한 분석이며 실행 trace/시험 결과가 아니다.

다른 경우는 B 또는 B보다 높은 같은 chain의 block이 유효 DA-certified anchor가 되는 것이다. Proposal의 position 0은 그 anchor이고 native final-tip 추출은 그 base부터 시작한다. 따라서 낮은 positions만으로 base의 ancestor B를 빼지 못한다. Leader가 보유한 highest DA certificate를 anchor로 삼는 경로가 있으므로 각 lane의 selected-prefix 끝을 미리 certified anchor로 확보하는 것은 검토할 보존 조건이다. Certificate/body/ancestry의 복구 가능성, actual-parent 및 frontier 정합성, cross-lane leading order와 view-change compatibility는 별도로 증명해야 한다. [\[15\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1880) [\[12\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143)

원문 Theorem 3의 stronger inclusion 조건은 correct producer의 B와 intervening path를 모든 correct processor가 view vote 전에 DA-vote하고 B가 Tips(Q) 위 e 이내에 있는 것이다. Ordinary proposal에서 B까지 3f+1 positive positions가 이미 있는 경우도 inclusion의 직접 충분조건이다. 이는 2f+1 intention report만의 보장이 아니다. 논문 §5.3의 Theorem 3 및 Corollary 2와 pinned source의 custody 계약을 구분한다. [\[10\]](https://arxiv.org/pdf/2607.21021v2) [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

Native 보존을 위한 미채택 연결 후보는 이미 준비된 certified anchors를 갖춘 prefix만 보존 대상으로 채택하는 방식과, proposal/vote validity에 prefix의 positive native adoption 조건을 추가하는 방식이다. 전자는 원래 tip extraction을 재사용할 여지가 있으나 direction의 eligibility를 제한하고, 후자는 추가 입력/DA-vote 대기로 liveness와 no-wait 계약을 바꿀 수 있다. 두 방식 모두 exact cross-lane prefix와 recovery 증명이 필요하다. Prefix가 아직 준비되지 않았는데 모든 ready cut이 반드시 이를 보존해야 한다면, 이를 버리는 fallback과 동시에 만족시킬 수 없다. 사용자 요구는 채택되었지만 이 실현 방식은 미채택이다.

## 6 Slot과 recovery 계약

Safety의 출발점은 report 수나 score가 아니라 인증된 해석과 irrevocable exact input이다. 다음은 검토 중인 policy 계열의 조건부 prefix 보조정리다. 한 segment에서 공통 이력 H·tip 원점 T·고정 sweep σ를 사용하고, σ가 ancestry를 지키며 모든 slot을 한 번씩 유한 순위에 열거한다고 하자. 추출 결과 F와 settledness S가 동일 block identity의 공통 completion G와 양립하고, settled chain은 G에서 더 늘지 않는다고 가정한다. σ를 따라 포함 block을 출력하고 settled-empty slot은 건너뛰되 unsettled-empty slot에서 멈추는 Emit(F,S)는 Ord(G)의 prefix다.

이유는 출력 전에 방문한 각 slot이 G와 같은 block을 내거나 G에서도 빈 위치이기 때문이다. 미확정 빈 위치를 넘어가지 않으므로 G의 predecessor를 누락한 채 뒤의 block을 출력할 수 없다. 따라서 서로 다른 유효 pool의 출력도 같은 Ord(G)의 prefix로서 양립한다. 단, 공통 completion·settledness 가정은 native extraction/branch 규칙에서 독립적으로 도출해야 한다. 같은 tip 집합마다 결정론적으로 재정렬하는 것만으로 extension 간 prefix 보존이 따라오지는 않는다. [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

Adapter의 권고 slot 상태는 included(digest d), irrevocably-empty, unresolved다. Slot은 인증 segment·lane·height로 식별하고 d는 application body commitment와 구분되는 canonical producer-header identity를 가리킨다. 같은 segment에서는 unresolved에서 두 terminal 상태로만 이동하며 included digest·포함 여부와 empty 판정을 유효 extension·recovery가 번복하지 않는다. Terminal 판정을 정당화할 native 증거가 없으면 unresolved에 둔다. Included는 방출, empty는 skip, unresolved는 stop이고 부재·local timeout으로 skip하지 않는다. Empty는 그 segment의 contribution에서 제외됨을 뜻한다. 다음 segment에 같은 lane height의 block이 나타날 수 있으므로 전역 blacklist로 사용하지 않는다.

Native settledness에는 proposed tip까지 도달한 position과 β+(n−|P|)≤f가 필요하다. β는 finalized tip보다 뒤를 지지한 pool vote 수다. n=6,f=1에서 position이 proposed tip이고 β=1이면 |P|=6은 settled이지만 그 vote를 포함한 5개 subset은 unsettled일 수 있다. Finalized tip이 같아도 skip 근거는 같지 않다. 이는 native predicate의 분석적 사례이며 실행 결과가 아니다. 복구 시 tips만 또는 임의 quorum subset만 남겨 원래 pool의 더 긴 emission을 그대로 정당화하지 않는다. 해당 terminal 판단을 검증할 authenticated evidence나 그 방출 이력을 보존하는 검증 가능한 checkpoint가 필요하다. 원문의 Lemma 7·8은 same-view tip compatibility/settledness와 공통 sweep을 연결하며, 변경한 policy의 공통 completion을 자동 증명하지 않는다. [\[10\]](https://arxiv.org/pdf/2607.21021v2) [\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md)

오래된 context와 leader 교체. 다른 parent·epoch·view의 report와 계산 결과를 현재 proposal에 결합하지 않는다. 새 leader와 recovery node는 local arrival order나 마지막 advisory direction 대신 exact anchor와 인증 이력에서 과거 segment의 policy·원점·rule을 복구해야 한다. 미완료 inherited segment도 원래 policy로 해석하고 새 policy는 native 규칙이 허용하는 새 segment에만 적용한다. 필요한 귀납 불변식은 ‘새 view의 canonical 순서가 이전 인증 이력에서 정상 node들이 합법적으로 방출한 모든 prefix를 확장한다’이다. 자신의 마지막 prefix나 chain-local tips 보존만으로는 부족하다. 원문의 Theorem 1은 참조된 V-QC 이력의 Ord 재귀와 Lemma 8을 연결한다. Baton도 각 참조 segment의 인증 policy가 그 재귀에서 보존된다는 추가 의무를 닫아야 한다. Consensus retention/re-anchor와 별개로 marshal의 방출 cursor와 필요한 policy·terminal 근거가 recoverable해야 하며, proof hash만 남기는 것은 내용 복구를 대신하지 않는다. Archive 또는 checkpoint의 구체 선택은 미정이다. Segment 내부 보조정리와 이 귀납 불변식의 native 대응은 미완료 통합 의무다. [\[10\]](https://arxiv.org/pdf/2607.21021v2) [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

새 요구에 따라 위 조건부 common-completion 계약은 각 valid proposal/recovery order가 보존 대상으로 채택한 p를 선두에서 유지한다는 조건도 포함해야 한다. Authentication된 prefix 자체와 그 native inclusion·availability 근거를 다른 의미의 policy나 anchor로 재해석하지 않는다. 이는 증명해야 할 추가 의무이며 slot representation만으로 성립하지 않는다.

## 7 실행 statement와 결과 인증

State finalization은 대상 구간의 irrevocable exact order와 canonical input state 연결, 그리고 동일 statement에 대한 서로 다른 해당 epoch validator f+1명의 유효 실행 서명을 모두 검증했을 때 수용한다. 이 endpoint는 채택된 설계다. Leader 서명·V-QC·높은 score만으로 수용하지 않는다. Speculation은 그전에 계속할 수 있지만 canonical 채택에는 두 조건이 모두 필요하다. 결과 인증과 local body fetch·apply·durable 저장 완료는 구분한다. [\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md)

실행 statement는 replay domain/epoch, canonical 구간의 시작·끝과 exact ordered input, 올바른 input state, runtime 및 결과에 영향을 주는 환경, 전체 output result를 모호함 없이 식별해야 한다. 이는 논리적 서명 대상이며 wire encoding은 미정이다. 같은 구간의 QC transcript가 달라도 statement identity는 같을 수 있다. 반대로 같은 proposal이라도 실행 범위나 input state가 다르면 별개 statement다.

선택한 intention prefix, irrevocably emitted prefix, 서명 구간은 서로 다른 대상이다. 선택 prefix의 보존은 authenticated policy와 §4의 공통 completion·recovery 가정에 의존하며, unresolved slot이 방출을 막으면 cut 시점에 선택 prefix 전체가 emitted되었다고 볼 수 없다. 2f+1 reports의 A→B 지지만으로 A→B→C→D의 실행 certificate가 생기지도 않는다. 공통 서명 경계가 B에 있고, A→B의 irrevocable order와 canonical input state가 확인되며, 직접 실행·검증된 같은 statement의 서명이 모여야 B까지 인증할 수 있다. 경계가 D라면 지지자들도 C→D를 실행·보정해야 한다. 따라서 §2.3의 공통-prefix 이득을 completion에 연결하려면 전역적으로 해석 가능한 서명 경계와 중간 결과의 재제공이 필요하다.

정직한 signer는 exact 문맥에서 직접 실행한 결과를 검증한 뒤 서명한다. 다른 node의 receipt나 signature를 복사해 자신의 실행 서명을 발행하지 않는다. Signer를 특정 ordering QC의 투표자 부분집합으로 제한하지 않으며, 늦게 따라온 해당 epoch validator도 참여할 수 있다. Identity 중복은 한 번만 센다. 긴 speculative root나 다른 범위의 서명을 잘라 짧은 구간의 결과로 사용할 수 없다.

결과 안전성은 별도 조건부 논증이다. 최대 f Byzantine identities, 인증된 epoch membership, 서명 위조 불가, 서명 subject의 모호함 없는 encoding과 사용한 digest의 collision resistance, deterministic execution 및 정직한 직접 실행·검증을 가정하면 f+1 matching signatures에는 정직한 signer가 적어도 한 명 있다. 따라서 그 결과는 서명된 exact 문맥의 결정론적 결과다. 수용자가 구간의 irrevocable order와 canonical input state 연결까지 확인하면 잘못된 canonical 결과는 수용되지 않는다. 동일 exact 문맥의 두 결과 certificate가 다르다면 각각의 정직한 signer가 다른 결정론적 결과를 계산했다는 모순이다. 두 f+1 signer 집합 사이의 교집합은 필요하지 않으며, f+1을 ordering quorum으로 쓰지 않는다.

첫 구간의 input state가 정당하고 각 후속 구간이 검증된 이전 output에 정확히 연결되면 이 논증을 구간별로 적용한다. 다른 parent에서 올바르게 계산된 결과도 canonical parent 확인 없이는 수용하지 않는다. Cache 재사용은 read 관측값·write·failure·fee·event와 dependency 검증을 통과해야 하며 stale completion은 배제한다. Unfinalized effect는 speculative 상태에 두고 확정 state를 direction 변경으로 rollback하지 않는다.

## 8 보관과 진행성

진행성은 ordering, ordered delivery, 결과 인증을 분리한다. 첫째, 기반 Native Multimmit의 진행성 가정, consensus 작업의 공정한 처리, fallback 필수 검증의 유한 종료 아래 report나 optimizer 없이 준비된 유효 policy 또는 기본 policy로 proposal을 진행할 수 있다. 고정 deadline과 단일 window 종료는 report 경로의 무한 대기를 막지만 자원 경쟁이나 동일 latency를 보장하지는 않는다.

둘째, 고정 sweep에서 포함 block의 slot 순위가 유한하고 앞선 모든 slot이 결국 동일 block 또는 정당한 settled-empty로 판명되면 Emit은 그 block까지 전진한다. 앞선 유한개 slot의 확인이 끝나기 때문이다. Finite rank만으로 unresolved slot이 풀리는 것은 아니므로 native 증거의 eventual resolution을 함께 요구한다. 이 논증은 native inclusion 자체나 고정 시간 상한을 보장하지 않는다.

셋째, canonical order·input state·body/runtime 자료가 결국 준비되고, 같은 공통 실행 경계에 대해 적어도 f+1 정상 validator가 직접 실행한 statement를 제공하며, 서명이 재요청·전달·검증될 수 있다면 결과 인증도 결국 완료된다. 각 node가 자기 최신 prefix에만 서명하면 모두 정직해도 범위가 달라 certificate가 모이지 않을 수 있다. Catch-up이 중간 경계를 건너뛰어도 필요한 결과를 보관하거나 재실행해 제공할 수 있어야 하며 단일 collector가 유일한 서명 보관본이어서는 안 된다. 다른 signer의 certificate를 기다린 뒤에만 다음 speculation을 시작하는 새 barrier는 요구하지 않는다. [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

권고하는 보관·복구 계약은 signer가 canonical statement와 signature를 재제공하고, collector 교체가 statement·범위·policy·epoch를 바꾸지 않는 것이다. 그러나 유한 local TTL만으로 안전한 garbage collection을 정의할 수는 없다. 예를 들어 f=1에서 같은 statement를 두 정상 signer가 만들었어도 유일 collector가 조립 전에 실패하고, 재요청이 두 signer의 삭제 시점 뒤에 도착하면 복구가 막힐 수 있다. 서명·중간 결과와 재실행에 필요한 과거 state/input도 남아 있지 않은 경우의 분석적 반례이며, 이미 수용된 결과의 오류를 뜻하지 않는다.

따라서 결과 인증의 eventual completion은 요청을 서비스하기로 한 구간에 대해 matching 서명 또는 직접 재실행·검증해 서명을 재생성할 자료가 결국 접근 가능하다는 조건을 포함한다. 삭제 전에는 그 의무를 유지할 certificate/결과 보관본이나 재구성 경로, 또는 명시적 service 범위 밖으로 넘기는 검증 가능한 checkpoint 조건을 정해야 한다. Checkpoint 선언만으로 아직 완료하지 못한 요청의 제공 의무를 없애지는 않는다. 현재 state root만으로 과거 중간 결과·서명을 복원할 수 없고, f+1 서명은 보관본의 durability/availability를 인증하지 않는다. 무기한 모든 과거 구간 제공과 bounded storage를 동시에 무조건 약속하지 않는다. 정확한 retention·checkpoint·GC 방식은 미채택이며 새 quorum·승인 round를 이 문장으로 추가하지 않는다.

여기서 no-wait는 direction 수집·계산·승인의 완료를 native consensus의 선행조건으로 두지 않는다는 계약이다. 2f+1 supported prefix가 없어도 sum-LCP 또는 유효 기본 ordering으로 진행하며, support를 채우기 위해 cut을 늦추지 않는다. Native availability·settledness·body retrieval·canonical-parent readiness·application dependency 대기는 남는다. 고정 policy의 앞선 unsettled slot x 뒤에 준비된 y가 있어도 x가 해결되기 전에는 y를 canonical prefix로 내보낼 수 없는 경우가 있다. 높은 prefix support가 이 head-of-line blocking이나 자원 간섭을 없애거나 latency 상한을 주지는 않는다.

[통합 의무 P2] 공통 completion, 인증 이력에 걸친 prefix 확장, 동일 execution statement의 복구·제공 조건을 Native Multimmit 경로에서 증명해야 한다. 위 논증은 명시한 가정의 귀결이며 완성된 native safety/liveness 증명이나 Byzantine fault-injection 결과가 아니다. Policy·window·공통 서명 범위의 남은 명세 선택은 §7에 정리한다.

## 9 미채택 선택

구현 전 남은 구체 선택은 report 생성·인증된 window 인지, policy 표현·continuation, 공통 실행 서명 범위다. §3의 원본 support·불변 frontier·한 번의 snapshot 종료 규칙은 어떤 구체화를 택해도 지켜야 한다. First-valid report admission과 검증 완료 순서, 동시 event tie, 후보 입력 범위의 세부 설정은 아직 명세해야 한다.

Policy 전달의 권고안은 크기가 제한된 canonical policy bytes를 proposal에 함께 넣고 일반 proposal 검증에서 확인·보관하며, recovery 시 같은 bytes를 복구하는 것이다. Commitment-only 표현을 택하면 별도의 내용 availability·retrieval 의무가 필요하다. 어느 표현도 미채택 상태이며 별도 direction 승인 round를 요구하지 않는다. Continuation의 한 후보는 기본 sweep의 유한 initial prefix를 ancestry-preserving permutation으로 바꾸고 그 뒤는 원래 sweep을 유지하는 방식이다. 정확한 범위·encoding은 선택 전이며, D+base-sweep이나 이 유한-permutation 안이 이미 채택되었다고 보지 않는다.

공통 실행 경계의 권고안 A는 매 canonical block 경계에 deterministic statement identity와 직전 canonical state를 연결하고 중간 checkpoint를 재제공하는 방식이다. Prefix 끝을 직접 인증하기 쉽지만 서명·보관 수가 늘 수 있다. 대안 B는 결정론적 multi-block 구간과 공통 short-tail 종료 규칙을 정하는 방식이다. 서명 수를 줄일 여지가 있지만 prefix 이득이 다음 경계까지 인증되지 않을 수 있다. Local timeout이나 각 node의 최신 prefix로 공통 경계를 정의하지 않는다. 두 안 모두 미채택이며 §3.4의 A→B 지지와 A→B→C→D 인증을 구분한다.

먼저 단일 epoch 안의 구간으로 한정하는 방식이 명세상 단순하다. 재구성을 포함하려면 authenticated transition checkpoint, 서명 membership의 전환 규칙과 이전 certificate 보관을 정해야 한다. 이 역시 검토안이며 승인 없이 reconfiguration 기능을 추가하지 않는다. 이미 채택한 Native Multimmit·2f+1 prefix 우선·4f+1-or-deadline·f+1 endpoint는 유지한다. 구체 명세 뒤에도 native extraction·recovery가 §4의 가정을 보장한다는 통합 증명은 남는다. [\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md)

Same-supported-prefix tail의 권고 기본값은 유효 incumbent를 유지하고 없으면 canonical tie-break하는 것이다. Churn을 줄이지만 높은 sum-LCP tail을 포기할 수 있다. Sum-first는 보조 score를 우선하고 hysteresis는 추가 threshold/update 계약이 필요하다. 이 권고도 미채택이며 first-tier longest-prefix 규칙을 낮추지 않는다.

네 기존 선택은 모두 미채택이다. Per-block signing은 statement/range와 common-boundary 결과 liveness 계약을, tail 선호는 결정론적 direction 갱신을, inline policy 여부는 proposal encoding/availability/recovery interface를, finite-prefix permutation 여부는 concrete continuation와 공통 prefix 증명을 각각 막고 있다. 최신 direction-preserving cut 요구는 이 네 항목을 자동 결정하지 않는다. τ·W·budget 수치와 실익은 이후 구현·측정 대상이다.

## 10 소스 대응

Pinned source는 Commonware commit 534af0ede48affd35b2111522527547b4cc9bf72다. Native leader digest/vote binding은 types/block.rs·vote.rs, tip-history commitment는 types/history.rs, final/safe tip rank와 settlement는 machine/algebra/tips.rs, local DA history에 따른 proposal/vote는 machine/chain.rs, exact-parent proposal eligibility는 machine/view.rs에서 확인했다. Source inspection은 완성된 Baton의 proof를 대신하지 않는다.

[\[6\]](https://github.com/djm07073/overpass-research/blob/main/overpass-prefix-plan.md) Overpass design memo. Native Multimmit 및 policy·결과 인증 채택 조건, §§7.1–7.2.

[\[7\]](https://github.com/djm07073/overpass-research/blob/main/overpass-submission-readiness-review.md) Overpass submission-readiness review. 조건부 ordering·recovery와 실행 서명 범위 검토, §§23–25.

[\[10\]](https://arxiv.org/pdf/2607.21021v2) Lewis-Pye and O’Grady. Multimmit: Extending Blocks for Faster Finality. arXiv:2607.21021v2, §§4.2, 5.1, 5.3 (Lemmas 7–8, Theorem 1, Corollary 3).

[\[11\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md) Commonware monorepo, pinned commit 534af0ede48affd35b2111522527547b4cc9bf72. Multimmit STATE_MACHINE.md; types/block.rs, vote.rs, history.rs; machine/algebra/tips.rs. Consensus/marshal ownership, re-anchor 및 settledness 경계.

[\[12\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143) Pinned tips.rs — FinalTipAccumulator::final_tips, FinalTips::from_prepared; proposed rank, extension support, settlement. [\[13\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978) Pinned chain.rs — begin_vote_body_pass/resume_vote_body_pass; local DA history가 없으면 position 0. [\[14\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L2601) Pinned view.rs — valid_proposal/proposal_extends; exact authenticated parent·anchors·history. [\[15\]](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1880) Pinned chain.rs — proposal pass; certified anchor 선택과 locally DA-voted payload suffix.
