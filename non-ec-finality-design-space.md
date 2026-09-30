# Non-EC State-Finality Design Space

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 연구 질문

별도 Execution Certificate(EC)를 만들지 않고 다음 간격을 줄일 수 있는가?

```text
T_gap = T_state-finality - T_ordering-cut
```

여기서 세 시점을 구분해야 한다.

1. **Ordering finality:** Multimmit L-QC가 exact producer-chain cut을 확정한 시점
2. **Protocol state finality:** 외부 검증자가 certificate와 public evidence로 exact post-state를 확인할 수 있는 시점
3. **Local materialization:** 특정 validator의 queryable state DB와 authenticated root가 준비된 시점

로컬 speculative execution만으로 3을 줄일 수는 있지만, cut이 state root를 인증하지 않으면 2가 줄었다고 주장할 수 없다.

## 2. 피할 수 없는 경계

일반적인 black-box transition `F(state, txs)`에 대해 ordering certificate가 transaction order만 인증한다면,
exact post-state를 얻는 주체는 다음 중 하나를 수행해야 한다.

1. `F`를 실행한다.
2. 다른 실행자의 결과에 대한 quorum attestation을 검증한다.
3. validity proof 또는 trusted hardware attestation을 검증한다.
4. Transaction 형식을 제한하여 post-state가 cut과 저비용 metadata로 직접 결정되게 한다.

따라서 **EC도 proof도 없이 arbitrary smart-contract state finality를 cut과 동시에 얻는 일반 해법은 없다.**
Non-EC 방향은 다음 둘 중 하나를 정직하게 선택해야 한다.

- 일반 실행을 유지하고 cut 이후의 **materialization latency**만 speculative execution으로 줄인다.
- Application contract를 제한하여 cut이 state effect를 직접 결정하는 fast path를 만든다.

## 3. 후보 비교

| 후보 | Protocol state gap | Ordering 영향 | 일반 실행 | novelty 위험 |
|---|---:|---:|---:|---|
| Multi-future speculative execution | 인증 root에는 효과 없음; local materialization만 감소 | 없음 | 가능 | Forerunner와 강하게 겹침 |
| State root를 기존 L-QC proposal에 포함 | 정상 경로에서 0 | 실행 검증이 vote critical path에 들어감 | 가능 | 일반적인 execute-before-vote와 겹침 |
| DA certificate를 execution-validity까지 확장 | 정상 경로에서 0 | DA/ordering eligibility가 실행을 기다림 | 가능 | EC를 DA로 이름만 바꾼 것으로 보일 수 있음 |
| Validity proof/TEE | proof/attestation ready 시 0 | 검증비용만 포함 | 가능 | Hyli, Flow, rollup/TEE 선행기술과 겹침 |
| Optimistic/fraud-proof apply | 0처럼 보이나 challenge 전에는 final이 아님 | 작음 | 가능 | 목표의 finality 정의를 만족하지 않음 |
| **Cut-Ready Effects + State-Carrying Cut** | fast path에서 0 | 저비용 guard/root 검증 | 제한적 | 가장 유망하지만 object/checker 연구와 비교 필요 |

## 4. 권장 후보: Cut-Ready Effects

### 4.1 Application contract

Application은 transaction을 다음 둘 중 하나로 분류한다.

```text
prepare(tx, snapshot) -> CutReadyEffect | SlowPath
```

`CutReadyEffect`의 최소 구조:

```text
CutReadyEffect {
  operation_id,
  nonce,
  expiry,
  participant_lanes,
  input_objects: [(object_id, version, value_commitment)],
  read_set,
  write_set,
  explicit_deltas_or_outputs,
  guard_predicate_id,
  conservation_commitment,
  cross_fragment_manifest,
  effect_data_commitment
}
```

Fast-path eligibility 조건:

1. 모든 mutable input과 read dependency가 version으로 고정된다.
2. Output/effect가 명시되며 application checker가 bounded cost로 검증할 수 있다.
3. 동일 input version의 소비 순서가 canonical cut에서 결정적이다.
4. Guard 실패는 deterministic no-op이며 partial effect를 만들지 않는다.
5. N-lane effect는 하나의 indivisible hyperedge로 취급한다.
6. Effect bytes와 materialization data가 participant block의 DA commitment에 포함된다.

Arbitrary dynamic calls, unknown access sets 또는 effect 검증 비용이 원 실행과 같은 transaction은 SlowPath로 보낸다.

### 4.2 Pre-cut preparation

Validator는 DA payload를 수신하면 별도 vote 없이 다음 값을 로컬에서 계산한다.

```text
EffectCapsule(i, h) = {
  exact_block_id,
  input_versions,
  deterministic_accept_or_noop,
  state_delta,
  updated_subtree_nodes,
  candidate_lane_root,
  dependency_hyperedges
}
```

