# Block-view synthesis: small-model results

> 2026-09-18 · synthetic unit-work experiment, **not a blockchain E2E benchmark**
>
> Design: [block-selected-view-protocol.md](./block-selected-view-protocol.md)
> Runner: [research/block_views/experiment.py](./research/block_views/experiment.py)

## 1. What was run

```sh
python3 -B -m unittest discover -s research/block_views -v
python3 -B research/block_views/experiment.py --trials 30
```

- 6 validators, 6 producer lanes, one selected block per lane.
- Fault bound f=1, state-result quorum q=4.
- 5 honest validators; validator 6 advertises a reverse-order, all-executed report
  and then contributes no result vote. This is one attack pattern, not an exhaustive adversary.
- 2 simulated execution workers per validator, one execution-time unit per block.
- Each honest validator sees each block independently with probability 0.8 before the cut.
- Shared-key selection probabilities: 0, 0.5, 1; seeds 0–29 for each setting.
- Every operation is a statically known `add` or `copy`. Observed RW/WW block-pair conflict
  fractions are 0%, 20.22%, and 77.56%. Shared read/read access is not a conflict.
- Adaptive search uses beam width 8 and exact-search limit 0. The algorithm's general defaults
  are different and must not be confused with these benchmark settings.
- Pre-cut execution is allowed to finish after each observed arrival. Rank mode revalidates
  its overlay when an earlier-ranked block arrives; repeated work is counted separately.
- For every mode, every honest node's repaired result must match fresh execution of that
  mode's exact selected plan. Results need not match across different serialization rules.

Unit-worker scheduling is simulated on the residual DAG. Metadata fetch, cache validation,
hashing, synthesis, voting, network and durable apply have **zero cost in that timing metric**.
Consequently these numbers cannot be presented as milliseconds, measured finality, or a TPS gain.
Also, a correctly executing node need not wait for an extra result quorum merely to know its
own state after canonical ordering. Quorum-ready time and local state readiness are different
service metrics; requiring an externally verifiable result certificate is an explicit design choice.

## 2. Remaining execution rounds until four honest validators finish

Mean over the 30 seeds. Lower is better.

| Pre-cut execution / final order | No conflicts | Moderate conflicts | High conflicts |
|---|---:|---:|---:|
| None / fixed rank | 3.0000 | 3.4000 | 5.2000 |
| Arrival order / fixed rank | 1.1667 | 2.3000 | 4.7000 |
| Common rank / fixed rank | 1.1667 | 1.4667 | 3.3667 |
| Arrival order / SelectedView | 1.1667 | 2.0000 | 4.3000 |
| Common rank / SelectedView | 1.1667 | 1.4333 | 3.2000 |

The strongest improvement in this experiment comes from aligning pre-execution with a
common rank. Adaptive selection provides a smaller additional improvement, not the whole gain.
Independent blocks benefit from pre-execution but not from view synthesis.

## 3. Recovery work is different from latency

Mean blocks per honest validator. “Post-cut rerun” excludes blocks never observed before the cut.

| Mode | Moderate: post-cut rerun | High: post-cut rerun | High: extra pre-cut rerun |
|---|---:|---:|---:|
| Arrival / fixed | 1.1867 | 3.4267 | 0.0000 |
| Rank / fixed | 0.1667 | 1.0467 | 2.2667 |
| Arrival / selected | 0.8800 | 2.9200 | 0.0000 |
| Rank / selected | 0.2200 | 1.2800 | 2.2667 |

Two important qualifications:

1. Common rank moves some recovery **before** the cut. Count total execution work, not only
   post-cut reruns, or the evaluation would hide that cost. With a finite CPU budget, this work
   can interfere with preparation for subsequent cuts.
2. SelectedView can finish a quorum earlier while doing more reruns overall. The slowest relevant
   dependency path matters; maximizing cache-hit count is not the same optimization problem.

Adaptive selection is also not a per-case improvement guarantee:

- Moderate setting, rank/selected versus rank/fixed: 1 better seed, 29 ties.
- High setting: 7 better seeds, 21 ties, **2 worse seeds** (6 and 14, one extra round each).

