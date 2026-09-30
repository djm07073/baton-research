# Conflict-Affinity Propagation and DA-to-Execution Quorum Promotion

> 상태: exploratory design note; authoritative protocol이 아님  
> 목적: state를 owner lane으로 분할하지 않는 speculative state-DAG 방향에서, cross-lane conflict와 cut-to-state latency를 함께 줄일 수 있는 입력 전파 및 실행 인증 경로를 정의한다.  
> 현재 authoritative baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

> **방향 정정:** 이 문서의 transaction-to-lane affinity routing은 사용자가 설명한 핵심 모델을 잘못 해석한 이전 제안이다. 현재 검토 중인 방향은 각 validator가 전파받은 blocks로 divergent local DAG를 실행한 뒤 candidate cut에 projection하는 [quorum-supported-speculative-state-dag.md](./quorum-supported-speculative-state-dag.md)다. 본 문서는 routing 대안 비교용으로만 남긴다.

## 1. 결론

두 문제를 분리해서 푼다.

1. **Conflict-affinity input routing:** 서로 충돌할 가능성이 높은 transactions를 같은 producer lane으로 보낼 확률을 높인다. State ownership을 나누는 것이 아니라 speculative execution stream만 배치한다.
2. **DA-to-execution quorum promotion:** `f+1` DA signers를 cut-relative execution voters의 warm set으로 우선 사용하고, 필요한 validator에게 artifact를 미리 전파해 execution certificate 형성을 앞당긴다.

두 번째 단계는 conflict 자체를 줄이지 않는다. 첫 번째 단계가 cross-lane speculative invalidation과 repair work를 줄이고, 두 번째 단계가 남은 결과를 state-final로 인증하는 시간을 줄인다.

핵심 제한은 다음과 같다.

- DA vote와 execution vote는 서로 다른 statement다. DA signature를 execution signature로 그대로 셀 수 없다.
- `f+1 + f = 2f+1`은 **모든 `f+1` DA signers가 새 `ExecVote`를 낸 정상 경로**의 산술이다.
- 고전적인 `2f+1` execution QC는 execution electorate가 `3f+1`일 때 안전하다. Multimmit의 전역 `5f+1` validators 전체를 electorate로 쓰면 `2f+1`은 충분한 intersection quorum이 아니다.
- Threshold는 conflict를 결정하지 않는다. Finalized cut과 deterministic reconciliation이 결과를 결정하고, threshold는 그 exact 결과에 대한 합의를 인증한다.

이 note의 execution-QC path는 현재 proof-aware baseline에 대한 **vote-only alternative**다. Sound validity proof를 계속 사용한다면 proof가 correctness를 이미 결정하므로 필수 ExecQC까지 다시 요구하는 것은 중복 검증과 두 번째 quorum latency를 만든다. Conflict-affinity routing은 두 방식 모두에 사용할 수 있지만, `validity proof + f+1 custody`와 `replicated execution + ExecQC` 중 어느 것이 state-admission predicate인지 논문에서 하나를 주 경로로 선택해야 한다.

## 2. System model

```text
Global application state S

producer lane 0 ── speculative effect DAG 0 ┐
producer lane 1 ── speculative effect DAG 1 ├─ finalized cut
...                                         │      -> deterministic reconciliation
producer lane L ── speculative effect DAG L ┘      -> execution certificate
                                                    -> state apply
```

- Application state는 producer별로 소유권 분할하지 않는다.
- Producer lane은 authenticated input order와 speculative execution stream이다.
- 한 lane 안의 order는 global ordering에서도 보존된다고 가정한다.
- Transaction의 conservative read/write footprint는 signed bytes와 immutable application schema에서 실행 전에 계산 가능해야 한다.
- Runtime-dependent arbitrary EVM access는 범위 밖이다.
- 모든 speculative execution은 마지막 finalized state root에서 시작하고, read-from versions와 write delta를 남긴다.
- Pre-cut state DAG는 candidate evidence이지 canonical state가 아니다.

각 speculative effect node는 최소 다음을 포함한다.

```text
EffectNode = {
  tx_digest,
  producer_lane,
  lane_position,
  parent_finalized_root,
  read_observations: [(key, version, value_commitment)],
  write_delta,
  status,
  code_version,
  local_dependencies
}
```

