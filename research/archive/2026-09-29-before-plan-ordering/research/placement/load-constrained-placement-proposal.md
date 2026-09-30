# Load-constrained, dependency-aware producer placement

Proposal, 2026-09-25. This is an optimization design, not an implemented Commonware protocol or a measured Ethereum performance result. It supersedes unconditional whole-component merging as the recommended research direction; the exact-independence model remains a reference baseline.

## 1. The two missions

1. Keep order-sensitive interactions within producer sequences where useful, reducing invalidation from late cross-producer block insertion. Cross-producer dependencies and reexecution are allowed when necessary.
2. Distribute dependency groups using **execution frequency times cost**, not the number of state keys. Split groups when retaining them would concentrate production demand.

The objective is not to maximize the number of cut dependencies. It is to separate largely independent work while minimizing the cost of the dependencies that must cross producer boundaries. Placement is not state ownership: validators can still execute all selected transactions against shared state.

## 2. Input and output contract

Input:

- A common finalized history window `H`, with transaction identities, conservative declared access modes and deterministic cost estimates `c(t)`.
- A versioned operation-compatibility table. Read/read is compatible; general write/read and write/write are treated as conflicting. Conditional compatibility is credited only under supported, checked semantics.
- Producer order, the common block-ordering rule, deterministic block-packing settings and producer load budgets `B_p` in the same work/window units.
- The previous complete routing policy `P_old`, including its representative-selection parameters, routing subdivisions and placement map.
- Fixed optimizer budgets: number of levels/passes, maximum bucket depth, candidate count, scenario definitions and rational scoring coefficients. These are work-count limits, not wall-clock timeouts.

Output: a complete candidate routing policy `P_new`, its predicted producer loads, cut-dependency proxy, replay scores and an evidence digest identifying the inputs. Alternatively return `KEEP` with a reason such as no feasible improving candidate found. Search failure is not proof of infeasibility.

Local arrival timestamps, local mempool contents and unnormalized per-machine execution timing cannot determine a consensus-reproduced policy. Cost calibration tables must be common versioned inputs. The optimizer is not allowed to alter transaction semantics, canonical block ordering or the runtime's validation rules.

## 3. Whole-transaction routing and exact demand accounting

### 3.1 A representative state selects a routing unit

For declared access mode `o` on state `s`, estimate conflict pressure from `H`:

```text
pressure(s, o) = sum(c(u) for u in H
                     if u accesses s with a mode incompatible with o)
```

Each historical transaction contributes at most once to this sum for a given state. Repeated occurrences with distinct transaction identities contribute separately. For a new transaction `t`, select the accessed state maximizing `pressure(s, mode(t,s))`; break ties by canonical state identifier. Unknown states have pressure zero and use the same tie rule. Transactions with no declared state access use an explicit fallback routing domain.

This representative heuristic is a proposal, not a theorem about the optimal anchor. Evaluate it against simpler representatives and direct transaction-hash routing. Missing or conservative declarations can degrade its prediction; runtime validation remains mandatory.

### 3.2 A hot representative must remain splittable

Mapping every invocation of a representative to one indivisible node would prevent balancing a single hot state. Therefore the routing domain may be subdivided:

```text
unit(t) = (representative(t), prefix_d(hash(domain, transaction_identity)))
producer(t) = placement_map[unit(t)]
```

Depth `d=0` means no subdivision. Refining one domain increases its depth and creates disjoint child buckets; the versioned policy specifies the hash, domain and depth. The whole transaction still goes to exactly one producer. A split does not duplicate transactions, split state transitions or remove dependencies.

Use subdivision to expose placement choices for a high-frequency representative. The optimizer may keep child buckets together if splitting creates too much replay work. Refinement is bounded; one individually oversized transaction cannot be split by this mechanism. Hash bucketing is a deterministic routing rule, not a Byzantine load-balance guarantee: future skew and identity grinding can defeat demand forecasts.

For an unobserved routing unit, the policy has a fixed transaction-hash fallback. Its future load is not covered by historical feasibility. Switching representatives, subdivisions or fallback rules changes the policy, not merely its final map; replay and churn comparisons must use the complete old and new policies.

### 3.3 Count cost once

For a routing unit `v`, define:

```text
w(v) = sum(c(t), t in H with unit(t) = v)
     = invocation_count(v) * mean_invocation_cost(v)
L_p(P) = sum(c(t), t in H with producer_P(t) = p)
```

Multi-state transactions are not charged once per touched state. Each historical transaction contributes to exactly one producer's base demand. A group of routing units has the sum of their disjoint attributed work. Reexecution cost is accounted for separately.

These weights forecast demand from a past window; they are not guarantees about a future window. Producer production/admission demand must also be distinguished from per-validator replicated execution work. If network bytes or admission CPU are the relevant production constraint, add those explicitly as separate measured/proxy constraints rather than treating executor cost as interchangeable with them.

## 4. Two evaluation levels

