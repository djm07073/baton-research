# Verifiable Computing Problem and Literature Map

> 기준일: 2026-09-16  
> 대상: `paper-outline.md`의 revised v12 cut-tail cross-lane DAG model  
> 주의: `proof-aware-multimmit-paper.md`와 `commonware-proof-sdk.md`는 아직 이전 branch-proof model을 active baseline으로 두고 있다. 이 문서는 두 방향을 합치지 않고, 최신 cut-tail 방향의 연구 경계만 분석한다.
> Concrete folding, distributed proving과 availability backend의 선택지는
> [`verifiable-computing-research-map.md`](./verifiable-computing-research-map.md)에 정리한다.

## 1. 먼저 정의해야 하는 연구 문제

Autobahn-family ordering layer가 finalized cut `F_k`를 확정했다고 하자. `F_k`는 각 producer lane `i`에서 canonical prefix height `h_(i,k)`를 선택하고, protocol의 deterministic extraction rule은 연속된 cuts 사이의 ordered input `B_k`를 만든다.

```text
F_k = (h_(1,k), ..., h_(m,k))
B_k = OrderedInputs(F_(k-1), F_k)
T_cut(v,k) = node v가 F_k를 finalized로 관측한 시점
```

`B_k`가 확정되었다는 것은 canonical input과 순서가 정해졌다는 뜻이지, 그 입력의 application transition, post-state proof, apply material과 serving state가 준비되었다는 뜻은 아니다. Node `v`와 state component `c`에 대해 다음을 측정한다.

```text
Delta(k,v,c) = T_applied(k,v,c) - T_cut(v,k)
Lag(v,c,t)   = latest_finalized_cut(t) - latest_applied_cut(v,c,t)
```

여기서 `T_applied`는 node가 exact finalized input에 바인딩된 proof를 검증하고 canonical-parent continuity를 확인한 뒤 delta를 durable하게 적용한 시점이다. 별도 state QC가 없으므로 모든 node가 동시에 state-final이 되는 global event를 주장하면 안 된다. 정확한 대상은 **node-local verifiable state readiness**이며, 안전성 정리는 같은 cut을 적용한 honest nodes의 결과 일치로 표현한다.

### 1.1 Application schedule

Transaction bytes와 immutable schema에서 conservative read/write set과 owner set을 정적으로 계산할 수 있다고 가정한다.

각 lane-local state partition `S_i`에 대해 producer는 candidate prefix마다 rolling proof `Q_i(h)`를 만들 수 있다. State isolation 때문에 `Q_i(h)`의 transition은 다른 lane의 아직 정해지지 않은 tip과 무관하고, cut이 `h_(i,k)`를 선택하면 node는 정확히 그 prefix의 proof만 join한다. 선택되지 않은 candidate proof는 canonicality를 얻지 않는다.

```text
L_k = transactions in B_k whose owner-set size is 1
X_k = transactions in B_k whose owner-set size is at least 2

ApplyCutTail(B_k, S_(k-1)) =
  S_local := JoinSelectedLocalProofs({Q_i(h_(i,k))}, S_(k-1))
  G_k     := ConflictDAG(X_k, finalized_priority, S_local)
  S_k     := VerifyAndApplyProofDAG(G_k, S_local)
```

`G_k`는 `W(x)`와 `R(y) ∪ W(y)`가 겹치는 두 operations 사이에 finalized priority 방향의 edge를 둔다. 따라서 DAG 결과는 그 priority를 보존하는 deterministic sequential execution과 동등해야 한다.

Cross-DAG task proof는 최소 `(F_k, G_k, task_id, predecessor commitments, pre-state commitments, output delta, post-state commitments, circuit version)`에 bind된다. 한 cross operation이 여러 components를 갱신하면 node는 그 delta를 crash-atomic하게 함께 적용하거나 전혀 적용하지 않는다. 다른 nodes의 apply 시점은 달라도, 같은 cut과 valid proofs를 적용한 honest nodes의 commitment는 같아야 한다.

이 schedule은 원래 global byte order를 그대로 실행하는 것이 아니라, local body 뒤에 cross tail을 두는 **application-visible semantic change**다. Typed block sections 또는 deterministic stable partition을 protocol contract로 명시해야 한다.

