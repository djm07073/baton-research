# Producer-placement research model

> **ARCHIVED — 2026-09-29:** Producer placement is not part of the [new research proposal](../../overpass-plan-ordering-outline.md). This directory remains intact for reference and reproducibility; an unchanged copy is preserved in the [archive](../archive/2026-09-29-before-plan-ordering/README.md).

Start with [Independent producer placement](independent-placement-spec.md) for the algorithm, reuse theorem, assumptions and Ethereum evaluation plan. The [load-aware follow-up](load-aware-grouping-research.md) distinguishes group execution frequency from state-group size and surveys load-constrained alternatives.

The subsequent [load-constrained placement proposal](load-constrained-placement-proposal.md) combines weighted multilevel search with replay-based ranking. It allows necessary cross-producer dependencies to achieve balance, includes splittable hot routing domains, and provides a checked seven-transaction tradeoff example. It is a proposal; the implemented exact-component model below remains its reference baseline.

## Implemented model

1. Construct exact conservative transaction-conflict components for a known window.
2. Keep each component on one producer, using frequency-weighted work for least-loaded assignment.
3. Pack producer blocks preserving their internal order.
4. Simulate reversed/skewed arrivals, buffering same-producer gaps and validating cached read observations.
5. Compare load and symbolic reruns against transaction-hash placement.

This creates cases in which a changed **cross-producer** block order does not require recomputing transaction results. It is a closed-window research model, not a Commonware integration or a complete online placement protocol.

```sh
node --test research/placement/*.test.mjs
node research/placement/analyze-independent-groups.mjs --input research/placement/independent-example.jsonl --producers 3 --simulate
```

The fixture is synthetic. For normalized trace input, use one JSON record per transaction containing `id`, `reads`, `writes` and optional positive integer `cost` (default 1). Include implicit protocol state accesses. Store extraction provenance separately; the tool does not download, extract or verify Ethereum traces. Pilot limits are documented in the specification.

Important outputs:

- `groupDemand`: transaction count, distinct state keys, average cost and total work per component. State-key count does not determine load.
- `componentPlacement.loads`: whole-component assignment's per-producer work.
- `loadLowerBound` and `loadToLowerBoundRatio`: distinguish indivisible hotspots from avoidable assignment imbalance.
- `crossProducerConflictPairs`: structural conflicts, not an execution retry count.
- `rerunsByScenario` and `prefixWaitEventsByScenario`: computation invalidation and prefix waiting, reported separately.

## Evidence audit

| Requested property | Evidence | Scope |
|---|---|---|
| An algorithm creates independent producer blocks | Union-find components and indivisible assignment in `independent-groups.mjs`; exact pairwise-closure tests | Complete conservative declarations for a known window |
| Reversed cross-producer order can reuse computation | Adjacent-swap proof in the specification; 4,096 footprint cases / 24,576 symbolic arrival schedules; numeric conditional-output test | Same parent/context, same selected branches, preserved local prefixes |
| Load reflects group frequency and execution cost | `groupDemand`, additive work assignment and five frequency/quality tests | Supplied window demand; no future-demand prediction |
| A logical case for the algorithm | Finest zero-conflict grouping proof, load lower bound, conservative assignment approximation bound and counterexamples | No claim of universal balance or zero finalization work |
| Related-work basis | Strife, TxAllo, Clay and partitioner sources in the follow-up | Precedent and design tradeoffs, not novelty proof |
| A method to evaluate on Ethereum transactions | Footprint/provenance requirements, baseline definitions, holdout protocol and metrics in §7 of the specification | Evaluation design; actual Ethereum collection/results remain future work |

All 86 local placement tests pass at the 2026-09-25 checkpoint. This includes legacy routing tests; those legacy algorithms were not changed. Neither passing tests nor symbolic results establish a network latency improvement.

## Not claimed or implemented

Arbitrary EVM access prediction, strict online deduplication and map handoff, Byzantine producer failover, capacity-bounded residual scheduling, automatic history forecasting, actual Ethereum results, consensus integration and measured end-to-end performance. These are not silently supplied by the grouping theorem. Future deployment must choose the closed-window or enforced-admission profile and account for its costs.
