# Paper Outline: Proof-Pipelined State Finality with Cut-Tail Cross-Lane Execution

> 보관본: 2026-09-19 회전형 라운드로빈 speculative execution 개요로 대체됨. 현재 논문 개요는 [paper-outline.md](./paper-outline.md)를 읽는다. 아래 내용은 이전 설계 기록이며 새 모델의 설명으로 사용하지 않는다.

> 상태: revised outline v12 — cut-tail cross-lane DAG model  
> 범위: Autobahn-family ordering을 유지하면서 local state finality를 앞당기고, arbitrary statically declared cross-lane execution을 검증 가능하게 분산하는 state layer  
> 주의: 이 개요는 기존 `Commit/Abort` branch-proof model을 대체하는 새 논문 방향이다. Active protocol 및 SDK 문서는 후속 동기화가 필요하다.

---

## Paper argument

- **Ordering boundary.** Autobahn-family consensus는 여러 producer lanes에서 어떤 입력이 어떤 finalized cut에 포함되는지를 빠르게 확정한다. 그러나 그 입력을 실행·검증하고 serving state에 적용하는 시점은 별도의 문제다.
- **Local opportunity.** 하나의 state-owner lane만 건드리는 transaction은 cut 결과와 무관하게 lane 순서대로 미리 실행하고 rolling proof를 만들 수 있다.
- **Cross-lane limit.** 여러 owner lanes를 읽거나 쓰는 transaction은 canonical input state와 conflict order가 finalized cut에서 정해지므로, lock·branch·잘못된 경로의 재실행 없이 canonical proof를 cut 전에 확정할 수 없다.
- **Design choice.** Local transaction과 cross-lane transaction의 application semantics를 분리한다. Local body는 cut 전에 실행·증명하고, cross-lane transaction은 하나의 완전한 intent로 ordering하되 해당 cut의 logical tail에서 실행한다.
- **Post-cut execution.** Finalized cut은 cross-lane intents와 정적 read/write declarations로 deterministic conflict DAG를 만든다. 서로 독립인 DAG nodes는 여러 validators가 분산 실행·증명하고, 모든 node는 proof를 검증해 atomic multi-lane delta를 적용한다.
- **Non-blocking property.** Proof readiness는 Autobahn-family ordering을 막지 않는다. Cross DAG가 늦으면 그 결과에 의존하는 state components만 늦고, 다음 cuts의 ordering과 무관한 state execution은 계속된다.

논문이 줄이려는 값은 다음과 같다.

\[
\Delta_{cut\rightarrow state,v,c}
=
T_{state\ applied,v,c}-T_{cut\ finalized}
\]

여기서 `c`는 state component다. Local components는 pre-cut proof로 간격을 숨기고, cross components는 post-cut DAG의 critical path를 병렬화해 간격을 줄인다.

### Central research question

> Autobahn-family ordering을 교체하거나 proof 때문에 막지 않으면서, cut-independent local execution은 ordering과 겹치고 cut-dependent N-lane execution은 finalized cut 직후 검증 가능하게 분산하여 cut-to-state latency를 얼마나 줄일 수 있는가?

### Contributions

1. **Cut-tail state semantics.** Statically declared transactions를 local body와 cross-lane intent로 나누고, local body는 pre-finality rolling proof path에서 처리하며 cross-lane intents는 finalized-cut-relative logical tail에서 처리하는 deterministic state model.
2. **Cut-derived verifiable execution DAG.** Finalized cut과 declared read/write sets에서 모든 honest nodes가 같은 cross-lane conflict DAG를 만들고, DAG nodes를 validators에 분산해 arbitrary N-lane transition과 failure/no-op을 proof-carrying atomic deltas로 확정하는 execution model.
3. **Non-blocking proof distribution and characterization.** Proof sidecar, `f+1` proof custody, deterministic worker failover와 component-scoped readiness를 결합하고, local latency hiding과 cross-DAG critical-path acceleration의 효과 및 한계를 구현·측정한다.

Tail placement, static access declarations, DAG scheduling, validity proofs 또는 `f+1` custody는 각각 단독 novelty가 아니다. Novelty 주장은 **Autobahn-family finalized cut 주위에 pre-cut local proof pipeline과 post-cut inter-validator verifiable cross-state DAG를 결합한 end-to-end state-finalization architecture**에 둔다.

### Minimal vocabulary

