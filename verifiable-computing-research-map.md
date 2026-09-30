# Verifiable Computing Research Map for Cut-to-State Finality

> 상태: literature-backed problem definition and design map  
> 기준일: 2026-09-16  
> 대상: `paper-outline.md` v12의 cut-tail local/cross-DAG 방향  
> 주의: `proof-aware-multimmit-paper.md`와 `commonware-proof-sdk.md`는 아직 이전
> conflict-scoped dual-branch model을 active baseline으로 기록한다. 이 문서는 최신 개요를
> 분석 대상으로 삼지만, protocol source of truth를 이 문서만으로 변경하지 않는다.
> 문제 정의, 정리 후보와 novelty threat는
> [`verifiable-computing-problem-map.md`](./verifiable-computing-problem-map.md)에 더 엄격하게
> 정리하고, 이 문서는 concrete proof/availability mechanism의 선택지를 보완한다.

## 1. 먼저 문제를 정확히 정의한다

### 1.1 우리가 풀려는 것은 consensus가 아니다

Autobahn-family consensus가 finalized cut `F_k`를 확정하면 다음 사실은 이미 결정된다.

```text
Ordered(F_k): 어떤 authenticated inputs가 어떤 canonical order에 포함되는가
```

그러나 read-serving node가 사용할 application state에는 추가 작업이 필요하다.

```text
StateReady_v(k,c): node v가 state component c에 대해
  1. F_k가 선택한 exact input과 canonical parent를 확인하고,
  2. 그 input의 execution result가 application transition을 만족함을 검증하고,
  3. 필요한 state delta/apply material을 확보하여,
  4. durable state에 적용했다.
```

논문의 주 측정값은 component별 다음 간격이다.

```text
Delta(k,v,c) = T_StateReady(k,v,c) - T_FinalizedCut(k)
```

모든 component의 최대값만 보면 hot component 하나가 전체 결과를 가리므로 다음을 함께
측정해야 한다.

```text
StateLagCuts(v,c) = latest_finalized_cut - latest_state_ready_cut(v,c)
ReadyGoodput      = proof-verified and durably applied computation / second
```

### 1.2 Verifiable-computing relation

Cut 전에 만드는 local proof는 아직 `F_k`를 알 수 없으므로 proof relation과 canonical admission
relation을 분리해야 한다. Base execution proof가 인증해야 하는 최소 relation은 다음과 같다.

```text
R_transition(
  application_id,
  circuit_version,
  canonical_parent_commitments,
  candidate_ordered_input_digest,
  declared_read_write_set,
  predecessor_output_commitments,
  status,
  state_delta_commitment,
  post_state_commitments;
  execution_witness
)
```

Cut 이후 state admission은 별도의 deterministic join을 요구한다.

```text
AdmissibleLocal(F_k, pi) iff
  Verify(R_transition, pi)
  AND candidate_ordered_input_digest(pi) = LocalPrefixDigest(F_k)
  AND parent_commitments(pi) = current_canonical_parents

AdmissibleCross(F_k, pi) iff
  Verify(R_transition, pi)
  AND finalized_cut_digest(pi) = H(F_k)
  AND cross_dag_digest(pi) = DeterministicCrossDAG(F_k)
  AND parent_commitments(pi) = verified predecessor outputs
```

Local proof는 candidate input에 bind되고 cut이 exact prefix를 선택할 때 late-bind된다. 반대로
cross proof는 cut 이후 생성되므로 finalized-cut와 DAG digest를 public input에 직접 포함한다.
`Verify(R_transition, pi) = true`는 execution correctness를 보장한다. 다음 사실은 별개의
protocol layer가 보장한다.

- **Canonicality:** finalized cut과 deterministic schedule이 보장한다.
- **Proof correctness:** succinct validity proof가 보장한다.
- **Proof/apply-material retrievability:** custody certificate 또는 information dispersal이 보장한다.
- **Durable visibility:** 각 node의 crash-atomic state apply가 보장한다.

따라서 PAC는 validity proof도 state-finality vote도 아니다.

### 1.3 두 종류의 computation

#### Cut-independent local work

하나의 state-owner lane만 읽고 쓰며 lane-local order가 candidate cut 선택과 양립하는 계산이다.
Execution과 proof accumulation을 cut 전에 수행할 수 있다.

```text
Delta_local ~= max(0, T_proof_available(exact_prefix) - T_cut)
               + T_fetch + T_verify + T_apply
```

