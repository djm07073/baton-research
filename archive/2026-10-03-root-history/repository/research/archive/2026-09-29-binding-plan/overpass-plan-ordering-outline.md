# Overpass: Plan-Assisted Pipelined Execution in Autobahn-Family Consensus

> 새 연구 개요 · 2026-09-29 · 설계 및 검증 계획이며, 완성된 BFT protocol이나 실험 결과가 아니다.
> 이 문서가 현재 연구 방향의 기준이다. 이전 producer placement·proof/PAC 설계는 [archive](research/archive/2026-09-29-before-plan-ordering/README.md)로 분리한다. 기존 manuscript와 Commonware fork는 아직 이 설계를 구현하지 않는다.

## 연구를 한 문장으로

**블록 전파와 cut consensus가 진행되는 동안 계속 speculative execution하고, 연속적인 plan 합의로 이미 수행한 실행의 순서가 뒤늦은 block 삽입 때문에 바뀌는 것을 제한하여 state-finalization latency를 줄인다.**

핵심은 새로운 execution engine이나 producer placement가 아니다. 실행을 미리 시작하는 pipeline과, 그 이득을 보존하기 위해 cut 전에 순서 제약을 합의하는 consensus 확장이다.

### 이번에 선택한 설계와 경계

- Base ordering은 기존의 공통 ordering rule이다. Relative-height round-robin은 가능한 예일 뿐 필수 조건이 아니다.
- Plan은 실행 순서에 대한 제안·합의다. 실행 완료, 올바른 state root, transaction 성공을 인증하지 않는다.
- Plan은 단순히 두 block의 상대 순서만 정하는 것이 아니라, 정확히 지정된 prefix와 그 내부·앞쪽에 새 block을 삽입하지 않는 경계를 보호한다.
- Leader가 연속적으로 plan을 제안하고 votes를 수집한다. Plan이 아직 없어도 block 생성·전파·speculative execution은 진행한다.
- **Cut을 시작할 때 leader는 진행 중인 마지막 plan을 마무리하고, 새 plan 제안을 멈춘 뒤 곧바로 cut을 제안한다.** 마지막 plan이 없다면 이미 인증된 마지막 plan까지를 경계로 삼는다.
- Cut은 마지막 plan까지의 제약과 tips를 함께 묶어 최종 입력·순서를 확정한다. 단순 checkpoint가 아니다.
- Plan에 맞지 않는 local work와 아직 보호되지 않은 suffix는 재검증·필요 시 재실행한다. Canonical state를 speculative state로 덮어쓰지 않는다.
- Producer placement, state-isolated ownership, ZK/folding/PAC, receipt bridge와 repair lane은 이번 제안에 포함하지 않는다.

## 1. Introduction

### 문제 → 접근 → 후속 문제 → 해결

Autobahn-family 구조는 병렬 block dissemination과 cut agreement를 분리한다. 그러나 ordering 이후 application 실행을 시작하는 구성에서는 execution과 결과 확인 비용이 state finalization까지의 경로에 남는다. 이는 기존 연구가 execution을 전혀 다루지 않았다는 주장이 아니라, **ordering과 execution을 연결하는 방식에서 개선할 수 있는 latency**에 관한 문제 제기다. [Autobahn](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)

Overpass는 수신한 block을 cut 전에 실행한다. 그 결과 execution과 dissemination·consensus가 겹치지만, 늦게 도착한 predecessor가 이미 실행한 순서 앞에 들어오면 speculative work가 무효화될 수 있다. 따라서 일찍 실행하는 것만으로는 이득이 보장되지 않는다.

우리는 기존 순서를 매번 처음부터 다시 계산하는 대신, **plan 합의로 보호한 prefix는 유지하고 나머지 구간에서만 기존 ordering rule을 적용**한다. Leader는 마지막 plan을 마무리한 뒤 tips와 함께 cut을 제안한다. 실행은 이 합의 절차와 독립적으로 계속되며, 최종 cut과 맞지 않는 부분만 복구한다.

### 연구 질문과 기여 후보

> Block production과 speculative execution을 plan 합의 대기로 막지 않으면서, cut 이전에 보호한 순서를 최종 cut과 안전하게 연결하여 state-finalization latency를 줄일 수 있는가?