- **finalized cut:** Autobahn committed cut 또는 Multimmit L-QC에서 즉시 global log로 방출되는 exact ordered batch의 공통 표현.
- **state-owner lane:** 특정 mutable state를 유일하게 변경하는 logical execution partition.
- **local transaction:** 정확히 하나의 owner lane만 읽고 쓰는 transaction.
- **cross-lane intent:** 둘 이상의 owner lanes를 읽거나 쓰며, 전체 payload와 정적 read/write declaration을 한 번에 담은 transaction.
- **cross-lane DAG:** 한 finalized cut의 cross-lane intents 사이 conflict와 canonical priority를 나타내는 execution graph.
- **proof bundle:** execution result, state delta, public commitments, apply material과 validity proof의 content-addressed package.
- **PAC:** `f+1` validators가 exact proof bundle을 검증·보관했다는 availability evidence. Correctness나 canonicality를 결정하지 않는다.

기존 개요의 lane별 fragments, participant handshake, `Commit/Abort` dual branches, decision deadline, branch overlays, completeness certificate, canonical rollback 및 repair lane은 이 모델에서 제거한다.

---

## 1. Introduction

### 1.1 Fast ordering is not ready state

첫 문단은 Autobahn-family consensus의 성과를 인정한 뒤 경계를 정확히 제시한다.

> Autobahn-family protocols rapidly finalize a global ordering over independently produced data lanes, but the finalized cut is not by itself an executed, proof-verified, and readily servable application state.

- 기존 protocol은 deterministic application execution을 전제하지만, transition proof 생성, post-state availability, durable apply와 cross-state scheduling은 application boundary에 둔다.
- 이는 Autobahn의 결함이 아니라 ordering과 dissemination에 집중한 의도적인 scope다.
- 본 연구는 ordering consensus를 교체하지 않고 그 출력인 finalized cut을 state finality로 변환하는 execution layer를 제안한다.

### 1.2 Why the gap grows

Baseline에서는 cut 이후 다음 작업이 순차적으로 노출된다.

```text
finalized cut
  -> canonical batch 해석
  -> application execution
  -> proof 생성/전파
  -> proof 검증
  -> durable state apply
  -> state serving readiness
```

- Ordering throughput이 높아질수록 execution/proof backlog가 누적되어 serving state가 ordering head보다 뒤처질 수 있다.
- Ordering DA는 input availability를 보장하지만 post-state proof와 apply material의 availability까지 보장하지 않는다.
- 따라서 ordering latency와 별도로 `cut-to-state latency`와 `state lag in cuts`를 측정해야 한다.

### 1.3 Why producer parallelism is not state parallelism

- Producer lane은 자동으로 state shard가 되지 않는다.
- 서로 다른 producers가 같은 balance, nonce, AMM reserve 또는 collateral을 건드리면 global execution order가 필요하다.
- State ownership을 분리해도 transfer, multi-account update, cross-market liquidation처럼 여러 partitions를 읽고 쓰는 operation은 남는다.
- Pre-cut canonical execution을 시도하면 unknown cut order 때문에 lock, speculative branches 또는 re-execution 비용 중 하나를 부담해야 한다.

Somnia MultiStream은 Autobahn-inspired multi-producer ordering이 shared EVM state로 병합되는 production motivation으로 사용한다. Somnia가 본 논문의 state model을 구현한다고 주장하지 않는다.

### 1.4 Key insight

모든 transaction을 같은 방식으로 최적화하지 않는다.

- Cut-independent local work는 block production 및 ordering과 함께 실행·증명한다.
- Cut-dependent cross-state work는 input만 ordering하고 execution은 cut-tail phase로 미룬다.
- Finalized cut 직후 하나의 leader가 임의 DAG를 제안하지 않는다. 모든 nodes가 same cut과 signed static declarations에서 같은 DAG를 계산한다.
- Cross DAG nodes는 validators에 분산되고 validity proof가 Byzantine worker의 잘못된 결과를 제거한다.
- Cross execution을 cut 이후 시작한다는 비용은 인정하되, witness prefetch·graph skeleton preparation·distributed proving으로 그 critical path를 줄인다.

### 1.5 Contributions and first-page results

- 위 세 contributions를 간결하게 배치한다.
- 측정 후 `Delta_local`, `Delta_cross`, state-ready goodput, cross-DAG speedup과 critical-path reduction을 첫 페이지에 제시한다.
- “cross-state proof를 cut 전에 완성한다”는 주장은 하지 않는다.
- “arbitrary EVM transaction”도 주장하지 않는다. Read/write owners를 transaction bytes와 immutable schema에서 보수적으로 정할 수 있는 application만 대상으로 한다.