Capsule은 consensus evidence가 아니라 branch-indexed cache다. 잘못 계산한 validator만 느려지거나 잘못된 local root를 얻으며,
protocol safety가 capsule 공유나 신뢰에 의존해서는 안 된다.

### 4.3 Cut-time selection

L-QC가 exact ordering cut `O_k`를 확정하면 다음 deterministic function을 계산한다.

```text
EligibleEffects(O_k)
  = maximal canonical set satisfying
      exact inclusion
      AND version single-consumption
      AND valid guards
      AND DCLP completeness for cross-lane effects
      AND dependency closure
```

Cross-lane operation `X`에 대해서는:

```text
Commit(X, O_k) iff
  every participant fragment is exactly included in O_k
  AND valid ReadyBundle/DCLP exists
  AND all input versions are live
  AND joint application guard accepts
  AND nonce is unconsumed
```

하나라도 실패하면 `X` 전체가 no-op/defer되고 participant subset은 적용하지 않는다.

### 4.4 Cut-parametric materialization

State commitment를 lane-root vector의 authenticated composition으로 둔다.

```text
GlobalRoot_k = MerkleRoot(sorted[(lane_id, LaneRoot_k[lane_id])])
```

Lane-local prefixes는 precomputed capsule의 root를 선택하고, eligible cross-lane hyperedge만 participant subtree에 함께 적용한다.
Durable commit은 state DB 전체 rewrite가 아니라 다음 작은 record의 atomic pointer swap으로 구현한다.

```text
CommitRecord {
  cut_hash,
  previous_global_root,
  new_global_root,
  selected_capsule_manifest,
  consumed_nonces
}
```

Compaction과 historical index update는 state finality 이후 비동기적으로 수행할 수 있다.

## 5. 외부 검증 가능한 State-Carrying Cut

Cut-Ready Effects만 사용하면 deterministic semantics는 cut에서 결정되지만, 외부 client가 확인할 state root가 L-QC에 없다.
진짜 protocol state finality를 cut과 동시에 만들려면 기존 Multimmit proposal에 다음을 추가하는 선택지가 있다.

```text
StateCarryingProposal {
  ordering_cut,
  eligible_effect_manifest_root,
  post_state_root
}
```

Validator는 precomputed capsules를 이용해 guard, exact effects와 root composition을 검증한 뒤 기존 L-QC vote 하나를 발행한다.
형성된 L-QC는 ordering cut과 post-state root를 함께 인증한다.

장점:

- 별도 EC message, aggregator 또는 certificate가 없다.
- 추가 network round 없이 `T_protocol-state-finality = T_ordering-cut`이 된다.
- Expensive contract execution 대신 bounded guard/root validation만 ordering vote 경로에 남길 수 있다.

비용과 한계:

- Validator가 proposed state root를 검증하지 못하면 L-QC vote가 늦어져 ordering latency가 증가한다.
- 모든 transaction을 fast path에 강제로 넣으면 arbitrary execution 문제를 다시 만난다.
- 단순히 full execution 후 state root에 vote하면 EC를 L-QC로 합친 것일 뿐 novelty가 아니다.
- 따라서 contribution은 certificate 통합이 아니라 **cut-determined effect contract와 factorized root validation**이어야 한다.

## 6. 반드시 해결해야 하는 반례

### 6.1 거짓 output

Contract가 `y = SHA256^N(x)`를 계산한다고 하자. Producer가 capsule에 임의의 `y`를 쓰면 input version과 signature만으로
정당성을 판단할 수 없다. Checker가 동일 계산을 수행하거나 proof를 검증해야 한다.

결론: Fast path는 owner-authorized delta, bounded checker 또는 저비용 conservation predicate에 제한해야 한다.

### 6.2 Write skew

초기 상태 `A=1, B=1`, invariant `A+B>=1`에서:

```text
T1: if B==1 then A=0
T2: if A==1 then B=0
```

두 effect를 동일 snapshot에서 독립적으로 준비하면 각각 유효하지만 함께 적용하면 invariant가 깨진다.

결론: complete read/write set, component-level deterministic serialization 또는 joint guard revalidation이 필요하다.

### 6.3 Prepared effect를 읽는 suffix

Cross effect `X`를 precomputed lane root에 반영한 뒤 후속 local transaction `Y`가 `X`의 output을 읽었다면,
`X`가 cut에서 no-op될 때 `Y`의 capsule도 무효다.

결론: prepared cross effects는 canonical local overlay와 분리하고, 이를 읽는 suffix를 같은 dependency component로 묶어야 한다.

### 6.4 Root 인증 부재

모든 validator가 같은 cut을 보더라도 각자 capsule 계산 완료 시점은 다르다. L-QC가 root를 bind하지 않으면 client는
어느 root가 quorum-supported인지 cut 순간에 확인할 수 없다.

