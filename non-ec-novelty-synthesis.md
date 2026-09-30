# Non-EC Cut-to-State Finality: Novelty Synthesis

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 목표와 성공 조건

목표는 EC를 다른 이름으로 옮기는 것이 아니라 다음 시간을 실제로 줄이는 것이다.

```text
T_gap = T_state-finality - T_ordering-cut
```

여기서 `T_state-finality`는 적어도 다음을 만족해야 한다.

1. Multimmit이 선택한 exact canonical cut에 대한 상태다.
2. Public evidence로 unique post-state root의 정당성을 검증할 수 있다.
3. 이후 admissible message가 도착해도 같은 cut의 root가 바뀌지 않는다.
4. Cross-lane effect가 participant subset에만 적용되지 않는다.

Queryable DB 준비는 별도 시점이다.

```text
T_root-finality <= T_queryable-materialization
```

Commonware Multimmit에서는 `n-f` authenticated votes가 arrival-first local pool에 도달하는 즉시 `FinalityFact`를 만들고, portable
L-QC aggregation은 비동기로 수행한다. 따라서 시점을 더 세분한다.

```text
T_ordering-local     = exact local vote pool이 ordering cut을 확정한 시점
T_lqc-portable       = 그 frozen vote transcript의 L-QC가 조립·전파된 시점
T_state-local        = 같은 pool에서 proof-relative state projection을 계산한 시점
T_state-portable     = L-QC + proof artifacts로 외부 verifier가 checkpoint를 확인 가능한 시점
```

“same-cut”은 우선 `T_state-local - T_ordering-local`을 의미한다. Client-facing portable finality를 주장할 때는
`T_state-portable - T_ordering-local`도 별도로 보고해야 한다.

## 2. 비-EC 해법의 경계

Arbitrary transition `R' = F(R, txs)`의 결과를 cut에서 확정하려면 다음 중 하나는 필요하다.

1. Validator가 `F`를 실행한다.
2. Quorum이 실행 결과에 동의한다. 이것은 message 위치나 명칭과 무관하게 EC 계열이다.
3. Validity proof 또는 trusted attestation을 검증한다.
4. Transaction semantics를 제한하여 effect와 root가 ordered data에서 저비용으로 직접 유도되게 한다.

따라서 strict non-EC 후보는 두 부류다.

```text
A. proof-backed general execution
B. proof-free restricted effect semantics
```

Optimistic apply, fraud window 또는 local speculation만으로는 strict state finality를 만들지 못한다.

## 3. 후보군 비교

| 후보 | Safety source | Same-cut 가능성 | 일반 실행 | 핵심 약점 | 판단 |
|---|---|---:|---:|---|---|
| State root를 ordinary vote에 서명 | quorum result agreement | 높음 | 가능 | L-QC 안으로 옮긴 EC | 제외 |
| Optimistic root + fraud window | future challenge | 겉보기만 높음 | 가능 | challenge 전에는 final 아님 | 제외 |
| TEE receipt sidecar | hardware attestation | 높음 | 가능 | hardware trust/rollback/availability | 보조 baseline |
| Proof transaction in later block | validity proof | proof가 늦으면 한 cut 이상 | 가능 | Hyli/rollup 계열 선행기술 강함 | baseline |
| Proof-Carrying Leader Proposal | validity proof | proposal 전에 proof ready 시 높음 | 가능 | leader censorship, proposal timing | 단순 후보 |
| Client Proof-Carrying Object Effect | per-tx proof + version rule | 높음 | object model로 제한 | client proving와 dynamic access | application fast path |
| Cut-Ready Effect | signatures/bounded checker | 높음 | 제한적 | expressiveness와 write skew | proof-free fast path |
| **Cut-Parametric Validity** | validity proof + L-QC canonicality | 높음 | 가능 | proof readiness/custody | 주 후보 |

## 4. 주 후보: Cut-Parametric Validity

핵심은 proof를 단순히 비동기 생성하는 것이 아니다. Multimmit의 final cut이 arbitrary order가 아니라 lane마다 한 proposal-relative
path의 prefix라는 사실을 이용하여, **가능한 모든 cut coordinate를 선형 크기의 proof basis로 미리 덮고**, 같은 L-QC에서 proof-ready
state coordinate를 추출한다.

