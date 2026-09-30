# Load-aware grouping: avoiding a giant independent component

Research update, 2026-09-25. Read with [the independence specification](independent-placement-spec.md). This note evaluates alternatives; it does not silently replace the implemented whole-component algorithm or introduce a new consensus phase.

## Problem

Zero cross-producer conflicts is insufficient as a performance objective: putting the entire workload on one producer achieves it trivially. Large groups can increase admission queues and reduce production parallelism enough to outweigh saved reexecution.

The placement weight is **execution frequency times cost per execution**, not the number of state keys in a group. A large, rarely used state group can be cheap; a one-key group invoked constantly can be the hotspot. Structural group size matters only insofar as it changes actual processing or resource costs.

For a common observation window of duration `H`, define:

```text
N_g      = number of transaction executions attributed to group g
mean_c_g = mean estimated cost per attributed execution
work_g   = N_g * mean_c_g = sum(cost(t), t attributed to g)
rate_g   = work_g / H
load_p   = sum(rate_g, g assigned to producer p)
```

With unit transaction costs, `N_g` alone is the frequency-based baseline. With heterogeneous transactions, use profiled costs or explicitly labeled proxies such as gas. If producers have different relevant capacities, compare `load_p / capacity_p`, not raw work alone. Producer queue/byte capacity and execution capacity need not have the same bottleneck.

Count a transaction once when several of its accesses belong to the same group. Transactions spanning groups are charged once to their selected producer or residual path; duplicating their full cost into every touched group would inflate total work. Their multi-group interaction is retained separately in the conflict model. Base execution demand excludes retries; add measured or modeled retry work separately to evaluate the placement's benefit.

For example, suppose groups A, B and C contain 1,000, 10 and 10 state keys, respectively, but receive 10,000, 100,000 and 90,000 unit-cost executions in the same window. Assigning B to one producer and A+C to another gives 100,000 versus 100,000 units of base work. Balancing the number of state keys would not capture this demand.

Estimate these frequencies from finalized history for a prospective map and test on later windows; do not use future demand in a claimed online policy. Recompute transaction attribution for candidate merges/splits rather than summing overlapping historical group counts. This metric is supported by the reference planner's additive transaction-cost input, but historical estimation and adaptive regrouping are not implemented by that planner.

In a replicated-execution architecture, placement does not mean that only the assigned producer executes a transaction. All executing validators may still process all selected transactions. Measure producer admission/production skew separately from per-validator total execution and reexecution work. Database shard-throughput formulas cannot be imported without this distinction.

## Relevant evidence

