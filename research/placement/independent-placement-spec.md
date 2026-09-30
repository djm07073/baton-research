# Independent producer placement for execution-result reuse

Status: research design and executable model, 2026-09-25. This note does not change the consensus implementation or the paper's current placement protocol. It specifies a stronger alternative to soft multilevel placement and identifies what remains necessary for online deployment.

Follow-up: [load-aware grouping research](load-aware-grouping-research.md) treats giant components and producer imbalance. Whole-component placement below is the exact-independence reference, not an unconditional recommendation to merge arbitrarily large workloads.

## 1. Objective: preserve work across different block orders

Suppose the finalized block order is `A → B`, but a validator has executed `B → A`. If the blocks are independent, their transaction computations need not run again. The objective is to **construct producer blocks with this property**, rather than merely reduce the expected number of conflicts.

The resulting claim is conditional and precise:

> For a fixed execution context and selected producer prefixes, placement that eliminates conflicts across producers permits reuse of transaction computations under any change in cross-producer interleaving that preserves each producer's internal order.

It does not imply zero finalization work. Nodes must still validate cut membership, obtain missing data, select the correct transaction occurrences, assemble state updates and rebuild order-dependent commitments. Nor does it remove retries caused by a changed parent, a fork, an incorrect access declaration, or speculative execution across a missing same-producer predecessor.

## 2. Independence condition

Let `R(t)` and `W(t)` conservatively cover all state observed and modified by transaction `t`. For a block, take the union over its transactions. Two blocks `A` and `B` satisfy the sufficient independence condition when:

```text
W(A) ∩ (R(B) ∪ W(B)) = ∅
W(B) ∩ R(A)           = ∅
```

Read/read sharing is allowed. Write/read, read/write and write/write sharing are conservatively treated as conflicts. This is a sufficient condition, not a necessary characterization of every reusable computation: two blind writes can reuse their computations while requiring ordered application of their deltas.

The condition covers application accesses **and** nonce, balance, fees, account existence, code and protocol-maintained state where applicable. If execution observes an ordering position, cumulative counter, timestamp or another environmental input, that observation must either remain fixed or be represented as a dependency. Checking only contract storage slots is insufficient.

An application may certify additional compatible operation pairs, but the first implementation deliberately uses only conservative read/write sets. `try_add`, `try_subtract`, snapshots and bounded aggregations are not unconditionally commutative: a different prefix can change a condition or returned value. They cannot simply be omitted from the conflict relation.

### Required execution contract

- Every transaction has a deterministic, enforced conservative access declaration; unlisted accesses cannot silently succeed.
- All replicas use the same parent state, runtime version, transaction bytes and relevant environmental inputs.
- A producer's selected chain is a prefix, and its transaction order is unchanged. Execution waits for missing local predecessors or independently validates the required input versions.
- Transactions have unique selected occurrences. A Byzantine duplicate or fork is not part of the reuse theorem.
- Access sets cover conditional branches that can arise in the supported context, not just a single historical execution path.

A declaration violation needs deterministic invalid-transaction handling, including any fee/nonce effects. A data-availability certificate is not evidence that these conditions hold.

## 3. Algorithm: conflict components, then whole-group placement

For a **closed, known transaction window** `T`, construct an undirected graph whose vertices are transactions and whose edges connect conflicting pairs. Put each connected component wholly on one producer. Multiple independent components may share a producer.

For example:

```text
t1: write x            t4: write p
t2: read x, write y    t5: read p, write q
t3: read y, write z    t6: read q, write r

Producer 0: {t1, t2, t3}     Producer 1: {t4, t5, t6}
```

The producer blocks can arrive and be inserted in different cross-producer orders. No transaction in the left group observes a write in the right group, or vice versa. Within each group, dependent transaction order must still be respected; placement alone does not supply a parallel execution engine.

### Pseudocode

```text
plan(T, ordered_producers, block_size):
    validate unique transaction IDs and complete access declarations
    make one disjoint-set element per transaction

    for each state key s:
        users   = transactions reading or writing s
        writers = transactions writing s
        if writers is nonempty:
            choose one writer w
            union(w, every transaction in users)
        # A read-only key does not merge its readers.

    groups = connected components of the disjoint sets
weight(group) = sum(transaction cost proxy)
    sort groups by descending weight, then smallest transaction ID

    for group in groups:
        p = producer with least assigned weight; break ties by producer index
        assign the entire group to p

    for each producer p:
        retain the common input order of transactions assigned to p
        pack that sequence into blocks without splitting a transaction
    return assignment, blocks, loads
```