```text
Multimmit proposal-relative path
       + cut-parametric proof basis
       + proof-relative L-QC projection
       + dependency-closed cross-lane selection
       = same-cut proof-backed state frontier
```

### 4.1 Lane proof basis

Lane `i`의 candidate path:

```text
R_0 --B_1--> R_1 --B_2--> ... --B_d--> R_d
```

모든 possible vector cut을 proof하면 경우의 수가 lane 간 곱으로 증가한다. State isolation 아래에서는 lane별 prefix validity만 있으면
되므로 다음 interval basis를 만든다.

```text
ProofNode(i, a, b) {
  lane_id,
  exact_blocks_commitment(B_a ... B_b),
  pre_root=R_(a-1),
  post_root=R_b,
  local_effect_root,
  prepared_cross_effect_root,
  materialization_commitment,
  validity_proof
}
```

Online binary-carry 방식으로 leaf proof를 합친다.

```text
new block proof arrives
  -> create size-1 segment
  -> if same-size adjacent segment exists, recursively merge
  -> retain canonical segment nodes
```

Path 길이가 `d`일 때:

- Proof basis node 수는 `O(d)`다.
- 임의 prefix는 최대 `O(log d)` disjoint proof nodes로 덮는다.
- `L` lane vector cut의 proof cover는 `O(L log d)`다.
- Cross-lane operation이 없으면 lane proof들을 서로 재증명할 필요가 없다.

IVC가 모든 prefix checkpoint를 더 싸게 제공한다면 이를 구현 variant로 사용한다. Novelty는 binary tree 자체가 아니라
proposal-relative cut uncertainty를 proof basis와 factorization하는 규칙이다.

### 4.2 Proof sidecar

Proof와 materialization data는 transaction ordering payload와 분리된 sidecar로 전파한다.

```text
ProofSidecar {
  ProofNode statement,
  proof bytes,
  changed values/effect log,
  authenticated-tree update data
}
```

Validity는 proof soundness가 담당한다. Sidecar availability는 다음 중 하나로 제공한다.

1. Existing DA plane을 재사용한 sidecar DA certificate
2. L-QC proof-support voters의 retention/custody rule
3. Proof bytes가 매우 작으면 L-QC attachment에 inline하고 effect data만 DA에서 복구

Sidecar DA certificate는 execution result agreement가 아니므로 EC가 아니다. Validator는 bytes custody에 투표할 뿐 post-state의
correctness에 투표하지 않는다.

### 4.3 Proof-relative signed coordinate

Ordinary Multimmit vote에 lane별 compact coordinate를 추가한다.

```text
ProofCoordinate[i] {
  highest_contiguous_proof_height,
  endpoint_root,
  proof_basis_commitment
}
```

Correct validator는 자신이 검증하고 retention한 proof cover만 보고한다. Proof가 늦어도 현재 state height를 보고하고 ordering vote는
즉시 낸다.

Local direct-finality pool 또는 그 exact frozen transcript로 조립된 L-QC에서 두 결과를 얻는다.

```text
O_k[i] = existing Multimmit ordering-tip extraction

S_raw_k[i] = highest proof coordinate h
             such that h <= O_k[i]
             and at least q_s L-QC votes support
             a connected compatible proof cover through h
```

`q_s`는 validity threshold가 아니다. Validity는 proof 하나로 충분하며 `q_s`는 common selection, censorship resistance와 artifact custody를
위한 parameter다.

초기 profile:

```text
n = 5f+1
L-QC = 4f+1 votes
q_s = 2f+1
```

Selected coordinate에는 최소 `f+1` honest supporters가 있다. 전체 committee에서 `3f+1`가 support하면 어떤 `4f+1` L-QC subset에도
최소 `2f+1` support가 남는다.

### 4.4 Cross-lane proof closure

Local proof가 N-lane atomicity를 자동으로 증명하지 않는다. Existing prepared overlay와 DCLP를 유지한다.

Cross operation `X`는 participant proof nodes가 동일 `attempt_id/manifest_digest`의 prepared effect를 각각 인증하게 한다.

```text
Finalize(X, LQC_k) iff
  valid ReadyBundle/DCLP(X)
  AND all exact participant blocks are in O_k
  AND every participant fragment is covered by S_raw_k
  AND participant roots/effects form one dependency-closed component
  AND joint application predicate accepts
  AND nonce is live and single-consumed
```