Range/predicate read, absent-key read, account nonce, fee state와 environmental input도 `read_observations`에 포함해야 한다. Producer가 제시한 dependency edge는 hint일 뿐이며 validator가 footprint와 read versions에서 다시 검증한다.

## 3. Certificate ladder

### 3.1 Availability certificate

```text
InputAvailVote_i = Sign_i(
  "INPUT_AVAIL",
  epoch,
  lane,
  position,
  input_digest
)
```

`f+1` distinct votes는 최대 `f` Byzantine faults 아래 exact input을 보유한 honest validator가 적어도 한 명 있음을 보장한다. Correctness, effect bundle 보유 또는 canonicality는 보장하지 않는다. Pre-execution effect sidecar에 별도 custody certificate를 붙일 수 있지만, 아래 quorum-promotion 산술에 필수는 아니다.

### 3.2 Cut-relative execution vote

Candidate 또는 finalized cut `C`가 도착하면 validator는 state DAG를 그대로 투표하지 않는다. `C`가 정한 canonical order로 effect reuse와 repair를 먼저 계산하고 다음 exact statement에 새로 서명한다.

```text
ExecKey = H(
  epoch,
  execution_committee_id,
  finalized_cut_digest,
  parent_state_root,
  conflict_component_id,
  canonical_tx_order,
  code_version
)

ExecValue = H(
  reused_effects,
  reexecuted_effects,
  post_component_or_state_root
)

ExecVote_i = Sign_i("EXEC", ExecKey, ExecValue)
```

`AVAIL`과 `EXEC`은 반드시 domain-separated signatures다.

`ExecKey`에는 result digest를 넣지 않는다. Honest validator는 같은 `ExecKey`에 최대 하나의 `ExecValue`만 서명한다. Result를 key 자체에 넣으면 서로 다른 결과가 서로 다른 logical instances처럼 보여 honest validator의 double-signing을 탐지할 수 없다.

첫 구현은 finalized cut 전체의 post-state root 하나에 투표하는 편이 가장 단순하다. Conflict-component별 비동기 QCs는 cut에서 계산한 components가 실제 access 기준으로 disjoint하고, 모든 component deltas를 한 global commitment에 결정적으로 join할 수 있을 때만 확장한다. Multi-key transaction을 서로 다른 certificates로 쪼개면 안 된다.

### 3.3 Finality predicate

```text
StateFinal(C, R')
  iff CutFinal(C)
      AND ValidExecutionCertificate(C, R')
```

Candidate cut에 대해 execution vote를 미리 만들 수 있지만, 해당 cut이 ordering-final이 되기 전에는 canonical state를 apply하지 않는다. 다른 cut이 확정되면 candidate computation과 vote를 폐기하며 canonical rollback은 없다.

## 4. Quorum-size correction

### 4.1 Execution electorate가 `N_e = 3f+1`인 경우

```text
q_exec = 2f+1
```

두 QCs의 교집합은 최소 `f+1`이고, 그 안에 honest signer가 적어도 한 명 있다. Honest validator가 같은 `(cut, parent, component)`에 서로 다른 roots를 서명하지 않으면 conflicting execution QCs가 공존할 수 없다.

정상 경로에서는:

```text
f+1 DA holders re-sign as ExecVote
+ f additional ExecVotes
= 2f+1 ExecQC
```

그러나 DA set에 `f` Byzantine signers가 있고 이들이 withholding하면 최초 set에서 honest vote는 한 개뿐일 수 있다. 이 최악 경로에서는 외부에서 `2f` votes가 더 필요하다. 따라서 요청 대상을 고정된 추가 `f`명으로 제한하면 안 되고 모든 eligible validators가 fallback voters여야 한다.

### 4.2 Multimmit 전역 `N = 5f+1`인 경우

전역 `2f+1` sets는 honest intersection을 보장하지 않는다. Intersection-based global execution QC는 다음을 만족해야 한다.

```text
2q_exec - N >= f+1
q_exec >= ceil((N+f+1)/2) = 3f+1
```

따라서 선택지는 두 가지다.