The score is based on declared readiness and a conservative read-history estimate, with a
unit-work critical-path lower bound. It does not know the actual future elapsed time. A false
report can affect efficiency even though it cannot supply trusted state or break result agreement.

## 4. What changed during validation

The initial cache policy required an identical predecessor graph. Tests showed that this
unnecessarily discarded blind writes and unchanged-value reads. The current model validates
the actual read inputs before rerunning a block, and the selection estimate tracks read-key
writer histories rather than every ordering ancestor.

Additional counterexamples covered:

- Per-key choices can create a cycle when combined with lane order.
- A payload-ID tie-break can undo a rank rule intended to avoid hash grinding.
- A made-up block reference in a report must not create a new DA-fetch obligation.
- Reusing a previously successful transfer after an earlier debit must not leave its old credit.
- An unchanged direct writer ID does not prove its transitive input values are unchanged.

The current suite has 32 tests, including 40 seeded six-block cases with worker-schedule
enumeration and an independent serial interpreter. Passing these tests is not a formal proof
or validation of a deployed Byzantine network.

A closed-input flow test connects view selection, five honest cache repairs, one forged result
and quorum formation. A separate test demonstrates that two **different candidate subjects**
can both collect valid result quorums. Only ordering can decide which candidate is canonical;
result quorum intersection is not a substitute for the input-closure rule.
Another test enumerates all 49 combinations of a Byzantine node's three-block observed-order
and executed-prefix claims, and checks all five honest cache repairs against the independent
serial interpreter. This exhausts that small claim space, not all network or protocol attacks.
A separate process-level spot check varied `PYTHONHASHSEED` across 1, 2 and 42 and constructed
the block store through a set; identical committed view bytes produced the same selected root.

## 5. Selection overhead is a separate risk

A development profiling run of the straightforward Python search, before adding its no-evidence
fast fallback, used six lanes, shared-key updates, no reports and beam width 16:

| Blocks | Prefixes expanded | Observed local synthesis time |
|---|---:|---:|
| 6 | 196 | 18.786 ms |
| 12 | 715 | 144.939 ms |
| 24 | 1,866 | 1,550.279 ms |

These are single local timing samples from an unoptimized model, not a protocol latency
benchmark. They motivated the current immediate fallback when the closed snapshot has no more
than f prepared reporters. They also show why bounded search and candidate-stage overlap are
necessary. The fallback does not eliminate this cost when adaptive search is actually enabled.

An implementation should avoid recomputing access sets and read histories for every candidate,
measure synthesis separately, and reject claims that save 1 ms of execution by spending 10 ms
selecting a plan. No optimized implementation or such millisecond trade-off has been measured here.

## 6. Next experiments needed for a paper

1. **Real baseline:** native Multimmit ordering with fixed-order execution on the same hardware,
   application, payloads and arrival traces. Preserve actual block admission and signature costs.
2. **Ablations:** cut-only; arrival/fixed; rank/fixed; rank/selected; candidate-stage preparation;
   read-validation on/off. Do not attribute pre-execution's gain entirely to view synthesis.
3. **Timing:** first block receipt, candidate receipt, selected-plan ready, ordering finalized,
   state-result quorum, durable apply and read readiness. Report p50/p95/p99 and end-to-end latency.
4. **Work:** initial execution, pre-cut repeated execution, post-cut newly executed versus rerun
   blocks, validation cost, selected-plan synthesis, memory and report bandwidth.
5. **Load/structure:** blocks per cut, transactions per block, read/write mix, hot-key skew,
   lane count, producer skew, rank inversions, missing-data rate and dependency-path length.
6. **Faults:** conflicting reports, dishonest progress claims, withholding, slow leaders,
   omitted report opportunities, unavailable state and changing candidate cuts.
7. **Prefix integration:** prove/test the unique selection-input closure rule on native
   Multimmit compatible emitted prefixes. Include partial-window closure delay in the metrics.
8. **Total capacity:** test sustained load and backlog recovery. A lower cut-to-state tail achieved
   by increasing duplicate execution is not automatically a throughput improvement.

Current conclusion: use common-rank pre-execution and input-validated reuse as the core;
retain deterministic adaptive selection as a bounded, measurable optimization. Its production
benefit and the full ordering-to-state latency reduction remain hypotheses to test.