### 4.1 Cheap dependency graph for candidate search

Vertices are routing units. For transaction pairs that have order-sensitive overlapping accesses, add an edge between their units and aggregate an estimated separation penalty. A pair sharing several conflicting states must not be counted several times merely because its footprint is larger.

Read-only co-access does not by itself create an edge. Transactions sharing a representative can become distinct vertices after subdivision; their remaining conflicts must then appear as cross-unit edges. Never split a vertex and forget the dependencies between its children.

Frequency-weighted conflict counts are an initial proxy. Estimated invalidation work can improve the weight, but an edge-cut score is not a count of actual retries: multiple predecessors may invalidate the same execution attempt, while blind writes may reuse their computations. A graph is sufficient for the initial implementation; hyperedges may capture joint interactions when their semantics and accounting are explicitly defined.

### 4.2 Replay score for final candidate ranking

For each shortlisted policy, reroute the same history transactions, repack producer blocks, apply the common ordering rule and replay a fixed set of arrival scenarios. Buffer missing same-producer predecessors. Use each candidate's own canonical serial result as its correctness reference.

For scenario `q`, let `R_q(P)` be the sum of cost of invalidated computation attempts that must be redone. Count one attempt once even if several conflict edges invalidate it, but count repeated invalidations of different attempts of the same transaction separately. Include dependent invalidations through observed inputs, not just the directly split edge.

One concrete ranking is:

```text
J(P) = mean_q R_q(P) + lambda * max_q R_q(P) + beta * Churn(P, P_old)

Churn(P, P_old) = sum(c(t), t in H
                     if producer_P(t) != producer_P_old(t))

subject to L_p(P) <= B_p for every producer p
```

Coefficients are fixed rational configuration values. Churn is a routing-change proxy, not a claim that physical state is migrated. Tail replay cost is optional (`lambda=0` disables it); it must not be described as measured tail latency.

Also report packing delay, prefix waiting, failed transaction outcomes, total work and application/state-assembly costs. A policy that saves replay but creates excessive admission waiting has not established an end-to-end win. Fixed-footprint symbolic replay is only a model: actual EVM outcomes may change access paths and costs under the new order.

## 5. Deterministic multilevel search

The algorithm searches for a good feasible policy; it does not guarantee a globally optimal partition.

1. Build a bounded family of routing granularities, starting with unsplit representatives. Refine heavy or high-penalty domains when doing so exposes useful alternatives. Keep child dependencies and recompute attributed work.
2. For each granularity, tentatively coarsen strongly connected units. Rank merge candidates by separation penalty saved per combined work, with canonical tie-breaking. Do not contract a group whose weight exceeds every producer's budget. Coarse groups are search artifacts, not permanent placement constraints.
3. Build initial assignments using weighted LPT and the previous policy where representable. Retain a fine-grained hash seed as a baseline. LPT's approximation bound concerns fixed additive weights and identical machines; it does not promise feasibility for every chosen hard budget or optimal replay cost.
4. Uncoarsen. Use bounded move/swap refinement to improve the dependency proxy under load constraints. An FM-style pass may explore temporary score deterioration and retain its best valid prefix; stopping at only immediately positive single moves can trap the search. Rebalancing must precede acceptance of an overloaded seed.
5. Replay-score the best distinct feasible candidates. Always include the old complete policy in replay evaluation when it is feasible under the current inputs, even if graph pruning would discard it.
6. Choose the candidate with the smallest replay objective, then lowest peak load, then canonical policy encoding. Switch only when the configured improvement margin over the feasible old policy is met. If the old policy is overloaded, a feasible replacement may be useful despite higher replay cost; expose that tradeoff explicitly.

An unbalanced LPT seed must not be reported as evidence that no balanced assignment exists. For example, `[3,3,2,2,2]` yields greedy loads `[7,5]`, while `[6,6]` is possible.

### Pseudocode

```text
propose(history, old_policy, config):
    validate common history, access schema and bounded cost inputs
    candidates = {old_policy}

    for routing_granularity in bounded_granularity_search(history, config):
        units, work = attribute_each_transaction_once(history, routing_granularity)
        graph = aggregate_order_sensitive_interactions(history, units)
        hierarchy = coarsen_with_weight_limits(graph, work, config)

        for seed in deterministic_seeds(hierarchy, old_policy, config):
            policy = uncoarsen_and_refine(seed, hierarchy,
                                         moves=true, swaps=true,
                                         fixed_pass_budget=config.passes)
            if all_predicted_loads_within_budget(policy):
                shortlist_by_dependency_proxy(candidates, policy)

    keep old_policy in shortlist if it is feasible
    scored = replay_complete_policies(shortlist, common_scenarios)
    reject any candidate failing its own serial-equivalence check
    best = deterministic_argmin(scored feasible candidates, J, peak_load, encoding)

    if no feasible candidate was found:
        return KEEP(reason="no feasible candidate found", overload_diagnostics)
    if old_policy is feasible and improvement(best, old_policy) < config.margin:
        return KEEP(reason="insufficient modeled improvement")
    return candidate(best, input_digest, load_and_replay_evidence)
```

