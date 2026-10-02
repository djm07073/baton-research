# Quorum-Supported Speculative State DAG

> 상태: exploratory design note; authoritative protocol이 아님  
> 기준: state ownership partition 없이, 각 validator/producer lane이 전파받은 blocks로 서로 다른 local execution DAG를 만들고 cut 전에 실행한다.  
> 목표: finalized cut 이전의 execution을 최대한 재사용하여 cut-to-state latency를 줄인다.

> Follow-up: 여러 local views로부터 실행 결과를 가장 많이 보존하는 하나의 plan을 선택하는 최신 탐색안은 [`local-dag-selection-algorithm.md`](./local-dag-selection-algorithm.md)에 정리한다. 이 문서의 cut-derived fixed plan은 안전한 baseline이다.

## 1. Design intent

각 validator `v`는 마지막 finalized state root `R_k` 이후 수신한 blocks를 이용해 local state view를 만든다.

```text
received blocks at validator v
  -> derive static/dynamic conflicts
  -> build local dependency DAG G_v
  -> choose a local topological schedule
  -> speculative execute
  -> retain read versions and effects
```

예를 들어 validator가 `X`, `Y`, `Z`를 받아 `X -> Y -> Z`로 실행할 수 있다. 다른 validator는 network arrival 차이 때문에 `Y -> X -> Z`를 실행할 수 있다. 두 결과는 아직 canonical하지 않다.

이 모델에서 producer lane은 state owner가 아니다. 모든 validators는 같은 global state를 추적하지만 서로 다른 candidate block set과 execution schedule을 먼저 볼 수 있다.

## 2. Important distinction: local linear schedule versus dependency DAG

Local executor는 편의를 위해 `X -> Y -> Z`라는 linear path로 실행할 수 있지만, certificate가 불필요한 order까지 고정하면 view support가 쉽게 분산된다.

예를 들어:

```text
X: writes Alice
Y: writes Bob
Z: reads Alice, writes Carol
```

실제 dependency는 다음이다.

```text
X ----> Z

Y         // independent
```

다음 두 local executions는 같은 partial order를 만족한다.

```text
validator 1: X, Y, Z
validator 2: Y, X, Z
```

따라서 quorum subject는 arbitrary total path가 아니라 다음을 인증해야 한다.

- Exact candidate block set/frontier.
- Conflict edges 또는 deterministic conflict priority.
- Read-from versions.
- Multi-key effects와 post-state commitment.
- Independent nodes의 commutativity/disjointness.

## 3. Continuous pre-cut phase

각 block은 최소 다음 metadata를 가진다.

```text
BlockInput = {
  epoch,
  producer_lane,
  lane_position,
  parent,
  transactions,
  static_access_manifests,
  input_digest,
  input_DA_certificate
}
```

각 validator는 block을 받는 즉시 local DAG에 삽입하고 speculative execution record를 만든다.

```text
SpecExecRecord = {
  base_finalized_root,
  tx_or_block_digest,
  predecessor_digest,
  read_observations: [(key, version, value_commitment)],
  write_delta,
  result,
  effect_commitment,
  code_and_environment_version
}
```

Local DAG는 계속 바뀔 수 있다. 늦게 도착한 conflicting block이 기존 node보다 앞에 놓이면 그 node와 dependency descendants는 stale이 된다. 이 단계의 결과는 speculative cache이며 state-final evidence가 아니다.

### 3.1 Tip plus local DAG view

우리 모델에서 validator/producer가 제출하는 state-aware object는 단순한 lane tip이 아니다.

```text
LaneViewReport_v = Sign_v({
  own_lane_tip,
  observed_frontier: [tip_0, tip_1, ..., tip_n],
  base_finalized_root,
  local_DAG_root,
  read_from_root,
  speculative_effects_root,
  code_and_environment_version,
  view_sequence
})
```

- `own_lane_tip`은 기존 Autobahn data lane의 authenticated prefix를 나타낸다.
- `observed_frontier`는 이 local DAG가 실제로 어느 lane prefixes까지 보았는지를 나타낸다. DAG가 다른 lanes의 blocks도 포함하므로 own tip 하나만으로는 execution context를 복원할 수 없다.
- `local_DAG_root`는 sequential dependency edges가 있는 whole local DAG의 commitment다.
- `read_from_root`와 `speculative_effects_root`는 어떤 state versions에서 무엇을 실행했는지 bind한다.
- 실제 DAG nodes, edges와 execution records는 content-addressed sidecar로 전파하고 report에는 commitments만 넣는다.

