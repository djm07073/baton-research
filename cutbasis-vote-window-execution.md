# CutBasis: Vote-Window Execution for Multimmit

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 연구 질문

별도 execution vote, EC 또는 validity proof 없이 다음 간격을 줄일 수 있는가?

```text
T_gap = T_state-ready - T_ordering-cut
```

이 문서에서 `T_state-ready`는 validator가 canonical cut의 deterministic post-state를 materialize하고 query에 제공할 수 있는 시점이다.
L-QC가 post-state root를 직접 인증하지 않는 한, 이를 외부 검증 가능한 별도 state certificate finality와 혼동하지 않는다.

## 2. Multimmit에서 이용할 구조

Multimmit leader proposal은 producer chain마다 bounded consecutive path를 제시한다. 각 validator vote는 자신이 실제로 보유한
proposal-relative position과 bounded extension을 서명한다. `n-f` vote pool에서 finalized lane position은 `(3f+1)`-th greatest
position, 즉 greatest `3f`를 drop하여 추출된다.

따라서 exact cut coordinate는 proposal 수신 시점에 확정되지 않지만 다음은 이미 알려진다.

1. 각 lane의 후보는 arbitrary transaction permutation이 아니라 하나의 authenticated chain path 위 prefix다.
2. Final coordinate는 L-QC vote transcript가 보고한 prefix positions 중 안전하게 추출된다.
3. State-isolated lane의 local effects는 다른 lane과 독립적으로 prefix execution할 수 있다.

이 구조를 이용하여 cartesian product의 모든 vector cut을 speculative execution하지 않고, lane별 prefix state만 계산한다.

## 3. CutBasis

Proposal `P`가 lane `i`에 대해 다음 path를 제시한다고 하자.

```text
base_i -> B_i,1 -> B_i,2 -> ... -> B_i,m_i
```

Validator는 proposal을 검증하고 ordering vote를 처리하는 동안 별도 worker에서 prefix capsules를 계산한다.

```text
PrefixCapsule(P, i, h) {
  proposal_id,
  lane_id,
  exact_prefix_tip,
  pre_root,
  local_post_root,
  prepared_cross_root,
  receipt_root,
  state_delta,
  updated_authenticated_nodes,
  dependency_manifest
}
```

`CutBasis(P)`는 다음 집합이다.

```text
CutBasis(P) = union over lanes i of
              { PrefixCapsule(P,i,h) | base_i < h <= max_held_i }
```

State isolation 아래에서 L-QC가 선택한 vector cut `O`의 local-only state는 다음처럼 조합된다.

```text
State_local(O) = Compose_i PrefixCapsule(P, i, O[i])
```

가능한 vector cut 수는 `product_i (m_i+1)`이지만, 필요한 speculative work와 cache는 prefix reuse를 통해
`sum_i m_i`에 비례한다. Cut 이후에는 lane당 capsule 하나를 선택하고 global root를 조합한다.

## 4. Vote-window overlap

Proposal 수신 시점을 `t_P`, L-QC로 ordering cut을 관찰한 시점을 `t_C`, proposal prefix execution 시간을 `E_P`라고 하자.

Post-cut execution baseline:

```text
Gap_post = E_selected + T_root_apply
```

CutBasis:

```text
Gap_cutbasis = max(0, t_P + E_P - t_C)
               + T_select_compose_apply
```

숨길 수 있는 실행 시간은 proposal부터 L-QC까지의 vote window다.

```text
HiddenExecutionBudget = t_C - t_P
```

실행이 이 window 안에 끝나면 cut-to-queryable-state gap은 capsule selection과 atomic root commit 비용으로 줄어든다.

Ordering vote는 execution 완료를 기다리지 않는다. Consensus-critical crypto/network queue와 execution worker를 분리하여
speculation이 L-QC 형성을 늦추지 않게 한다. Execution을 vote 선행조건으로 만들면 gap을 cut 앞쪽으로 이동시킬 뿐
end-to-end latency가 줄었다고 할 수 없다.

## 5. Exact cut selection

L-QC 또는 local finalized vote pool이 도착하면:

1. Multimmit 규칙으로 lane별 finalized position을 추출한다.
2. 각 position이 proposal/finalized tip history의 exact authenticated branch에 있는지 확인한다.
3. 동일 proposal/branch의 `PrefixCapsule(P,i,O[i])`를 선택한다.
4. Missing capsule만 post-cut fallback execution한다.
5. Local roots와 eligible cross-lane patches를 조합한다.
6. Durable commit record를 atomic append/pointer swap한다.

```text
CutBasisCommit {
  lqc_or_finality_fact_id,
  ordering_cut,
  selected_prefix_capsules,
  selected_cross_components,
  previous_global_root,
  new_global_root
}
```

Capsule은 consensus evidence가 아니므로 다른 validator에게서 신뢰하여 받아서는 안 된다. Remote capsule을 재사용하려면
EC, proof 또는 trusted attestation이라는 별도 trust mechanism이 다시 필요하다.