1. **Global mode:** `5f+1` 전체에서 `3f+1 ExecVotes`를 모은다. `f+1` DA fast set에서 정상적으로 시작해도 `2f` votes가 더 필요하다.
2. **Committee mode:** 이전 finalized randomness로 cut별 `3f+1` execution committee를 정하고 그 안에서 `2f+1 ExecVotes`를 모은다. Committee 안의 faults도 최대 `f`이므로 위의 정상 경로 산술을 사용할 수 있다.

본 아이디어의 `f+1 -> +f -> 2f+1` fast path를 Multimmit에 그대로 쓰려면 **committee mode가 더 깔끔하다.** Producer는 계속 모든 validators에게 block을 broadcast하되, execution warm set으로 쓸 `f+1` input-availability acknowledgements는 해당 execution committee에서 우선 수집한다. Ordering quorum은 변경하지 않는다.

단, 기존 ordering DA certificate의 signers가 committee 밖에 있으면 그 certificate를 그대로 warm set으로 셀 수 없다. Committee mode에서는 다음 중 하나를 명시해야 한다.

- DA vote 중 committee members의 votes만 `ExecutionWarmSet`에 센다.
- Ordering DA와 병렬로 committee 내부 `f+1` input-availability acknowledgements를 모은다. 이 acknowledgements는 ordering의 선행조건으로 만들지 않는다.

DA signer set `D`, 그 안의 Byzantine signer 수를 `b`, execution threshold를 `q_exec`이라 하면, 실제로 upgrade하는 honest DA signers는 최악에 `f+1-b`명이다.

| Mode | `q_exec` | 모든 DA signers가 upgrade할 때 DA set 밖 추가 | `b=f` withholding 때 DA set 밖 추가 |
|---|---:|---:|---:|
| `3f+1` electorate/committee | `2f+1` | `f` | `2f` |
| global `5f+1` electorate | `3f+1` | `2f` | `3f` |

어느 경우든 DA-only signatures 자체는 `q_exec`에 포함되지 않는다. 표는 DA signers가 이후 exact `(ExecKey, ExecValue)`에 새 `ExecVote`를 발행한다는 뜻이다.

Validity proof가 deterministic unique result를 객관적으로 증명한다면 quorum intersection 없이도 correctness를 얻을 수 있다. 그 경우 `2f+1`은 execution consensus QC가 아니라 readiness/replication support이고, correctness는 proof가 담당한다고 표현해야 한다.

## 5. Conflict objective

Transaction `x`의 statically known sets를 `R(x), W(x)`라고 한다.

```text
Conflict(x,y) iff
  W(x) intersects (R(y) union W(y))
  OR W(y) intersects (R(x) union W(x))
```

실제 conflict edge `e=(x,y)`의 예상 repair cost를 `c_e >= 0`, routing assignment를 `a(x)`라고 하면 줄여야 할 값은 다음이다.

```text
CrossLaneCost(a)
  = sum_{e=(x,y)} c_e * 1[a(x) != a(y)]
```

이 최적화는 load constraint가 있는 weighted graph/hypergraph partitioning이므로 일반적으로 exact online solution을 기대하기 어렵다. 제안은 global pending graph 없이도 deterministic하게 동작하는 locality-sensitive approximation을 사용한다.

## 6. Weighted conflict-affinity routing

### 6.1 Deterministic footprint vector

Finalized history까지만 사용해 key `k`의 deterministic hotness를 계산한다.

```text
h_e(k) = 1 + EWMA_finalized(
  write_frequency(k) * median_repair_cost(k)
)
```

Transaction `x`의 non-negative weighted footprint는 다음처럼 둔다.

```text
w_x(k) = h_e(k) * mode_weight_x(k)

mode_weight_x(k) = alpha  if k in W(x)
                   beta   if k in R(x) \ W(x)
                   0      otherwise

alpha > beta >= 0
```

Write/hot-key에 큰 weight를 주어 많은 부수 read keys가 중요한 conflict key를 희석하지 않게 한다. Read-only traffic은 별도 load-balanced path로 보내거나, 해당 key의 observed write frequency에 비례해 `beta`를 정한다.

모든 routers는 같은 finalized epoch statistics와 shared routing seed를 사용한다.

### 6.2 Consistent weighted sample

두 transactions의 weighted Jaccard similarity를 다음처럼 정의한다.