State evaluator는 complete component만 all-or-none으로 적용하고 incomplete prepared effects는 canonical local root에 섞지 않는다.

### 4.4.1 Proof granularity boundary

Lane cumulative proof가 global `pre_root -> post_root`만 공개하면 cross overlay를 제외하거나 independent effects를 다른 proof arrival order로
합칠 수 없다. Root hash는 semantic commutativity를 알지 못한다.

두 profile을 분리한다.

```text
Prefix profile:
  cumulative lane proofs
  -> lane scalar prefix만 전진
  -> lag containment는 lane/component 단위

Effect profile:
  root-independent object input/output proof
  + version/nullifier rules
  + authenticated sparse multipatch
  -> event-level dependency ideal
  -> lag containment는 exact dependency cone
```

Effect profile의 proof는 global root transition이 아니라 consumed/read objects에서 created/written objects로의 semantic transition을
인증한다. Current checkpoint root에 대한 membership과 patch application을 분리해야 unrelated state update 후에도 proof를 rebase할 수 있다.

### 4.5 State commitment와 materialization

같은 L-QC의 signed attributed transcript에서 state cut을 결정적으로 유도한다.

```text
StateCutCommitment_k = H(
  LQC_k,
  previous_state_cut,
  selected lane proof coordinates,
  selected cross-lane components
)
```

이 시점에 post-state root의 validity와 canonicality가 고정된다. DB apply는 copy-on-write pages와 atomic root pointer update로 수행하고,
secondary index/compaction은 뒤로 보낸다.

```text
T_gap = max(0, T_proof_support_ready - T_ordering_cut)
        + T_extract
        + T_dependency_close
        + T_root_commit
```

Same-cut fast path에서는 첫 항이 0이다.

### 4.6 Transcript-relative checkpoint

서로 다른 correct replica가 같은 leader에 대해 서로 다른 first-arrival `4f+1` vote pools를 가질 수 있다. 두 pool이 같은 ordering tip을
추출하더라도 proof-support voter 구성이 달라 state frontier가 다를 수 있다.

```text
O(Pool_A) = O(Pool_B)
does not imply
S(Pool_A) = S(Pool_B)
```

따라서 `S_k`를 ordering cut만의 globally unique root라고 정의하면 안 된다. 정확한 객체는 다음이다.

```text
StateCheckpoint(EvidenceId, OrderingFrontier, ProofFrontier, StateRoot)
```

서로 다른 valid evidence가 만든 checkpoint는 동일 canonical history 위에서 compatible한 state prefixes 또는 dependency-closed
order ideals여야 한다. 더 많은 valid proof evidence가 도착하면 checkpoint는 monotonic하게 refine된다.

필요한 정리:

1. 같은 exact transcript에서는 state projection이 deterministic하다.
2. 서로 다른 valid transcripts의 selected local proof prefixes는 서로 충돌하지 않는다.
3. Cross-lane component selection까지 포함한 checkpoints 사이에 deterministic partial order가 존재한다.
4. 더 낮은 checkpoint를 본 client가 더 높은 compatible checkpoint를 안전하게 채택할 수 있다.

Application/API가 view마다 정확히 하나의 canonical state root를 요구한다면 다음 중 하나가 추가로 필요하다.

- 특정 canonical L-QC/evidence ID를 checkpoint 이름으로 사용
- 후속 ordering에서 checkpoint ID를 anchor
- 모든 valid pools가 공유하는 더 보수적인 support threshold 사용

첫 번째가 additional round 없이 가장 단순하지만, state finality claim은 `certificate-relative monotone checkpoint`로 표현해야 한다.

## 5. 보조 novelty: Quorum-Predictive Proving

Proof generation을 모든 speculative fork에 즉시 수행하면 낭비가 크다. 현재 collector의 monotonic vote pool에서 lane height `h`에 대한
support가 `3f+1`에 도달하면, 그 exact pool을 `4f+1` L-QC로 완성할 때 `h`가 final-tip order statistic을 통과한다.

```text
3f+1 support for h
  -> reserve exact supporters in local aggregation job
  -> start/raise proof priority for prefix h
  -> overlap proving with arrival of remaining f votes
  -> send proof sidecar alongside completed L-QC
```

