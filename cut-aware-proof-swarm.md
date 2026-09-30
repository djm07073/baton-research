# Cut-Aware Proof Swarm

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 목적

Consensus-free validity refinement가 proof의 next-cut wait를 제거해도 proof generation 자체가 늦으면 state frontier는 뒤처진다.

```text
T_state-finality
  >= T_validity-proof-ready
```

한 lane owner/prover가 execute + prove + fold를 순차 수행하는 대신, proposal-relative candidate path의 proof tasks를 여러 permissionless
workers가 병렬 생성하고 recursive proof forest로 합친다.

핵심 차별화 후보는 generic distributed proving이 아니라 **Multimmit partial vote support가 알려주는 cut likelihood/inevitability에 따라 proving
priority와 redundancy를 조절하는 것**이다.

## 2. Proof task graph

Lane `i`의 candidate path:

```text
R0 --B1--> R1 --B2--> ... --Bd--> Rd
```

Leaf task:

```text
LeafTask(i,h) {
  exact block B_h,
  pre_root R_(h-1),
  post_root R_h,
  statement/effect commitment,
  execution/proof-system version
}
```

Merge task:

```text
MergeTask(i,a,m,b) {
  left proof  [a,m],
  right proof [m+1,b],
  require left.post_root = right.pre_root,
  output proof [a,b]
}
```

Canonical task ID:

```text
TaskId = H(epoch, lane, interval, exact block sequence,
           pre/post roots, proof system/version)
```

Proof bytes는 self-authenticating하므로 여러 workers가 같은 task를 중복 수행해도 safety voting이 필요 없다.

## 3. Critical path

Block `h`의 witness가 준비되는 시점을 `W_h`, leaf proving 시간을 `P_h`, merge 시간을 `M`이라고 하자.

One sequential prover/fold:

```text
T_seq(h) ~= W_h + sum_{j=1..h} Fold_j
```

Enough parallel workers와 binary aggregation:

```text
T_swarm(h)
  ~= max_{j<=h}(W_j + P_j)
     + ceil(log2 h) * M
```

Execution/witness discovery가 lane state dependency 때문에 sequential하면 `W_h`는 제거할 수 없다. 그러나 earlier leaf proving은 later block
execution과 overlap하고 leaf proofs 간 proving은 병렬화할 수 있다.

Effect-mode에서 dependency-disjoint objects를 사용하면 witness generation도 component별로 병렬화할 수 있다. Prefix mode에서는 proving만
parallel이고 lane execution은 sequential이다.

## 4. Multimmit-aware priority frontiers

Local arrival-first vote pool `P_t`에서 lane `i`, position `h`를 지지하는 vote 수를 `support_t(i,h)`라고 하자.

### 4.1 Speculative frontier

DA-certified/held candidate blocks 전체다. Canonical cut에 들어갈지는 아직 모른다.

```text
Speculative_i(t) = highest held connected candidate
```

### 4.2 Carry frontier

Multimmit의 safe extension support와 관련된 `f+1` support를 가진 path다. Finality가 보장된 것은 아니지만 단일 producer announcement보다
stronger demand signal이다.

```text
Carry_i(t) = max h with support_t(i,h) >= f+1
```

### 4.3 Locally inevitable frontier

현재 pool의 already-admitted votes 중 `3f+1`가 `h` 이상을 지지하면, 그 exact votes를 포함해 pool을 `4f+1`로 완성하는 local finality
transcript에서 `h`는 drop-`3f` rule을 통과한다.

```text
Inevitable_i(t) = max h with support_t(i,h) >= 3f+1
```

중요:

- 이 guarantee는 현재 local pool의 admitted supporters를 보존하는 exact completion에 상대적이다.
- 다른 replica의 first-arrival pool이 같은 height를 선택한다고 보장하지 않는다.
- Protocol safety fact가 아니라 local proving scheduler signal이다.

## 5. Scheduling policy

Priority tiers:

```text
P0: proof gaps at/below Inevitable frontier
P1: connected tasks at/below Carry frontier
P2: remaining held proposal-prefix tasks
P3: equivocated/non-voted branches
```

Redundancy:

```text
P0: primary + r backups
P1: one primary, backup after logical-view deadline
P2: best-effort marketplace
P3: no proving unless canonicality evidence improves
```

Task assignment is deterministic but proof submission is permissionless.

```text
rank(TaskId, prover) = RendezvousHash(previous_final_evidence, TaskId, prover)
```

The ranking only avoids duplicate work. Any valid proof is accepted, so assignment failure does not affect safety or permanently exclude takeover.

## 6. Pipeline

```text
block/DA arrives
  -> execute and expose witness/effect statement
  -> create leaf proof task
  -> speculative worker starts

proposal/votes arrive
  -> update Carry/Inevitable frontiers
  -> raise priority and spawn backups for likely final prefix

proofs complete
  -> recursively merge available adjacent intervals
  -> gossip proof artifact
  -> objective verification / f+1 verified custody

ordering cut arrives
  -> select exact proof cover
  -> refine evidence-closed state ideal
```

Proof readiness never gates Multimmit vote reservation.

## 7. Cross-lane tasks

Cross operation `X` can use:

1. Participant-local effect proofs plus one joint predicate proof
2. One joint proof covering all participant effects