1. **Execution pipeline:** 수신·sync·ordering 준비·실행을 같은 cut의 consensus와 중첩하는 구조.
2. **Plan-assisted ordering:** 연속적인 plan으로 late insertion을 제한하고, 마지막 plan과 tips를 하나의 cut 결정에 연결하는 protocol.
3. **안전성 및 실증 분석:** Byzantine leader·late certificates·leader change 아래의 보존 조건과, 추가 합의 비용 대비 execution 재사용의 순이득.

각 기여는 아직 검증할 주장이다. Speculative execution, quorum certificate, prefix extension 각각을 새로운 발명으로 주장하지 않는다.

## 2. Background and Motivation

### 2.1 Dissemination, cut, execution의 경계

- Producer lane은 block을 생성하는 chain이고 validator는 consensus·검증 참여자다. 같은 노드가 두 역할을 수행할 수 있지만 lane을 state shard로 간주하지 않는다.
- Tips는 선택할 lane prefixes를 지정한다. Certificate를 알고 있다는 사실과 해당 body를 이미 보유·실행했다는 사실은 다르다.
- Cut proposal을 받으면 실행 대상을 파악하고 부족한 데이터를 sync하면서 실행할 수 있다. 모든 cut voter가 같은 local execution view나 완료 상태를 가진다고 가정하지 않는다.
- Autobahn을 설계 배경으로, Commonware Multimmit을 가능한 구현 기반으로 구분한다. 서로의 threshold·tip extraction·finality 조건을 혼합하지 않는다.

### 2.2 먼저 실행하면 생기는 비용

같은 state를 갱신하는 B1과, 그보다 앞에 놓이도록 base rule이 정한 A1을 생각한다. B1을 먼저 실행한 뒤 A1이 도착하면 B1이 읽은 값이 달라져 재실행이 필요할 수 있다. 반대로 서로 독립적인 block이면 수신 순서가 달랐어도 결과를 재사용할 수 있다.

공통 ordering rule은 **동일 입력 집합의 순서**를 결정하지만, 앞으로 어떤 입력이 추가될지까지 알려주지 않는다. Plan이 해결하려는 것은 이 late insertion에 의한 변경 가능성이다. 모든 재실행이나 shared-state 의존성을 없애는 것은 아니다.

### 2.3 설계 원칙

- 실행의 시작 조건에 plan certificate나 cut finality를 넣지 않는다.
- 보호한 순서는 새 plan·cut·leader change에서도 일관되게 보존한다.
- 실행 재사용은 정확성 검증을 통과해야 하며 local progress report를 correctness evidence로 취급하지 않는다.
- Cut-to-state 간격뿐 아니라 ingress-to-state 전체 latency도 개선해야 한다.

**그림 1:** 같은 block stream에서 post-cut 실행 / speculative-only / plan-assisted 실행의 시간선을 비교한다. 마지막에는 세 경우 모두 같은 finality·apply 완료 조건을 사용한다.

## 3. System Design

### 3.1 System model과 concurrent pipeline

초기 profile은 고정 validator 집합 `n = 5f + 1`, 최대 `f` Byzantine, 인증된 메시지, deterministic application execution, eventual synchrony를 전제로 연구한다. Dynamic membership은 초기 범위 밖이다. Data availability와 state 복구는 해당 자료를 실제로 보관·제공하는 정상 노드 및 자원 용량을 요구한다.

각 노드는 다음 작업을 중첩한다.

| 경로 | 역할 | 기다리지 않는 것 |
|---|---|---|
| Block production / dissemination | 자신의 block 생성·전파, 다른 block 수신·검증·DA 처리 | Application 실행 완료, plan 완성 |
| Speculative execution | 알려진 block을 순서에 맞게 실행·재검증·재실행 | Plan certificate, cut finality |
| Plan coordination | Leader의 제안, validator의 호환성 확인·투표, 인증서 전파 | 모든 validator의 실행 완료 |
| Cut consensus | 마지막 plan 경계와 tips·최종 순서 확정 | 모든 노드의 state apply |
| State finalization / apply | 확정 입력에 대한 올바른 결과 채택·저장 | 모든 노드의 동시 완료 |

여기서 non-blocking은 앞의 데이터·실행 경로를 consensus 완료 barrier로 막지 않는다는 뜻이다. Parent state 의존, 누락 데이터, 자원 한도 때문에 개별 작업이 기다릴 수 있고, plan 또는 cut 합의의 진행성은 별도로 증명해야 한다.

