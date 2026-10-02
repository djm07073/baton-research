# Proof-Hedged State Finality

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 질문

기존 EC fast path를 유지하면서 succinct validity proof를 대체 evidence로 허용하면 다음 간격을 더 줄일 수 있는가?

```text
T_gap = T_state-finality - T_ordering-cut
```

핵심 아이디어는 proof validity에 다시 quorum vote를 모으는 `Proof Certificate`가 아니다.
EC와 validity proof가 동일한 typed state-transition statement를 인증하게 하고, 먼저 준비된 evidence를 사용한다.

## 2. 공통 transition statement

Block `B=(epoch,lane,height,block_id)`에 대한 statement를 다음과 같이 고정한다.

```text
TransitionStatement {
  epoch,
  lane_id,
  start_height,
  end_height,
  canonical_block_sequence_commitment,
  pre_state_root,
  post_state_root,
  local_effects_root,
  prepared_cross_effects_root,
  receipt_root,
  execution_version
}
```

두 evidence가 이를 인증할 수 있다.

1. **EC edge:** `start_height + 1 = end_height`, matching `n-2f` execution votes
2. **Validity-proof edge:** 한 block 또는 연속 segment에 대한 succinct proof

Validity proof에는 zero knowledge가 필요하지 않다. Privacy blinding 없이 soundness와 succinct verification만 사용한다.

## 3. Latency crossover

Block payload arrival을 `t_0`, ordering cut을 `t_c`라고 하자.

```text
t_EC = q번째 validator execution 완료
       + EC vote propagation/aggregation

t_PI = witness generation + proving + proof propagation + verification
```

EC-only:

```text
Gap_EC = max(0, t_EC - t_c) + T_join_apply
```

Proof-only:

```text
Gap_PI = max(0, t_PI - t_c) + T_verify_join_apply
```

Hedged path:

```text
Gap_H = max(0, min(t_EC, t_PI) - t_c) + T_selected_join_apply
```

Proof가 실제 gap을 줄이는 필요조건:

```text
t_PI < t_EC
AND t_EC > t_c
```

따라서:

- EC와 proof가 모두 cut 전에 준비되면 `Gap_EC = Gap_H ≈ apply cost`다.
- EC가 cut 전에 준비되고 proof가 늦으면 proof는 latency 이득이 없다.
- EC가 cut 뒤까지 늦고 proof가 더 먼저 준비될 때만 proof가 gap을 줄인다.
- Proof race의 1차 목표는 median보다 p95/p99와 EC-gap recovery다.

Prover가 validator execution과 CPU/memory bandwidth를 경쟁하면 `t_EC` 자체가 증가할 수 있다.
“Hedging은 EC-only보다 느리지 않다”는 주장은 prover resource isolation 또는 explicit CPU budget 아래에서만 가능하다.

## 4. Heterogeneous Evidence Frontier

Lane별 state history를 root vertex와 evidence edge의 graph로 본다.

```text
V = (lane, height, state_root)

E_EC = single-block EC edge
E_PI = single- or multi-block validity-proof edge
```

예시:

```text
root_10 --EC(B11)--> root_11
root_11 ===== proof(B12..B15) =====> root_15
root_15 --EC(B16)--> root_16
```

Ordering cut `O_k`에 대한 frontier는 다음과 같다.

```text
EvidenceFrontier_k[i]
  = max canonical height h <= O_k[i]
    reachable from the previous finalized root
    using valid EC or proof edges
```

모든 edge는 `O_k`가 선택한 exact canonical block sequence에 완전히 바인딩되어야 한다.
Proof가 다른 fork의 valid transition을 증명해도 frontier에는 사용할 수 없다.

## 5. Segment proof as EC-gap repair

EC가 한 height에서 빠지면 현재 contiguous frontier는 그 뒤의 valid EC를 사용할 수 없다.

```text
B10 finalized
B11 EC
B12 EC missing
B13 EC
B14 EC
```

다음 segment proof는 gap을 복구한다.

```text
SegmentProof(B12..B14) {
  pre_root: root(B11),
  post_root: root(B14),
  exact_block_sequence_commitment: H(B12,B13,B14),
  effects_root,
  validity_proof
}
```

이 proof는 EC가 누락된 `B12`만 증명하는 것보다 이후 prefix를 함께 덮어 proof overhead를 amortize한다.

Proof edge가 만족해야 하는 조건:

1. Start root가 현재 reachable frontier root와 정확히 일치한다.
2. Segment 안에 height gap이나 다른 fork block이 없다.
3. End height가 ordering cut을 넘지 않는다.
4. Execution version과 application semantics가 전체 segment에서 고정되거나 proof가 upgrade transition을 명시한다.
5. State effects와 updated authenticated-tree nodes가 proof statement에 binding되고 DA-retrievable하다.

## 6. Frontier-triggered proof hedging

모든 block을 항상 proving하면 proof-only pipeline과 같아지고 비용과 선행기술 충돌이 커진다.
대신 proof를 EC frontier stall 위험에 선택적으로 사용한다.

```text
When:
  block is DA-certified
  AND it is the earliest missing EC after the current state frontier
  AND logical_age(block) >= hedge_trigger_views
  AND no proof job already covers the lane gap

Then:
  start a proof job from the gap through the longest available canonical candidate prefix
```

운영 규칙:

- Raw wall-clock timestamp가 아니라 consensus-visible logical view age를 사용한다.
- Lane마다 earliest gap proof job 하나만 활성화한다.
- Global proving budget과 per-application gas/bond budget을 둔다.
- EC가 먼저 형성되면 취소 가능한 proof phase는 중단하고, 이미 비싼 proving phase에 들어갔다면 background completion/recursive checkpoint 용도로 재사용한다.
- Mapping/fork 변경 시 exact block binding이 다른 proof job은 state finality에 쓰지 않고 폐기한다.

이 정책의 목적은 average block을 proving하는 것이 아니라 frontier를 실제로 막는 gap에 prover capacity를 집중하는 것이다.

## 7. Cross-lane composition

Cross-lane operation `X`의 participant는 서로 다른 evidence type을 사용할 수 있다.

```text
Lane A: EC edge
Lane B: single-block proof edge
Lane C: segment proof edge
```

`X`의 finalize 조건:

```text
valid ReadyBundle/DCLP
AND exact participant blocks are canonical in O_k
AND every participant pre-root is reachable
AND every participant effect is covered by EC or proof evidence
AND participant evidence commits the same attempt/manifest digest
AND application joint predicate accepts
AND dependency closure holds
```

Lane-local proof는 다른 participant fragment의 존재나 conservation을 자동으로 증명하지 않는다.
DCLP와 joint application predicate는 그대로 필요하다. 이를 proof로 대체하려면 별도 N-lane bundle circuit이 필요하다.

Segment가 unresolved cross-lane operation을 지나가려면 다음 중 하나가 필요하다.

1. Segment를 cross boundary 직전에서 끊는다.
2. Foreign input/effect commitments와 complete DCLP를 public input으로 증명한다.
3. Participant lanes를 함께 다루는 joint segment proof를 만든다.

Baseline은 1번이 가장 단순하고, 2번은 다음 단계, 3번은 proof scalability 연구로 남긴다.

## 8. Proof certificate와 availability

Sound validity proof는 누구나 검증할 수 있으므로 proof correctness에 `3f+1` vote를 다시 모을 필요가 없다.

Quorum이 추가로 보장할 수 있는 것은 다음뿐이다.

- Proof bytes retention
- Effect log와 updated state nodes retrievability
- Branch/statement binding을 확인한 custody

Proof와 materialization sidecar를 기존 Multimmit DA path에 넣을 수 있다면 기존 DA Certificate를 재사용한다.
별도 certificate가 필요하다면 의미는 `Proof Availability Certificate`이지 `Proof Validity Certificate`가 아니다.

Proof만 있고 effect data가 없으면 client는 post-state root의 correctness를 확인할 수 있지만 validator는 queryable state를 재구성하지 못할 수 있다.
다음 데이터를 함께 DA해야 한다.

```text
proof bytes
public inputs / statement
receipt/effect log
changed object values
authenticated-tree update nodes or a deterministic reconstruction input
```

## 9. Safety properties

### Evidence compatibility

같은 exact canonical input과 deterministic execution version에 대해 valid EC와 sound proof가 서로 다른 post-root를 인증할 수 없다.

필요 가정:

- EC quorum uniqueness와 honest deterministic execution
- Proof-system soundness
- Exact pre-root, block sequence와 execution-version binding

### Frontier prefix safety

Evidence graph는 현재 finalized root에서 reachable한 canonical prefix만 확정하므로 중간 root나 block을 건너뛰지 않는다.

### Cross-lane atomicity

Participant evidence type이 달라도 state-cut evaluator가 operation hyperedge를 all-or-none으로 선택하면 partial participant state apply가 발생하지 않는다.

### Evidence monotonicity