이것은 proof generation을 consensus-visible likelihood에 따라 scheduling하는 optimization이다.

중요한 한계:

- 한 collector의 reserved L-QC에는 유효하지만 다른 `4f+1` subset까지 `h`를 포함한다고 보장하지 않는다.
- 모든 가능한 L-QC subset에서 `3f+1` support를 남기려면 global support `4f+1`가 필요하여 proving lead time이 사라진다.
- 따라서 이것만 protocol-wide state frontier claim으로 사용하면 안 된다.

권장 용도는 safety mechanism이 아니라 proof-ready-at-cut ratio를 높이는 local scheduling heuristic이다.

## 6. 대안 fast path: Proof-Carrying Object Effects

Validator/producers가 lane block 전체 proof를 만드는 대신 client가 object transition proof를 transaction에 넣는다.

```text
ProofCarryingEffect {
  consumed_object_versions,
  created_object_versions,
  read_dependencies,
  explicit_effects,
  conservation/authorization statement,
  validity_proof,
  cross-lane manifest
}
```

Cut은 다음만 결정한다.

1. 어떤 object version consumer가 canonical order에서 먼저인가?
2. 모든 participant fragment가 포함됐는가?
3. Valid proof와 dependency closure를 만족하는 effect set은 무엇인가?

장점:

- Proving latency가 validator critical path에서 client submission path로 이동한다.
- Dynamic validator execution backlog에 덜 민감하다.
- Cross-lane bundle 하나의 proof로 conservation을 인증할 수 있다.

한계:

- Proof 생성 전 input version을 알아야 한다.
- Unknown dynamic access, oracle read, global shared invariant는 어렵다.
- Zcash, proof-carrying transaction과 zkApp 계열과의 선행기술 경계가 약하다.

따라서 main general path보다 object/cross-lane workload의 application fast path로 두는 편이 안전하다.

[Anoma Resource Machine](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/data_structures/transaction/transaction.html)이 이미
resource logic/compliance/delta proofs, nullifier와 transaction proof composition을 제공하므로 object/effect proof 자체는 novelty가 아니다.
Effect profile은 해당 아이디어를 Multimmit late-bound refinement에 적용하는 mechanism으로만 위치시킨다.

## 7. Proof-free fast path의 정직한 범위

Validity proof까지 사용하지 않으려면 transaction effect가 self-authenticating이어야 한다.

가능한 예:

- Owner-signed UTXO/object transfer
- Escrow debit/credit with conservation check
- Commutative counter/CRDT update
- Capability-authorized object replacement
- Bounded invariant checker가 execution보다 훨씬 싼 transaction

이 경우 Cut-Ready Effect와 version single-consumption으로 cut에서 결과를 직접 계산할 수 있다. Arbitrary contract call은 SlowPath다.

이 방향의 novelty는 object model 자체가 아니라 다음 조합이어야 한다.

```text
proposal-relative vector cut
  -> deterministic version/conflict selection
  -> N-lane effect hyperedge closure
  -> partition-independent root composition
```

## 8. 폐기하거나 claim을 낮춰야 할 아이디어

### Execute-and-root in the ordering vote

별도 EC message가 없더라도 validators가 같은 root를 실행하고 quorum 서명하면 execution agreement를 L-QC에 합친 EC다.

### Proof Certificate after proof generation

Proof correctness에 다시 quorum을 모으면 cryptographic soundness를 BFT approval로 중복 인증하고 additional delay를 만든다. Quorum의
역할은 custody/common selection으로 한정해야 한다.

### Finalize only proofs completed up to cut k-d

Pipeline throughput은 좋아질 수 있으나 같은 ordering cut의 state-finality gap을 줄인 것이 아니라 state frontier를 `d` blocks 뒤로
미룬 것이다.

### Optimistic state finality

Challenge period 전에는 final이 아니라 speculative/soft-confirmed다. Strict metric과 분리한다.

### Local pre-execution only

Cut 이후 queryable state는 빨라지지만 public evidence가 root를 bind하지 않으면 protocol state finality improvement가 아니다.

### Single state root in the leader proposal