```text
J_w(x,y)
  = sum_k min(w_x(k), w_y(k))
    / sum_k max(w_x(k), w_y(k))
```

Consistent Weighted Sampling(CWS)으로 전체 sample `S(x)=(k,t)`를 만든다. CWS의 성질은 다음과 같다.

```text
Pr[S(x) = S(y)] = J_w(x,y)
```

Sample의 key만 사용하지 않고 **전체 `(k,t)` sample**을 사용해야 한다. 그 뒤 epoch-seeded rendezvous hash로 producer lane을 고른다.

```text
anchor_x = CWS(route_seed_e, w_x)
lane_x   = WeightedRendezvous(epoch, anchor_x, lane_capacities)
```

같은 anchor는 한 routing window 동안 반드시 같은 lane에 붙인다. Transaction마다 별도 load-aware choice를 하면 아래 확률 보장이 깨진다.

### 6.3 Expected conflict reduction

`L` lanes가 균등하고, 서로 다른 anchors의 lane hashes가 독립·균등하다고 가정하면:

```text
Pr[lane(x) != lane(y)]
  = (1 - J_w(x,y)) * (1 - 1/L)
```

같은 CWS sample이면 sticky mapping 때문에 반드시 같은 lane이다. Samples가 다를 확률은 `1-J_w`이고, 서로 다른 samples의 independent lane hashes가 다를 조건부 확률은 `1-1/L`이므로 두 항을 곱한다.

Uniform random routing은 `1 - 1/L`이므로 affinity routing은 pairwise cross-lane probability를 `1-J_w` 배로 낮춘다.

Lane selection probability가 `p_l`인 capacity-weighted case에서는:

```text
Pr[lane(x) != lane(y)]
  = (1 - J_w(x,y)) * (1 - sum_l p_l^2)
```

따라서 conflict graph 전체에 대해:

```text
E[C_random]
  = (1 - 1/L) * sum_e c_e

E[C_affinity]
  = (1 - 1/L) * sum_e c_e * (1 - J_e)

relative expected reduction
  = sum_e(c_e * J_e) / sum_e(c_e)
```

모든 실제 conflict edge에서 `J_e >= gamma`라면 uniform random routing보다 기대 cross-lane repair cost가 최소 `gamma` 비율만큼 감소한다. 이 결과는 edge들 사이의 독립성을 요구하지 않고 expectation의 선형성만 사용한다.

이것은 fixed seed의 모든 workload에 대한 worst-case 보장이 아니다. Epoch seed 또는 random-oracle choice에 대한 expected bound다.

### 6.4 Load balance and overflow

- Base scheme은 capacity-weighted rendezvous hashing으로 `p_l`을 lane capacity에 비례시킨다.
- 동일 anchor bucket은 개별 transaction 단위로 쪼개지 않는다. Epoch boundary에서 finalized load statistics로 bucket mapping을 갱신한다.
- 한 hot component 자체가 한 lane capacity보다 크면 perfect affinity와 perfect balance를 동시에 달성할 수 없다.
- Hard limit을 넘은 anchor만 secondary sample로 split하거나 post-cut repair path로 보낸다. 이 fallback에는 위의 conflict-reduction bound가 그대로 적용되지 않음을 명시한다.
- Global fee/account bookkeeping key처럼 모든 transaction이 형식적으로 공유하는 key는 semantics상 commutative하거나 별도 집계 가능한 경우에만 footprint에서 분리한다. 실제 serialization dependency라면 제외할 수 없다.

## 7. Propagation and quorum promotion

### 7.1 Input path

```text
signed transaction
  -> derive static R/W footprint
  -> calculate CWS affinity anchor
  -> route to deterministic producer lane
  -> broadcast block and collect f+1 InputAvailVotes
  -> lane-order speculative execute in parallel
  -> broadcast EffectNode sidecar when ready
```

Routing은 consensus safety rule이 아니라 deterministic dissemination policy다. Misrouted transaction은 canonical routing metadata로 거부하거나 deterministic no-op 처리해야 한다. Over-declaration/grinding을 막기 위해 footprint는 application schema에서 derivation하고 declared access bytes와 execution work에 비용을 부과한다.

### 7.2 Warm-set promotion