### 3.2 Leader가 plan을 만들고 확장하는 방법

Leader는 tips와 제한된 local execution-order/progress reports를 참고해 재사용할 수 있는 작업이 많은 순서를 제안한다. 전체 DAG를 모든 노드에 무제한 전송하는 방식은 전제하지 않는다. Report의 요약 방식·상한과 plan 빈도는 구현·평가에서 정한다.

Plan에는 적어도 다음 문맥이 필요하다.

- Chain/epoch, 대상 cut 구간, leader view, plan sequence.
- Canonical parent와 parent plan digest.
- 추가하는 exact block references와 순서.
- 기존 prefix와 새 구간을 어디까지 보호하는지 나타내는 no-insertion boundary.
- Ordering/runtime 문맥과 서명 domain.

Validator는 producer-chain 순서·ancestor completeness·block identity·parent plan과의 호환성을 확인하고 투표한다. Local 실행과 다른 제안이라면 실행 보고로 대안을 알릴 수 있지만, 이미 한 binding vote와 충돌하는 vote를 임의로 추가하지 않는다.

`3f+1`개 노드가 **동일 문맥에서 같은 대안**을 지지하면 leader가 아직 보호되지 않은 제안을 그 대안으로 조정하는 경로를 연구한다. `3f+1`명이 서로 다른 이유·순서로 반대한다는 것만으로 하나의 대안이 합의된 것은 아니다. 이미 인증된 prefix를 다수의 현재 실행 취향으로 뒤집지는 않는다.

예시:

```text
Plan 1:      B1 → C1
Plan 2:           C1 → A1 → B2   (parent = digest(Plan 1))
누적 보호:   B1 → C1 → A1 → B2
```

C1은 연결 anchor이며 두 번 포함·실행하지 않는다. `B1 → C1`이라는 edge만으로는 A1의 앞쪽 삽입을 막을 수 없으므로, Plan 1은 해당 canonical parent 다음의 prefix `[B1, C1]`까지 함께 보호해야 한다. 누락된 producer ancestor가 있다면 이 plan 자체를 유효하게 인증해서는 안 된다.

**그림 2:** 늦은 A1을 `[B1, C1]` 앞에 넣어 재실행하는 경우와, 보호된 구간 뒤에 두는 경우를 대비한다. 순서를 바꾸므로 application 결과도 달라질 수 있음을 함께 표시한다.

### 3.3 마지막 plan을 마무리하고 cut으로 전환

정상 경로를 단순화하기 위해 leader는 한 번에 하나의 plan 인증 시도를 진행한다. 여러 plan을 동시에 투표시키는 최적화는 초기 모델에서 제외한다.

1. **종료 결정:** leader가 cut을 시작하기로 하면 새 plan을 더 제안하지 않는다. 진행 중인 plan `P_m`을 마지막으로 지정한다.
2. **현재 시도 마무리:** `P_m` 인증을 완료한다. 진행 중인 시도가 없으면 이미 인증된 마지막 plan을 사용한다. Application execution의 완료를 기다리는 단계가 아니다.
3. **Cut 즉시 제안:** `P_m`과 그 parent chain, 이를 포함하는 certified tips, 최종 ordered-input commitment와 canonical parent를 함께 묶어 제안한다. 다른 plan이 더 생기기를 기다리지 않는다.
4. **Validator 확인:** 필요한 plan이 누락되거나, 자신의 아직 유효한 plan vote/lock과 충돌하거나, 보호된 block을 제외·재배열한 proposal에는 투표하지 않는다. Cut vote 이후 같은 구간의 새 plan에 다시 투표하지 않는 경계도 필요하다.
5. **Cut 확정:** 완전한 cut consensus 절차가 완료되면 그 exact 입력·순서를 canonical execution 문맥으로 채택한다. 다음 plan 구간은 이 cut에 연결한다.

아직 plan을 제안하거나 투표한 적이 없다면 빈 plan 경계로 cut을 제안할 수 있다. 반대로 인증서가 없다는 이유만으로 outstanding binding votes가 없다고 간주하지 않는다. Cut의 signed subject는 대상 구간과 마지막 plan sequence·digest도 명시하여, 정상 노드가 무엇을 닫는지 동일하게 판단하도록 한다.