### 1.2 최적화 목표

연구 문제는 단순히 proof를 붙이는 것이 아니다.

> Finalized ordering을 변경하거나 proof readiness 때문에 막지 않으면서, cut-independent local work는 cut 이전에 실행·증명하고, cut-dependent multi-owner work는 finalized cut에서 파생된 DAG를 Byzantine workers 사이에 분산하여 `Delta(k,v,c)`와 validator별 중복 실행을 얼마나 줄일 수 있는가?

목표는 세 축을 함께 측정해야 한다.

1. `Delta_local`, `Delta_cross`와 `Lag`의 p50/p95/p99.
2. Replicated execution 대비 per-validator 및 system-wide execution/proving work.
3. Proof 또는 witness withholding이 있을 때 ordering과 dependency-disjoint components의 progress.

공통 경로의 총 계산량은 대략 다음 조건에서만 유리하다.

```text
replicated baseline:       n * E
verifiable distribution:  P + n * V + communication

benefit requires: P + n*V + communication < n*E
```

`E`, `P`, `V`는 각각 execution, proof generation, verification cost다. Proof가 무거우면 latency를 겹쳐도 총 자원 사용량은 오히려 증가한다.

이 조건은 소수 validator 실험에서 특히 엄격하다. Piperine의 payment-service 평가도 proof delegation의 총비용 교차점을 `10^4`개가 넘는 replicas에서 보고했다. 현재 계획처럼 약 6 validators를 쓰는 경우, cryptographic proof가 replicated native execution보다 총 계산량을 줄인다고 가정하면 안 된다. Local path는 proving을 cut 이전에 숨겨 **latency**를 줄일 수 있지만, post-cut cross path는 `critical-path execution + proof generation + dissemination + verification`이 baseline re-execution보다 실제로 짧은지 real backend로 입증해야 한다.

### 1.3 Proof 효과를 분리하기 위한 필수 대조군

State isolation이 성립하면 proof가 없어도 모든 validators가 candidate lane prefixes를 수신 즉시 speculative하게 실행하고, cut이 고른 exact prefix의 결과를 채택할 수 있다. 따라서 local pre-cut latency hiding 자체를 validity proof의 효과로 주장하면 안 된다. Proof의 추가 역할은 **모든 validators의 중복 실행을 한 번의 untrusted execution과 여러 번의 cheap verification으로 대체하는 것**이다.

Cross tail도 마찬가지다. 모든 validator가 cut-derived DAG를 로컬 cores에서 병렬 실행하는 baseline과, DAG tasks를 validators 사이에 분산하고 proof로 채택하는 제안을 비교해야 한다. 제안이 wall-clock latency를 줄이는 조건은 대략 다음이다.

```text
distributed critical path
  = task execution/proving critical path
  + proof transfer
  + verification/apply

distributed critical path < per-validator local DAG execution critical path
```

따라서 최소 대조군은 `(a)` post-cut sequential replicated execution, `(b)` pre-cut speculative replicated local execution, `(c)` per-validator local parallel DAG, `(d)` distributed proof DAG다. 이 비교가 없으면 state isolation, pre-execution, DAG parallelism과 proof outsourcing 중 무엇이 latency를 줄였는지 분리할 수 없다.

## 2. PAC가 정확히 해결하는 문제

Proof bundle subject는 최소 다음에 바인딩되어야 한다.

```text
H(epoch,
  finalized_cut_digest,
  dag_digest,
  task_or_local_prefix_id,
  predecessor_commitments,
  pre_state_commitments,
  output_delta_commitment,
  circuit_version,
  proof_bundle_digest)
```

Custodian은 exact bytes를 검증하고 durable하게 저장한 뒤에만 share를 서명한다. `f+1` shares는 최대 `f` Byzantine faults 아래 최소 한 honest holder가 존재함을 보장한다.

PAC의 보장과 비보장은 다음처럼 분리된다.

| 질문 | 담당 메커니즘 |
|---|---|
| 어떤 input/branch가 canonical인가? | finalized cut |
| transition이 올바른가? | validity proof와 exact public-input binding |
| 완료된 proof bundle을 나중에 가져올 수 있는가? | PAC custody |
| proof가 아직 생성되지 않았을 때 누가 다시 만드는가? | deterministic failover + witness availability |
| ordering이 proof를 기다리지 않는가? | ordering/execution decoupling |

