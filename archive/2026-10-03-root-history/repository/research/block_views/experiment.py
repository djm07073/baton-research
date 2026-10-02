"""Synthetic block-work experiment; no network or consensus implementation."""

import argparse
import json
import random
import statistics

import selection as m


def schedule_time(nodes, edges, dirty, workers):
    pending, dirty, done, elapsed = set(nodes), set(dirty), set(), 0
    if workers < 1 or not dirty <= pending:
        raise ValueError("invalid worker schedule")
    while pending:
        while True:
            cached = {b for b in pending - dirty
                      if all(a in done for a, c in edges if c == b)}
            if not cached:
                break
            done.update(cached)
            pending.difference_update(cached)
        if not pending:
            break
        ready = sorted(b for b in pending & dirty
                       if all(a in done for a, c in edges if c == b))[:workers]
        if not ready:
            raise ValueError("cyclic or incomplete schedule")
        elapsed += 1
        done.update(ready)
        pending.difference_update(ready)
    return elapsed


def fixture_plan(ctx, blocks, order):
    edges = m.edges_for_order(blocks, order)
    return m.Plan(tuple(sorted(blocks)), edges, m.digest((ctx, sorted(blocks), edges)),
                  "experiment", (), (), 0)


def preexecute(ctx, blocks, base, arrivals, common_rank):
    observed, cache, reexecution = {}, None, 0
    for name in arrivals:
        observed[name] = blocks[name]
        order = tuple(sorted(observed, key=lambda b: m.rank(ctx, blocks[b]))) \
            if common_rank else tuple(observed)
        plan = fixture_plan(ctx, observed, order)
        result = m.execute(ctx, plan, observed, base, cache=cache)
        reexecution += len(set(result.ran) & (set(cache.records) if cache else set()))
        cache = result
    return observed, cache, reexecution


def trial(seed, shared_probability, visibility=0.8, byzantine=True):
    rng = random.Random(seed)
    lanes = tuple("ABCDEF")
    base = {**{f"k{i}": 10 for i in range(6)}, **{f"u{i}": 0 for i in range(6)},
            "hot": 10}
    ctx = m.Context("e", "parent", m.digest(base), tuple((l, 0) for l in lanes),
                    lanes, tuple(range(6)), 1, 2)
    blocks = {}
    for i, lane in enumerate(lanes):
        key = "hot" if rng.random() < shared_probability else f"k{i}"
        op = ("add", key, i + 1) if rng.random() < 0.5 else ("copy", f"u{i}", key)
        blocks[lane] = m.Block(lane, lane, 1, None, (op,))
    arrivals = {}
    honest = tuple(range(5)) if byzantine else ctx.committee
    for signer in honest:
        known = [b for b in blocks if rng.random() < visibility]
        rng.shuffle(known)
        arrivals[signer] = tuple(known)
    canonical = tuple(sorted(blocks, key=lambda b: m.rank(ctx, blocks[b])))
    fixed = fixture_plan(ctx, blocks, canonical)
    results = {}
    preparations = {}
    for common in (False, True):
        preparations[common] = {}
        for signer in honest:
            preparations[common][signer] = preexecute(ctx, blocks, base,
                                                     arrivals[signer], common)
    for label, common, adaptive in (
        ("cut-only", None, False), ("arrival/fixed", False, False),
        ("rank/fixed", True, False), ("arrival/selected", False, True),
        ("rank/selected", True, True),
    ):
        plan = fixed
        prep = preparations.get(common, {})
        if adaptive:
            views = []
            for signer, (observed, cache, _) in prep.items():
                order = tuple(sorted(observed, key=lambda b: m.rank(ctx, blocks[b]))) \
                    if common else tuple(observed)
                views.append(m.View(signer, 1, ctx.base_id, tuple(observed),
                                    m.edges_for_order(observed, order),
                                    tuple(cache.records) if cache else ()))
            if byzantine:
                # A false "all executed" preference, never a source of state.
                views.append(m.View(5, 1, ctx.base_id, tuple(blocks),
                                    m.edges_for_order(blocks, canonical[::-1]), tuple(blocks)))
            view_store = {m.digest(v): v for v in views}
            refs = tuple(m.ViewRef(v.signer, 1, m.digest(v)) for v in views)
            plan = m.select(m.Input(ctx, tuple(blocks), refs), blocks, view_store,
                            exact_limit=0, beam_width=8)
        fresh = m.execute(ctx, plan, blocks, base)
        times, reexecuted, remaining, prework, same = [], [], [], [], []
        for signer in honest:
            _, cache, prior_reexecution = prep.get(signer, ({}, None, 0))
            final = m.execute(ctx, plan, blocks, base, cache=cache)
            times.append(schedule_time(plan.nodes, plan.edges, final.ran, ctx.workers))
            remaining.append(len(final.ran))
            reexecuted.append(len(set(final.ran) & (set(cache.records) if cache else set())))
            prework.append(prior_reexecution)
            same.append(final.result_root == fresh.result_root)
        results[label] = {
            "quorum_work_rounds": sorted(times)[m.quorum(ctx) - 1],
            "mean_remaining": statistics.mean(remaining),
            "mean_reexecuted": statistics.mean(reexecuted),
            "mean_pre_reexecution": statistics.mean(prework),
            "same_result": all(same),
        }
        if not all(same):
            raise AssertionError("cached execution differs from selected-plan execution")
    pairs = [(a, b) for i, a in enumerate(blocks) for b in tuple(blocks)[i + 1:]]
    return {"seed": seed, "conflict_fraction": statistics.mean(
        int(m.conflicts(blocks[a], blocks[b])) for a, b in pairs), "modes": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--honest", action="store_true")
    args = parser.parse_args()
    output = {"trials_per_setting": args.trials, "validators": 6, "blocks": 6,
              "workers_per_validator": 2, "visibility": 0.8,
              "one_false_report_and_silent_voter": not args.honest, "settings": []}
    for p in (0.0, 0.5, 1.0):
        samples = [trial(seed, p, byzantine=not args.honest) for seed in range(args.trials)]
        rows = {}
        for label in samples[0]["modes"]:
            rows[label] = {metric: round(statistics.mean(s["modes"][label][metric]
                                                        for s in samples), 4)
                           for metric in ("quorum_work_rounds", "mean_remaining",
                                          "mean_reexecuted", "mean_pre_reexecution")}
        output["settings"].append({"shared_probability": p,
                                    "conflict_fraction": round(statistics.mean(
                                        s["conflict_fraction"] for s in samples), 4),
                                    "modes": rows})
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