Multimmit의 final cut은 proposal이 아니라 proposal-relative vote positions/extensions의 order statistic으로 정해진다. 같은 proposal에서
서로 다른 valid vote pools가 서로 다른 cuts를 만들 수 있으므로 proposal 시점의 root 하나는 일반적으로 모든 outcome을 bind하지 못한다.
가능한 cut roots를 factorize하거나 exact vote transcript 이후에 root를 선택해야 한다.

## 9. 가장 방어적인 논문 contribution

### C1 — Cut-Parametric Proof Basis

Multimmit proposal-relative lane paths가 만드는 exponential vector-cut space를 linear-size lane proof basis로 factorize하고, 임의 finalized
prefix를 `O(log d)` preverified proof nodes로 즉시 구성한다.

### C2 — Proof-Relative Dual Frontier

동일한 attributed L-QC transcript에서 full ordering frontier와 shorter proof-supported state frontier를 동시에 추출한다. Proof readiness는
ordering vote를 막지 않고 proof를 다음 transaction/cut에서 다시 sequence하지 않는다.

### C3 — Dependency-Closed Proof Cut

Per-lane proof coordinates를 DCLP/prepared effects와 결합하여 N-lane operation을 atomic하게 state-finalize하고, proof lag를 관련 dependency
component에 제한한다.

### C4 — Root/Materialization Separation

Cryptographic root finality와 queryable DB materialization을 별도 metric과 implementation path로 정의하여 latency를 어디로 옮겼는지
정확히 측정한다.

### C5 — Transcript-Relative Monotone State Checkpoints

Commonware의 arrival-first local finality와 asynchronous L-QC construction을 반영하여, state frontier를 ordering cut의 유일한 함수가 아니라
exact attributed evidence에 상대적인 compatible checkpoint로 정의한다. 서로 다른 evidence의 checkpoints가 conflict하지 않고 monotonic하게
refine됨을 증명한다.

한 문장 claim:

> We make validity evidence cut-parametric: a linear-size basis of asynchronously generated lane proofs covers every proposal-relative Multimmit cut, while the same attributed L-QC deterministically extracts both the ordering frontier and the maximal dependency-closed proof frontier, eliminating a separate execution certificate and proof-transaction round.

## 10. Falsification criteria

다음 중 하나라도 성립하면 main claim을 낮춰야 한다.

1. Proof basis generation이 proposal-to-L-QC window보다 지속적으로 느려 same-cut ratio가 낮다.
2. Proof worker가 ordering worker와 resource contention을 일으켜 end-to-end latency가 증가한다.
3. Vote/tally proof-coordinate overhead가 lane 수에 따라 L-QC latency를 유의하게 악화시킨다.
4. Materialization sidecar를 제때 복구하지 못해 root finality와 queryability gap이 과도하게 커진다.
5. Cross-lane dependency graph가 giant component가 되어 한 proof lag가 대부분의 state frontier를 막는다.
6. Binary/IVC proof basis가 단일 cumulative lane proof보다 실제 proving cost나 readiness에서 이점이 없다.
7. 직접 선행기술이 동일 L-QC dual-frontier와 proposal-prefix proof basis의 결합을 이미 제안했다.
8. 서로 다른 valid arrival-first vote pools가 dependency-closed state checkpoints의 compatibility를 깨뜨린다.

## 10.1 선행연구 경계

