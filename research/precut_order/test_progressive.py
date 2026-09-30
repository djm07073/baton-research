import itertools
import unittest

from progressive import (CounterExecution, extend_round_robin,
                         negative_excludes_quorum, speculate)


A1, A2, B1, B2, C1, C2 = [(p, h) for p in "ABC" for h in (1, 2)]
PRIORITY = ("A", "B", "C")


class ProgressiveOrderingTests(unittest.TestCase):
    def test_round_robin_is_relative_to_last_agreed_boundary(self):
        for name, prefix, tips, expected in [
            ("ordinary zip", (), {"A": 2, "B": 2, "C": 1},
             (A1, B1, C1, A2, B2)),
            ("missing lane deferred", (), {"A": 0, "B": 1, "C": 1},
             (B1, C1)),
            ("late A never inserted in decided prefix", (B1, C1),
             {"A": 1, "B": 2, "C": 2}, (B1, C1, A1, B2, C2)),
            ("unequal heights reset relative offset", (A1, A2, B1),
             {"A": 3, "B": 2, "C": 1}, (A1, A2, B1, ("A", 3), B2, C1)),
        ]:
            with self.subTest(name=name):
                self.assertEqual(extend_round_robin(prefix, tips, PRIORITY), expected)

    def test_invalid_boundaries_cannot_rewrite_history(self):
        for name, prefix, tips, priority in [
            ("rewind B", (B1,), {"A": 0, "B": 0, "C": 0}, PRIORITY),
            ("gap in protected producer", (A2,), {"A": 2, "B": 0, "C": 0}, PRIORITY),
            ("duplicate block", (B1, B1), {"A": 0, "B": 1, "C": 0}, PRIORITY),
            ("missing lane boundary", (), {"A": 0, "B": 1}, PRIORITY),
            ("unknown lane", (), {"A": 0, "B": 1, "D": 1}, PRIORITY),
            ("negative height", (), {"A": -1, "B": 0, "C": 0}, PRIORITY),
            ("fractional height", (), {"A": 1.5, "B": 0, "C": 0}, PRIORITY),
            ("duplicate priority", (), {"A": 0, "B": 0}, ("A", "B", "A")),
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                extend_round_robin(prefix, tips, priority)

    def test_speculation_runs_without_any_agreement_and_holds_producer_gaps(self):
        for name, prefix, received, expected in [
            ("no agreed prefix", (), {B1, C1}, (B1, C1)),
            ("late predecessor changes open order", (), {A1, B1, C1}, (A1, B1, C1)),
            ("late predecessor cannot change protected order", (B1, C1),
             {A1, B1, C1}, (B1, C1, A1)),
            ("A2 waits for A1 but others execute", (), {A2, B1, C1}, (B1, C1)),
            ("protected predecessor need not be in received set", (A1,), {A2, B1},
             (A1, A2, B1)),
        ]:
            with self.subTest(name=name):
                self.assertEqual(speculate(prefix, received, PRIORITY), expected)

    def test_execution_reuses_only_matching_read_inputs(self):
        for name, first, protected, expected_order, expected_state, expected_executed, expected_reused in [
            ("no protection: B reruns", (B1, C1), (), (A1, B1, C1),
             {"x": 2, "y": 1}, (A1, B1), (C1,)),
            ("protected B,C: only new A executes", (B1, C1), (B1, C1),
             (B1, C1, A1), {"x": 2, "y": 1}, (A1,), (B1, C1)),
            ("protected prefix does not protect conflicting open suffix", (B1, C1, B2, C2),
             (B1, C1), (B1, C1, A1, B2, C2), {"x": 3, "y": 2},
             (A1, B2), (B1, C1, C2)),
        ]:
            with self.subTest(name=name):
                engine = CounterExecution({A1: "x", B1: "x", B2: "x", C1: "y", C2: "y"})
                initial_state = {"x": 1, "y": 1} if len(first) == 2 else {"x": 2, "y": 2}
                self.assertEqual(engine.run(first), (initial_state, first, ()))
                order = speculate(protected, set(first) | {A1}, PRIORITY)
                self.assertEqual(order, expected_order)
                self.assertEqual(engine.run(order),
                                 (expected_state, expected_executed, expected_reused))

    def test_order_agreement_can_require_reexecution_of_existing_work(self):
        engine = CounterExecution({A1: "x", B1: "x", C1: "y"})
        engine.run((A1, B1, C1))
        # A replica had A early, but consensus chose B,C first; local execution is not a veto.
        self.assertEqual(engine.run((B1, C1, A1)),
                         ({"x": 2, "y": 1}, (B1, A1), (C1,)))

    def test_order_only_change_of_independent_blocks_needs_no_rerun(self):
        engine = CounterExecution({A1: "x", B1: "y"})
        engine.run((B1, A1))
        self.assertEqual(engine.run((A1, B1)), ({"x": 1, "y": 1}, (), (A1, B1)))

    def test_every_contiguous_arrival_schedule_preserves_protected_prefix(self):
        for arrival in itertools.permutations((A1, A2, B1, B2, C1, C2)):
            received, protected = set(), ()
            for block in arrival:
                received.add(block)
                candidate = speculate(protected, received, PRIORITY)
                self.assertEqual(candidate[:len(protected)], protected)
                self.assertEqual(len(set(candidate)), len(candidate))
                protected = candidate  # An external agreement event, not an implementation of it.
            self.assertEqual(set(protected), {A1, A2, B1, B2, C1, C2})


class NegativeEvidenceTests(unittest.TestCase):
    def test_honest_intersection_required_for_mutually_exclusive_statements(self):
        for name, n, f, q, r, expected in [
            ("3f+1 plain f+1 negative insufficient", 4, 1, 3, 2, False),
            ("3f+1 supermajority negative", 4, 1, 3, 3, True),
            ("5f+1 plain f+1 negative insufficient", 6, 1, 5, 2, False),
            ("5f+1 2f+1 negative excludes 4f+1 positive", 6, 1, 5, 3, True),
            ("but not a smaller DA quorum", 6, 1, 4, 3, False),
            ("larger negative excludes DA quorum", 6, 1, 4, 4, True),
        ]:
            with self.subTest(name=name):
                self.assertEqual(negative_excludes_quorum(n, f, q, r), expected)

    def test_f_plus_one_nonendorsements_can_coexist_with_positive_certificate(self):
        positive, negative, byzantine = {0, 1, 2, 3, 4}, {0, 5}, {0}
        self.assertEqual(positive & negative, byzantine)
        self.assertFalse(negative_excludes_quorum(6, 1, len(positive), len(negative)))


if __name__ == "__main__":
    unittest.main()