Union-find avoids materializing a quadratic clique around a frequently accessed key. With `I` total transaction/key incidences, component construction takes `O(I α(|T|))` after access normalization. Sorting, cost balancing and block packing add work; the small reference implementation also scans transactions once per producer. These costs must be measured rather than described as free.

The mapping is deterministic given the same transaction set, declarations, costs and ordered producer list. Input order does not affect component membership or assignment, but does affect the order inside produced blocks. Replicas must therefore agree on that sequence as well. Independent local mempool snapshots do not produce an agreed placement plan.

### Why connected components are the right hard boundary

If every transaction must be included and **no conservative conflict edge may cross producers**, the endpoints of every edge must share a producer. By transitivity, an entire connected component must share a producer. Conversely, assigning complete components ensures no such edge crosses producers.

Thus connected components give the finest permissible grouping under this conflict relation. This is not an NP-hard graph-cut search; balancing these indivisible groups is a separate scheduling problem. A multilevel partitioner that cuts a component may improve balance, but forfeits the zero-cross-producer-conflict guarantee. It remains useful as a soft-placement comparison, not as the justification for this theorem.

## 4. Why reversed execution can be reused

For deterministic transactions `a` and `b` meeting the condition above, neither changes the other's observed inputs, and their write destinations are disjoint. Therefore executing `a;b` or `b;a` preserves both the resulting application state and the transaction-local outputs, under the stated execution contract.

Any two interleavings of fixed producer sequences can be transformed into each other by adjacent swaps of transactions from different producers. Every such swap is between independent transactions. Repeatedly applying the argument proves equivalence of the two interleavings.

For incremental block arrival, a late block from another producer therefore cannot invalidate an already executed transaction's inputs. A late predecessor from the same producer can; the model buffers blocks until that producer's prefix is contiguous. This waiting cost is explicitly separate from reexecution cost.

Reuse means retaining validated transaction outputs and state deltas. A cached global state root after `B` alone is not the global state root after `A;B`. Receipt ordering, cumulative gas fields and state commitments may require reassembly even when the underlying transaction computations are reusable.

### Selected prefixes and changing cuts

The proof applies to the exact selected producer branches and prefixes. Discarding an unselected suffix is harmless to earlier same-lane work only if execution respected that lane's forward order. Replacing a branch or changing the canonical parent is outside this proof. The executable model tests a fixed eventual selected set; it does not implement fork selection or certify reuse across changing parents.

## 5. Balance and online arrival are real constraints

For additive transaction-cost estimates and `p` producers, every whole-component assignment has maximum assigned load at least:

```text
max(total estimated work / p, largest component's estimated work)
```

This is a load lower bound, not a wall-clock latency bound when intra-producer parallelism is available. A common mutable fee sink or highly connected application state can place the entire window in one component. Splitting that component does not preserve the guarantee. Best case: many balanced independent components. Worst case: one component and no cross-producer execution independence to exploit.

The weight is the number of attributed transaction executions times their mean cost over a common window, not the number of state keys. For example, a 1,000-key group executed 10 times can be lighter than a one-key group executed 100 times. The planner sums each transaction's cost once, even if that transaction touches many keys. Its current input is a known window; extrapolating the window's frequency to future demand is an additional estimation step, not a guarantee.

### A conservative quality bound for whole-group assignment

For `p` equal-capacity producers and fixed positive additive group weights, let `OPT` be the smallest possible maximum assigned load without splitting a group. The least-loaded-producer rule used here has maximum load `L <= (2 - 1/p) OPT`. This bound follows directly without assuming that greedy is optimal:

```text
Let j be the last group assigned to a producer with final load L.
Its weight is w_j, total weight is W, and its start load is S_j.
At assignment time that producer was least loaded:
    S_j <= (W - w_j) / p
Therefore:
    L = S_j + w_j <= W/p + (1 - 1/p) w_j
Since OPT >= W/p and OPT >= w_j:
    L <= (2 - 1/p) OPT
```

Descending-weight placement is the implementation's additional heuristic; the above weaker bound already suffices for a self-contained argument. It does not apply unchanged to inaccurate forecasts, heterogeneous producer capacities or queueing latency. Greedy is not always optimal: weights `[3,3,2,2,2]` yield loads `[7,5]` on two producers, whereas `[3,3]` and `[2,2,2]` attain `[6,6]`.

The analysis tool reports `loadToLowerBoundRatio = max(loads) / loadLowerBound`. A value of 1 certifies optimal assigned maximum load for this input/model; a larger value is an upper bound on the ratio to the unknown optimum, not proof that the lower bound is attainable. It reports 0 for an empty workload. This distinguishes an unavoidable hot-group bottleneck from a poor assignment.

### Why an online greedy merge is not enough

