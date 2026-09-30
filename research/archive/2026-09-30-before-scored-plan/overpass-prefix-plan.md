# Overpass: Common-Prefix Discovery and Leader-Guided Adjustment

> 2026-09-30 대화 결정 기록. 연구 설계이며 구현·안전성 증명·성능 검증 완료가 아니다. [논문 개요](overpass-plan-ordering-outline.md)의 plan 경로를 구체화한다.

## 1. 목적과 이번 결정

**같은 기준 cut·canonical parent에서 시작하는 예정 순서의 공통 prefix를 3f+1 지지로 찾아 활용한다. 공통 prefix가 없으면 leader가 유효한 조정안을 제안하여 노드들이 그 순서를 채택하게 한다.**

노드가 이미 실행한 순서와 일치하는 경우에만 투표하는 방식이 아니다. 처음 맞추는 과정의 재실행은 허용하고, 이후 late block마다 기존 순서가 반복해서 뒤집히는 것을 줄인다. 계획 수립·수용은 block 생성·전파·sync·실행과 병렬로 진행한다.

현재 profile은 n=5f+1, 최대 f Byzantine identities, plan support 목표 q=3f+1이다. Producer lane이 아니라 validator identity 단위로 계수한다. 동일 validator가 여러 lane을 담당해도 한 표다.

## 2. 보고하는 것은 예정 순서다

보고에는 epoch, leader view, report/plan round, 기준 finalized cut, canonical parent, ordering-rule version, exact ordered block references를 묶어 서명한다. 실행 완료 위치·state root·실행 proof는 요구하지 않는다.

- 보고는 scheduler가 따르려는 순서의 제안이다. 이미 동일하게 실행했다는 증거가 아니다.
- 공통 prefix는 동일한 기준점부터 block hash와 순서가 정확히 같아야 한다. 중간의 공통 조각, subsequence나 상대 순서 일치로 대체하지 않는다.
- 각 counting context에서 validator당 하나의 불변 보고만 계수한다. 갱신은 새 context로 분리하며 서로 다른 rounds/revisions의 표를 섞지 않는다.
- Prefix 지지는 서명된 전체 sequence가 그 prefix로 시작한다는 것을 확인하여 얻을 수 있다. 서로 다른 suffix는 허용한다.
- Referenced blocks의 ancestry와 필요한 입력 유효성·가용성 근거를 검증한다. 서명된 예정 순서 자체를 DA 증거로 취급하지 않는다.

정확한 wire encoding, report retention과 round 전환은 후속 설계 항목이다. 위 context 분리는 중복 계수 방지를 위한 요구사항이다.

## 3. 경로 A: 공통 prefix 발견

Leader는 보고들을 prefix trie로 구성하고 각 prefix를 지지하는 distinct validator 수를 센다. q 이상 지지받는 가장 긴 유효 prefix를 찾아 근거 보고와 함께 전파한다.

```text
n=6, f=1, q=4; 동일 기준 cut·parent

V1: A → B → C → X
V2: A → B → C → Y
V3: A → B → D
V4: A → B → E
V5: X → A → B

선택: A → B  (V1,V2,V3,V4)
V5의 중간 A→B는 지지로 세지 않는다.
```

**보고 q개 도착 ≠ q-supported prefix 존재.** 첫 blocks부터 다르면 비어 있는 prefix만 공통일 수 있으며 이는 새 진행으로 세지 않는다. 기존 채택 prefix를 모두 보고한 경우에도 그보다 긴 prefix가 없으면 새 확장은 없는 것이다.

이 경로는 보고들을 절충해 불일치 점수가 작은 새 순서를 합성하는 optimizer가 아니다. 이미 지지받는 정확한 prefix를 발견한다.

## 4. 경로 B: Leader가 순서 조정을 제안

새로운 q-supported prefix가 없으면 leader가 하나의 유효한 후보를 제안한다. 후보는 같은 parent, 필수 producer ancestry·application 선행 제약을 지키고 현재 유지하는 prefix를 확장한다. 아직 확정되지 않은 suffix는 기본 ordering rule로 구성한다. 임의 dependency를 무시하거나 누락된 필수 선행 block을 뒤에 배치하지 않는다.

```text
기존 예정 순서:
V1: A → B → C
V2: B → A → C
V3: C → A → B

Leader 조정안: A → B → C
       ↓
정상 validators: 유효성 확인 → 예정 순서 채택 → support 전송
       ↓
동일 조정 prefix에 대한 3f+1 support
```