이 동안 block 생성·전파와 아직 보호되지 않은 구간의 speculative execution은 계속한다. **Plan 제안 경로를 잠시 닫는 것과 execution을 멈추는 것은 다르다.**

늦게 도착하는 메시지는 다음처럼 구분한다.

| 상황 | 처리 원칙 |
|---|---|
| 마지막 plan 또는 그 ancestor의 vote/certificate 재수신 | 같은 digest이면 중복 처리; 늦었다는 이유로 효력을 잃지 않음 |
| 마지막 plan의 body/certificate를 아직 못 받은 validator | 해당 자료를 복구·검증; 실행 완료와는 별개 |
| Leader가 닫은 구간에 후속 plan을 추가 제안 | 정상 cut voter는 해당 구간을 다시 열어 투표하지 않음 |
| Cut과 충돌하는 binding vote 또는 certificate 발견 | 무시하거나 local arrival time으로 승자를 정하지 않음; cut 전환/leader recovery 규칙으로 해소 |
| 마지막 plan 인증 중 leader 중단·split votes | 이전 plan까지만 임의 확정하지 않음; 투표·lock을 보존한 recovery 필요 |

**검증 필요:** 위는 정상 경로와 필수 voting constraints다. 마지막 plan 인증 실패를 안전하게 마무리하는 절차, cut vote와 plan vote의 정확한 lock 전이, leader change 메시지와 quorum은 아직 완성해야 한다. Leader 혼자 “끝냈다”고 선언하는 것만으로 Byzantine safety가 성립하지 않는다. 취소가 필요하면 timeout 자체가 아니라 안전한 recovery 근거가 필요하다.

**그림 3:** `P1 → P2 → 마지막 P3 인증 → cut 제안·확정`과, 그 아래에서 끊기지 않는 production·execution 시간선을 함께 배치한다.

### 3.4 Tips와 plans로 최종 순서를 결정

Tips는 최종 포함 범위를, 마지막 plan까지의 chain은 보존할 prefix를 정한다. 남은 block은 producer ancestry와 이미 보호된 prefix를 존중하는 공통 base rule로 결정적으로 배치한다.

```text
Tips:             A1, B2, C1
보호된 prefix:    [B1 → C1]
가능한 최종 순서: [B1 → C1] → A1 → B2
```

이 예시는 B1·C1 앞에 추가 ancestor가 필요하지 않고, 잔여 구간의 base rule이 A1을 B2보다 먼저 두는 경우다. Cut은 보호된 prefix의 모든 block과 필수 ancestors를 포함해야 한다. Tips만 같고 plan chain이 다르면 같은 execution context가 아니므로, L-QC가 인증할 값에 이 둘과 최종 순서를 함께 묶는다.

이는 Multimmit의 기존 proposal-relative tip extraction과 extension voting을 제거·변경하려는 **새 fixed-cut profile**이다. 기존 L-QC의 이름이나 `4f+1` 숫자를 유지한다고 안전성이 자동 계승되지 않는다. Commonware는 구현 기반이고 변경된 protocol의 lock·recovery·inclusion 조건은 별도 검증 대상이다.

### 3.5 실행 재사용과 state finalization

Plan을 받으면 local speculative order를 조정한다. 입력·읽은 값·선행 effects가 변한 transaction과 그 dependent work를 재검증하고 필요한 부분만 재실행한다. 무관한 순서 변경은 올바른 검증 아래 재사용할 수 있다. 구체적인 STM/VM은 비교 실험에서 동일하게 고정할 backend이지 별도 기여가 아니다.

Finalized cut, canonical parent, runtime과 정확히 일치하는 결과만 state-final로 채택한다. Plan vote나 cut vote만으로 application 실행의 정확성이 확인된 것은 아니다. 직접 실행·검증과 인증된 결과 전달 중 실제 사용할 경로를 구현에서 명시하고, 모든 비교군에 같은 완료 기준을 적용한다.

기존 `f+1` matching execution signatures는 선택 가능한 구현 경로다. 고정된 입력의 결정적 결과를 실제 검증한 정상 signer가 최소 하나 포함된다는 논증이며, 새 ordering이나 plan을 선택하는 quorum이 아니다. 이 경로를 채택하면 exact subject·자료 보관·복구·parent 연결을 별도 정의한다. 서명 숫자 자체를 신규 기여로 삼지 않는다.