Suppose `a(write x)` has already been assigned to producer 0 and `b(write y)` to producer 1. A later `c(read x, write y)` connects both groups. Updating a union-find structure cannot retroactively make the already exposed blocks independent.

Two deployment profiles must be distinguished:

1. **Closed-window planning.** Collect/seal a finite set, compute its full components, then produce blocks. All transactions can be placed safely, at the possible cost of a collection barrier or a giant component. Different windows cannot overlap execution without accounting for their cross-window dependencies.
2. **Frozen-map admission.** Prepare and authorize a state-to-producer map before its interval. Admit a transaction to the independent stream only when every declared access has the same mapped producer. Unknown or cross-home accesses are deferred; they do not bypass the guard based on a preferred-producer score.

The reference model implements the second profile's admission check, **not** its recovery, fair inclusion or map-handoff protocol. Its conservative guard also defers read-only transactions spanning multiple mutable homes; supporting shared immutable reads would be a separately checked relaxation.

A deployable frozen-map profile additionally needs:

- A common map version and activation boundary, with old-map work drained or dependencies explicitly carried across that boundary. Announcing `cut + 2` alone does not establish this safety property.
- A bounded, fair route for deferred transactions, such as the ordinary validated execution path outside the independence guarantee. That path cannot write into an overlapping independent stream without dependency accounting.
- Byzantine checks on block placement and declarations; a producer cannot unilaterally route a cross-home transaction into a supposedly independent block.
- Limits on declarations and planning work. Adversarial oversized or bridging transactions can collapse components and attack performance even without violating safety.

Consequently, unrestricted online arrivals, admission of every transaction, balanced producers and strict cross-producer independence cannot all be promised without additional coordination or restrictions. The finite-window algorithm solves the hard grouping problem; it is not by itself a complete nonblocking routing protocol.

## 6. Evidence and relation to prior work