이 report는 local observation/execution evidence이지 ordering proposal이나 canonical state가 아니다. 서로 다른 validators는 서로 다른 reports를 정상적으로 제출할 수 있다.

Ordering leader는 reports와 lane tips를 이용해 candidate cut을 제안한다. Candidate를 받은 validator의 ordering vote에는 ordering 판단과 별도로, 자신의 local report를 candidate에 projection한 execution result를 optional하게 실을 수 있다. Ordering vote는 execution projection을 기다리지 않으며 execution shares는 별도로 gossip해 누구나 aggregate할 수 있다.

## 4. Why propagation alone cannot close the view

`f+1` DA는 최소 한 honest holder를 보장하지만, 모든 validators가 같은 block 집합을 보았다는 뜻은 아니다. 더 강하게, `3f+1` validators가 현재 동일 effect를 지지해도 아직 그들이 보지 못한 `f+1`-available conflicting block이 finalized cut에서 앞에 들어올 수 있다.

따라서 pure asynchronous propagation만으로 다음 absence statement를 증명할 수 없다.

```text
"이 transaction보다 앞에 들어올 unseen conflicting transaction은 없다."
```

Pre-cut execution은 가능하지만 safe reuse에는 다음 중 하나가 필요하다.

1. Exact candidate cut/frontier가 input universe를 닫는다.
2. 별도 sealed frontier/fence를 만든다.
3. Finalized cut 이후 local result의 compatibility를 다시 검사한다.

두 번째 방법은 사실상 추가 prepare/coordination round가 되므로 기본안은 candidate cut을 fence로 사용한다.

## 5. Candidate-cut projection

Ordering leader가 candidate cut `C*`를 전파하면 각 validator는 서로 다른 local view를 그대로 투표하지 않는다. Local cache를 `C*`의 exact block set에 projection한다.

```text
on_candidate_cut(C*)
  fetch missing blocks from their f+1 DA holders
  derive the deterministic conflict DAG G(C*)
  partition G(C*) into deterministic conflict components
  for each component:
    reuse compatible SpecExecRecords
    reexecute stale or missing dependency closure
    calculate component delta/result
    sign CandidateExecVote(C*, component, result)
```

Conflict DAG의 edge는 arrival order가 아니라 protocol-wide deterministic priority를 따라야 한다.

```text
Conflict(x,y) iff
  W(x) intersects (R(y) union W(y))
  OR W(y) intersects (R(x) union W(x))

if Conflict(x,y) and Priority_C*(x) < Priority_C*(y):
  add edge x -> y
```

모든 edge가 하나의 deterministic priority 방향을 따르므로 graph가 acyclic하다. Producer가 제공한 DAG는 hint로만 사용하고 validators가 다시 계산한다.

### 5.1 Projection determinism의 정확한 의미

`LocalDAGView` 전체를 동일하게 만드는 것은 목표도 아니고 가능하지도 않다. Validators마다 block 도착 순서와 speculative cache가 다르기 때문이다. Projection은 다음 두 결과로 분리한다.

```text
Project(C*, V_v) = (
  CanonicalPlan(C*),
  ReusePlan(CanonicalPlan(C*), V_v)
)
```

- `CanonicalPlan(C*)`은 동일한 candidate cut과 parent state를 본 모든 honest validators에게 byte-for-byte 동일해야 한다.
- `ReusePlan`은 validator의 cache에 따라 달라도 된다. 어떤 node를 재사용하고 어떤 node를 재실행할지를 정하는 local optimization이다.
- Execution vote와 QC에는 `ReusePlan`, local arrival order, physical worker schedule을 넣지 않는다.
- Validators가 서로 다른 양을 재실행해도 canonical transaction outcomes, effects와 post-state root는 같아야 한다.

따라서 요구되는 성질은 다음과 같다.

```text
CanonicalPlan(C*, V_i) == CanonicalPlan(C*, V_j)

Digest(Materialize(C*, V_i))
  == Digest(Materialize(C*, V_j))
```

첫 식에서 `V_i`, `V_j`는 plan의 입력이 아니라 data source/cache로만 나타난다. Candidate data가 누락된 경우에는 더 작은 plan을 만들지 않고 `NeedData(missing_ids)`를 반환한다.

### 5.2 Candidate가 반드시 고정해야 하는 것