따라서 PAC는 proof generation을 빠르게 하지 않고, proof가 없는 상태를 proof-certified failure로 바꾸지도 않는다. Latest outline처럼 valid proof를 받은 node가 즉시 apply할 수 있다면 PAC는 fast-path finality prerequisite가 아니라 late/recovering nodes를 위한 recovery primitive다. 반대로 PAC를 state admission의 필수조건으로 만들면 특히 post-cut cross proof에 한 RTT를 추가한다.

### 2.1 PAC 자체의 novelty 판정

PAC의 quorum idea는 신규성이 약하다. [Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)은 data proposal을 저장한 `f+1` replicas의 vote로 PoA를 만들고, 최소 한 correct holder로부터 나중에 데이터를 회수한다. PAC는 같은 custody argument를 execution proof bundle에 적용한다.

따라서 논문에서는 다음처럼 써야 한다.

> PAC is a result-availability adaptation of Autobahn's input-availability pattern, not a new quorum primitive. Its role is to preserve non-blocking proof-carrying execution under result withholding.

Lane이 막히지 않는 성질은 PAC 단독이 아니라 다음 조합에서 나온다.

```text
ordering/proof decoupling
  + state ownership
  + dependency-scoped readiness
  + proof-carrying results
  + recoverable proof custody
```

## 3. Threat model and liveness contract

### 3.1 Safety assumptions

- Underlying Autobahn-family protocol의 finalized-cut safety, liveness와 ordered-input availability를 상속한다.
- `n` validators 중 최대 `f`가 Byzantine이다. Autobahn instantiation은 `n=3f+1`; Multimmit artifact의 별도 resilience 조건은 구현 절에서 분리한다.
- Safety는 asynchronous network에서도 유지하고, liveness는 authenticated reliable channels와 eventual synchrony 이후에 주장한다.
- Adversary는 proof를 위조할 수 없고 collision-resistant commitment와 signature를 깨지 못한다.
- Application transition은 deterministic하며 code/circuit version이 public input에 bind된다.
- 실제 read/write set이 signed conservative declaration 밖으로 나가면 proof가 verify되지 않는다.
- Apply는 node-local crash-atomic batch다. Irreversible external effects는 proof-admissible state 이전에 노출하지 않는다.

### 3.2 Byzantine actions covered

- Worker가 invalid result/proof, wrong parent, wrong DAG digest 또는 undeclared access를 제출한다.
- Worker가 task를 equivocate하거나 proof를 withholding한다.
- Custodian이 bundle을 withholding하거나 PAC share를 equivocate한다.
- Producer가 duplicate cross intent 또는 invalid application transaction을 포함한다.
- Adversary가 hot keys와 oversized manifests로 DAG width를 줄이거나 proving queue를 과부하시킨다.

Proof soundness는 invalid result를 막지만 withholding과 overload는 막지 않는다.

### 3.3 Conditional liveness assumptions

State liveness는 다음 조건을 명시해야 한다.

1. Finalized cuts가 계속 증가한다.
2. 각 ready task의 deterministic ranked worker set에 결국 live honest prover가 존재한다.
3. Ordered transaction data뿐 아니라 authenticated pre-state witness, predecessor output과 circuit artifact를 takeover worker가 얻을 수 있다.
4. Proving/verification/apply service rate가 장기 arrival rate보다 충분히 크다.
5. Honest PAC custodian은 retention window 동안 fair하게 digest-addressed requests에 응답한다.
6. Request load와 stored unresolved dependency width가 bounded다.

이 조건 아래:

- Ordering liveness는 proof/PAC와 무관하다.
- Stalled proof는 그 node의 descendants와 그 state dependency closure만 늦춘다.
- Dependency-disjoint components는 계속된다.
- `D_failover` finalized cuts 뒤 다음 ranked worker가 takeover하여 affected component도 eventually ready가 된다.

`f+1` PAC는 static fault model에서 Byzantine withholding만 견딘다. 추가 honest crash `c`개까지 견디려면 `q >= f+c+1`, erasure coding 또는 proactive replication이 필요하다. Mobile/adaptive corruption에서 과거 honest holder까지 차례로 corrupt할 수 있다면 `f+1`만으로 장기 availability를 주장할 수 없다.