#### Cut-dependent cross-state work

둘 이상의 owner state를 읽거나 쓰며 canonical parents와 conflict order가 finalized cut에서
결정되는 계산이다. Cut 전에 signature/access-set 검증과 witness prefetch는 가능하지만 exact
canonical proof는 일반적으로 완성할 수 없다.

```text
Delta_cross ~= CriticalPath(
                  execute + prove + disseminate + verify over CrossDAG_k
                )
                + T_atomic_apply
```

이 구분은 중요하다. 하나의 proof system이 두 문제를 같은 방식으로 해결하지 않는다.

### 1.4 Proof가 실제로 추가하는 효과를 분리한다

State isolation과 deterministic execution이 이미 성립한다면 proof가 없어도 모든 validators가
candidate local prefixes를 cut 전에 실행하고, cut이 선택한 exact prefix의 결과를 채택할 수 있다.
그러므로 local pre-execution의 latency hiding 자체는 proof의 효과가 아니다.

Proof의 독자적인 역할은 다음 치환이다.

```text
n validators x native execution
        ->
untrusted execution/proving + n validators x succinct verification/apply
```

Cross path도 모든 validator가 같은 cut-derived DAG를 자신의 cores에서 병렬 실행하는 방법과
validators 사이에 DAG tasks를 분산하고 proof로 결과를 채택하는 방법을 구분해야 한다. 제안이
유리하려면 proof orchestration의 critical path가 local parallel re-execution보다 실제로 짧아야 한다.

## 2. 필요한 성질

### 2.0 Scope assumptions

- Signed transaction bytes와 immutable application schema만으로 conservative owner/read/write set을
  실행 전에 계산할 수 있다.
- Runtime의 actual access는 declaration의 subset이어야 하며 proof circuit이 이를 강제한다.
- Application transition은 같은 inputs와 parent commitments에 대해 deterministic하다.
- Prover failover가 가능하도록 ordered input, authenticated state witness와 circuit version을 복구할
  수 있다.
- Runtime-dependent storage address나 dynamic call target으로 footprint가 바뀌는 arbitrary EVM
  transaction은 현재 범위 밖이다.
- Proof soundness는 등록된 circuit relation에 상대적이다. Circuit 자체가 business intent를 올바르게
  표현한다는 보장은 별도 audit/formal verification 문제다.

### 2.1 Safety

1. **Exact-cut binding:** 다른 candidate prefix에 대한 valid proof를 canonical state에 적용하지 않는다.
2. **Parent continuity:** proof의 pre-state commitments가 현재 canonical parents와 일치한다.
3. **Access confinement:** actual reads/writes가 signed static declaration 밖으로 나가지 않는다.
4. **Serial equivalence:** conflict DAG의 병렬 결과가 finalized priority를 보존한 순차 실행과 같다.
5. **N-owner atomicity:** 하나의 cross operation은 모든 participant commitments를 함께 갱신하거나
   proof-certified failure/no-op이 된다.
6. **No missing-proof inference:** proof가 없다는 이유로 application failure라고 판단하지 않는다.

### 2.2 Non-blocking liveness

`non-blocking`은 모든 state가 항상 전진한다는 뜻이 아니다.

```text
Proof delay must not block:
  - Autobahn-family ordering progress
  - dependency-disjoint state components

Proof delay may block:
  - the affected component
  - its causal descendants
```

Affected component의 eventual readiness에는 다음 조건이 필요하다.

- 적어도 하나의 live prover가 task와 witness를 재구성할 수 있다.
- proof system의 sustained service rate가 ordered proof work의 arrival rate 이상이다.
- proof와 apply material이 retention window 동안 복구 가능하다.
- network eventual synchrony와 bounded request load가 성립한다.

### 2.3 Performance condition

Succinct verification이 re-execution보다 싸다는 사실만으로 충분하지 않다.

```text
steady state requires:
  proving_capacity >= admitted_proof_work_rate

latency benefit requires:
  critical_path(distributed prove + fetch + verify + apply)
    < critical_path(replicated execute + apply)
```

Conflict가 높은 hot state에서는 application dependency depth가 하한이므로 prover 수를 늘려도
직렬 critical path를 제거할 수 없다.

## 3. Verifiable-computing 문헌이 해결하는 하위 문제