결론: 이 경우 주장할 수 있는 것은 semantic determinacy와 local materialization latency 감소뿐이다.

### 6.5 Invalid-capsule spam

Invalid effect도 ordering될 수 있게 두면 adversary가 validator precompute와 cut-time checker를 소모시킨다.

결론: capsule size/gas bound, admission fee/bond, invalid-attempt nonce consumption과 per-block checker budget이 필요하다.

## 7. Related-work boundary

- [Forerunner, SOSP 2021](https://doi.org/10.1145/3477132.3483564): multiple futures를 constraint와 memoization으로 pre-execute하지만 official order 이후 실행을 가속하는 목적이다.
- [Hyperledger Fabric, EuroSys 2018](https://arxiv.org/abs/1801.10228): execute-order-validate, endorsed read/write sets와 MVCC validation을 사용한다. Endorsement가 execution result certificate 역할을 한다.
- [Chainspace, NDSS 2018](https://arxiv.org/abs/1708.03778): object/checker model과 S-BAC cross-shard atomic commit을 사용한다.
- [Mysticeti, NDSS 2025](https://docs.sui.io/paper/mysticeti.pdf): owned/mixed-object fast path를 DAG vote/certificate pattern에 결합한다.
- [NeuChain+, Applied Sciences 2024](https://doi.org/10.3390/app14114897): merged reserve table과 deterministic concurrency control로 cross-shard commit/abort를 결정한다.
- [EIP-7862](https://eips.ethereum.org/EIPS/eip-7862): state-root computation을 다음 block으로 지연해 consensus critical path를 줄인다. 본 후보는 반대로 precomputed root를 current cut에 결합한다.

안전한 novelty 표현:

> We define a cut-ready effect contract under which a proposal-relative Multimmit vector cut uniquely determines a dependency-closed state transition. Validators factor execution into pre-cut lane capsules and validate only the selected effect composition at proposal time, allowing the same L-QC to authenticate order and state without a separate execution certificate or cross-lane atomic-commit round.

금지할 표현:

- “Speculative execution을 최초로 제안한다.”
- “Object state를 최초로 사용한다.”
- “Execution certificate를 완전히 불필요하게 만든다.”
- “Arbitrary smart contracts를 execution/proof 없이 즉시 finalize한다.”

## 8. 검증할 연구 가설

### H1 — Fast-path coverage

실제 workload에서 몇 %의 transaction을 bounded checker를 가진 Cut-Ready Effect로 표현할 수 있는가?

### H2 — Gap reduction

```text
T_cut_to_certified_root
T_cut_to_queryable_state
```

를 별도로 측정한다. State-Carrying Cut을 사용하지 않는 구성은 첫 metric의 개선으로 주장하지 않는다.

### H3 — Ordering trade-off

State-Carrying Cut의 proposal validation이 ordering L-QC latency를 얼마나 증가시키는가?

```text
T_end_to_end = T_ordering_cut + T_cut_to_state
```

`T_cut_to_state`만 줄고 `T_ordering_cut`이 더 크게 증가하는 구성은 실패다.

### H4 — Speculation efficiency

```text
capsule_cache_hit_rate
speculative_waste_ratio
root_composition_time
atomic_pointer_commit_time
```

를 candidate-cut width, cross-lane fanout과 conflict rate별로 측정한다.

### H5 — Safety and fallback

False output, write skew, version conflict, incomplete DCLP, stale capsule과 slow validator에서:

- ordering safety가 유지되는가?
- fast path가 deterministic no-op 또는 SlowPath로 떨어지는가?
- participant subset이 적용되지 않는가?

## 9. 현재 판단

1. Generic multi-future pre-execution만으로는 novelty와 protocol state-finality claim이 부족하다.
2. State root를 L-QC에 넣는 것만으로는 기존 execute-before-vote의 변형이다.
3. 가장 강한 후보는 **Cut-Ready Effects + cut-parametric materialization + State-Carrying L-QC**의 결합이다.
4. 이 후보의 핵심 위험은 application expressiveness와 ordering critical-path regression이다.
5. 다음 단계는 작은 transfer/object workload에서 checker contract와 root composition algorithm을 형식화하고,
   기존 EC baseline과 end-to-end로 비교하는 것이다.

별도 state certificate보다 queryable-state materialization latency를 목표로 할 경우에는
[CutBasis vote-window execution](./cutbasis-vote-window-execution.md)이 더 단순한 후보다. CutBasis는 Multimmit
proposal-relative vote가 만드는 lane-prefix lattice를 선형 크기의 prefix capsule basis로 precompute하여,
L-QC 이후 transaction 재실행 대신 exact prefix selection과 root composition만 수행한다.