`D`를 `f+1` DA signers라고 하자. Artifact는 모든 validators에게 announce하되 다음 recipients에게 full bundle을 먼저 push한다.

```text
PriorityRecipients(C, component)
  = D
    union TopRankedEligibleValidators(
        execution_electorate \ D,
        cut_candidate,
        component_anchor,
        required_count)
```

- `3f+1` execution electorate에서 normal fast path의 `required_count = f`다.
- 이 recipient set은 latency optimization이지 exclusive committee가 아니다.
- Full bundle announce/fetch와 `ExecVote` 요청은 모든 eligible validators에게 열려 있어야 Byzantine DA signers의 withholding이 liveness를 막지 않는다.
- Ranking은 previous finalized randomness와 rendezvous hash로 deterministic하게 정한다. 같은 affinity component를 자주 검증하는 validators에게 witness/cache locality를 줄 수 있지만 safety에는 사용하지 않는다.

### 7.3 Candidate-cut pipelining

Leader proposal이 candidate cut `C*`를 제시하면 DA holders와 priority recipients는 ordering commit을 기다리지 않고 다음을 background에서 수행한다.

1. Missing effect bundles와 read witnesses를 fetch한다.
2. `C*`의 exact canonical order를 계산한다.
3. Reusable effects와 stale effects를 구분한다.
4. Stale dependency closure만 re-execute한다.
5. Exact `(ExecKey(C*), ExecValue(C*))`에 `ExecVote`한다.

`C*`가 그대로 finalized되면 execution certificate가 이미 준비되어 cut-to-state latency가 작아진다. 다른 cut이 finalized되면 votes는 branch-specific cache로만 남고 canonical effect는 없다. Ordering vote는 execution readiness를 기다리지 않는다.

## 8. Cut reconciliation

Finalized cut `C`의 canonical order에서 transaction `t_i`의 speculative effect는 다음 조건을 만족할 때만 그대로 재사용한다.

```text
Reusable(t_i, C) iff
  effect.parent_finalized_root == canonical_parent_root
  AND every read observation of t_i equals
      the version/value produced by its canonical predecessor in C
  AND code/environment commitments match
```

Reusable하지 않은 transaction을 dirty로 표시하고, 그 output을 읽은 descendants까지 fixed point로 확장한다. Dirty closure만 canonical order로 re-execute한다. 다른 effects는 그대로 채택한다.

```text
dirty := directly_stale_effects(C)
repeat
  dirty := dirty union dependents_of(dirty)
until fixed_point

reexecute dirty in canonical order
vote on exact (ExecKey, ExecValue)
```

단순히 같은 output root가 여러 번 보였다는 이유로 채택하면 안 된다. 예를 들어 두 lanes가 모두 `x=0`을 읽고 `x := x+1`을 실행하면 둘 다 `x=1`을 제시하지만 canonical serial result는 `x=2`다. Exact read-from context와 cut-relative revalidation이 필수다.

## 9. Example

`L=4`, unweighted footprints가 다음과 같다고 하자.

```text
X = {AliceBalance, AliceNonce}
Y = {AliceBalance, AliceCollateral}
```

`J(X,Y)=1/3`이다.

```text
random routing:
  Pr[different lanes] = 1 - 1/4 = 0.75

affinity routing:
  Pr[different lanes] = (1 - 1/3) * 0.75 = 0.50
```

이 pair의 cross-lane conflict probability는 `0.75 -> 0.50`, 즉 약 33.3% 감소한다. Footprints가 동일하면 `J=1`이어서 항상 같은 lane에 가고, disjoint이면 `J=0`이어서 random routing과 같아 load distribution을 유지한다.

`n_e=4`, `f=1` execution electorate에서는:

```text
DA holders: V1, V2
normal path: V1 + V2 ExecVotes, then V3 or V4 -> 3 = 2f+1

if V2 is Byzantine and withholds:
  V1 + V3 + V4 -> 3
  DA set 밖에서 f가 아니라 2f votes가 필요
```

## 10. Safety and liveness conditions

### Safety