| 하위 문제 | 가장 가까운 연구 | 가져올 수 있는 것 | 해결하지 않는 것 |
|---|---|---|---|
| Block별 online proof accumulation | [Nova, CRYPTO 2022](https://crypto.iacr.org/2022/papers/538806_1_En_13_Chapter_OnlinePDF.pdf), [HyperNova, CRYPTO 2024](https://www.microsoft.com/en-us/research/publication/hypernova-recursive-arguments-for-customizable-constraint-systems/) | History 길이와 무관한 step-wise folding, multi-folding, non-uniform circuits | Cut canonicality, proof availability, Byzantine scheduling |
| Folding proof의 succinct verification | [MicroNova, IEEE S&P 2025](https://eprint.iacr.org/2024/2099.pdf) | Incremental folding 뒤 compressed proof, verifier 비용 감소 | 임의 height마다 compression을 공짜로 제공하지 않음 |
| Sublinear accumulator/decider | [KZH-Fold, CCS 2025](https://doi.org/10.1145/3719027.3744796) | Constant-size accumulation verifier와 sublinear accumulator/decider의 trade-off | 2000-step benchmark에서 Nova 대비 prover time 증가; cut-to-state protocol은 아님 |
| Stateful program/memory proof | [Nebula, IEEE S&P 2026](https://www.microsoft.com/en-us/research/publication/nebula-proving-machine-executions-via-folding-schemes/) | Commitment-carrying IVC, efficient read/write memory arguments, pay-per-use instruction cost | 본 연구는 VM보다 application circuit SDK가 우선이며 protocol orchestration은 별도 |
| RSM execution을 proof/delta로 위임 | [Piperine, IEEE S&P 2020](https://www.microsoft.com/en-us/research/uploads/prod/2020/05/2020-195.pdf) | Untrusted prover가 transition proof와 succinct delta를 만들고 replicas가 verify/apply; takeover 가능한 liveness | Autobahn cut uncertainty, component별 readiness, cross-state DAG scheduling은 없음 |
| Proof가 computation DAG를 따라 흐름 | [Proof-Carrying Data, ICS 2010](https://projects.csail.mit.edu/pcd/), [Cluster Computing in Zero Knowledge, EUROCRYPT 2015](https://eprint.iacr.org/2015/377) | 각 DAG vertex가 predecessor proofs와 local transition을 검증하여 piecewise proof를 생성; distributed computation과 유사한 proof graph | BFT finalized cut, modern concrete latency, artifact custody |
| Multi-stage state sharing | [Geppetto, IEEE S&P 2015](https://www.microsoft.com/en-us/research/publication/geppetto-versatile-verifiable-computation/) | MultiQAP으로 computation 사이 state sharing과 MapReduce식 decomposition 비용 절감 | 최신 proof backend 및 Byzantine public-worker liveness |
| Parallel computation과 proof의 이론적 시간 | [SPARKs, JACM 2022](https://doi.org/10.1145/3549523) | Parallel RAM computation에 대해 near-optimal parallel prover라는 목표점 | 시스템 구현과 BFT task recovery의 직접 해법은 아님 |
| 하나의 large proof를 여러 machines가 생성 | [DIZK, USENIX Security 2018](https://www.usenix.org/conference/usenixsecurity18/presentation/wu), [Pianist, IEEE S&P 2024](https://ieeexplore.ieee.org/document/10646741/), [HEKATON, CCS 2024](https://eprint.iacr.org/2024/1208.pdf) | General circuit partitioning, distributed proving, shared-wire consistency, succinct aggregation | Whole-proof barrier와 coordinator dependency; component별 readiness를 자동 제공하지 않음 |
| Byzantine-accountable distributed SNARK | [Cirrus, NDSS 2026](https://www.ndss-symposium.org/ndss-paper/cirrus-performant-and-accountable-distributed-snark/) | Invalid final proof 뒤 malicious worker fault localization | Withholding liveness, ledger scheduling과 global proof barrier는 별도 문제 |
| Data-parallel distributed proof | [zkBridge/deVirgo, CCS 2022](https://doi.org/10.1145/3548606.3560652) | 반복 subcircuit의 distributed sumcheck와 빠른 proof generation | Arbitrary dependency DAG보다 identical data-parallel circuits에 적합 |
| Blockchain proof work queue | [Coda/Mina](https://eprint.iacr.org/2020/352.pdf) | Block production과 SNARK work를 분리하고 parallel scan tree로 leaf/merge jobs 수행 | Autobahn cut uncertainty와 component-local state readiness |
| Decentralized proof aggregation | [Snarktor](https://eprint.iacr.org/2024/099.pdf) | Independent proofs를 recursive aggregation service에서 결합 | Execution scheduling, state atomicity, proof availability가 주 목적은 아님 |
| Static accesses + parallel execution/proof | [GIGA](https://doi.org/10.1007/s10791-025-09828-3) | Declared accesses, non-conflicting batches, decentralized provers, transaction/batch/block proof aggregation | Final proof 전 whole-block barrier, block-producer orchestration, BFT cut-relative asynchronous apply가 없음 |
| Proof-verified multi-shard deltas | [RollShard, IEEE TC 2026](https://doi.org/10.1109/TC.2026.3673996) | Transaction DAG, stateless executor, per-shard delta와 global conservation proof | Optimistic delta application 모델이며 Autobahn cut/local pre-proof pipeline과 다름 |
| Intra-validator scale-out execution | [Pilotfish](https://arxiv.org/abs/2401.16292), [Remora](https://arxiv.org/abs/2607.02817) | Ordered transaction dependency scheduling, versioned queues, distributed execution, recovery | Validators 사이 결과 신뢰를 proof로 대체하지 않음 |
| Proof pipeline orchestration | [push0, 2026 preprint](https://arxiv.org/abs/2602.16338) | Head-of-chain ordering, intra-block parallelism, persistent queues와 failed-task reassignment | Cloud/Kubernetes crash model이며 Byzantine protocol이나 canonicality proof가 아님 |
| Proof bytes/state material availability | [AVID, SRDS 2005](https://crypto.ethz.ch/publications/CacTes05.html), [balanced AVID, 2022](https://eprint.iacr.org/2022/052) | Byzantine sender 아래 consistent dispersal·retrieval, erasure-coded custody | Computation validity와 state scheduling |
| Certificate 뒤 비동기 retrieval | [PoA&R, Financial Cryptography 2023](https://doi.org/10.1007/978-3-031-47751-5_3), [DispersedLedger, NSDI 2022](https://www.usenix.org/system/files/nsdi22-paper-yang_lei.pdf) | Push certificate와 pull retrieval의 분리; metadata ordering 뒤 node별 asynchronous fetch | Execution proof correctness와 component dependency를 자동 해결하지 않음 |

## 4. 가장 중요한 문헌별 판정

### 4.1 HyperNova/MicroNova: local path의 적합한 cryptographic substrate

HyperNova의 multi-folding과 non-uniform IVC는 application이 여러 transition circuits를 SDK로
제공하는 모델에 Nova보다 잘 맞는다. Lane은 새 local block마다 fold를 갱신할 수 있다.

그러나 folding accumulator와 cheap-to-verify succinct proof는 같은 것이 아니다. MicroNova의
compressed proof는 더 이상 folding으로 incrementally update할 수 없고, 논문 측정에서 compression은
대략 수십 초인 반면 verification은 약 14ms다. Final compression을 cut 이후에 시작하면 compression
latency가 그대로 `Delta_local`에 노출된다. 따라서 "rolling compressed proof" 대신 updateable
accumulator와 terminal snapshot compression을 분리하고 다음 variant를 비교해야 한다.

1. 매 block/height에 compressed snapshot 생성
2. 최신 high-likelihood prefix만 background compression
3. Cut 이후 selected fold만 compression
4. Fold proof를 그대로 검증하고 compression은 checkpoint/fast-sync에만 사용

PAC를 형성할 대상도 단순 running fold인지, compressed proof와 apply material을 포함한
`ProofBundle`인지 명확히 해야 한다.

KZH-Fold는 accumulation verifier를 constant-size로 유지하면서 accumulator와 decider를 sublinear로
만드는 다른 trade-off다. 2000 Poseidon benchmark에서 Nova 대비 communication과 decider time을 크게
줄였지만 prover time은 약 3배였다. 따라서 이름만 보고 HyperNova/MicroNova보다 우월하다고 선택할
수 없고, 우리 step circuit과 prefix cadence로 직접 측정해야 한다.

### 4.2 PCD: cross-DAG와 가장 잘 맞는 추상화

PCD는 distributed computation을 DAG로 보고 각 vertex의 output이 다음을 증명하게 한다.

```text
all predecessor messages were compliant
AND local program transformed them correctly
AND outgoing message satisfies the compliance predicate
```

이를 본 연구에 대응시키면 다음과 같다.

```text
CrossDAG node proof verifies:
  finalized_cut_digest
  + DAG digest and node identity
  + predecessor output proofs/commitments
  + declared access confinement
  + application transition
  + atomic multi-owner delta
```

이 방식은 independent component가 전체 cut proof를 기다리지 않고 별도 proof-carrying output을
만들 수 있어 non-blocking 목표와 잘 맞는다. 논문에서 새 cryptographic primitive를 발명할 필요는
없고, PCD-style composition을 protocol semantics로 채택한 뒤 concrete backend를 평가하면 된다.

### 4.3 Pianist/HEKATON: task 내부 가속에는 좋지만 전체-cut barrier로 쓰면 부적합

Pianist와 HEKATON은 arbitrary circuit을 여러 worker에게 분해하고 하나의 succinct proof로
집계할 수 있다. HEKATON은 shared wires를 global memory trace와 commit-carrying aggregation으로
검사한다. 이는 큰 cross component 하나의 proof를 여러 machines가 만드는 데 유용하다.

그러나 whole cut을 하나의 circuit/proof로 만들면 가장 느린 worker가 모든 state readiness를 막는다.
권장 사용법은 다음이다.

```text
PCD/component layer: independent components finalize independently
Distributed-SNARK layer: one large component/task 내부의 proving을 가속
```

Cirrus는 invalid final proof가 나왔을 때 malicious worker를 식별하는 accountability를 더하지만,
withholding worker 때문에 proof job이 끝나지 않는 문제를 자동으로 해결하지 않는다. 따라서 fault
localization backend와 cut-count failover를 구분해야 한다.

### 4.4 GIGA: 가장 직접적인 novelty overlap

GIGA는 본 설계와 다음을 이미 공유한다.

- transaction이 read/write set을 미리 선언한다.
- conflicting transactions를 같은 sequential batch에 둔다.
- disjoint batches를 decentralized provers가 병렬 실행·증명한다.
- transaction proofs를 batch proof와 final block proof로 recursive aggregation한다.
- proof가 없거나 invalid하면 timeout 후 transaction을 다음 block으로 미룬다.

따라서 다음은 독립 novelty로 주장할 수 없다.

```text
static access declaration
+ conflict partitioning
+ distributed execution/proving
+ recursive block proof aggregation
```

남는 차이는 검증해야 할 hypothesis다.

- GIGA는 block producer가 proof를 모은 뒤 proof-carrying block을 생성하므로 proof가 block creation의
  barrier다. 본 연구는 ordering cut을 proof와 무관하게 확정한다.
- 본 연구는 whole-cut proof를 기다리지 않고 independent component의 state readiness를 허용한다.
- Local owner-only work는 ordering과 proof fold를 overlap한다.
- BFT validator network의 finalized-cut-count failover와 proof custody를 정의한다.
- Cross work가 늦어도 next cuts의 ordering과 dependency-disjoint execution을 계속한다.

이 차이가 실제로 더 낮은 user-visible latency와 더 높은 ready goodput을 만드는지를 GIGA-like
whole-block aggregation baseline과 비교해야 한다.

### 4.5 PAC/AVID: availability mechanism이지 main novelty가 아니다

`f+1` full-copy custody shares는 committee size와 무관하게 최대 `f` faulty nodes라는 bound,
static fault set, honest custodian의 retention/response를 가정하면 최소 한 honest copy를 보장한다.
구체적인 Autobahn profile은 `n >= 3f+1`, Multimmit artifact는 `n >= 5f+1`일 수 있지만 이
counting argument 자체는 동일하다.

```text
f+1 custody signatures => at least one honest custodian
```

그러나 다음을 보장하지 않는다.

- proof statement의 correctness
- selected branch/prefix의 canonicality
- 여러 honest nodes가 동시에 높은 bandwidth로 복구할 수 있음
- adaptive corruption 또는 certificate 뒤 추가 crash에 대한 availability
- large state delta/apply material의 efficient dispersal

ProofBundle이 작으면 `f+1` full replication이 가장 단순하다. Apply material이 크거나 recovery
fan-out이 크면 AVID/erasure coding이 더 적합하지만, dispersal quorum과 추가 latency를 부담한다.
PAC는 시스템 조합의 중요한 liveness mechanism이지만 단독 novelty claim으로는 약하다.

또한 exact cut-bound proof를 이미 받은 node는 verifier를 통과한 즉시 apply할 수 있다. `f+1` PAC를
기다리는 것을 모든 node의 state-admission rule로 만들면 post-cut path에 불필요한 quorum RTT가
추가된다. PAC의 주 역할은 late/recovering node가 digest-addressed bundle을 적어도 한 honest
custodian에게서 가져오게 하는 것이다. 이 certificate/pull 분리는 PoA&R의 모델과 직접 비교해야 한다.

### 4.6 Piperine: proof-and-delta apply는 이미 알려진 핵심 선행연구

Piperine은 untrusted prover가 transaction batch를 실행해 output, post-state digest, succinct state
delta와 proofs를 만들고, RSM replicas가 원래 transition을 재실행하는 대신 verifier를 복제하여
delta를 검증·적용한다. 임의 party가 prover가 될 수 있고 replicas가 state를 보유하여 takeover할 수
있도록 liveness도 다룬다. 따라서 다음은 독립 novelty로 주장할 수 없다.

```text
one untrusted executor/prover
+ succinct state-transition proof and delta
+ replicas verify and apply without re-execution
```

Piperine의 payment-service 평가에서 proof delegation의 총비용이 native replicated execution보다
유리해지는 교차점은 `10^4`개가 넘는 replicas였다. 6-validator 실험에서는 proof가 system-wide
compute를 절감한다고 전제하면 안 된다. 본 연구가 입증해야 할 차이는 비용 절감 일반론이 아니라
Autobahn cut uncertainty 아래 pre-cut exact-prefix reuse, canonical cross-DAG scheduling,
component-local readiness와 Byzantine withholding recovery의 결합이다.

## 5. 권장 architecture

### 5.1 Local owner-only path

```text
producer block
  -> native execute
  -> application-defined step circuit
  -> HyperNova-style incremental fold
  -> content-addressed ProofBundle
       |-> finalized cut exact-prefix join -> verify and durable apply
       |      (PAC is not an admission prerequisite)
       |-> [parallel recovery path] f+1 PAC or stronger dispersal
       `-> [off critical path] selected snapshot compression/checkpoint
```

Zero knowledge는 필요하지 않다. Privacy가 목표가 아니므로 concrete implementation은 ZK를 끄고
succinct validity만 사용해 prover overhead를 줄일 수 있다.

### 5.2 Cross-state path

```text
finalized cut
  -> deterministic CrossDAG and connected conflict components
  -> deterministic primary/backup task assignment
  -> each ready node executes one atomic multi-owner transition
  -> emits PCD-style proof-carrying output
  -> successor verifies predecessor proof/commitment
  -> independent component root becomes StateReady immediately
```

큰 node/component 안에서 Pianist 또는 HEKATON식 distributed proving을 선택적으로 사용한다.
전체 cut을 한 proof로 묶는 것은 checkpoint/fast-sync용 optional late aggregation으로 둔다.

### 5.3 Proof availability and recovery

```text
proof correctness: validity proof
proof identity: content digest + exact public statement
minimum recovery: f+1 full-copy PAC
large bundle option: erasure-coded AVID
task liveness: finalized-cut-count deterministic failover
```

PAC readiness는 ordering vote나 finalized-cut construction의 전제조건이 되어서는 안 된다.
Valid proof를 이미 가진 node의 state apply 전제조건으로도 두지 않는다.

## 6. 방어 가능한 contribution 표현

현재 문헌 조사 이후 가장 안전한 framing은 다음이다.

> We design a cut-decoupled proof-carrying execution layer for lane-based BFT ordering. Local
> state transitions are incrementally proven before ordering finality, while cut-dependent
> cross-state transitions form a deterministic proof-carrying execution DAG after the cut.
> Proof availability and deterministic failover remain outside the ordering critical path, so
> stalled proving delays only causally dependent state components rather than consensus or the
> entire finalized batch.

한국어로 줄이면 다음과 같다.

> finalized cut을 기다리지 않아도 되는 local work는 온라인 fold로 숨기고, cut이 필요한
> cross-state work는 PCD식 component DAG로 분산 증명하며, proof availability를 ordering과
> 분리하여 느린 prover의 영향을 causal component로 제한한다.

Main novelty 후보는 PAC 자체가 아니라 다음 **결합과 end-to-end property**다.

1. Autobahn-family finalized cut과 exact-prefix online proof의 late binding
2. Whole-block proof barrier가 없는 component-scoped PCD state readiness
3. Ordering-independent proof custody와 cut-count failover
4. Local pre-cut proof pipeline과 post-cut cross-DAG proof pipeline의 동시 진행
5. 한 prover의 지연/withholding이 dependency closure 밖 state readiness에는 전파되지 않는
   delay-locality

각 primitive는 선행연구가 강하므로 “first distributed proving”, “first proof-carrying state”,
“first proof availability certificate”라고 주장하면 안 된다.

## 7. 반드시 비교할 baselines

| Baseline | 분리하려는 효과 |
|---|---|
| Post-cut replicated sequential execution | cut-to-state gap의 기본값 |
| Pre-cut speculative replicated local execution, no proof | state isolation/speculation과 proof 효과의 분리 |
| Pilotfish/Remora-like per-validator parallel DAG execution | proof가 아닌 local scale-out execution 효과 |
| Piperine-like proof-and-delta apply | generic verifiable delegation 대비 cut-relative 설계 효과 |
| GIGA-like whole-cut distributed proof + final aggregation | component-level readiness가 whole-proof barrier보다 나은지 |
| Local IVC only | pre-cut proof overlap의 효과 |
| Cross PCD DAG without PAC | custody/recovery가 tail latency에 주는 효과 |
| Proposed local IVC + component PCD + PAC/failover | end-to-end 결과 |

주요 변수:

- Local/cross ratio와 N-lane fan-out
- Conflict graph: disjoint, chain, layered, star, hot-key clique
- Execution/proof cost 비율
- Proof ready-at-cut ratio
- Worker crash/withholding/invalid proof와 witness-fetch delay
- PAC threshold/replication 방식과 bundle 크기
- Verification/apply throughput과 state lag in cuts

성공 기준은 평균 TPS만이 아니다.

```text
p50/p95/p99 Delta_local
p50/p95/p99 Delta_cross
component StateLagCuts distribution
ReadyGoodput
per-validator executed work and verified work
proof amplification and wasted proving
fault recovery delay in finalized cuts
```

## 8. 아직 열려 있는 연구 질문

1. HyperNova running proof를 그대로 state admission에 검증할지, MicroNova compression을 어느
   cadence로 수행할지 결정되지 않았다.
2. PCD node proof가 predecessor proof bytes를 직접 verify할지 commitment/accumulator만 이어받을지
   concrete backend가 필요하다.
3. Multi-owner delta를 node-local crash-atomic하게 적용하는 storage commitment와 apply material
   format이 필요하다.
4. `f+1` PAC의 static-fault/retention 가정을 논문에 둘지, AVID로 더 강한 recovery를 제공할지
   선택해야 한다.
5. 다음 cut의 local transaction이 unresolved cross output을 읽을 때 component read barrier와
   admission policy를 명세해야 한다.
6. GIGA와 RollShard 대비 차이가 구현·측정에서 유의미하지 않으면 novelty는 약해진다.
7. 최신 `paper-outline.md`의 cut-tail model과 현재 active protocol/SDK 문서의 dual-branch model을
   하나로 선택하고 동기화해야 한다.
8. PAC를 fast-path prerequisite가 아닌 recovery certificate로 둘 때 retention, signer discovery,
   retry fan-out과 garbage collection 조건을 명세해야 한다.

## 9. 결론

Verifiable-computing 연구는 필요한 암호 도구를 상당 부분 이미 제공한다.

- Local rolling proof: HyperNova/MicroNova
- Stateful circuit optimization: Nebula의 commitment-carrying IVC 아이디어
- Cross-DAG proof semantics: PCD/Cluster Computing in Zero Knowledge
- Large task 내부 distributed proving: Pianist/HEKATON
- Proof work scheduling: Mina와 push0
- Proof/apply-material recovery: PAC 또는 AVID

따라서 연구의 핵심은 새 SNARK를 만드는 것이 아니라, 이 도구들을 **Autobahn-family cut의
시간축과 component-level state readiness에 맞게 결합하는 distributed-systems protocol**이다.
가장 강한 평가 질문은 “proof를 만들 수 있는가”가 아니라 “whole-cut barrier 없이 어느
component가 언제 안전하게 ready가 되며, 그 결과 cut-to-state tail latency가 얼마나 줄어드는가”다.