With deterministic bounded loops and tie rules, this computation terminates and is reproducible for identical inputs. Neither property proves liveness of transaction admission or actual future performance.

## 6. Ordering, execution and activation remain separate

The optimizer runs in the background. Absence of a new candidate must not stall block production or ordering. Existing execution validation determines whether a speculative result matches the finalized order; the grouping score never certifies an execution result.

This proposal creates no residual execution lane, separate cross-state phase or new ordering quorum. All transactions retain the ordinary execution path; crossing a group boundary can lead to validation and reexecution rather than rejection or hidden deferral.

A candidate is not active merely because its optimizer finishes. The existing protocol must authorize a complete policy version and activation boundary. Already certified blocks and old-policy pending transactions cannot be silently reinterpreted, dropped or declared invalid. Admission handoff, deduplication and faulty-producer rerouting remain protocol integration obligations; an arbitrary two-cut delay does not prove them safe. This note specifies optimization and fixed-policy routing, not a completed activation protocol.

## 7. Checked synthetic example

The following diagnostic uses the existing `simulateBlockArrivals` model, not a new implementation of the multilevel optimizer. It exhaustively enumerates all 128 two-producer assignments of seven unit-cost transactions, preserving original transaction order inside each producer:

```text
a1: read/write x       b1: read/write y
a2: read/write x       b2: read/write y
a3: read/write x       b3: read/write y
c:  read/write x,y

Input sequence: a1,b1,a2,b2,a3,b3,c
Block size: one transaction
Canonical block rank: (producer-local height, producer index)
Load budget: four transactions per producer
```

Four scenarios are used for each assignment: canonical arrival; reverse canonical arrival; all producer-0 blocks then producer-1 blocks; all producer-1 blocks then producer-0 blocks. Local heights ascend in the last two scenarios. Missing same-producer prefixes are buffered for every assignment, not only for the preferred policy.

| Placement | Loads | Reruns in the four scenarios | Sum |
|---|---|---|---:|
| Everything on producer 0 | 7 / 0 | 0, 0, 0, 0 | 0, but infeasible |
| `{a1,a2,a3,c}` / `{b1,b2,b3}` | 4 / 3 | 0, 0, 3, 0 | 3 |
| `{a3,b3,c}` / `{a1,b1,a2,b2}` | 3 / 4 | 0, 4, 2, 6 | 12 |

There are 70 assignments satisfying the load budget. The dependency-aware placement above attains the smallest total modeled rerun cost among those 70 for these four scenarios; the last row attains the largest. This establishes a concrete example in which equal load balance still leaves room for dependency-aware improvement. It is not proof that the proposed heuristic finds the optimum generally, nor that these scenarios predict Ethereum latency.

It also illustrates why refusing to split the full conflict component is not the final policy: transaction `c` connects both chains, so full closure merges all seven transactions and violates the budget.

## 8. Research basis and claims to test

- [Schism, PVLDB 2010](https://www.vldb.org/pvldb/vol3/R04.pdf): workload-derived placement graphs and access-frequency weights. Our penalty targets speculative invalidation rather than distributed database transactions.
- [Multilevel Hypergraph Partitioning with Vertex Weights Revisited, SEA 2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2021.8): heavy vertices, feasible balance definitions and scheduling-based initial placement. Its guarantees do not automatically cover forecast error or our replay objective.
- [High-Quality Hypergraph Partitioning, ACM JEA 2022](https://publikationen.bibliothek.kit.edu/1000152818): multilevel coarsening and refinement as candidate search machinery, not a global optimum certificate.
- [Dynamic Balanced Graph Partitioning, SIAM J. Discrete Mathematics 2020](https://epubs.siam.org/doi/10.1137/17M1158513): repeated interaction and placement-change costs. Its online bounds use a different model and cannot be inherited without a reduction.

The research contribution to investigate is a producer-routing objective and evaluation that account for operation compatibility, block-order changes and invalidated execution attempts under a frequency-weighted load constraint. Combining named algorithms is not by itself a novelty result.

Required comparisons: hash placement; full conflict components; load-only LPT; weighted cut minimization without replay ranking; and the full proposed method. Ablate representative choice, subdivision, operation compatibility and replay ranking. Use chronological history/held-out windows, account for every transaction, report planning overhead and unknown-unit demand, and preserve ordinary correctness validation in every baseline. Reuse the Ethereum extraction/provenance requirements in [the evaluation specification](independent-placement-spec.md#7-ethereum-trace-evaluation-plan).

Completion boundary for this proposal: both requested optimization missions have explicit objectives, routing/weight definitions, search steps and a checked example. The optimizer itself, online activation, real Ethereum traces and end-to-end latency measurements are not claimed as implemented or complete.