## 4. Correctness and Liveness

### 4.1 증명해야 할 성질

1. **Plan compatibility:** 동일 문맥에서 상충하는 prefix가 동시에 보호되지 않는다.
2. **Prefix preservation:** 후속 plan, cut, leader change가 유효하게 보호된 prefix를 삭제·재배열하거나 그 앞에 삽입하지 않는다.
3. **Safe closure:** 마지막 plan 지정과 cut voting이 겹쳐도, 확정 cut과 충돌하는 새 plan 인증이 가능하지 않다.
4. **Deterministic execution:** 동일 canonical parent·cut·plan chain·runtime에서 동일 순차 의미를 얻고, speculative reuse도 그 의미와 일치한다.
5. **No premature state finality:** plan 인증 또는 speculative 완료만으로 canonical state를 공개하지 않는다.

초기 threshold 후보는 plan `3f+1`, cut `4f+1`이다. `n=5f+1`에서 두 plan quorum의 최소 교집합은 `f+1`, plan과 cut quorum은 `2f+1`이다. 정상 노드가 호환되지 않는 문맥에 이중으로 binding vote하지 않는다면 이 교집합이 안전성 논증의 재료가 된다. **교집합 계산만으로 view change·split votes·liveness까지 증명되지는 않는다.**

### 4.2 Byzantine behavior와 복구

| 행위 | 필요한 방어 / 남은 검증 |
|---|---|
| Leader의 conflicting plan 제안 | Exact parent/sequence binding, durable non-equivocation·lock 규칙 |
| Certificate 은닉·leader 교체 | 마지막 인증서뿐 아니라 유효 vote/lock의 recovery; 인증서 미수신을 부재로 오인하지 않음 |
| Cut에서 protected plan 누락 | Signed cut subject에 마지막 plan chain 포함, 충돌하는 cut vote 거부 |
| Cut 도중 후속 plan 서명 유도 | 구간 closure와 cut/plan 사이 voting fence; view 변경에서도 보존 |
| Producer fork·body withholding | Exact block identity, ancestry와 DA 확인·복구; DA와 execution correctness 구분 |
| 거짓 실행-progress report | 성능 hint로 제한; 실행 correctness·canonicality로 승격하지 않음 |

진행성은 plan 합의, cut 합의, 실행 진척을 나누어 설명한다. Speculative execution이 계속되어도 canonical progress가 멈출 수 있다. 정상 leader와 eventual synchrony 아래 마지막 plan 또는 안전한 recovery가 완료되고 cut으로 넘어갈 수 있음을 증명해야 한다. 무제한 speculation 대신 자원 상한·backpressure도 필요하다.

## 5. Evaluation

### 5.1 검증할 질문과 비교군

| 비교군 | 목적 |
|---|---|
| 기존 ordering + post-cut execution | 기본 latency 분해 |
| 같은 fixed-cut profile + post-cut execution | 합의 profile 변경 효과를 execution overlap과 분리 |
| 같은 profile + speculative execution, plan 없음 | 일찍 실행하는 것만의 이득과 재실행 비용 |
| 같은 profile + speculative execution + plans | 순서 보호의 추가 순이득 |
| 더 짧은 간격의 cut + speculative execution | Plans가 단순히 cut을 자주 수행하는 것보다 나은지 확인 |

자원·application·완료 조건을 맞춘다. 더 잦은 cut 역시 production·execution과 겹칠 수 있으므로 그 비교군에 인위적 execution barrier를 두지 않는다. Native Multimmit과 변경 profile의 비교는 서로 다른 protocol임을 명시한다.

### 5.2 Workload와 측정

- 핵심 축: RTT, application state-operation 수, conflict density, lane별 전파 지연, offered load.
- Plan 크기·빈도, local view 불일치, cut 빈도와 보호 전/후 late predecessor를 추가로 변화시킨다.
- Ingress → state finalization 및 cut → state finalization의 p50/p95/p99; durable read readiness는 별도 측정한다.
- Cut 이전에 순서가 이미 되돌릴 수 없게 되는 경우 **최초 binding order decision → state finalization**도 기록한다. Cut을 뒤로 미뤄 gap만 축소한 것을 개선으로 세지 않는다.
- 재사용·재검증·재실행량, execution CPU, plan 통신·검증 비용, ordering latency, backlog·미완료 요청과 producer별 대기를 함께 보고한다.
- 최소 안전성 실험: conflicting plans, 마지막 plan 도중 leader 중단, 늦은 certificate, cut/plan race, missing ancestor. 대규모 공격 성능 평가가 아니라 targeted deterministic tests로 시작한다.