Candidate가 lane tips만 정한 뒤 각 validator가 자신의 local DAG를 그대로 trim하면 projection은 결정적이지 않다. 같은 cut에 `X`, `Y`가 포함되어도 한 validator는 `X -> Y`, 다른 validator는 `Y -> X`를 만들 수 있기 때문이다. 안전한 선택지는 두 가지다.

#### Mode A: cut-derived canonical plan

Candidate가 exact lane tips를 고정하고, protocol에 versioned deterministic plan derivation rule을 둔다.

```text
CandidateStateAnchor = {
  epoch,
  parent_finalized_cut,
  parent_state_root,
  candidate_lane_tips,
  plan_rule_version,
  application_code_hash,
  execution_environment_hash
}
```

모든 validator가 이 anchor와 cut payloads에서 같은 plan을 다시 계산한다. Submitted local DAG views는 candidate 선택과 cache hit를 돕지만 canonical edges를 정하지 않는다. 이것이 가장 단순하고 안전한 첫 구현이다.

#### Mode B: plan-carrying candidate

Local views가 최종 execution schedule 선택에도 영향을 주게 하려면 candidate proposal이 선택한 plan까지 명시적으로 commit해야 한다.

```text
CandidateStateAnchor = {
  ...,
  canonical_plan_root
}
```

Leader는 reports 중 reuse가 높을 것으로 예상되는 plan을 선택할 수 있지만, validators는 다음을 독립적으로 검증한 뒤에만 execution vote를 낸다.

- plan의 node set이 candidate cut의 exact node set과 일치한다.
- lane-local causal order와 explicit dependencies를 보존한다.
- 모든 declared conflicts가 한 방향으로 order된다.
- graph가 acyclic이고 manifests와 context가 유효하다.
- plan serialization과 root 계산이 canonical하다.

이 mode에서는 `tip + local DAG view`가 proposal construction에 직접 기여하지만, leader에게 scheduling 선택권과 성능 조작면을 준다. Ordering vote는 여전히 `CutDigest`에, execution vote는 `CutDigest || PlanRoot || ResultRoot`에 별도로 서명해야 한다.

### 5.3 Canonical plan derivation

Mode A의 기준 알고리즘은 다음과 같다.

```text
derive_plan(anchor):
  nodes := expand every lane prefix from the previous finalized tip
           through anchor.candidate_lane_tips
  if any authenticated block or access manifest is missing:
    return NeedData(missing_ids)

  verify each prefix, DA certificate, transaction occurrence,
         static access manifest, code hash and execution context

  order := canonical_merge(
    lane-local order,
    explicit causal dependencies,
    protocol tie-break rule
  )

  edges := deterministic_conflict_edges(nodes, order)
  components := deterministic_connected_components(nodes, edges)

  return CanonicalPlan(
    anchor,
    node_root(nodes),
    order_root(order),
    edge_root(canonical_sort(edges)),
    component_root(components)
  )
```

Transaction occurrence는 단순 transaction hash가 아니라 다음처럼 candidate 안의 위치에 bind한다.

```text
OccurrenceID = H(lane_id, block_position, tx_index, tx_digest)
```

Conflict graph는 모든 pair를 materialize하지 않고 canonical order를 scan하면서 key별 `last_writer`와 `readers_since_last_write`를 추적해 만들 수 있다. 다만 모든 구현이 동일한 edge 생성 규칙을 사용해야 하며, 구현마다 다른 transitive reduction을 적용해서는 안 된다.

Access manifest에는 명시적인 application keys만이 아니라 nonce, fee balance, absent-key/range read, module/config version처럼 결과에 영향을 주는 hidden access도 포함해야 한다. 실제 접근이 manifest를 벗어나면 deterministic failure 또는 protocol-defined serial fallback으로 처리한다.

### 5.4 Local reuse는 달라도 된다

Canonical plan의 node `x`에 대해 validator의 cached result를 재사용하려면 최소 다음 fingerprint가 일치해야 한다.

```text
InputFingerprint_C(x) = H(
  transaction_digest,
  application_code_hash,
  execution_environment_hash,
  [(key, canonical_source_writer, version, value_hash)]
)

Reusable_v(x, C*) iff
  cache.base_root == anchor.parent_state_root
  AND cache.input_fingerprint == InputFingerprint_C(x)
  AND cache.actual_accesses are contained in the declared manifest
  AND cache.effect was locally executed or validity-verified
```

