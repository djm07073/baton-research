"""Hand-checked attacks and an independent serial oracle for block DAG selection."""

import itertools
import random
import unittest
from dataclasses import replace

import selection as m


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(m, "Block"), "block selection model not implemented")
        self.base = {"x": 10, "y": 0, "z": 0}
        self.ctx = m.Context("epoch-1", "cut-9", m.digest(self.base),
                             (("A", 0), ("B", 0), ("C", 0)),
                             ("A", "B", "C"), tuple(range(6)), 1)

    def block(self, name, lane, height=1, parent=None, ops=()):
        return m.Block(name, lane, height, parent, tuple(ops))

    def view(self, signer, blocks, order, executed=(), sequence=1):
        edges = m.edges_for_order(blocks, order)
        return m.View(signer, sequence, self.ctx.base_id,
                      tuple(sorted(blocks)), tuple(sorted(edges)), tuple(sorted(executed)))

    def inputs(self, blocks, views=(), selected=None):
        store = {m.digest(v): v for v in views}
        refs = tuple(m.ViewRef(v.signer, v.sequence, m.digest(v)) for v in views)
        inp = m.Input(self.ctx, tuple(sorted(selected or blocks)), refs)
        return inp, blocks, store

    def test_rank_is_relative_and_does_not_use_payload_hash(self):
        ctx = replace(self.ctx, tips=(("A", 50), ("B", 2), ("C", 0)),
                      lanes=("B", "A", "C"))
        a = self.block("A51", "A", 51)
        b = self.block("B3", "B", 3)
        self.assertEqual(m.rank(ctx, a), (1, 1))
        self.assertEqual(m.rank(ctx, b), (1, 0))
        self.assertEqual(m.rank(ctx, replace(a, id="different-payload")), (1, 1))

    def test_selection_tie_break_does_not_reintroduce_payload_hash_grinding(self):
        blocks = {"zzz": self.block("zzz", "A", ops=(("add", "x", 1),)),
                  "aaa": self.block("aaa", "B", ops=(("add", "x", 1),))}
        plan = m.select(*self.inputs(blocks))
        self.assertEqual(plan.edges, (("zzz", "aaa"),))

    def test_cycle_preferences_produce_complete_acyclic_block_plan(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", i + 1),))
                  for i, n in enumerate("ABC")}
        orders = (("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B"))
        views = [self.view(i, blocks, orders[i % 3], blocks) for i in range(6)]
        inp, bs, vs = self.inputs(blocks, views)
        result = m.select(inp, bs, vs)
        self.assertEqual(set(result.nodes), set(blocks))
        self.assertEqual(len(result.edges), 3)
        self.assertEqual(len(m.topological(result.nodes, result.edges, bs, self.ctx)), 3)
        self.assertEqual(m.execute(self.ctx, result, bs, self.base).state["x"], 16)

    def test_selection_preserves_popular_executed_view_instead_of_forcing_rank(self):
        blocks = {"A": self.block("A", "A", ops=(("add", "x", 1),)),
                  "B": self.block("B", "B", ops=(("copy", "y", "x"),))}
        views = [self.view(i, blocks, ("B", "A"), blocks) for i in range(5)]
        views.append(self.view(5, blocks, ("A", "B"), blocks))
        result = m.select(*self.inputs(blocks, views))
        self.assertEqual(result.edges, (("B", "A"),))
        self.assertEqual(m.execute(self.ctx, result, blocks, self.base).state,
                         {"x": 11, "y": 10, "z": 0})

    def test_independent_worker_order_is_not_a_dependency(self):
        blocks = {"A": self.block("A", "A", ops=(("add", "x", 1),)),
                  "B": self.block("B", "B", ops=(("add", "y", 1),))}
        views = [self.view(0, blocks, ("A", "B"), blocks),
                 self.view(1, blocks, ("B", "A"), blocks)]
        result = m.select(*self.inputs(blocks, views))
        self.assertEqual(result.edges, ())
        for order in (("A", "B"), ("B", "A")):
            execution = m.execute(self.ctx, result, blocks, self.base, order=order)
            self.assertEqual(execution.state, {"x": 11, "y": 1, "z": 0})

    def test_input_permutations_do_not_change_selected_root(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", i),))
                  for i, n in enumerate("ABC")}
        views = [self.view(i, blocks, tuple(p), blocks)
                 for i, p in enumerate(itertools.permutations("ABC"))]
        inp, bs, vs = self.inputs(blocks, views)
        expected = m.select(inp, bs, vs).root
        rng = random.Random(12)
        for _ in range(20):
            refs = list(inp.views)
            rng.shuffle(refs)
            names = list(bs)
            rng.shuffle(names)
            candidate = replace(inp, nodes=tuple(names), views=tuple(refs))
            self.assertEqual(m.select(candidate, {n: bs[n] for n in names}, vs).root,
                             expected)

    def test_committed_missing_data_waits_instead_of_becoming_empty(self):
        blocks = {"A": self.block("A", "A", ops=(("add", "x", 1),))}
        v = self.view(0, blocks, ("A",), blocks)
        inp, bs, vs = self.inputs(blocks, (v,))
        for label, block_store, view_store in (("view", bs, {}), ("block", {}, vs)):
            with self.subTest(label=label), self.assertRaises(m.NeedData):
                m.select(inp, block_store, view_store)

    def test_tip_expansion_completes_membership_without_selecting_local_extras(self):
        ctx = replace(self.ctx, tips=(("A", 1), ("B", 1), ("C", 0)))
        anchors = (("A", "A1"), ("B", "B1"), ("C", None))
        tips = (("A", 3, "A3"), ("B", 2, "B2"), ("C", 0, None))
        blocks = {
            "A2": self.block("A2", "A", 2, "A1", (("set", "x", 20),)),
            "A3": self.block("A3", "A", 3, "A2", (("copy", "y", "x"),)),
            "B2": self.block("B2", "B", 2, "B1", (("add", "z", 1),)),
            "B3": self.block("B3", "B", 3, "B2", (("set", "x", 999),)),
        }
        # The report omits the selected A3 tip; its omission must not censor A3.
        view = m.View(0, 1, ctx.base_id, ("A2",), (), ("A2",))
        refs = (m.ViewRef(0, 1, m.digest(view)),)
        roots = set()
        for reversed_input in (False, True):
            ordering = tuple(reversed(tips)) if reversed_input else tips
            store = dict(reversed(list(blocks.items()))) if reversed_input else blocks
            inp = m.input_from_tips(ctx, anchors, ordering, store, views=refs)
            self.assertEqual(inp.nodes, ("A2", "A3", "B2"))
            plan = m.select(inp, store, {m.digest(view): view})
            roots.add(plan.root)
            self.assertEqual(plan.edges, (("A2", "A3"),))
            self.assertEqual(plan.accepted_signers, (0,))
            self.assertEqual(m.execute(ctx, plan, store, self.base).state,
                             {"x": 20, "y": 20, "z": 1})
        self.assertEqual(len(roots), 1)

    def test_selected_tip_or_ancestor_missing_requires_exact_data_recovery(self):
        anchors = (("A", None), ("B", None), ("C", None))
        tips = (("A", 2, "A2"), ("B", 0, None), ("C", 0, None))
        blocks = {"A1": self.block("A1", "A"),
                  "A2": self.block("A2", "A", 2, "A1")}
        for missing in ("A1", "A2"):
            with self.subTest(missing=missing):
                store = {k: v for k, v in blocks.items() if k != missing}
                with self.assertRaises(m.NeedData) as raised:
                    m.input_from_tips(self.ctx, anchors, tips, store)
                self.assertEqual(raised.exception.args, ((missing,),))
        recovered = m.input_from_tips(self.ctx, anchors, tips, blocks)
        self.assertEqual(recovered.nodes, ("A1", "A2"))

    def test_tip_descriptor_cannot_guess_missing_slots_or_replace_ancestry(self):
        ctx = replace(self.ctx, tips=(("A", 1), ("B", 0), ("C", 0)))
        anchors = (("A", "A1"), ("B", None), ("C", None))
        unchanged = (("A", 1, "A1"), ("B", 0, None), ("C", 0, None))
        advancing = (("A", 2, "A2"),) + unchanged[1:]
        cases = (
            ("missing slot", ctx, anchors, unchanged[:-1], {}),
            ("duplicate slot", ctx, anchors, unchanged + unchanged[:1], {}),
            ("unknown lane", ctx, anchors, unchanged + (("D", 0, None),), {}),
            ("missing anchor", ctx, anchors[:-1], unchanged, {}),
            ("unknown tip", ctx, anchors, (("A", 2, None),) + unchanged[1:], {}),
            ("regression", ctx, anchors, (("A", 0, None),) + unchanged[1:], {}),
            ("same-height fork", ctx, anchors,
             (("A", 1, "other-A1"),) + unchanged[1:], {}),
            ("wrong parent", ctx, anchors, advancing,
             {"A2": self.block("A2", "A", 2, "other-A1")}),
            ("wrong lane", ctx, anchors, advancing,
             {"A2": self.block("A2", "B", 2, "A1")}),
            ("wrong height", ctx, anchors, advancing,
             {"A2": self.block("A2", "A", 3, "A1")}),
            ("wrong identity", ctx, anchors, advancing,
             {"A2": self.block("other-A2", "A", 2, "A1")}),
            ("bound before fetch", replace(ctx, max_blocks=1), anchors,
             (("A", 3, "A3"),) + unchanged[1:], {}),
        )
        for label, context, starts, ends, store in cases:
            with self.subTest(label=label), self.assertRaises(m.InvalidInput):
                m.input_from_tips(context, starts, ends, store)
        inp = m.input_from_tips(ctx, anchors, unchanged, {})
        self.assertEqual(inp.nodes, ())
        self.assertEqual(m.execute(ctx, m.select(inp, {}, {}), {}, self.base).state,
                         self.base)

    def test_invalid_and_equivocating_reports_are_bounded_preferences(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", 1),)) for n in "AB"}
        good = self.view(0, blocks, ("A", "B"), blocks)
        bad_cases = {
            "cycle": replace(good, signer=1, edges=(("A", "B"), ("B", "A"))),
            "missing conflict": replace(good, signer=1, edges=()),
            "wrong base": replace(good, signer=1, base_id="stale"),
            "unknown signer": replace(good, signer=999),
            "executed outside view": replace(good, signer=1, executed=("not-a-block",)),
        }
        for label, bad in bad_cases.items():
            with self.subTest(label=label):
                result = m.select(*self.inputs(blocks, (good, bad)))
                self.assertEqual(result.accepted_signers, (0,))
        fork1 = self.view(1, blocks, ("A", "B"), blocks)
        fork2 = self.view(1, blocks, ("B", "A"), blocks)
        result = m.select(*self.inputs(blocks, (good, fork1, fork2, fork1)))
        self.assertEqual(result.accepted_signers, (0,))
        result = m.select(*self.inputs(blocks, (good, good, good)))
        self.assertEqual(result.accepted_signers, (0,))

    def test_duplicate_lane_position_is_not_resolved_by_hash(self):
        blocks = {"A": self.block("A", "A"), "Afork": self.block("Afork", "A")}
        with self.assertRaises(m.InvalidInput):
            m.select(*self.inputs(blocks))

    def test_lane_edges_must_be_preserved_across_state_components(self):
        blocks = {
            "A1": self.block("A1", "A", ops=(("set", "x", 1),)),
            "A2": self.block("A2", "A", 2, "A1", (("set", "y", 2),)),
            "B1": self.block("B1", "B", ops=(("set", "y", 3),)),
            "B2": self.block("B2", "B", 2, "B1", (("set", "x", 4),)),
        }
        views = [self.view(0, blocks, ("B1", "B2", "A1", "A2"), blocks),
                 self.view(1, blocks, ("A1", "A2", "B1", "B2"), blocks)]
        result = m.select(*self.inputs(blocks, views))
        self.assertIn(("A1", "A2"), result.edges)
        self.assertIn(("B1", "B2"), result.edges)
        self.assertEqual(len(m.topological(result.nodes, result.edges, blocks, self.ctx)), 4)

    def test_late_writer_invalidates_reader_but_keeps_independent_cache(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 20),)),
                  "B": self.block("B", "B", ops=(("copy", "y", "x"),)),
                  "C": self.block("C", "C", ops=(("add", "z", 1),))}
        first = m.select(*self.inputs(blocks, selected=("B", "C")))
        cache = m.execute(self.ctx, first, blocks, self.base)
        final = m.select(*self.inputs(blocks))
        execution = m.execute(self.ctx, final, blocks, self.base, cache=cache)
        self.assertEqual(execution.reused, ("C",))
        self.assertEqual(set(execution.ran), {"A", "B"})
        self.assertEqual(execution.state, {"x": 20, "y": 20, "z": 1})

    def test_excluded_writer_is_not_reused_through_projection(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 20),)),
                  "B": self.block("B", "B", ops=(("copy", "y", "x"),))}
        full = m.select(*self.inputs(blocks))
        cache = m.execute(self.ctx, full, blocks, self.base)
        projected = m.select(*self.inputs(blocks, selected=("B",)))
        execution = m.execute(self.ctx, projected, blocks, self.base, cache=cache)
        self.assertEqual(execution.reused, ())
        self.assertEqual(execution.state, {"x": 10, "y": 10, "z": 0})

    def test_changed_dependencies_do_not_force_rerun_when_actual_reads_are_unchanged(self):
        cases = [
            ("blind write", (("set", "x", 20),), (("set", "x", 5),),
             {"x": 20, "y": 0, "z": 0}),
            ("same read value", (("copy", "y", "x"),), (("set", "x", 10),),
             {"x": 10, "y": 10, "z": 0}),
        ]
        for label, b_ops, a_ops, expected in cases:
            with self.subTest(label=label):
                blocks = {"A": self.block("A", "A", ops=a_ops),
                          "B": self.block("B", "B", ops=b_ops)}
                initial = m.select(*self.inputs(blocks, selected=("B",)))
                cache = m.execute(self.ctx, initial, blocks, self.base)
                final = m.select(*self.inputs(blocks))
                repaired = m.execute(self.ctx, final, blocks, self.base, cache=cache)
                self.assertEqual(repaired.reused, ("B",))
                self.assertEqual(repaired.state, expected)

    def test_reuse_prediction_tracks_read_inputs_not_every_ordering_ancestor(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 5),)),
                  "B": self.block("B", "B", ops=(("set", "x", 20),)),
                  "C": self.block("C", "C", ops=(("copy", "y", "x"),))}
        alone = m.fingerprints(self.ctx, {"B": blocks["B"]}, ("B",))
        together = m.fingerprints(self.ctx, blocks, ("A", "B", "C"))
        self.assertEqual(alone["B"], together["B"])
        opposite = m.fingerprints(self.ctx, blocks, ("B", "A", "C"))
        self.assertNotEqual(together["C"], opposite["C"])

    def test_read_validation_is_bound_to_block_program(self):
        blocks = {"B": self.block("B", "B", ops=(("set", "x", 20),))}
        initial = m.select(*self.inputs(blocks))
        cache = m.execute(self.ctx, initial, blocks, self.base)
        changed = {"B": self.block("B", "B", ops=(("set", "x", 999),))}
        final = m.select(*self.inputs(changed))
        repaired = m.execute(self.ctx, final, changed, self.base, cache=cache)
        self.assertEqual(repaired.reused, ())
        self.assertEqual(repaired.state["x"], 999)

    def test_root_claim_is_not_used_as_an_execution_result(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 20),))}
        result = m.select(*self.inputs(blocks))
        cache = m.execute(self.ctx, result, blocks, self.base)
        forged = replace(cache, records={"A": replace(cache.records["A"],
                                                      writes=(("x", 999),))})
        # Remote reports are never accepted as the node's authenticated local cache.
        with self.assertRaises(m.InvalidInput):
            m.execute(self.ctx, result, blocks, self.base, remote_result=forged)
        self.assertEqual(m.execute(self.ctx, result, blocks, self.base).state["x"], 20)

    def test_quorum_binds_plan_subject_and_distinct_signers(self):
        cases = [
            ("matching", [(i, "S", "R") for i in range(4)], True),
            ("too few", [(i, "S", "R") for i in range(3)], False),
            ("duplicates", [(0, "S", "R")] * 4, False),
            ("mixed subject", [(0, "S", "R"), (1, "S", "R"),
                               (2, "other", "R"), (3, "S", "R")], False),
            ("mixed result", [(0, "S", "R"), (1, "S", "R"),
                              (2, "S", "bad"), (3, "S", "R")], False),
            ("outsiders", [(i, "S", "R") for i in (0, 1, 8, 9)], False),
        ]
        for label, votes, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(m.certified(self.ctx, "S", "R", votes), expected)

    def test_fallback_bounds_search_and_completes_every_block(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", i),))
                  for i, n in enumerate("ABC")}
        inp, bs, vs = self.inputs(blocks)
        a = m.select(inp, bs, vs, exact_limit=0, beam_width=1)
        b = m.select(inp, dict(reversed(list(bs.items()))), vs,
                     exact_limit=0, beam_width=1)
        self.assertEqual(a.root, b.root)
        self.assertEqual(set(a.nodes), set(blocks))
        self.assertLessEqual(a.expanded, 6)

    def test_no_evidence_or_one_byzantine_claim_cannot_trigger_search(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", 1),)) for n in "ABC"}
        liar = self.view(5, blocks, ("C", "B", "A"), blocks)
        for views in ((), (liar,)):
            with self.subTest(report_count=len(views)):
                plan = m.select(*self.inputs(blocks, views))
                self.assertEqual(plan.expanded, 0)
                self.assertEqual(m.topological(plan.nodes, plan.edges, blocks, self.ctx),
                                 ("A", "B", "C"))

    def test_input_budget_is_checked_before_fetch_and_bad_report_cannot_expand_it(self):
        self.assertIn("max_blocks", m.Context.__dataclass_fields__, "missing input bound")
        blocks = {n: self.block(n, n, ops=(("add", "x", 1),)) for n in "AB"}
        inp, bs, vs = self.inputs(blocks)
        bounded = replace(inp, context=replace(self.ctx, max_blocks=1))
        with self.assertRaises(m.InvalidInput):
            m.select(bounded, {}, vs)
        good = self.view(0, blocks, ("A", "B"), blocks)
        inflated = replace(good, signer=1, edges=(("A", "B"),) * 100)
        plan = m.select(*self.inputs(blocks, (good, inflated)))
        self.assertEqual(plan.accepted_signers, (0,))

    def test_report_cannot_create_an_unavailable_reference(self):
        blocks = {"A": self.block("A", "A", ops=(("add", "x", 1),))}
        bogus = m.View(0, 1, self.ctx.base_id, ("made-up-block",), (), ())
        result = m.select(*self.inputs(blocks, (bogus,)))
        self.assertEqual(result.accepted_signers, ())
        self.assertEqual(result.nodes, ("A",))
        extra = self.block("made-up-block", "B")
        inp, bs, vs = self.inputs(blocks, (bogus,))
        replica_with_extra_data = m.select(inp, {**bs, extra.id: extra}, vs)
        self.assertEqual(replica_with_extra_data.root, result.root)

    def test_committed_extra_evidence_is_resolved_but_never_becomes_a_selected_block(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", 1),)) for n in "AB"}
        view = self.view(0, blocks, ("A", "B"), blocks)
        inp, bs, vs = self.inputs(blocks, (view,), selected=("B",))
        inp = replace(inp, evidence=("A",))
        plan = m.select(inp, bs, vs)
        self.assertEqual(plan.nodes, ("B",))
        self.assertEqual(plan.accepted_signers, (0,))
        with self.assertRaises(m.NeedData):
            m.select(inp, {"B": blocks["B"]}, vs)

    def test_selected_plan_rejects_a_leader_omitted_conflict(self):
        blocks = {n: self.block(n, n, ops=(("add", "x", 1),)) for n in "AB"}
        result = m.select(*self.inputs(blocks))
        forged = replace(result, edges=())
        self.assertFalse(m.verify_proposal(*self.inputs(blocks), proposed=forged))

    def test_read_history_change_invalidates_descendant_with_same_direct_writer(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 20),)),
                  "B": self.block("B", "B", ops=(("copy", "y", "x"),)),
                  "C": self.block("C", "C", ops=(("copy", "z", "y"),))}
        initial = m.select(*self.inputs(blocks, selected=("B", "C")))
        cache = m.execute(self.ctx, initial, blocks, self.base)
        reports = [self.view(i, blocks, ("A", "B", "C"), blocks) for i in range(6)]
        final = m.select(*self.inputs(blocks, reports))
        repaired = m.execute(self.ctx, final, blocks, self.base, cache=cache)
        self.assertEqual(repaired.reused, ())
        self.assertEqual(repaired.state, {"x": 20, "y": 20, "z": 20})

    def test_failed_transfer_removes_old_speculative_writes(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 0),)),
                  "B": self.block("B", "B", ops=(("transfer", "x", "y", 10),))}
        initial = m.select(*self.inputs(blocks, selected=("B",)))
        cache = m.execute(self.ctx, initial, blocks, self.base)
        self.assertEqual(cache.state, {"x": 0, "y": 10, "z": 0})
        final = m.select(*self.inputs(blocks))
        repaired = m.execute(self.ctx, final, blocks, self.base, cache=cache)
        self.assertEqual(repaired.records["B"].status, (False,))
        self.assertEqual(repaired.state, {"x": 0, "y": 0, "z": 0})

    def test_critical_path_cost_distinguishes_serial_and_parallel_repair(self):
        blocks = {"A": self.block("A", "A", ops=(("set", "x", 20),)),
                  "B": self.block("B", "B", ops=(("copy", "y", "x"),)),
                  "C": self.block("C", "C", ops=(("copy", "z", "y"),))}
        plan = m.select(*self.inputs(blocks))
        self.assertEqual(m.repair_cost(self.ctx, plan, ("A", "B")), (2, 2))
        independent = replace(plan, edges=())
        self.assertEqual(m.repair_cost(self.ctx, independent, ("A", "B")), (1, 2))


if __name__ == "__main__":
    unittest.main()