현재 `research/precut_order/`의 기존 toy tests는 일부 prefix·재사용 사례의 탐색 자료다. 이 문서의 leader coordination·closure·L-QC 결합을 구현·검증한 결과로 인용하지 않는다. 실제 성능 수치는 아직 없다.

## 6. Related Work

- **Autobahn:** parallel dissemination과 cut agreement가 배경이다. 본 연구는 pre-cut 실행을 보호하는 순서 제약과 final cut 연결을 다룬다. [논문](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- **HotStuff 계열의 locking/recovery:** leader change에서 무엇을 보존해야 하는지 비교한다. Timeout은 block·certificate가 존재하지 않는다는 증거가 아니다. [HotStuff](https://arxiv.org/abs/1803.05069)
- **Dependency-based BFT:** 순서가 필요한 관계와 서로 다른 local observations를 합의하는 연구와 비교해야 한다. Leader를 둔다는 차이만으로 novelty를 주장하지 않는다. [ISOS / Egalitarian Byzantine Fault Tolerance](https://arxiv.org/abs/2109.06811)
- **Speculative execution / deterministic parallel execution:** execution 재사용과 rollback·retry의 기존 기법을 인정한다. 새 기여는 execution engine 자체가 아니라 plan/cut 결합과 latency trade-off다.
- **Multimmit:** 실제 선택한 upstream commit과 protocol 문서를 고정하고, 원래 L-QC와 수정 profile의 차이를 기술한다. 학술적 계보와 구현 기반을 구분한다.

문헌의 알고리즘을 그대로 구현한 것과 설계 아이디어만 참고한 것을 나누어 쓴다. Producer placement 문헌은 이번 핵심 related work에서 제외하고 archive에 남긴다.

## 7. Discussion and Limitations

- Binding plan은 cut 전의 부분적인 ordering 결정이다. “합의를 추가하지 않았다”거나 “완전히 비용 없는 hint”라고 표현할 수 없다.
- 마지막 plan의 완성을 기다리는 시간과 recovery 비용이 cut latency를 늘릴 수 있다. Non-blocking execution이 이 비용을 없애지는 않는다.
- Leader는 communication 집중점이며 scheduling bias·검열·MEV와 report 조작에 따른 성능 저하가 가능하다. Plan 선택의 공정성은 별도 성질이다.
- Plan certificate 형성 전과 보호되지 않은 suffix의 재실행은 남는다. Parent 변경·data recovery·실행 backlog 역시 별도 원인이다.
- Protected block을 이후 cut이 반드시 포함해야 한다면 조기 membership obligation이 생긴다. DA·producer ancestry·recovery 조건을 포함해야 한다.
- Global shared-state의 본질적 직렬 의존성이나 Byzantine 실행 비용 증폭에 대해 무조건적인 latency 상한을 주장하지 않는다.
- Closure와 leader recovery의 완성 전에는 배포 가능한 안전한 protocol로 표현하지 않는다.

## 8. Conclusion

결론은 **execution을 cut 앞으로 이동 → 늦은 삽입으로 인한 이득 손실 → plan으로 prefix 보호 → 마지막 plan과 tips를 결합한 cut → 정확한 결과 재사용**의 흐름으로 정리한다. 실험으로 확인한 latency 순이득과 이득이 사라지는 조건을 함께 제시한다.

### 다음 연구 작업의 우선순위

1. 마지막 plan·cut voting·leader recovery의 상태 전이를 정의하고 safety/liveness 반례를 탐색한다.
2. Plan이 보장하는 prefix와 cut의 membership·최종 순서 관계를 형식화한다.
3. Placement 없이 speculative-only와 plan-assisted prototype을 먼저 비교한다.

이 개요는 논문의 새 출발점이다. 기존 LaTeX/PDF·Google Docs·Commonware 구현이 함께 갱신되었다는 뜻은 아니다.