값만 같고 source writer 또는 version이 다르면 기본적으로 재실행한다. 이는 ABA, negative read와 same-value write를 안전하게 처리하는 보수적 규칙이다. Directly stale인 node와 그 dependency successor closure만 재실행한다. 실행 중 canonical input fingerprint가 cache와 다시 일치하는 successor는 재사용할 수 있다.

### 5.5 Determinism argument

동일한 anchor와 complete candidate data를 가진 두 honest validators에 대해:

1. Hash-linked lane prefixes로부터 같은 node occurrences를 추출한다.
2. 같은 manifests, lane order와 tie-break rule로 같은 canonical order를 만든다.
3. 같은 conflict predicate로 같은 dependency edges와 components를 만든다.
4. Canonical topological order를 따라 각 node를 induction하면, cache hit은 같은 input fingerprint의 effect를 재사용하고 cache miss는 같은 deterministic execution을 수행한다.
5. Conflict edge가 없는 ready nodes는 disjoint/commutative하므로 physical parallel schedule과 무관하게 같은 joined delta를 만든다.

따라서 다음이 성립한다.

```text
Materialize(C*, V_i).result_root
  == Materialize(C*, V_j).result_root
  == SerialReference(CanonicalPlan(C*)).result_root
```

이 성질 때문에 `3f+1` validators가 동일한 raw local view를 가질 필요는 없다. 모두가 서명해야 하는 것은 다음 normalized result다.

```text
H(CandidateStateAnchor, CanonicalPlanRoot, ResultRoot)
```

## 6. The `3f+1` execution view certificate

Multimmit의 global validator set을 `N=5f+1`이라 하면 execution vote는 다음 exact subject에 bind한다.

```text
ExecKey = H(
  "CANDIDATE_EXEC",
  epoch,
  candidate_cut_digest,
  base_finalized_root,
  conflict_component_id,
  exact_component_node_set_root,
  access_manifest_root,
  deterministic_dependency_DAG_root,
  code_and_environment_version
)

ExecValue = H(
  read_from_root,
  ordered_effects_root,
  component_delta_root,
  post_component_commitment
)

CandidateExecVote_v = Sign_v(ExecKey, ExecValue)
```

`3f+1` matching votes가 모이면 `CandidateExecQC`가 된다. `conflict_component_id`는 proposer가 정하지 않고 candidate cut의 complete access graph에서 결정적으로 도출한다. 서로 access-disjoint한 components는 서로 다른 QCs를 비동기적으로 만들 수 있지만, 한 component 안의 edge/node certificates를 따로 합치지는 않는다.

```text
q_exec = 3f+1
intersection(Q1,Q2) >= 2(3f+1) - (5f+1) = f+1
```

따라서 honest validator가 같은 `ExecKey`에 하나의 `ExecValue`만 서명하면 conflicting certificates는 honest double-signing 없이 공존할 수 없다.

이 certificate는 candidate-specific하다. Canonical state admission은 다음 conjunction이다.

```text
StateFinalComponent(C, Q) iff
  OrderingFinal(C)
  AND ValidCandidateExecQC(Q)
  AND Q.candidate_cut_digest == C.digest
  AND Compatible(C, Q)
```

Candidate와 exact same cut이 finalized되면 execution result를 즉시 apply할 수 있다. 다른 cut이 finalized되면 QC가 canonicality를 만들지 않으며 affected records를 revalidate/reexecute한다. Component QCs를 하나의 global state commitment에 합치려면 declared key sets의 disjointness와 deterministic sparse-delta join을 검증해야 한다. 이를 구현하지 않는 첫 prototype은 whole-cut post-state root 하나에 투표한다.

## 7. Do not certify edges independently

`3f+1`은 동일한 exact subject의 uniqueness를 보장할 뿐, 서로 다른 edge certificates를 안전하게 합칠 수 있게 하지는 않는다.

`f=1`, `N=6`, `q=4`에서 다음 세 edges가 각각 quorum을 받을 수 있다.

```text
X -> Y: 4 votes
Y -> Z: 4 votes
Z -> X: 4 votes
```

각 honest validator의 local DAG는 acyclic이어도 signer sets가 다르면 세 certificates의 union은 cycle이다.

따라서 다음 중 하나가 필요하다.

- Whole candidate DAG/result digest에 `3f+1` matching votes.
- 모든 edges가 공통 deterministic rank의 증가 방향이라는 검증 가능한 rule.

기본안은 둘 다 사용한다. DAG는 deterministic rank로 만들고 certificate는 whole candidate execution result에 건다.