## 6. Cross-lane operations

State isolation은 local effects에만 factorization을 준다. Cross-lane operation `X`는 participant fragment들을 하나의
hyperedge capsule로 표현한다.

```text
CrossCapsule(X) {
  attempt_id,
  manifest_digest,
  participant_lanes,
  [(lane, exact_block, input_versions, prepared_effect)],
  joint_guard,
  joint_effect_root
}
```

각 participant fragment는 lane prefix execution 중 prepared overlay에 계산하되 canonical local root에는 섞지 않는다.
L-QC-derived cut `O`가 다음 조건을 만족할 때만 hyperedge를 atomic apply한다.

```text
valid ReadyBundle/DCLP
AND all exact participant blocks are included in O
AND every participant prefix capsule reaches the required pre-root
AND input versions are live and single-consumed
AND joint application predicate accepts
AND dependency closure holds
```

일부 fragment만 cut에 포함되면 local prefix root는 계속 선택할 수 있지만 `X`의 prepared patch는 적용하지 않는다.

## 7. Duplicate and interleaving boundary

Multimmit의 external `Ord/Emit`은 producer chains 사이의 dense order와 duplicate removal을 담당한다. CutBasis가 안전하려면
다음 중 하나가 필요하다.

1. Transaction/object ownership mapping이 동일 mutable operation을 정확히 한 execution lane에만 admission한다.
2. Duplicate transaction은 nonce/idempotency rule로 어느 occurrence가 선택되어도 동일 no-op semantics를 가진다.
3. Cross-lane operation은 canonical anchor와 manifest nonce가 하나의 occurrence만 소비하게 한다.

Arbitrary shared-state transaction의 결과가 global interleaving에 따라 달라지면 lane-prefix factorization은 성립하지 않는다.
그 transaction은 cross component 또는 post-cut SlowPath로 보내야 한다.

## 8. View change와 Byzantine waste

### Faulty leader proposal

Byzantine leader가 실행비용이 큰 valid proposal을 보내고 L-QC 형성을 방해하면 speculative work가 폐기될 수 있다.

완화:

- Proposal과 per-view execution gas cap
- Consensus-critical queue와 execution pool 분리
- At most one active execution job per `(view,lane,proposal)`
- Correct-leader progress를 위한 reserved CPU/network capacity
- Retained view window에 맞춘 capsule cache bound

### Equivocating proposals

동일 view의 여러 leader block을 관찰하더라도 validator의 direct-vote stance는 하나에만 durable하게 고정된다.
Execution은 local vote subject 또는 first eligible proposal에만 우선순위를 주고 다른 fork는 낮은-priority/bounded job으로 둔다.

### Final cut shorter than executed prefix

Lane execution이 copy-on-write prefix capsules를 유지하므로 낮은 prefix를 선택할 때 rollback이나 inverse transition이 필요 없다.
높은 prefix capsule과 그 전용 pages를 폐기하거나 후속 compatible proposal에 cache reuse한다.

### Extension above leader proposal

Vote extension으로 finality가 proposal tip보다 전진할 수 있다. Validator는 자신이 DA-voted/held한 bounded extension도 동일 lane
prefix basis에 포함한다. 보유하지 않은 extension이 final cut에 들어오면 DA recovery 후 missing suffix만 실행한다.

## 9. Safety와 성능 주장의 경계

CutBasis는 local optimization이다.

- 잘못된 capsule은 해당 validator의 local state를 망가뜨릴 수 있으므로 deterministic runtime과 implementation correctness가 필요하다.
- Capsule은 Byzantine correctness를 증명하지 않는다.
- Consensus safety는 capsule readiness에 의존하지 않는다.
- Capsule miss/failure는 post-cut deterministic execution으로 fallback한다.

따라서 protocol-level claim은 다음으로 제한한다.

```text
Given the same canonical cut and deterministic application semantics,
precomputed prefix capsules select the same post-state as post-cut execution.
```

외부 client가 cut 순간에 quorum-authenticated post-state root를 요구하면 다음 중 하나가 추가로 필요하다.

- State root를 기존 L-QC vote subject에 포함
- Execution Certificate
- Validity proof

이 중 아무것도 사용하지 않으면 논문 metric은 `cut-to-materialized/queryable-state latency`라고 명시하는 편이 정확하다.

## 10. Related-work boundary