- Finalized cut과 exact parent root가 다른 execution votes는 합칠 수 없다.
- Multi-key transaction의 entire effect는 한 component digest 안에서 atomic하게 인증한다.
- Honest voter는 같은 `(cut, parent, component, code_version)`에 conflicting roots를 서명하지 않는다.
- Producer-supplied DAG omission은 validators가 static footprint와 dynamic read observations로 재검사한다.
- Equivocated sidecars, stale roots, replayed votes와 wrong-code results는 digest binding으로 거부한다.
- State apply는 `CutFinal AND ExecQC` 뒤에만 수행한다.

### Liveness

- DA와 execution requests는 first-recipient set에 국한하지 않는다.
- Candidate-cut execution failure는 ordering progress를 막지 않는다.
- Missing artifact는 known DA signers에게 digest-addressed fetch하고, unavailable/invalid speculative effects는 canonical re-execution한다.
- Dirty component width, re-execution work, pending cuts와 overlay bytes를 제한한다.
- Hot component가 bound를 넘으면 그 component만 sequential post-cut fallback으로 보내고 disjoint components는 계속 진행한다.
- Failover는 local wall-clock이 아니라 finalized-cut count 또는 ordering view progress로 결정한다.

## 11. Evaluation plan

비교 대상:

1. Uniform random transaction-to-lane routing.
2. Key-hash routing using one fixed key.
3. CWS conflict-affinity routing.
4. CWS + capacity-weighted sticky rendezvous routing.
5. Oracle balanced min-cut for small offline traces. 이는 optimality gap을 측정하는 용도다.

변수:

- lane count와 capacity skew.
- read/write footprint size와 declared-access over-approximation.
- Uniform/Zipf hot-key access.
- Conflict density와 connected-component width.
- `alpha/beta`, hotness EWMA window와 epoch length.
- Byzantine DA signer withholding, slow voters와 sidecar loss.
- Candidate cut hit rate와 cut change rate.

핵심 metrics:

```text
cross_lane_conflict_weight
stale_effect_ratio
reexecuted_tx_count and reexecution_gas
dirty_closure_width
lane_load_p50/p95/max and imbalance
DA_to_ExecQC_latency
additional_votes_after_DA
ExecQC_ready_at_cut_ratio
cut_to_state_latency
```

검증할 수학적 prediction:

```text
observed cross-lane conflict ratio
  ~= random baseline * conflict-weighted mean(1 - J_e)
```

## 12. Positioning

- Autobahn의 `f+1` PoA는 적어도 한 honest holder가 있음을 보장하는 availability mechanism이다. 본 제안은 그 holder set을 cut-relative execution voter warm set으로 재사용하지만 statement를 혼합하지 않는다.
- Consistent Weighted Sampling은 weighted-Jaccard에 비례한 collision probability를 제공하는 기존 locality-sensitive technique다.
- Conflict graph scheduling과 balanced partitioning도 기존 분야다.
- 따라서 개별 primitive를 novelty로 주장하지 않는다.

가능한 논문 기여 표현은 다음 조합에 둔다.

> Autobahn-family multi-producer ordering에서 global state ownership을 사전에 고정하지 않고, access-footprint similarity에 비례해 speculative conflicts를 같은 producer stream으로 모으는 deterministic propagation과, `f+1` availability holders를 cut-bound execution electorate로 승격해 candidate-cut reconciliation을 ordering과 겹치는 end-to-end execution-finality path.

이 claim은 prototype에서 CWS expected bound, load-balance trade-off, DA-to-ExecQC best/worst path와 cut-relative safety를 모두 검증한 뒤에만 사용한다.

## References

- Autobahn: Seamless High-Speed BFT, SOSP 2024: <https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf>
- Sergey Ioffe, Improved Consistent Sampling, Weighted Minhash and L1 Sketching, ICDM 2010: <https://research.google.com/pubs/archive/36928.pdf>
- Multimmit: Extending Blocks for Faster Finality: <https://arxiv.org/abs/2607.21021>
- Eve: Execute-Verify Replication for Multi-Core Servers, OSDI 2012: <https://www.cs.cornell.edu/lorenzo/papers/Kapritsos12All.pdf>
- On the Efficiency of Dynamic Transaction Scheduling in Blockchain Sharding, DISC 2025: <https://drops.dagstuhl.de/storage/00lipics/lipics-vol356-disc2025/LIPIcs.DISC.2025.2/LIPIcs.DISC.2025.2.pdf>