The mathematical basis is conflict independence and adjacent-swap equivalence, not a new theorem about consensus. A close systems precedent is **Strife**, which forms conflict-free transaction clusters and handles residual transactions separately. Its analysis, conflict-free and residual phases are synchronized; importing its clustering idea does not establish a nonblocking blockchain protocol. [Prasaad et al., SIGMOD 2020](https://homes.cs.washington.edu/~suciu/guna-sigmod-2020-pdfa.pdf)

The paper should not claim transaction clustering itself as novel. A defensible research direction is the coupling of declared-access producer placement, pre-cut block execution, cut-relative result reuse and its admission/latency tradeoff. That contribution still requires comparison with relevant prior work and measurement.

## 7. Ethereum-trace evaluation plan

### Separate three questions

1. **Structural opportunity:** how often do real transactions form several sufficiently balanced conflict components?
2. **Reexecution mechanism:** under a specified arrival and scheduling model, does grouping preserve computations that hash/soft placement invalidates?
3. **End-to-end improvement:** do saved computations outweigh planning, admission, prefix waiting and state-assembly costs?

Trace partitioning and symbolic simulation can support the first two questions under explicit assumptions. They do not, alone, establish lower measured cut-to-state latency or correct replay of arbitrary Ethereum contracts under a new order.

### Obtain complete footprints, not just state differences

Pin chain ID, fork rules, block range, block hashes, parent roots, client/tracer versions and extraction configuration in a provenance manifest. Record transaction hashes and original positions, failed transactions, and the reason for any exclusion. Use contiguous windows from multiple time periods; publish the sampling rule before reporting favorable windows.

An instrumented EVM trace should capture storage reads/writes and relevant account-level accesses, including implicit fee/nonce processing and accessed code/existence. Reads that influence failure still matter. Conservatively retaining reverted-frame accesses is safe for grouping but may overmerge; distinguish these from committed writes when reporting refined results. `prestateTracer` diff mode only describes net state changes and cannot supply the complete dependency input on its own. [Geth tracer documentation](https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers)

Ethereum's optional EIP-2930 access list is not the enforced complete read/write declaration assumed here; accesses outside it remain possible. Historical observed accesses are **oracle inputs** for the executed historical path, not automatically valid prospective declarations under reordered execution. [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930)

Report separate profiles:

- **Full-state conservative:** include protocol and application dependencies. This is the primary safety-oriented footprint analysis.
- **Application-only diagnostic:** show the opportunity remaining after removing protocol accounting, but explicitly do not claim full-state independence.
- **Semantically justified operations:** only if a specified runtime supports validated deferred/commutative accounting; document its conditions rather than silently removing fee writes.

Use storage-slot/account-field granularity, with a contract-address-level sensitivity check. Shared token code does not itself create a write conflict; merging every transaction calling one token contract can badly overestimate dependencies.

### Baselines and fair comparisons

- Transaction-hash placement with identical block capacities and scheduling rules.
- State-affinity / existing soft multilevel placement, including the same load constraints.
- Full-window connected-component placement, labeled a closed-window or hindsight oracle when it uses transactions unavailable at routing time.
- A prospective frozen map trained on previous windows and evaluated on later, held-out windows, with the admission guard and deferred work counted.

Each placement changes the producer sequences and hence may change the reference order. Validate each run against **its own** resulting canonical serial order. Cross-policy application outcomes need not be identical. Keep arrival assumptions, transaction inventory, parent context and same-producer prefix handling comparable. Do not let only the proposed algorithm wait for missing local predecessors while forcing a baseline to execute across gaps.

Measure component count, largest-component work fraction, cross-producer conflict pairs, assigned-load imbalance, planning time, independent admission coverage and deferred waiting. For modeled execution, report changed read observations, rerun count/cost and prefix waits separately. Conflict-edge count is not itself a rerun count. Never report zero retries after dropping hard transactions without also reporting their fraction and cost.

Sweep producer count, window/block size, arrival skew, hotspot concentration and cost weighting. Use chronological train/test separation, not future accesses when building a claimed prospective map. Use measured execution costs when available; transaction count or gas is only a proxy. Report adverse cases, especially fee coupling and giant components.

An actual engine or calibrated event simulation is needed for quantitative latency claims. Until then, describe results as structural opportunity and model-level avoided reexecution, not measured throughput or latency improvements. Dynamic-access EVM transactions require revalidation/reexecution or enforced conservative declarations before the reuse guarantee can be applied to them.

## 8. Executable evidence delivered with this note

Files in this directory:

- `independent-groups.mjs`: exact components, whole-group assignment, frozen-map guard and symbolic block-arrival model.
- `independent-groups.test.mjs`: grouping, admission, equivalence, arrival and invalid-input checks.
- `analyze-independent-groups.mjs`: bounded JSONL pilot analysis against transaction-hash placement.
- `analyze-independent-groups.test.mjs`: report and CLI checks.
- `independent-example.jsonl`: **synthetic** nine-transaction fixture, not Ethereum data.

Normalized JSONL input contains one record per transaction:

```json
{"id":"transaction-hash","reads":["storage:address:slot"],"writes":["account:address:nonce"],"cost":1}
```

All implicit accesses must already be present in the normalized input. The tool does not extract Ethereum traces or verify declaration completeness. Keep provenance separately. The pilot is limited to 2,000 transactions per window and 16 MiB input; pairwise comparison and repeated symbolic replay are not designed for full-chain scale.

```sh
node --test research/placement/*.test.mjs
node research/placement/analyze-independent-groups.mjs --input research/placement/independent-example.jsonl --producers 3 --simulate
```

At this revision, all **86 tests** pass, including the existing routing tests. The new independence suite checks all **4,096** three-transaction/two-key read/write declarations against independently computed conflict closure, and all six block-arrival permutations for each case: **24,576** symbolic schedules. A separate numeric interpreter checks actual conditional transaction outputs across lane-preserving orders. Frequency-weighted cases distinguish state-key count, invocation count and per-invocation cost; they also expose a dominant indivisible group and a non-optimal greedy assignment.

The `groupDemand` report lists each component's attributed transaction count, distinct state keys, mean cost, total estimated execution work and assigned producer. Distinct state keys are diagnostic metadata, not the placement weight. Each row describes a component of this input window; its ID is not a permanent application-group identity.

For the synthetic fixture, across eight specified arrival scenarios:

| Measure | Whole-component placement | Transaction-hash placement |
|---|---:|---:|
| Assigned transaction counts | 3 / 3 / 3 | 2 / 4 / 3 |
| Cross-producer conflict pairs | 0 | 4 |
| Symbolic reruns by scenario | 0, 0, 0, 0, 0, 0, 0, 0 | 0, 2, 2, 1, 1, 0, 0, 2 |

Both policies recover their own reference-order symbolic results. The maximum observed rerun count is not a general worst-case bound. The model has no EVM, actual CPU timing, network, forks or consensus. No Ethereum empirical benefit or end-to-end latency result has been established yet.

## 9. Recommended paper claim

> We identify a sufficient placement condition under which changes in cross-producer block interleaving do not invalidate previously computed transaction results. We realize this condition through indivisible conflict-component placement and explicitly account for the load-balance and online-admission limitations. Ethereum traces are used to evaluate the prevalence and cost of the resulting independent execution opportunities.

The final sentence is an evaluation plan until the real-data experiment has been performed. Avoid the stronger claims that multilevel partitioning guarantees zero reexecution, that arbitrary EVM access lists are complete, or that independence eliminates all post-cut state-finalization work.