### 3.4 논문에서 증명해야 할 properties

1. **Cut determinism.** 같은 `F_k`와 이전 state commitment를 가진 honest nodes는 같은 local/cross partition, priority, `G_k`와 proof public inputs를 계산한다.
2. **Proof-admission safety.** Sound proof를 통과한 delta만 적용하면 각 applied transition은 `ApplyCutTail`의 유효한 step이고, undeclared access나 wrong predecessor는 state에 들어오지 않는다.
3. **Atomic visibility.** 한 N-component operation의 delta는 한 node에서 all-or-none으로 노출되고, successor는 모든 predecessor commitments가 ready일 때만 실행·적용된다.
4. **Convergence.** 같은 cut prefix까지 valid proof DAG를 적용한 honest nodes는 동일 state commitment에 도달한다. 이는 동시 apply 또는 global state-QC를 뜻하지 않는다.
5. **Ordering non-interference.** Proof generation, PAC formation과 recovery 실패는 finalized-cut protocol의 vote/admission predicate가 아니다.
6. **Scoped conditional liveness.** 위 liveness assumptions 아래 stalled task와 conflict/dependency-disjoint component는 계속 advance하고, failover 뒤 affected component도 eventually advance한다.

## 4. Primary literature map

### 4.1 Ordering/execution separation and execution certificates