- [Proof-of-Execution](https://arxiv.org/abs/1911.00838)은 consensus 전에 speculative execution하고 proof-of-executions와 check-commit protocol을 사용한다.
- [Forerunner, SOSP 2021](https://doi.org/10.1145/3477132.3483564)은 transaction dissemination 중 multiple execution futures를 constraint와 memoization으로 가속한다.
- [Hyperledger Fabric, EuroSys 2018](https://arxiv.org/abs/1801.10228)은 pre-order execution outputs/read-write sets를 endorsement한 뒤 order/validate한다.
- [Block-STM](https://arxiv.org/abs/2203.06871)은 이미 정해진 block transaction order 아래에서 speculative parallel execution한다.
- [Mysticeti](https://docs.sui.io/paper/mysticeti.pdf)는 object fast path transaction votes를 DAG causal structure와 결합한다.

CutBasis의 차별화 후보:

1. Execution future를 예측하지 않고 Multimmit proposal-relative vote가 정의하는 bounded prefix lattice를 사용한다.
2. Exponential vector-cut candidates를 lane-prefix basis와 cross-lane hyperedges로 factorize한다.
3. Proposal-to-L-QC vote window와 execution을 overlap하되 execution readiness를 ordering 선행조건으로 만들지 않는다.
4. Final L-QC cut을 capsule lookup/compose/atomic pointer commit으로 materialize한다.

안전한 claim:

> CutBasis exploits the prefix structure of proposal-relative Multimmit votes: it materializes a linear-size basis of lane-prefix states during the proposal-to-L-QC window, then composes the exact L-QC-derived vector cut without post-cut transaction re-execution. Cross-lane effects are represented as dependency hyperedges selected only under complete canonical placement.

단순 speculative execution으로만 표현하면 선행기술과 겹치므로 `prefix-basis factorization`과 exact Multimmit cut relation이 formal contribution이어야 한다.

## 11. 정리 후보

### Lemma 1 — Cut coordinate coverage

각 finalized lane coordinate는 retained L-QC vote transcript의 proposal-relative positions/extensions가 지지하는 authenticated path 위에 있다.

### Theorem 1 — Prefix-basis equivalence

Lane states가 격리되고 cross-lane effects가 별도 hyperedge로 분리되면, L-QC cut 이후 transaction을 재실행한 state와
동일 proposal paths의 selected prefix capsules를 composition한 state가 같다.

### Theorem 2 — No speculative rollback requirement

Prepared capsules가 immutable copy-on-write overlays이고 canonical state pointer가 cut 이후에만 갱신되면,
non-canonical proposal/view의 폐기는 canonical state inverse execution을 요구하지 않는다.

### Theorem 3 — Cross-lane atomic selection

Cross capsule이 complete participant placement, reachable participant pre-roots와 joint guard를 모두 요구하고 one durable commit
record로 적용되면 participant effect의 진부분집합은 canonical state에 나타나지 않는다.

### Theorem 4 — Consensus non-interference

Execution jobs가 consensus-critical queues/resources를 소비하지 않고 ordering vote가 capsule completion을 기다리지 않으면,
capsule readiness/failure는 Multimmit의 logical ordering transitions를 변경하지 않는다.

Theorem 4의 wall-clock non-regression은 formal safety가 아니라 resource isolation을 전제로 한 systems property다.

## 12. 평가 계획

Baselines:

```text
B0 post-cut sequential execution
B1 payload-arrival speculative execution
B2 proposal-triggered full-vector speculation
B3 CutBasis lane-prefix factorization
B4 CutBasis + cross-lane hyperedge capsules
```

Metrics:

```text
proposal_to_lqc_window
cut_to_queryable_state p50/p95/p99
prefix_capsule_hit_rate_at_cut
missing_suffix_execution_time
speculative_cpu_waste
noncanonical/view-change cache waste
root_selection/composition/atomic-commit time
ordering latency regression
```

Workloads:

- Lane-local ratio 100/90/50%
- Cross-lane fanout 2/3/5
- Execution cost small/medium/CPU-heavy
- Proposal depth and vote-extension depth sweep
- Honest/faulty leader views, equivocation and timeout
- Hot shared object SlowPath
- Duplicate transaction/nonce conflicts

Success criteria:

1. B3가 B0보다 cut-to-queryable-state p50/p95/p99를 줄인다.
2. B3가 all-vector speculation B2보다 같은 hit rate에서 speculative work를 줄인다.
3. Execution pool 활성화가 ordering cut latency를 유의하게 악화시키지 않는다.
4. View change와 shortened cut에서도 canonical root가 B0와 byte-identical하다.
5. B4에서 incomplete cross-lane operation의 partial effect가 나타나지 않는다.

## 13. 현재 판단

1. EC 없는 단순 speculative execution은 선행기술 때문에 novelty가 약하다.
2. Multimmit의 proposal-relative prefix geometry를 이용한 **CutBasis factorization**은 더 구체적인 systems contribution 후보다.
3. 이 방식은 protocol state certificate를 새로 만들지 않고 local materialization gap을 줄인다.
4. 외부 인증 state finality를 주장하려면 EC/proof/state-carrying L-QC 중 하나가 여전히 필요하다.
5. 원래 목표가 실제 application query readiness라면 CutBasis가 proof-hedged EC보다 단순하고 정상경로 latency에 직접적이다.