Figure 1은 논문 전체를 한 번에 보여준다.

```text
Baseline:
  ordering ---------------->| cut | execute all -> prove -> apply

Proposed:
  local blocks: execute -> fold -> sidecar/PAC ---->| exact proof join -> apply
  cross intents: declare/prefetch/prepare ---------->| build DAG -> distributed execute/prove -> atomic apply
  next ordering: -------------------------------------------> continues without waiting
```

---

## 2. Background and Motivation

### 2.1 Autobahn-family finalized cut

- [Autobahn: Seamless High-Speed BFT (SOSP 2024)](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)의 data lanes, availability certification, cut-of-tips와 committed ordering을 설명한다.
- Protocol별 vote internals 대신 state layer가 소비하는 공통 출력 `FinalizedCut(F_k)`를 정의한다.
- `FinalizedCut(F_k)`는 authenticated lane boundaries와 즉시 global order에 배치된 exact inputs를 포함한다.
- State proof는 membership-final tip이 아니라 실제 emitted ordering batch와 결합해야 한다.

### 2.2 Multimmit as the reference artifact

- [Multimmit](https://arxiv.org/abs/2607.21021)의 producer chains, proposal-relative votes, L-QC와 deterministic sweep를 설명한다.
- `n >= 5f+1`에서 leader proposal 이후 consensus step을 줄이는 장점과 replica cost를 함께 설명한다.
- 학술적 framing은 Autobahn-family로 유지하고, Commonware Multimmit fork는 concrete implementation/evaluation vehicle로만 사용한다.

### 2.3 Three failed extremes

1. **Everything after the cut:** 가장 단순하고 안전하지만 execution/proof latency가 전부 노출된다.
2. **Everything before the cut:** local transaction에는 가능하지만 cross-state input/order가 달라지면 proof가 무효가 되거나 rollback/re-execution이 필요하다.
3. **Synchronous cross-lane coordination:** locks 또는 prepare/commit은 atomicity를 주지만 ordering path에 RTT와 stalled-owner dependency를 추가한다.

이 관찰에서 다음 요구사항을 도출한다.

- Local work는 cut 전에 최대한 완료한다.
- Cross work는 canonical dependencies가 확정된 뒤에만 한 경로를 증명한다.
- Cross execution은 한 validator에 집중하지 않는다.
- Byzantine executor는 consensus vote가 아니라 proof verification으로 걸러낸다.
- Ordering은 proof readiness를 기다리지 않는다.
- Failure는 rollback이 아니라 deterministic failed/no-op transition으로 표현한다.

### 2.4 Why a cut-tail phase

한 finalized batch `B_k`의 application schedule을 두 단계로 정의한다.

```text
B_k = inputs ordered between F_(k-1) and F_k
L_k = local transactions in B_k
X_k = cross-lane intents in B_k

StateSchedule(B_k) =
  ExecuteLocal(L_k)
  ; ExecuteCrossDAG(X_k, PostLocalState_k)
```

- `L_k`와 `X_k` 내부의 canonical priority는 finalized ordering에서 유도한다.
- Physical block encoding은 `local_body`와 `cross_tail` 두 sections를 권장한다. Typed entries를 섞어 전파해도 모든 nodes가 같은 stable partition을 계산할 수 있다.
- Cross intent의 원래 byte position은 inclusion/priority를 정하지만 local transition 사이에 즉시 실행된다는 의미는 아니다.
- 이는 consensus ordering을 바꾸는 것이 아니라 application execution semantics를 명시적으로 바꾸는 것이다.
- 장점은 local proof path가 cross outcome 때문에 fork되지 않는다는 점이다.
- 비용은 cross transaction이 최소한 해당 cut 확정까지 기다리고, 동일 cut 안에서 모든 local effects 뒤의 state를 읽는다는 점이다.

### 2.5 Design positioning

- Arete의 intra-shard/cross-shard phase separation은 가장 가까운 structural precedent다.
- Chainspace, OmniLedger, Byzcuit은 coordination-based atomicity와 비교한다.
- Nightshade/Monoxide는 receipt/async message 방식과 비교한다.
- X-Shard/Prophet은 optimistic execution 또는 preordering과 비교한다.
- Pilotfish와 Remora는 deterministic dependency scheduling 및 scale-out execution의 직접 참고점이지만 intra-validator architecture다.
- RollShard는 proof-carrying multi-shard delta의 참고점이다.

---

## 3. System Design

### 3.1 System model and assumptions

- Underlying Autobahn-family protocol의 ordering safety/liveness와 transaction-input availability를 상속한다.
- `n` validators 중 최대 `f`가 Byzantine이며 concrete Multimmit benchmark는 `n >= 5f+1`을 따른다.
- Producer lane은 authenticated input chain이고, state-owner lane은 mutable state partition이다. Reference implementation은 `producer lane = state-owner lane`으로 단순화한다.
- 모든 validator는 global ordering과 state commitments를 추적한다. Execution은 분산할 수 있지만 proof verification 결과는 누구나 독립적으로 확인할 수 있다.
- Transaction의 participant lanes와 conservative read/write keys는 signed bytes와 immutable application schema에서 execution 전에 결정 가능해야 한다.
- Actual read/write가 declaration 밖으로 나가면 proof가 검증되지 않는다.
- Runtime-dependent storage address, dynamic call graph와 arbitrary EVM execution은 범위 밖이다.

### 3.2 Typed producer block

권장 logical block format은 다음과 같다.

```text
ProducerBlock_i,h = {
  local_body:   [transactions whose owner set = {i}],
  cross_tail:   [complete intents whose owner-set size >= 2]
}
```

- Cross transaction은 participant별 fragment가 아니라 전체 operation을 나타내는 하나의 self-contained intent다.
- 동일 intent가 여러 producer blocks에 중복 포함되면 finalized order의 첫 valid occurrence만 효력이 있고 나머지는 deterministic no-op이다.
- 따라서 한 fragment만 포함되는 partial-inclusion 문제, participant handshake와 completeness certificate가 사라진다.
- Mempool은 complete intent를 producers에 전파하고, consensus는 일반 input과 동일하게 그 inclusion을 확정한다.

### 3.3 Pre-cut local execution and rolling proof

각 owner lane은 local body를 producer-chain order대로 즉시 실행하고 proof snapshot을 누적한다.

```text
blocks          b1 ------> b2 ------> b3 ------> b4
local execute      e1 ------> e2 ------> e3 ------> e4
proof fold            p1 ------> p2 ------> p3 ------> p4
ordering          ------------------------------- F_k
```

- Proof는 exact local input digest, canonical parent commitment, post-state delta, declared access와 circuit version에 bind된다.
- Height별 proof snapshot을 보관해 finalized cut이 선택한 exact prefix와 일치하는 snapshot만 사용한다.
- Proof bundle은 준비 즉시 sidecar로 broadcast한다.
- Validators는 bundle을 검증·보관하고 custody share를 전파한다. `f+1` shares가 PAC를 이룬다.
- Multimmit vote에는 이미 검증·보관된 bounded readiness claim을 선택적으로 넣을 수 있지만 vote는 이를 기다리지 않는다.
- PAC는 recovery를 돕는 availability evidence이며 state correctness 또는 canonicality를 투표하지 않는다.

### 3.4 Pre-cut preparation for cross intents

Canonical cross proof는 cut 전에 만들지 않지만 다음 작업은 ordering과 겹칠 수 있다.

- Signature, nonce format, owner-set와 declared read/write set 검증.
- Candidate intents의 conflict-graph skeleton 계산.
- 필요한 authenticated state witness와 circuit data prefetch.
- Proof worker 후보와 backup 순서 계산.
- Circuit compilation, witness-independent preprocessing과 task queue reservation.

이 준비는 latency optimization일 뿐 safety input이 아니다. Finalized cut과 post-local state가 다르면 candidate skeleton/witness를 다시 검증하거나 폐기한다.

### 3.5 Finalized-cut-derived cross-lane DAG

`F_k`가 확정되면 모든 node가 `X_k`와 post-local commitments에서 같은 DAG를 만든다.

```text
Conflict(x,y) iff
  W(x) intersects (R(y) union W(y))
  OR W(y) intersects (R(x) union W(x))

if Conflict(x,y) and x precedes y in finalized priority:
  add edge x -> y
```

- Edge는 state dependency를 보존한다.
- Conflicting intents는 finalized priority를 따라 직렬화된다.
- Disjoint intents는 같은 DAG level에서 병렬 실행된다.
- DAG는 leader가 임의로 제안하지 않으므로 malicious scheduling graph에 대한 별도 합의가 필요 없다.
- 모든 nodes는 cut, transaction digests와 signed declarations만으로 DAG hash를 재계산한다.

### 3.6 Inter-validator execution and proving

Ready DAG node는 deterministic worker assignment로 validator에 배치한다.

```text
ranked_workers(x,F_k) = DeterministicRank(validator_set, F_k, operation_id)

primary executes x
  -> reads authenticated predecessor/state commitments
  -> evaluates application transition
  -> emits Success(delta) or ApplicationFailure(no-op)
  -> generates validity proof
  -> broadcasts ProofBundle
```

- Worker는 transaction의 모든 participant lanes를 하나의 proof relation 안에서 실행한다.
- 결과는 owner별 independent fragments가 아니라 하나의 atomic multi-lane delta commitment다.
- Invalid proof, wrong parent, wrong DAG predecessor 또는 undeclared access는 모든 honest nodes가 거부한다.
- Primary가 proof를 내지 않으면 `D_failover` finalized cuts 뒤의 다음 ranked worker가 takeover한다. Local wall-clock timeout은 protocol decision에 사용하지 않는다.
- Ordering은 takeover를 기다리지 않는다. Descendants와 해당 state components만 pending이고 disjoint DAG components는 계속된다.

### 3.7 Proof verification and atomic state apply

Cross proof의 public input은 최소 다음을 포함한다.

```text
CrossProofPublicInput = {
  finalized_cut_digest,
  cross_dag_digest,
  operation_id,
  predecessor_output_commitments,
  participant_lanes,
  declared_reads_and_writes,
  pre_state_commitments,
  status: Success | ApplicationFailure,
  multi_lane_delta_commitment,
  post_state_commitments,
  circuit_version
}
```

- `Success` proof는 모든 lane preconditions와 state updates를 검증한다.
- `ApplicationFailure` proof는 동일 canonical inputs에서 application rule이 실패했으며 state effect가 no-op임을 검증한다.
- Proof missing은 failure가 아니다. 해당 DAG node와 descendants가 pending이다.
- 각 node는 valid proof를 받는 즉시 state apply를 할 수 있다. `f+1` PAC는 late/recovering nodes가 exact bundle을 가져올 수 있게 하지만 apply correctness의 추가 quorum은 아니다.
- Multi-lane delta는 node-local crash-atomic batch로 모든 participant commitments를 함께 갱신한다. 일부 lane만 보이는 canonical outcome은 허용하지 않는다.
- Canonical rollback은 없다. Cross operation은 proof가 검증되기 전에는 canonical state에 반영되지 않는다.

### 3.8 Pipelining across cuts

세 종류의 작업이 동시에 진행된다.

```text
time ------------------------------------------------------------>

Cut k ordering:       current producer blocks and local proof fold
Cut k-1 state:        cross DAG execute/prove/verify/apply
Cut k+1 preparation:  cross-intent validation and witness prefetch
```

- Cross execution이 느려도 next ordering cuts는 생성된다.
- 아직 해결되지 않은 cross output을 읽는 다음 local/cross transaction은 해당 component에서 기다린다.
- 다른 owner lanes 또는 disjoint state components는 계속 실행·증명할 수 있다.
- 따라서 non-blocking은 “모든 state가 항상 전진한다”가 아니라 “ordering 및 dependency-disjoint state progress가 느린 cross component에 묶이지 않는다”는 뜻이다.

### 3.9 End-to-end example

Cut `k`에 다음 transactions가 들어 있다고 하자.

```text
Local body:
  L1: Alice nonce update
  L2: Bob local transfer

Cross intents:
  X: Alice@L1 -> Bob@L2 transfer
  Y: Alice@L1 collateral + BTC@L3 position liquidation
  Z: Carol@L4 -> Dave@L5 transfer
```

1. `L1`, `L2` local bodies는 cut 전에 실행·증명된다.
2. Cut `k`가 확정되면 local proof의 exact prefix를 검증·적용한다.
3. `X`와 `Y`는 Alice state에서 충돌하므로 finalized priority에 따라 `X -> Y` edge가 생긴다.
4. `Z`는 disjoint하므로 `X`와 병렬 실행될 수 있다.
5. Assigned workers가 `X`와 `Z`를 실행·증명한다.
6. `X` proof가 적용되면 `Y`가 새 Alice commitment를 입력으로 실행된다.
7. `Y`의 liquidation 조건이 false면 proof-certified no-op으로 끝난다. 앞선 local state와 `X`를 rollback하지 않는다.

---

## 4. Correctness and Liveness

### 4.1 Deterministic schedule

- 같은 finalized cut을 가진 honest nodes는 같은 local/cross partition, stable order, conflict edges와 DAG digest를 계산한다.
- Duplicate intent의 first-valid-occurrence rule도 deterministic하다.

### 4.2 Local proof safety

- Exact cut-selected local prefix, canonical parent와 일치하는 rolling proof만 admissible하다.
- Candidate proof가 다른 prefix를 증명하면 valid proof여도 canonical state에는 적용되지 않는다.

### 4.3 Cross-DAG serializability

- Actual accesses가 declared sets 안에 있음을 proof가 강제한다.
- 모든 conflicting operations 사이에 finalized priority 방향의 edge가 존재한다.
- 따라서 DAG 병렬 실행 결과는 그 priority를 보존한 deterministic sequential execution과 동등하다.

### 4.4 Atomic N-lane state transition

- 하나의 proof가 every participant pre-state와 multi-lane delta를 함께 bind한다.
- Honest node는 전체 proof가 valid한 경우에만 participant commitments를 crash-atomically 갱신한다.
- Success 또는 proof-certified failure/no-op 중 하나만 존재하며 partial fragment state는 없다.

### 4.5 Byzantine workers

- 잘못된 result나 DAG를 낸 worker는 proof/binding verification에서 거부된다.
- Equivocating valid outputs는 deterministic transition과 proof soundness 가정 아래 같은 public inputs에 대해 다른 valid state roots를 만들 수 없다.
- Withholding은 safety를 깨지 않고 해당 component의 readiness만 늦춘다.
- Finalized-cut-count-based deterministic takeover와 recoverable witnesses 아래 eventual proof generation을 보인다.

### 4.6 Non-blocking and conditional liveness

- Proof/PAC는 ordering quorum의 선행조건이 아니다.
- Ready DAG nodes와 dependency-disjoint components는 stalled node와 무관하게 진행한다.
- Bounded request load, eventual synchrony, at least one live ranked prover, witness availability와 sufficient proof throughput 아래 affected components도 eventual state finality에 도달한다.

### 4.7 Explicit non-guarantees

- Arbitrary runtime-dependent EVM access discovery.
- Hot shared key에 대한 parallel speedup.
- Cross-lane proof generation을 cut 이전에 숨기는 것.
- Proof throughput이 workload보다 낮을 때 bounded state lag.
- Pre-proof state의 external finality.

---

## 5. Evaluation

### 5.1 Prototype and workload

- Commonware Multimmit fork, base commit `534af0ed`.
- Primary setup: 6 validators, 6 producer/state-owner lanes. 이는 protocol requirement가 아니라 `f=1` benchmark configuration이다.
- Cosmos Bank-like typed state model with `owner(address) = H(address) mod 6`.
- Local transfer와 2/3/4/6-lane atomic transfer or liquidation-shaped synthetic operations.
- Background local proof fold, proof sidecar/PAC, cut-derived DAG, deterministic worker assignment, proof verification과 atomic apply.
- Mock prover는 scheduling/pipeline overhead만 측정하고, small CPU real-proof backend로 cryptographic cost를 별도 측정한다.

### 5.2 Research questions

1. Autobahn-family ordering head와 application-ready state 사이의 gap은 load에 따라 얼마나 커지는가?
2. Local pre-execution/rolling proofs가 `Delta_local`과 state-ready goodput을 얼마나 개선하는가?
3. Cross-DAG distributed execution이 sequential post-cut execution보다 `Delta_cross`를 얼마나 줄이는가?
4. 이득은 cross ratio, conflict density, DAG critical-path length와 proof cost에 따라 어떻게 달라지는가?
5. Faulty/slow worker와 proof withholding 아래 unrelated progress와 eventual recovery가 유지되는가?
6. Cut-tail semantics가 receipt, synchronous atomic commit 및 optimistic branch execution과 비교해 어떤 latency/semantic trade-off를 갖는가?

### 5.3 Baselines and ablations

- **O0 Ordering-only:** Multimmit ordering ceiling을 측정한다.
- **S0 Sequential post-cut:** finalized batch 전체를 cut 후 모든 validators가 순차 실행한다.
- **L0 Local pipeline:** local work만 pre-execute/pre-prove하고 cross work는 한 worker가 순차 실행한다.
- **D0 DAG single-worker:** proposed deterministic DAG를 만들지만 한 worker가 실행해 graph construction 효과를 분리한다.
- **D1 Distributed DAG:** proposed inter-validator scheduling과 mock proof를 사용한다.
- **D2 Distributed DAG + real proof:** cryptographic backend가 포함된 end-to-end variant다.
- **R0 Receipt reference:** source-final 후 destination apply 방식의 logical latency를 비교한다.
- **C0 Synchronous coordination reference:** 작은 2PC/lock baseline이 가능할 때만 구현한다.
- 기존 dual-branch proof prototype이 있다면 abandoned design comparison으로만 측정하고 핵심 baseline으로 요구하지 않는다.

### 5.4 Workload variables

- Local/cross ratio: `0/25/50/75/100%`.
- Number of participant lanes per cross operation: `2/3/4/6`.
- Conflict graph: disjoint, chain, star, layered DAG, hot-key clique.
- Uniform and Zipf state access.
- Offered TPS, block gas/byte limit, cut batch size와 block interval.
- Proof generation/verification delay, proof bytes와 witness-fetch delay.
- Validator count, worker concurrency, network delay와 bandwidth.
- Faults: slow/crashed/Byzantine worker, invalid proof, proof withholding, stale witness, false access declaration.

### 5.5 Primary metrics

- `Delta_local` and `Delta_cross`: p50/p95/p99.
- `state_lag_in_cuts` by component and whole node.
- Ordered throughput, state-applied goodput and successful cross-operation goodput.
- Cross-DAG makespan, critical-path length, parallelism and worker utilization.
- Proof-ready-at-cut ratio for local transactions.
- Cross proof time, verify time, bundle/PAC bytes and witness bytes.
- Per-validator execution/proving load balance.
- Application failure/no-op rate and duplicate-intent rate.
- Takeover frequency and recovery latency measured in finalized cuts.
- Invalid or partial state installation count; expected value is zero.

### 5.6 Claim-to-experiment discipline

- Mock proof results support only pipeline, scheduling and network-overhead claims.
- Cryptographic speed claims require a real backend.
- Tail scheduling alone의 throughput을 novelty 결과처럼 제시하지 않는다.
- Proposed protocol은 local state latency와 cross critical-path latency를 별도로 보고한다. 하나의 평균으로 숨기지 않는다.
- Cross-DAG conflict가 clique이면 speedup이 사라질 것으로 예상하며 이를 negative result로 포함한다.

---

## 6. Related Work

### 6.1 Multi-producer ordering

- Autobahn, Multimmit, Narwhal/Tusk, DAG-Rider, Bullshark, Mysticeti.
- Ordering output, availability와 application execution boundary를 비교한다.

### 6.2 Cross-shard execution

- Chainspace/S-BAC, OmniLedger/Atomix, Byzcuit: synchronous coordination and replay-safe atomic commit.
- Monoxide, NEAR Nightshade: asynchronous receipts/messages.
- X-Shard, Prophet, Presto: optimistic execution or preordering.
- Arete, SharPer, Lemonshark: intra/cross transaction classification, separated phases or delayed fragments.
- RollShard: proof-based batched multi-shard state deltas.

### 6.3 Parallel and distributed execution

- Block-STM: preset order를 보존하는 conflict-driven parallel execution.
- Pilotfish: consensus sequence를 versioned queues와 execution workers로 분산하는 intra-validator architecture.
- Remora: ownership/versioning과 subgraph-first scheduling을 이용한 scale-out execution.
- 본 연구의 구분점은 finalized cut에서 DAG를 결정하고 **validators 사이**에서 untrusted execution을 분산하며 validity proof로 결과를 채택한다는 점이다.

### 6.4 Verifiable computation and availability

- Nova/SuperNova and related IVC: rolling local proof의 cryptographic building blocks.
- Proof-of-Execution, Zaptos: consensus와 execution overlap.
- Validity proof와 proof availability/custody의 역할을 분리한다.

Related Work는 별도 section으로 유지한다. System Design에서는 각 선택의 가장 가까운 precedent를 짧게 인용하고, 이 section에서는 comparison matrix로 assumptions, coordination, rollback, cross-state generality, proof timing과 executor trust를 정리한다.

---

## 7. Discussion and Limitations

- **Semantic change.** Cross intents는 byte-level ordering position에서 즉시 실행되지 않고 cut-tail에서 실행된다. Application과 clients가 이 규칙을 명시적으로 받아들여야 한다.
- **Cross critical path remains.** Canonical DAG와 post-local root가 cut에서 정해지므로 cross proof generation은 여전히 post-cut critical path다.
- **Hot-state serialization.** 동일 shared key를 건드리는 intents는 하나의 chain이 되어 distributed execution speedup이 사라진다.
- **Next-cut dependency.** 미완료 cross result를 읽는 다음 transaction은 해당 component에서 대기한다. Ordering은 진행돼도 state lag가 누적될 수 있다.
- **Static declaration requirement.** Conservative over-declaration은 안전하지만 false conflicts를 늘리고, under-declaration은 proof rejection을 만든다.
- **Witness availability.** Transaction DA와 별도로 authenticated pre-state witness와 proof bundle availability가 필요하다.
- **PAC strength.** `f+1` custody는 최소 한 honest holder를 보장하지만 추가 honest crashes까지 자동으로 견디지는 않는다.
- **Atomic apply scope.** Network-wide simultaneous clocks가 아니라, 같은 proof를 적용한 honest nodes가 partial lane effect를 보이지 않는다는 의미다.
- **Fairness.** Cut-tail batching은 local transactions가 same-cut cross intents보다 먼저 실행되는 application-visible priority를 만든다.
- **Proof cost.** Execution을 분산해도 total proving work는 사라지지 않으며 worker assignment와 admission pricing이 필요하다.

---

## 8. Conclusion

1. Autobahn-family finalized ordering과 application-ready state는 동일한 event가 아니다.
2. State-isolated local work는 cut 전에 실행·증명하여 ordering과 state finality 사이의 간격을 대부분 숨길 수 있다.
3. General cross-state work는 clean하게 한 번의 complete intent로 ordering하고 finalized cut에서 deterministic conflict DAG로 만드는 편이 branch/rollback/fragment coordination보다 단순하다.
4. Cross proof 자체는 cut 이후 생성되지만 inter-validator verifiable execution으로 DAG의 parallel width를 활용해 critical path를 줄일 수 있다.
5. 결과는 ordering progress를 proof readiness와 분리하면서도 Byzantine executors의 결과를 재실행 합의가 아닌 proof verification으로 채택하는 state-finalization architecture다.

---

## Figures and tables

### Figures

1. Baseline versus proposed local/cross critical paths.
2. Producer blocks의 `local_body`와 `cross_tail`, finalized cut과 state schedule.
3. Block generation, local rolling proof와 previous-cut cross DAG가 겹치는 pipeline.
4. Finalized cross intents에서 deterministic conflict DAG를 만드는 예시.
5. Inter-validator worker assignment, proof sidecar/PAC와 atomic multi-lane apply.
6. Transfer plus N-lane liquidation example and proof-certified failure/no-op.
7. Stalled DAG component와 dependency-disjoint progress.

### Tables

1. Ordering, state execution, proof system과 application의 trust responsibilities.
2. Atomic commit, receipt, optimistic branching, phase separation과 proposed model 비교.
3. Baseline/ablation matrix.
4. Threat, detection, affected scope와 failover outcome.
5. Claim-to-experiment mapping.
6. Previous branch-proof design versus revised cut-tail DAG design.

---

## Paper-wide wording constraints

- “기존 연구는 state finality를 다루지 않았다” 대신 “Autobahn-family ordering output을 proof-verified state readiness로 바꾸는 execution path는 핵심 scope 밖이었다”고 쓴다.
- “rollback”은 사용하지 않는다. Proposed model은 unverified cross result를 canonical state에 적용하지 않으며 failure는 proof-certified no-op이다.
- “all transactions are pre-proved”라고 쓰지 않는다. Local proof만 cut 전 canonical candidate가 될 수 있고 cross proof는 cut 이후다.
- “DAG consensus”라고 부르지 않는다. Consensus가 확정한 cut에서 deterministic execution DAG를 유도한다.
- “proof certificate가 correctness를 투표한다”고 쓰지 않는다. Validity proof가 correctness를, PAC가 custody/recovery를 담당한다.
- “distributed execution eliminates latency”라고 쓰지 않는다. Speedup은 cross DAG의 available parallelism과 critical path에 제한된다.