새 EC 또는 proof edge는 reachable frontier를 전진시키거나 유지할 뿐 이미 finalized root를 변경하지 않는다.

## 10. Liveness와 공격

### Proof-job amplification

Adversary가 여러 lane에서 EC를 deadline 직전까지 지연하여 proof jobs를 반복 유발할 수 있다.

완화:

- Earliest-gap-only scheduling
- Per-lane active job cap
- Global proof gas budget
- Operation fee/bond
- 동일 segment/fork proof deduplication

### Witness withholding

Public deterministic application에서는 DA payload와 pre-state로 다른 prover가 witness를 재생성할 수 있어야 한다.
Private witness application에서는 original prover withholding이 proof liveness를 정지시키므로 threshold escrow나 별도 trust assumption이 필요하다.

### Canonicality waste

Pre-cut proof가 non-canonical producer branch에 대해 생성될 수 있다. 이는 safety 문제가 아니라 wasted proving 문제다.
Proof scheduler는 proposal support와 branch age를 사용할 수 있지만, prediction을 safety 전제로 사용해서는 안 된다.

### Resource interference

Proof generation이 execution workers, DA networking 또는 EC aggregation과 자원을 공유하면 hedge가 오히려 tail latency를 악화할 수 있다.
프로토타입은 CPU core, memory budget와 queue priority를 분리해 이 효과를 반드시 측정해야 한다.

## 11. Related-work boundary

- [Hyli pipelined proving](https://docs.hyli.org/concepts/pipelined-proving/): sequencing과 proof settlement를 분리하고 proof timeout/rejection을 처리한다.
- [Mina parallel scan state](https://minaprotocol.com/wp-content/uploads/technicalWhitepaper.pdf): block production과 recursive SNARK work를 분리하고 proof tree를 병렬 계산한다.
- [Kaspa vProgs](https://kaspa.co.il/wp-content/uploads/2025/09/vProgs_yellow_paper.pdf): conditional proofs와 Computation DAG를 이용해 cross-program dependency와 proof stitching을 다룬다.
- [Flow](https://arxiv.org/abs/1909.05832): execution receipt와 distributed verification을 consensus 이후 pipeline한다.

약한 claim:

- Async proof generation
- Proof가 준비된 state를 finalize
- Recursive proof batching
- Proof certificate 추가

남길 수 있는 claim 후보:

> A proposal-relative heterogeneous evidence frontier in which quorum execution certificates and variable-length validity proofs are substitutable transition edges. Frontier-triggered proof jobs repair only the earliest EC gaps, while dependency-closed state-cut extraction permits mixed evidence across N-lane atomic operations.

이 claim도 단순 composition으로 평가될 수 있다. Formal evidence-substitution theorem, adaptive scheduling algorithm과 실제 tail-latency/compute crossover가 모두 필요하다.

## 12. 평가 판정 기준

### Latency

```text
T_payload_to_cut
T_cut_to_state p50/p95/p99
EC_ready_at_cut_ratio
proof_ready_at_cut_ratio
min_evidence_ready_at_cut_ratio
frontier_stall_duration
```

### Cost

```text
proof_jobs_started/completed/cancelled
proving_cpu_seconds_per_finalized_tx
noncanonical_proof_waste
proof_bytes and materialization_sidecar_bytes
EC vote bytes retained/garbage-collected
```

### Crossover experiments

변수:

- Validator execution cost
- WAN vote delay
- Prover speed and count
- EC signer delay/withholding
- Segment length
- Cross-lane ratio/fanout
- CPU isolation on/off

성공 조건:

1. EC-fast workload에서 end-to-end latency regression이 통계적으로 유의하지 않는다.
2. EC-lag workload에서 p95/p99 cut-to-state gap과 frontier backlog가 감소한다.
3. Proving cost가 all-block proof baseline보다 명확히 낮다.
4. Mixed EC/proof evidence에서 모든 honest node의 finalized roots가 일치한다.

## 13. 현재 판단

1. Validity proof를 proof certificate로 감싸는 설계는 중복이며 latency에 불리하다.
2. EC-or-proof race는 안전한 latency hedge지만 정상 경로 median novelty는 약하다.
3. Variable-length segment proof는 contiguous EC gap을 복구하고 proof cost를 amortize할 수 있다.
4. **Frontier-triggered segment proving + heterogeneous evidence frontier**가 현재 proof 방향에서 가장 강한 후보다.
5. 이 방향은 기존 non-EC Cut-Ready Effects 후보와 경쟁 관계가 아니라 서로 다른 연구 경로다.