- [DiemBFT](https://developers.diem.com/papers/diem-consensus-state-machine-replication-in-the-diem-blockchain/2019-10-24.pdf)는 vote/QC가 block과 execution state를 함께 인증한다. 따라서 “한 certificate가 order와 state를 동시에 인증”은 novelty가 아니다.
- [Coda/Mina](https://eprint.iacr.org/2020/352.pdf)는 최신 staged ledger와 뒤처진 SNARK ledger를 병렬 scan queue로 유지한다. Dual frontier라는 넓은 개념도 novelty가 아니다.
- [Flow](https://arxiv.org/abs/2002.07403)는 asynchronous execution receipts/approvals를 후속 block seal로 consensus에 넣는다.
- [GRANDPA](https://research.web3.foundation/pdf/grandpa.pdf)는 heterogeneous highest-block votes에서 quorum-supported ancestor prefix를 추출한다. Highest checkpoint order statistic 자체도 novelty가 아니다.
- [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)는 commitment와 sidecar data propagation/custody를 분리한다. Sidecar도 novelty가 아니다.
- [Hyli](https://docs.hyli.org/concepts/pipelined-proving/)는 execution/proving을 pipeline하고 proof transaction을 나중에 sequence한다.

직접 대응을 찾지 못한 결합은 다음으로 한정된다.

```text
proposal-relative Multimmit vote transcript
  + cut-selectable lane proof basis
  + payload-free proof checkpoint report
  + simultaneous ordering/proof-frontier projection
  + dependency-closed N-lane state checkpoint
```

검색 부재는 특허 수준의 신규성을 보장하지 않는다. 논문은 구성요소가 아니라 이 결합의 maximality, compatibility, zero-added-round와
lag-containment 정리로 방어해야 한다.

[Kaspa vProgs](https://down.kastop.com/2025/vProgs_yellow_paper.pdf)는 conditional read/write proofs, Computation DAG와 stitching proof로
state commitment를 갱신하므로 proof DAG/cross-program stitching도 강한 선행기술이다. 차이는 vProgs가 proof operations와 stitching
commitment를 L1 covenant/index에 publish해 settle하는 반면, 본 후보는 self-authenticating evidence를 이미 final한 Multimmit cut에
late-bind하여 새 ordering round 없이 compatible state ideal을 refine한다는 점으로 좁혀야 한다.

## 11. 최소 실험

```text
B0: post-cut execution
B1: async proof submitted as later proof transaction
B2: one cumulative proof per lane
B3: cut-parametric proof basis
B4: B3 + proof-relative L-QC coordinates
B5: B4 + cross-lane dependency closure
```

측정:

```text
T_ordering_cut
T_cut_to_root_final p50/p95/p99
T_cut_to_queryable p50/p95/p99
same_cut_state_ratio
proof_ready_before_vote_ratio
proof basis work / wasted work / bytes
vote and L-QC size
proof verification CPU
state frontier lag by lane/component
cross-lane fanout and giant-component ratio
```

논문 성공 조건은 `T_cut_to_root_final`만 작아지는 것이 아니다.

```text
T_submission_to_root_final
  = T_submission_to_ordering_cut + T_cut_to_root_final
```

도 함께 줄거나 최소한 악화되지 않아야 한다.

## 12. 현재 권장 최소 프로토콜

Red-team과 선행연구 대조 후, 첫 prototype은 모든 아이디어를 한꺼번에 구현하지 않고 다음 세 mechanism만 결합하는 것이 좋다.

### 12.1 Ordered conditional effect statement

Producer block은 proof가 아니라 proof가 나중에 인증할 statement를 먼저 DA/order한다.

```text
ConditionalEffectStatement {
  event_id,
  exact block/tx commitment,
  execution_version,
  declared input/read object versions,
  declared output/write commitments,
  local/prepared effect commitment,
  dependency/participant manifest,
  proving policy
}
```

Proof가 없으면 effect는 ordered이지만 state-final하지 않다.

### 12.2 Validity Artifact Availability Certificate

Proof와 materialization sidecar는 transaction으로 다시 ordering하지 않는다. Existing Multimmit DA threshold profile을 적용한 별도 sidecar
header에 `n-2f` custody shares를 모은다.

```text
ValidityArtifactHeader {
  epoch,
  event_or_segment_id,
  canonical statement_id,
  proof_commitment,
  effect/materialization_commitment,
  encoded_size,
  retention_epoch
}
```

Certificate subject는 exact artifact bundle commitment다. Proof system이 randomized proof encodings를 허용하면 서로 다른 prover artifacts는
서로 다른 certificates를 만들 수 있지만, 모두 같은 canonical `statement_id`를 인증하면 state evaluator는 어느 하나든 사용할 수 있다.
Conflicting post-state statements는 proof soundness 아래 동시에 valid할 수 없다.

정확히 `n=5f+1`이면 availability quorum은 `n-2f=3f+1`이다.

Certificate의 의미:

```text
YES: exact proof/effect artifact is retrievable
NO:  state transition is correct
NO:  event is canonically ordered
NO:  cross-lane operation is complete
```

Correctness는 artifact를 fetch한 뒤 public proof verification이 담당한다. Invalid proof도 availability-certified될 수 있으므로 size/gas budget과
invalid-sidecar fee가 필요하다.

Share policy는 두 profile로 평가한다.

```text
Custody-only:
  bounded bytes를 보관한 뒤 share
  -> 낮은 latency, invalid-artifact DA spam 가능

Verified-custody:
  proof를 검증하고 effect/materialization commitment를 보관한 뒤 share
  -> invalid spam 억제, verification CPU/latency 추가
```

Verified-custody를 사용해도 validity의 trust source는 quorum이 아니라 public proof soundness다. Certificate는 proof를 보지 못한 verifier가
결과를 믿게 하는 대체 증거가 아니라 exact artifact recovery를 보장하는 transport evidence다.

Effect/materialization bytes가 original transaction blocks의 `n-2f` DA에 이미 포함되고 late sidecar가 succinct proof bytes뿐이면 더 낮은
durability profile도 가능하다.

```text
q_proof = f+1 verified custodians
```

이는 최소 한 correct proof holder를 보장한다. `n-2f`는 stronger tail recovery, `f+1`은 lower response-order-statistic latency를 제공한다.
Proof readiness가 ordering vote 전에 도착하면 ordinary vote에 custody coordinate를 piggyback하고, 늦게 도착하면 standalone receipts를
모으되 다음 cut을 기다리지 않는다. 상세 분석은 [asymmetric-validity-custody.md](./asymmetric-validity-custody.md)에 둔다.

### 12.3 Evidence-refined state ideal

Replica는 다음 조건이 성립하는 event를 dependency-closed ideal에 추가한다.

```text
canonical ordering inclusion
AND valid/retrievable proof artifact
AND exact statement binding
AND all predecessors finalized
AND version/conflict rule accepts
AND cross-lane DCLP/all-participant/joint predicate accepts
```

Proof가 cut 전에 availability-certified되면 same-cut fast path다. Cut 뒤에 certificate가 생겨도 다음 ordering cut을 기다리지 않고 바로
existing state ideal을 refine한다.

```text
T_event-state-final
  = max(T_ordering-cut,
        T_valid-proof-availability,
        T_predecessor-finality)
    + T_join
```

### 12.4 Optional named checkpoint

Ordinary Multimmit vote의 proof coordinate/L-QC dual frontier는 첫 prototype의 safety 선행조건이 아니다. 다음 용도로만 optional layer로 둔다.

- Replica들이 어느 evidence snapshot을 보유했는지 common naming
- Portable checkpoint와 client sync
- Custody redundancy telemetry

Event correctness/finality를 vote support에 의존시키면 다시 certificate-based execution agreement로 보일 수 있다. Main protocol은
validity proof + availability certificate + canonical cut으로 effect finality를 정의하고, L-QC checkpoint는 later anchoring optimization으로
평가한다.

## 13. 최종 novelty hierarchy

강한 순서:

1. **Consensus-Free Validity Refinement:** proof를 후속 payload로 ordering하지 않고 already-final Multimmit cut에 late-bind한다.
2. **Evidence-Refined State Lattice:** 서로 다른 proof subsets가 만든 checkpoints를 revoke 없이 dependency-closed join한다.
3. **Cross-Lane Atomic Proof Hypernodes:** DCLP와 all-participant proof/effect를 one state-final event로 만든다.
4. **Cut-Parametric Proof Basis:** proposal-relative arbitrary prefix를 pre-generated proof forest로 덮어 same-cut ratio를 높인다.
5. **Proof-relative L-QC coordinates:** portable checkpoint naming/custody를 같은 transcript에서 추출한다.

1~3이 protocol contribution이고, 4는 proving scheduler/data structure, 5는 optional checkpoint mechanism으로 두는 것이 현재 가장 방어적이다.
Proof generation 자체를 줄이는 optional scheduler는 [cut-aware-proof-swarm.md](./cut-aware-proof-swarm.md)에 정리한다. Mina류 distributed
proving과 달리 partial Multimmit vote support의 `f+1/3f+1` frontiers로 task priority와 redundancy를 조절하지만, 이는 correctness novelty가
아니라 same-cut proof readiness optimization이다.

권장 claim:

> We decouple validity arrival from ordering after Multimmit finality: asynchronously generated validity artifacts are availability-certified but never re-sequenced, and each artifact monotonically refines a dependency-closed state ideal over the already-final cut. Cross-lane effects enter the ideal as all-participant hypernodes, so late or withheld proofs stall only their dependency cones without revoking finalized effects or blocking ordering.