| Work | Mechanism relevant here | Boundary of applicability |
|---|---|---|
| [Strife, SIGMOD 2020](https://homes.cs.washington.edu/~suciu/guna-sigmod-2020-pdfa.pdf), §§2–3 | Avoids merging all transactions because of a few connecting transactions. Builds conflict-free clusters and leaves residual transactions for a separate concurrency-controlled phase. It explicitly discusses skewed cluster sizes and uses work sharing across clusters. | Its synchronized phases are not a nonblocking blockchain protocol; work sharing does not split one intrinsically hot dependency chain. |
| [TxAllo, ICDE 2023](https://arxiv.org/html/2212.11584v1), §§IV–VI | Models capacity and cross-shard workload, initializes with Louvain and improves the allocation using throughput gain. Provides Ethereum-based simulation and discusses overloaded hot accounts. | Account/shard allocation and throughput optimization, not a proof of zero retries from producer-block reordering. Its own results still show limits from hot accounts. |
| [Clay, PVLDB 10(4)](https://db.cs.cmu.edu/papers/2016/p445-serafini.pdf), §§4–7 | Uses a load model including local and remote accesses and adapts groups around hot, co-accessed tuples. Explains why minimizing the total cut can leave a single partition overloaded. | Physical database repartitioning; its load model and migration mechanism require adaptation to our replicated execution setting. |
| [Mt-KaHyPar, project documentation](https://github.com/kahypar/mt-kahypar) | Supports weighted graph/hypergraph partitioning with an explicit imbalance parameter. Useful as a constrained multilevel baseline. | A low weighted cut is not execution independence or an estimate of actual invalidated transaction work. |

These sources suggest separating three objectives: independent-work coverage, maximum assigned load, and the cost of connecting transactions. They do not establish that one algorithm dominates for our workload.

## A suitable constrained formulation

For a known window, partition transactions into producer groups `F_1 ... F_p` and a residual set `R`. Choose a load budget `B_p` for each producer and seek:

```text
minimize estimated residual/coordination cost
subject to:
    every transaction belongs to exactly one F_p or R
    sum(cost(t), t in F_p) <= B_p
    no conservative conflict crosses F_p and F_q, for p != q
```

Residual cost is not merely residual count: a cheap connecting transaction can invalidate expensive downstream computations. Hard budget feasibility is not guaranteed, especially if one transaction alone exceeds a budget. Such cases must be reported or admitted through the fallback, not hidden by changing weights.

On a transaction conflict graph, selecting residual vertices so that the remaining components can be placed under load limits has the form of a weighted separator problem plus whole-component scheduling. This is our formulation of the design problem, not a claim that Strife optimally solves it. Ordinary edge-cut partitioning permits residual conflicts; removing transactions from the independent phase is a different operation.

## Example and unavoidable tradeoff

Assume unit transaction costs and two producers. There are 100 transactions using mutable state `x`, 100 using mutable state `y`, and one transaction `c` touching both. Conservative full closure creates a 201-transaction component.

- Whole-component placement: loads `201 / 0`; no cross-producer conflicts.
- Independent groups with `c` residual: independent loads `100 / 100`, plus the cost and ordering dependencies of `c`.
- Balanced placement of all transactions: distributes production work, but the conflicts through `c` remain and must be validated/repaired.

The second case is safe with Strife-like phase ordering only if the protocol actually places/executes the independent work before the residual work. It cannot move `c` to the end after a different canonical order has already been fixed. If `c` occurs before a dependent transaction in that order, the dependent computation may need revalidation and reexecution. Removing `c` from the grouping graph alone does not make that dependency disappear.

If almost all transactions update the same order-sensitive state, even removing a few connectors will not produce useful independent groups. There is no placement-only solution promising all transactions, perfect balance and unconditional zero reexecution in that case.

## Recommended experiment, before choosing a protocol change

Compare these on identical trace windows and with all work accounted for:

1. Hash placement: balance-oriented reference.
2. Full conflict components: exact-independence reference and giant-component diagnostic.
3. Balanced multilevel placement: cap load and accept some conflicts; retain transaction-level validation and track downstream invalidation, not just cut edges.
4. Capacity-bounded, Strife-inspired grouping: independent groups plus residuals, explicitly charging residual processing and any phase/admission waiting.

For item 3, accept reuse only for results whose input observations remain valid. For item 4, either specify a legal ordering/phase policy or label it an offline opportunity analysis; do not claim all non-residual results are reusable under an arbitrary interleaved order.

Sweep imbalance allowance, grouping window length and group-access frequency skew. Plot **independent-work coverage versus maximum frequency-weighted load and total modeled completion time**, with planning time, residual work, queue waiting and reexecution exposed separately. Where timing is uncalibrated, report the structural/load/reexecution measures without a latency claim.

The key decision is empirical: does a small residual set recover good balance, or is the workload dominated by a genuine shared-state hotspot? Ethereum traces can answer this structural question. A low cross-producer edge count alone cannot.

## Recommendation

Do not make unconditional component merging the final placement policy. Keep it as the correctness reference. Evaluate a capacity-constrained candidate alongside it, using Multilevel for balanced soft placement and Strife as the principal reference for preserving conflict-free subsets. Only adopt a residual-phase protocol if its ordering and latency costs fit the main pipelined-consensus design.

The reference implementation now exposes per-group demand and the achieved load relative to an indivisible-work lower bound. Verified synthetic cases are:

| Window demand | Resulting producer work | Interpretation |
|---|---|---|
| A: 10 calls, 1,000 keys; B: 100 calls, 1 key; C: 90 calls, 1 key; unit cost | 100 / 100 | Frequency, not state count, controls assignment. |
| A: 2 calls costing 50 each; B: 100 calls costing 1 each | 100 / 100 | Frequency is weighted by per-call cost. |
| A: 190 calls; B: 10 calls; unit cost | 190 / 10 | Imbalanced but optimal under whole-group independence. |
| Five independent groups with work 3, 3, 2, 2, 2 | 7 / 5 | Greedy is not optimal; an alternative assignment achieves 6 / 6. |

The first three cases also retain zero symbolic reruns in the tested block-arrival scenarios. These are synthetic correctness/model checks, not a measured throughput comparison. Capacity-bounded residual grouping, forecasting and adaptive regrouping are not implemented, and no Ethereum measurements are claimed.