## 8. Aligned propagation

각 block이 독립적인 첫 `f+1` holders에게만 전파되면 여러 blocks의 holder intersection은 비어 있을 수 있다. 동일한 validators가 dependency closure 전체를 빨리 보게 해야 local views가 수렴한다.

권장 propagation은 다음과 같다.

```text
block producer
  -> broadcast block normally
  -> stop waiting once f+1 input DA votes form
  -> in parallel, eagerly push block/effect metadata to
     the same deterministic execution fanout for this cut window
```

`N=5f+1`에서 `3f+1` execution votes를 fault-tolerantly 얻으려면 eager fanout target은 최소 `4f+1`로 둔다.

```text
fanout size = 4f+1
maximum Byzantine/withholding = f
remaining potential responders >= 3f+1
```

- 모든 producer lanes가 같은 cut window에서 같은 fanout cohort를 사용한다.
- Cohort는 previous finalized randomness로 deterministic하게 선택·회전한다.
- `f+1` DA 뒤의 background propagation은 block production과 ordering을 막지 않는다.
- Candidate cut이 오면 missing blocks를 DA signer set과 fanout peers에게 병렬 fetch한다.
- Shares는 aggregator 한 명에게만 보내지 않고 gossip하여 누구나 QC를 재구성할 수 있게 한다.

이 fanout은 `3f+1`이 cut 전에 반드시 준비된다는 synchrony guarantee가 아니다. 동일 dependency closure가 같은 validators에 도착할 가능성과 cache locality를 높이는 common-case optimization이다. Formal liveness는 finalized cut 이후 eventual fetch/execution까지 포함해야 한다.

## 9. Reuse and repair after the cut

Finalized cut `C`에서 speculative record `r(t)`는 다음 조건을 만족해야 재사용한다.

```text
Reusable(t,C) iff
  t is included in C
  AND r.base_root == current finalized parent root
  AND r.predecessor_digest == CanonicalPredecessors(t,C)
  AND every read version/value equals the canonical predecessor output
  AND code/environment versions match
```

직접 stale인 node에서 시작해 dependency descendants를 dirty closure로 확장한다.

```text
dirty := directly_incompatible_records(C)
repeat
  dirty := dirty union descendants_reading_outputs_of(dirty)
until fixed_point

reexecute dirty in deterministic cut order
reuse all remaining compatible records
```

Candidate cut과 final cut이 같고 `CandidateExecQC`가 이미 있으면 이 repair는 필요 없다. Candidate가 달라지더라도 independent components는 그대로 재사용할 수 있다.

## 10. End-to-end example

```text
X: Alice 100 -> 70
Y: Bob 20 -> 30
Z: read Alice; if Alice >= 50, Carol += 5
```

Validators may preexecute:

```text
V1 local schedule: X, Y, Z
V2 local schedule: Y, X, Z
V3 local schedule: X, Z, Y
```

All are compatible with the same dependency DAG:

```text
X -> Z
Y independent
```

Candidate cut `C*={X,Y,Z}` fixes conflict priority `X<Z`. Validators project their caches, compute the same post-state and gossip matching votes.

- If `3f+1 CandidateExecQC` forms and `C*` finalizes, state apply can coincide with cut finality.
- If final cut inserts `W` before `X`, where `W` writes Alice, `X` and `Z` become dirty; `Y` remains reusable.
- The entire cut is not rolled back. Only the affected dependency closure is repaired.

## 11. What this achieves

The model does not claim that pre-cut local views are already consensus. It provides three latency layers.

1. **Continuous speculation:** every validator executes whatever complete local DAG it currently has.
2. **Candidate normalization:** a candidate cut supplies the common closed input universe; local work is projected and repaired while ordering is still deciding.
3. **Final join:** finalized cut plus matching `3f+1 CandidateExecQC` makes state immediately admissible; missing QC completes asynchronously without stopping later ordering.

The main measurable value is not the percentage of validators with the same arbitrary linear path. It is:

```text
candidate_cache_reuse_ratio
candidate_exec_QC_ready_at_cut
dirty_closure_ratio
cut_to_state_latency
```

The central claim candidate is:

> Validators continuously build and execute divergent local state DAGs, then project those caches onto the ordering candidate's closed input frontier and form a `3f+1` certificate over the exact cut-derived dependency DAG and result. This moves most execution before ordering finality without treating local arrival order or edge-wise majority as canonical.