Joint task ID binds:

```text
attempt_id
manifest/DCLP digest
all participant exact blocks/input versions
all prepared effect commitments
joint application predicate
```

Joint proving priority is the minimum readiness of participant blocks and predecessor components. A single participant lag cannot be hidden by proving other
fragments repeatedly.

## 8. Incentives and stealing

Proof artifact may bind a payout key and maximum fee in its public input/signature-of-knowledge wrapper. This prevents a peer from copying a proof and
claiming the worker reward.

Suggested policy:

- Original transaction reserves proof budget/bond.
- First accepted valid artifact for a TaskId earns base reward.
- Backups earn only after consensus-visible logical deadline or primary failure evidence.
- Duplicate valid proofs without authorized backup status receive no reward.
- Invalid proof consumes submitter bond and verification gas.

Economic policy is not safety-critical and should be separated from protocol theorem claims.

## 9. Attacks and limitations

### Byzantine task withholding

Deterministic assignee can withhold, but permissionless takeover and multiple P0 backups preserve liveness if public witness reconstruction is possible.

### Witness monopoly

If only the lane producer can reconstruct private witness, proof swarm does not work. Original block/DA must expose sufficient trace/effect data or use a
threshold witness escrow. Public-state execution should allow any validator/prover to reconstruct.

### Expensive valid-work spam

Adversary can create many expensive candidate branches or transactions that never finalize.

Mitigation:

- Per-block proving gas
- Transaction-funded proof bond
- P0/P1 priority based on authenticated vote support
- Per-view speculative proof budget
- Bounded fork/task cache

### Sequential witness bottleneck

Hot state or a long dependency chain keeps `W_h` sequential. More provers cannot beat application dependency depth.

### Merge bottleneck

If recursive merge proving is expensive, `log h * M` or a centralized final aggregator remains critical. Distributed aggregation protocols may help but add
network coordination.

### Different local cut predictions

Replicas can prioritize different proof tasks. This wastes work but does not create conflicting state because proofs bind exact paths and final join checks the
actual ordering cut.

## 10. Related-work boundary

- [Mina parallel scan state](https://minaprotocol.com/wp-content/uploads/2021/01/technicalWhitepaper.pdf)는 block production과 SNARK work queue를 분리하고 workers가 transaction proofs를 병렬 생성·merge한다.
- [Mina Snarketplace](https://minaprotocol.com/blog/what-are-snark-workers-and-the-snarketplace)는 permissionless proof workers와 proof-bound rewards를 사용한다.
- [Snarktor](https://eprint.iacr.org/2024/099.pdf)는 여러 ZK proofs의 recursive aggregation work를 decentralized servers에 분배한다.
- [GIGA](https://eprint.iacr.org/2025/645.pdf)는 non-conflicting transaction batches를 병렬 execute/prove하고 block proof로 recursive aggregate한다.
- [Hekaton](https://www.cs.umd.edu/~imiers/pdf/HEKATON.pdf)은 horizontally scalable proving과 aggregation을 다룬다.

따라서 다음은 novelty가 아니다.

- Parallel leaf proving
- Binary recursive aggregation
- Permissionless SNARK workers/marketplace
- Deterministic task assignment

남는 차별점 후보:

1. Multimmit proposal-relative cut의 불확실성을 proof-task forest로 표현한다.
2. Partial proposal-relative vote support의 `f+1/3f+1` frontiers를 proving priority/redundancy signal로 사용한다.
3. Proof artifacts를 후속 block/work queue state에 반드시 포함하지 않고 already-final cut의 state ideal에 late-bind한다.
4. Cross-lane proof tasks를 DCLP-bound atomic hypernodes로 scheduling한다.

이 조합의 직접 대응은 현재 조사에서 찾지 못했지만, 구성요소 선행연구가 강하므로 main novelty보다 systems optimization contribution으로
두는 것이 안전하다.

## 11. Evaluation

Baselines:

```text
B0 one prover, sequential folding
B1 Mina-like FIFO parallel scan queue
B2 proof forest without vote-aware priorities
B3 Cut-Aware Proof Swarm
B4 B3 + f+1 asymmetric proof custody
```

Variables:

```text
workers
lane count and path depth
proof leaf/merge cost
validator response heterogeneity
proposal equivocation/abandon rate
cross-lane fanout and dependency depth
proof gas budget
```

Metrics:

```text
proof-ready-before-cut ratio
T_cut_to_event-state-final p50/p95/p99
proof critical path
worker utilization
useful/wasted proving work
duplicate proof ratio
takeover recovery latency
merge-tree backlog
ordering CPU/network regression
```

Success requires B3 to improve proof-ready-at-cut and cut-to-state tail latency over B1/B2 at comparable total proving work. If it only spends more redundant
compute to win latency, the cost/latency Pareto frontier must be reported rather than claiming unconditional scalability.

## 12. 현재 판단

1. Distributed proving alone is heavily covered by Mina, Snarktor, GIGA and distributed SNARK research.
2. Multimmit vote-aware proving priority is plausible but is an optimization, not a new correctness primitive.
3. The strongest use is to increase same-cut proof readiness for Consensus-Free Validity Refinement.
4. It should remain optional until a simulator shows that the `3f+1 -> 4f+1` vote-arrival window or reduced speculative waste is material.
