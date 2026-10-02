"""Enumerated small schedules and a serial interpreter independent of selection."""

import itertools
import random
import unittest

import selection as m


def serial_oracle(blocks, order, base):
    state = dict(base)
    for name in order:
        for op in blocks[name].ops:
            if op[0] == "set":
                state[op[1]] = op[2]
            elif op[0] == "add":
                state[op[1]] = state.get(op[1], 0) + op[2]
            elif op[0] == "copy":
                state[op[1]] = state.get(op[2], 0)
            else:
                _, source, target, amount = op
                if state.get(source, 0) >= amount:
                    state[source] = state.get(source, 0) - amount
                    state[target] = state.get(target, 0) + amount
    return state


def schedule_is_valid(order, edges):
    positions = {b: i for i, b in enumerate(order)}
    return all(positions[a] < positions[b] for a, b in edges)


class ModelProperties(unittest.TestCase):
    def test_all_49_three_block_byzantine_order_and_progress_claims_preserve_results(self):
        base = {"alice": 10, "bob": 0, "carol": 0}
        ctx = m.Context("e", "parent", m.digest(base),
                        (("A", 0), ("B", 0), ("C", 0)),
                        ("A", "B", "C"), tuple(range(6)), 1)
        blocks = {
            "A": m.Block("A", "A", 1, None, (("transfer", "alice", "bob", 7),)),
            "B": m.Block("B", "B", 1, None, (("transfer", "alice", "carol", 7),)),
            "C": m.Block("C", "C", 1, None, (("add", "alice", 5),)),
        }
        honest_views, caches = [], []
        for signer, order in enumerate(tuple(itertools.permutations(blocks))[:5]):
            edges = m.edges_for_order(blocks, order)
            plan = m.Plan(tuple(blocks), edges, "local", "local", (), (), 0)
            caches.append(m.execute(ctx, plan, blocks, base))
            honest_views.append(m.View(signer, 1, ctx.base_id, tuple(blocks), edges,
                                       tuple(blocks)))
        checked = 0
        for size in range(4):
            for known in itertools.permutations(blocks, size):
                subset = {b: blocks[b] for b in known}
                for done in range(size + 1):
                    liar = m.View(5, 1, ctx.base_id, known,
                                  m.edges_for_order(subset, known), known[:done])
                    views = honest_views + [liar]
                    inp = m.Input(ctx, tuple(blocks), tuple(
                        m.ViewRef(v.signer, 1, m.digest(v)) for v in views))
                    plan = m.select(inp, blocks, {m.digest(v): v for v in views})
                    order = m.topological(plan.nodes, plan.edges, blocks, ctx)
                    expected = serial_oracle(blocks, order, base)
                    roots = set()
                    for cache in caches:
                        result = m.execute(ctx, plan, blocks, base, cache=cache)
                        self.assertEqual(result.state, expected)
                        roots.add(result.result_root)
                    self.assertEqual(len(roots), 1)
                    checked += 1
        self.assertEqual(checked, 49)

    def test_result_quorums_alone_do_not_choose_the_canonical_candidate(self):
        base = {"x": 0}
        ctx = m.Context("e", "parent", m.digest(base), (("A", 0), ("B", 0)),
                        ("A", "B"), tuple(range(6)), 1)
        blocks = {"A": m.Block("A", "A", 1, None, (("add", "x", 1),)),
                  "B": m.Block("B", "B", 1, None, (("add", "x", 2),))}
        # Both candidates have valid results, but neither result quorum orders them.
        certificates = []
        for sequence, order in ((1, ("A", "B")), (2, ("B", "A"))):
            edges = m.edges_for_order(blocks, order)
            views = [m.View(i, sequence, ctx.base_id, tuple(blocks), edges, tuple(blocks))
                     for i in ctx.committee]
            inp = m.Input(ctx, tuple(blocks), tuple(
                m.ViewRef(v.signer, v.sequence, m.digest(v)) for v in views))
            plan = m.select(inp, blocks, {m.digest(v): v for v in views})
            result = m.execute(ctx, plan, blocks, base)
            subject = m.digest((ctx, plan.input_root, plan.root))
            votes = [(i, subject, result.result_root) for i in range(4)]
            self.assertTrue(m.certified(ctx, subject, result.result_root, votes))
            certificates.append((subject, plan.edges))
        self.assertNotEqual(certificates[0][0], certificates[1][0])
        self.assertNotEqual(certificates[0][1], certificates[1][1])

    def test_closed_input_to_repaired_results_and_quorum_with_one_false_result(self):
        base = {"alice": 10, "bob": 0, "carol": 0}
        ctx = m.Context("e", "parent", m.digest(base), (("A", 0), ("B", 0)),
                        ("A", "B"), tuple(range(6)), 1)
        blocks = {
            "A": m.Block("A", "A", 1, None, (("transfer", "alice", "bob", 7),)),
            "B": m.Block("B", "B", 1, None, (("transfer", "alice", "carol", 7),)),
        }
        views, caches = [], []
        for signer in range(6):
            order = ("B", "A") if signer in (0, 1, 5) else ("A", "B")
            edges = m.edges_for_order(blocks, order)
            local = m.Plan(tuple(blocks), edges, "local", "local", (), (), 0)
            caches.append(m.execute(ctx, local, blocks, base))
            views.append(m.View(signer, 1, ctx.base_id, tuple(blocks), edges, tuple(blocks)))
        inp = m.Input(ctx, tuple(blocks),
                      tuple(m.ViewRef(v.signer, 1, m.digest(v)) for v in views))
        view_store = {m.digest(v): v for v in views}
        plan = m.select(inp, blocks, view_store)
        subject = m.digest((ctx, plan.input_root, plan.root))
        outputs = []
        for signer in range(5):
            self.assertTrue(m.verify_proposal(inp, blocks, view_store, plan))
            outputs.append(m.execute(ctx, plan, blocks, base, cache=caches[signer]))
        self.assertEqual(len({o.result_root for o in outputs}), 1)
        self.assertEqual(base, {"alice": 10, "bob": 0, "carol": 0})
        self.assertEqual(outputs[0].state["alice"], 3)
        self.assertEqual(sum(outputs[0].state.values()), 10)
        valid_root = outputs[0].result_root
        votes = [(5, subject, "forged root")]
        for signer in range(3):
            votes.append((signer, subject, valid_root))
        self.assertFalse(m.certified(ctx, subject, valid_root, votes))
        self.assertFalse(m.certified(ctx, subject, "forged root", votes))
        votes.append((3, subject, valid_root))
        self.assertTrue(m.certified(ctx, subject, valid_root, votes))
        self.assertFalse(m.certified(ctx, "different cut", valid_root, votes))

    def test_40_seeded_cases_all_worker_schedules_and_cache_repair(self):
        for seed in range(40):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                base = {k: 10 for k in "xyz"}
                ctx = m.Context("e", "parent", m.digest(base),
                                (("A", 0), ("B", 0), ("C", 0)),
                                ("A", "B", "C"), tuple(range(6)), 1)
                blocks = {}
                for lane in "ABC":
                    for height in (1, 2):
                        name = f"{lane}{height}"
                        key, other = rng.sample(list(base), 2)
                        op = rng.choice((("set", key, rng.randrange(10)),
                                         ("add", key, 1), ("copy", key, other),
                                         ("transfer", key, other, 12)))
                        blocks[name] = m.Block(name, lane, height,
                                               f"{lane}1" if height == 2 else None, (op,))
                lane_edges = tuple((f"{lane}1", f"{lane}2") for lane in "ABC")
                possibilities = [p for p in itertools.permutations(blocks)
                                 if schedule_is_valid(p, lane_edges)]
                views, caches = [], []
                for signer in ctx.committee:
                    order = rng.choice(possibilities)
                    local = m.Plan(tuple(sorted(blocks)), m.edges_for_order(blocks, order),
                                   "local", "local", (), (), 0)
                    cache = m.execute(ctx, local, blocks, base)
                    caches.append(cache)
                    views.append(m.View(signer, 1, ctx.base_id, tuple(blocks), local.edges,
                                        tuple(blocks)))
                refs = tuple(m.ViewRef(v.signer, 1, m.digest(v)) for v in views)
                inp = m.Input(ctx, tuple(blocks), refs)
                plan = m.select(inp, blocks, {m.digest(v): v for v in views})
                schedules = [p for p in possibilities if schedule_is_valid(p, plan.edges)]
                self.assertTrue(schedules)
                expected = serial_oracle(blocks, schedules[0], base)
                roots = set()
                for order in schedules:
                    self.assertEqual(serial_oracle(blocks, order, base), expected)
                    result = m.execute(ctx, plan, blocks, base, order=order)
                    self.assertEqual(result.state, expected)
                    roots.add(result.result_root)
                for cache in caches:
                    repaired = m.execute(ctx, plan, blocks, base, cache=cache)
                    self.assertEqual(repaired.state, expected)
                    roots.add(repaired.result_root)
                self.assertEqual(len(roots), 1)


if __name__ == "__main__":
    unittest.main()