- 정상 validator는 자신의 기존 예정 순서와 다르다는 이유만으로 거부하지 않는다.
- 아직 시작하지 않은 작업은 새 순서로 scheduling한다. 수행 중·완료 작업은 read dependencies 등을 재검증하고 필요한 부분만 재실행한다.
- **순서 채택에 대한 support는 재실행 완료를 기다리지 않는다.** 따라서 support를 실행 인증으로 사용할 수 없다.
- 한 조정 round에서 leader 후보는 고정한다. 늦은 X가 도착해도 수집 중인 후보 앞에 삽입하거나 같은 round의 내용만 바꾸지 않는다. X는 다음 확장에 반영한다.
- 발견 보고와 조정 support의 subject/phase를 구분한다. 예전 보고와 새 조정 support를 임의 합산하지 않는다.
- Leader equivocation으로 support가 갈리면 같은 round에서 중복 서명하지 않고 새 round/leader로 넘어가야 한다. 정확한 전환·회수·stale support 처리는 검증 과제로 남긴다.

공통 prefix 탐색을 얼마나 기다린 뒤 조정 경로로 갈지의 decision window는 성능 설정이다. Timeout은 비수신 증명이나 canonical 결정이 아니다.

## 5. Quorum이 보장하는 것과 보장하지 않는 것

동일 counting context에 대해 정상 validator가 충돌하는 sequence/prefix에 중복 서명하지 않는다는 조건 아래:

```text
n = 5f+1, q = 3f+1
두 q 집합의 교집합 ≥ 2q−n = f+1
→ 정상 identity가 최소 1명 포함
→ 동일 context에서 서로 양립 불가능한 두 prefix의 동시 q-support 방지

한 q 집합의 정상 signer ≥ q−f = 2f+1
```

서로 포함관계인 prefix들의 인증은 충돌이 아니다. 이 논증은 **서로 다른 report/adjustment rounds·leader views를 넘는 불변성이나 ordering finality를 증명하지 않는다.** 그런 증명 없이 과거와 현재 support를 합치거나 가장 큰 round를 무조건 canonical로 고르지 않는다.

정상 leader, 안정된 동일 문맥, 검증 가능한 유효 후보, 충분한 데이터 복구와 eventual synchrony 아래 정상 노드는 최소 4f+1명이므로 Byzantine 협조 없이 q를 모을 수 있다. 모든 round 성공·무조건적인 시간 상한·실행 완료는 보장하지 않는다.

## 6. Prefix 유지, cut과 finality의 경계

정상 leader 경로에서는 채택한 prefix의 앞/내부에 늦은 block을 삽입하지 않고 다음 plan과 cut 후보가 이를 확장하도록 한다. 같은 parent에서 그 prefix대로 실행한 작업의 late-insertion invalidation을 줄이려는 정책이다.

Plan support는 변경 가능한 사전 순서 채택이며 **별도 ordering finality나 leader 교체를 넘는 영구 lock이 아니다.** 기반 합의의 안전한 후보·parent가 우선하고, plan이 양립하지 않으면 실행을 보정한다. Byzantine leader도 plan을 반드시 보존한다고 주장하지 않는다.

최종 cut은 tips와 실제 선택한 exact order 또는 그 검증 가능한 commitment를 함께 인증해야 한다. Tips-only 인증 뒤에 다른 순서를 붙이지 않는다. Plan과 다르다는 이유만으로 기반 합의상 유효한 cut을 무조건 거부하는 규칙은 현재 채택하지 않는다.

Block 생성·전파·실행은 report/support 수집 중에도 계속한다. q가 안 모였다는 이유로 cut이 무조건 기다리는 barrier를 두지 않는다. 아직 완료되지 않은 조정은 canonicality를 얻지 않으며, finalized cut 도착 후에는 exact input에 맞춰 검증한다. 실제 cut proposal 이후의 plan 갱신이 이미 보낸 proposal/vote를 바꾸지 않게 해야 한다.

이 설계는 fallback에서 cut 전 순서 조율을 위한 추가 통신을 수행한다. 작은 cut과의 차이는 plan이 finality를 제공하지 않는다는 데 있지만, **이름만 다르다고 더 저렴한 것은 아니다.** 더 잦은 cut·early proposal 대비 비용과 latency를 측정해야 한다.

## 7. 최소 평가와 남은 의무

- Discovery 성공률, 발견한 새 prefix 길이, 조정 fallback 비율, q 형성 시간과 report/support bytes.
- 초기 조정에 필요한 재실행과 이후 late-insertion 재실행을 분리 계측한다.
- Leader에게만 X가 늦은 경우, 다수 노드에 늦은 경우, 공통 중간 조각만 있는 경우를 비교한다.
- 동일 round equivocation, round 간 상충 support, leader 교체, stale parent, 미완료 plan 중 cut 확정을 검증한다.
- Post-cut / unguided speculation / discovery-only / discovery+adjustment / early proposal / frequent cuts를 동일 조건에서 비교한다.
- Cut-to-state와 ingress-to-state, ordering latency, goodput, backlog, 총 실행량과 통신 비용을 함께 보고한다.

미완성 항목은 report/adjustment context 전환, equivocation recovery, plan update 한도, input availability 경로, cut 제안과 늦은 support의 경계, 변경된 ordering adapter의 safety/liveness다. Prefix quorum 선택은 설계 결정이고 완성된 BFT protocol의 증명은 아니다.