- [LazyLedger](https://arxiv.org/abs/1905.09274)는 consensus를 transaction ordering과 input availability로 제한하고 application execution을 clients에 위임한다. Ordering-only ledger boundary 자체는 알려져 있다.
- [Executing and Proving over Dirty Ledgers](https://eprint.iacr.org/2022/1554.pdf)는 SMR을 ordering layer와 execution layer로 명시적으로 분해하고 E-Safety/E-Liveness 및 succinct state certificates를 정의한다. “ordering-final is not state-ready”라는 문제 정의의 가장 직접적인 formal precedent다.
- [Zaptos](https://arxiv.org/abs/2501.10612)는 optimistic execution, state certification과 storage를 consensus와 겹쳐 end-to-end latency를 줄인다. Pre-cut execution overlap 자체는 신규성이 아니다.
- [CHIRON](https://arxiv.org/abs/2401.14278)은 finalized execution hints를 lagging nodes에 제공해 full re-execution을 가속하며, hints를 consensus critical path 밖에 둔다. 또한 `f+1` matching hints로 최소 한 honest source를 얻는 패턴을 사용한다.
- [Piperine: Replicated State Machines without Replicated Execution](https://www.microsoft.com/en-us/research/uploads/prod/2020/05/2020-195.pdf)은 이 연구에 대한 가장 강한 verifiable-SMR 선행연구다. 임의의 untrusted prover가 transaction batch를 실행해 output, post-state digest, succinct state delta와 proofs를 만들고, RSM replicas는 원래 state machine 대신 verifier를 복제하여 delta를 검증·적용한다. 따라서 “한 worker가 실행하고 다른 validators가 proof로 적용한다”는 주장은 이미 알려져 있다. 현재 방향은 finalized-cut-derived cross-state dataflow, validator-set task scheduling/failover, pre-cut local path와 dependency-scoped readiness의 결합으로 구분해야 한다.

### 4.2 State/object isolation and distributed execution

- [Sui Lutris](https://sonnino.com/papers/sui-lutris.pdf)는 owned objects의 consensusless path와 shared objects의 consensus-ordered path를 결합한다. Ownership isolation, static object access와 shared-state serialization은 알려져 있다.
- [Pilotfish](https://sonnino.com/papers/pilotfish.pdf)는 각 validator 내부에서 object state를 ExecutionWorkers에 shard하고 consensus sequence의 dependency graph를 deterministic하게 실행한다. Workers는 validator 내부 crash-fault domain이며, correct validators는 같은 transaction을 각각 실행한다.
- [Remora](https://arxiv.org/abs/2607.02817)는 validator 내부 Coordinator/Workers, strict ownership/object versioning, subgraph-first scheduling과 pre-consensus stateless execution overlap을 제공한다. Local overlap, ownership과 DAG scheduling 각각은 신규성이 아니다.
- [Block-STM](https://arxiv.org/abs/2203.06871)은 preset order를 보존하는 optimistic parallel execution과 conflict validation/re-execution을 제공한다.

Pilotfish/Remora와의 구분점은 **한 validator 내부 scale-out**이 아니라 validator fault domains를 가로지르는 execution이다. 그러나 inter-validator/untrusted execution outsourcing 자체는 Piperine과 dirty-ledger execution protocol이 이미 다루므로, 그것만으로 novelty를 주장할 수 없다. 남는 후보는 Autobahn-family cut에서 canonical cross-state DAG와 proof public inputs를 결정하고, 그 DAG의 ready tasks를 validator set에 분산·failover하며, 느린 task의 영향을 dependency closure로 제한하는 protocol composition이다.

### 4.3 Verifiable multi-shard execution

- [Arete](https://www.vldb.org/pvldb/vol18/p2198-zhang.pdf)는 dissemination, ordering, execution을 deconstruct하고 하나의 ordering shard와 여러 processing shards를 조합하며 certify-order-execute pipeline으로 intra-/cross-shard work를 겹친다. 따라서 local/cross phase separation과 ordering/execution decoupling도 직접적인 structural precedent다. 다만 processing shards는 proof-carrying DAG tasks가 아니라 shard committees로 안전성과 실행을 담당한다.
- [RollShard](https://doi.org/10.1109/TC.2026.3673996)는 가장 가까운 선행연구다. Sequencer Shard가 multi-shard transaction DAG를 만들고 stateless off-chain executor가 hierarchical state-delta tree와 ZK proof로 per-shard deltas 및 global value conservation을 증명한다.

RollShard 때문에 “transaction DAG + off-chain execution + ZK atomic multi-shard delta”는 주장할 수 없다. 남는 후보 차이는 다음과 같다.

1. DAG를 별도 Sequencer Shard가 정하는 것이 아니라 Autobahn finalized cut과 signed declarations에서 모든 node가 동일하게 유도한다.
2. Cross path만 다루지 않고 pre-cut local proof pipeline과 post-cut cross DAG를 하나의 cut-to-state protocol로 결합한다.
3. DAG tasks를 validator set에 deterministic하게 분산하고 Byzantine result를 quorum execution이 아니라 validity proof로 채택한다.
4. Exact proof/apply bundle availability, cut-count failover와 component-scoped state readiness를 protocol liveness에 포함한다.

이 차이가 실제 contribution이 되려면 RollShard보다 넓은 arbitrary transition relation, inter-validator task assignment/failover, proof composition과 availability를 구현·평가해야 한다.

### 4.4 Proof-carrying distributed computation

- [Proof-Carrying Data](https://projects.csail.mit.edu/pcd/)는 mutually distrustful parties의 distributed computation에서 각 message가 local compliance와 history를 증명하는 proof를 운반하는 일반 primitive다.
- [Recursive SNARKs and PCD](https://eprint.iacr.org/2012/095.pdf)는 recursive composition으로 distributed computation history를 succinct하게 검증하는 기반을 제공한다.
- [Proof-carrying data from arithmetized random oracles](https://doi.org/10.1007/978-3-031-30617-4_13)는 PCD가 서로 불신하는 parties의 distributed computation을 검증하는 일반 framework임을 더 확장한다.
- [Mina/Coda](https://minaprotocol.com/wp-content/uploads/2021/01/technicalWhitepaper.pdf)는 parallel scan state로 block production과 recursive proof work를 분리한다. Async proof queue와 recursive aggregation 자체는 알려져 있다.

따라서 “DAG node마다 proof를 붙인다” 또는 “proof를 background에서 생성한다”는 단독 novelty가 아니다. System novelty는 finalized cut, ownership schedule, worker assignment, proof handoff, custody와 state apply의 결합 규칙에서 찾아야 한다.

### 4.5 Distributed proof generation

- [DIZK](https://www.usenix.org/system/files/conference/usenixsecurity18/sec18-wu.pdf)는 한 ZK proof의 생성을 cluster에 분산한다.
- [Pianist](https://doi.org/10.1109/SP54263.2024.00035)는 general circuits의 Plonk proof generation을 여러 machines에 분산하면서 constant proof size와 verifier cost를 유지한다.
- [zkBridge/deVirgo](https://arxiv.org/abs/2210.00264)는 distributed sumcheck와 polynomial commitment로 proof generation을 병렬화하고 recursive proof로 on-chain verification cost를 줄인다.
- [CrowdProve](https://arxiv.org/abs/2501.03126)는 unreliable commodity provers에 ZK-rollup proving jobs를 분산하는 orchestration layer를 제안한다.

이 연구들은 prover throughput과 orchestration의 해법이다. 그러나 BFT finalized cut에서 파생된 state dependency DAG, component-level state liveness와 exact result custody를 함께 정의하지는 않는다.

### 4.6 Proof/data availability

- [Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf)의 `f+1` PoA가 PAC의 가장 직접적인 quorum precedent다.
- [Proof of Availability and Retrieval in a Modular Blockchain Architecture](https://eprint.iacr.org/2022/455.pdf)는 availability를 push certificate와 pull/retrieval protocol로 명시적으로 분리하고 대규모 participant 환경의 retrieval을 분석한다. PAC를 논하려면 certificate 생성뿐 아니라 signer discovery, pull fan-out, retention과 unavailable responder 아래 retrieval termination까지 이 abstraction과 비교해야 한다.
- [Narwhal and Tusk](https://arxiv.org/abs/2105.11827)는 reliable transaction dissemination/storage를 ordering과 분리한다.
- [DispersedLedger](https://www.usenix.org/system/files/nsdi22-paper-yang_lei.pdf)는 full content를 받지 않고도 available/unmalleable block commitments를 ordering하고 node별 retrieval을 비동기화한다.
- [Fraud and Data Availability Proofs](https://arxiv.org/abs/1809.09044)는 validity와 availability가 별도 속성임을 명시한다.

Proof soundness가 proof bytes, witness 또는 apply material availability를 보장하지 않는다는 구분은 기존 DA 연구와 일치한다. PAC의 가치는 새 threshold보다 **post-execution result를 이 availability discipline에 포함하는 protocol integration**에 있다.

### 4.7 Sequencer/prover decoupling

- [Scroll architecture](https://docs.scroll.io/en/technology/)와 [rollup process](https://docs.scroll.io/en/technology/chain/rollup/)는 sequencing/execution, coordinator-managed prover pool, proof aggregation과 L1 finalization을 별도 pipeline으로 둔다. Coordinator는 chunk/batch proving task를 prover에 배치하고 proof가 돌아온 뒤 relayer가 finalization transaction을 제출한다.
- [push0](https://arxiv.org/abs/2602.16338)는 head-of-chain dependency, persistent queues, fault-tolerant proof-task reassignment과 intra-block parallelism을 다루는 recent prover orchestration system이다. Byzantine state-transition admission을 설계하지는 않지만, proof task scheduling과 retry/failover 자체는 novelty가 아님을 보여준다.
- ZK-rollups, Mina scan state와 distributed prover systems 모두 execution/ordering과 proof generation이 다른 속도로 진행하는 구조를 이미 사용한다.

따라서 “proof generation을 block production과 비동기화한다”는 단독 contribution이 아니다. 본 연구는 rollup처럼 별도 L1 settlement을 기다리는 모델이 아니라, BFT validator network 내부에서 finalized cut 직후 node-local state readiness를 만드는 것이 구분점이어야 한다.

## 5. Known versus defensibly open

### 이미 알려진 것

- Ordering과 execution/state readiness의 분리.
- Pre-consensus speculative execution과 pipeline overlap.
- Object/state ownership, static access lists와 shared-state serialization.
- Dependency DAG에 의한 deterministic parallel execution.
- Intra-validator scale-out execution.
- Untrusted prover가 state transition proof와 succinct delta를 만들고 RSM replicas가 검증·적용하는 non-replicated execution.
- Recursive proof/PCD, background proof queues와 distributed proving.
- Off-chain ZK execution을 통한 atomic multi-shard deltas.
- `f+1` custody로 최소 한 honest data holder를 확보하는 availability certificate.

### 방어 가능한 open combination

현재 조사에서 가장 방어 가능한 system contribution은 다음 조합이다.

> An asynchronous state-readiness protocol for frontier-ordered BFT that combines exact-prefix pre-cut local proofs with a finalized-cut-derived cross-state dataflow. Unlike generic verifiable RSM delegation, the finalized cut determines one canonical conflict DAG and proof namespace; ready DAG tasks are deterministically placed and failed over across the validator set, while proof-bound deltas let every node advance dependency-disjoint state without placing execution readiness on the ordering path.

핵심은 PAC가 아니라 다음 end-to-end property다.

```text
one finalized cut
  -> one deterministic execution dataflow
  -> untrusted inter-validator task execution
  -> proof-carrying atomic deltas
  -> node-local asynchronous apply
  -> only dependency closure stalls on withholding
```

이를 뒷받침하려면 최소 다음 네 결과가 필요하다.

1. Cut-tail schedule의 deterministic serializability와 semantic contract.
2. Byzantine worker 아래 proof-admission safety와 N-lane atomic apply.
3. PAC/witness/failover 가정 아래 component-scoped conditional liveness.
4. Pilotfish/Remora-style replicated execution 및 RollShard-style off-chain proof baseline 대비 cut-to-state latency와 per-validator work 감소.

## 6. 권장 contribution statement

1. **Cut-relative state semantics.** Frontier-based finalized cut을 local pre-proved prefixes와 deterministic cross-state tail로 변환하는 application schedule을 정의한다.
2. **Cut-derived proof-carrying cross-state execution.** Finalized cut에서 하나의 canonical conflict DAG와 proof namespace를 유도하고 ready nodes를 mutually distrustful validators에 분산·failover하여, quorum re-execution 없이 proof-verified atomic multi-owner deltas를 적용한다. Generic verifiable delegation이 아니라 cut-relative scheduling과 composition rule이 contribution이다.
3. **Non-blocking result recovery and characterization.** Exact bundle custody, cut-count failover와 dependency-scoped readiness를 결합하고, proof lag·contention·faults 아래 cut-to-state latency 및 work trade-off를 정식화·평가한다.

PAC는 Contribution 3의 핵심 mechanism이지만 독립 contribution으로 두지 않는다.

## 7. 피해야 할 주장

- “PAC가 처음이다.” Autobahn PoA가 직접적인 구조적 precedent다.
- “Proof가 lane을 non-blocking하게 만든다.” Ordering decoupling과 dependency isolation이 progress를 만들고 PAC는 retrieval을 돕는다.
- “모든 lane이 계속 state-finalize한다.” Unresolved output을 읽는 dependency closure는 기다려야 한다.
- “State isolation/DAG/static manifest가 처음이다.” Sui, Pilotfish와 Remora가 강한 precedent다.
- “Proof-based atomic cross-shard execution이 처음이다.” RollShard가 직접 겹친다.
- “Untrusted worker 한 곳이 실행하고 replicas가 proof/delta만 적용하는 것이 처음이다.” Piperine이 직접 겹친다.
- “Async proof generation이 처음이다.” Mina와 zk-rollups가 이미 사용한다.
- “Proof가 DA를 해결한다.” Proof validity, witness availability와 apply-material availability는 별도다.
- “Mock proof benchmark가 cryptographic speedup을 입증한다.” Real proof backend가 반드시 필요하다.

## 8. 현재 문서 충돌

`paper-outline.md` v12는 다음을 명시적으로 제거한다.

- participant fragments와 handshake
- pre-cut `Commit/Abort` dual branches
- decision deadline과 branch overlays
- completeness certificate와 canonical rollback

반면 `proof-aware-multimmit-paper.md`, `commonware-proof-sdk.md`, `README.md`와 `AGENTS.md`는 이 branch-proof model을 active source of truth로 둔다. 두 모델은 cross path의 canonical proof timing과 public inputs가 달라 동시에 active일 수 없다.

- Branch model: cross result 두 개를 cut 전에 증명하고 cut이 선택한다.
- Cut-tail model: complete intent만 ordering하고 cut 뒤 canonical DAG에서 한 결과를 증명한다.

공유 가능한 부분은 local pre-cut rolling proof, exact cut binding, proof sidecar/custody와 proof-independent ordering뿐이다. 논문 방향을 cut-tail로 확정한다면 protocol/SDK/README/AGENTS를 별도 migration으로 동기화해야 한다.
