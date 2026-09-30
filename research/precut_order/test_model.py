import itertools
import unittest

from model import is_closed_cut, ready_batches, supported_dependencies


class DependencyExecutionTests(unittest.TestCase):
    def test_supported_edges_preserve_honest_evidence_and_mandatory_ancestry(self):
        reports = {0: {"invented"}, 1: {"A"}, 2: {"A", "B"}, 3: {"B"}, 4: set()}
        self.assertEqual(supported_dependencies(reports, 6, 1, {"parent"}), {"A", "B", "parent"})
        for name, bad_reports, n, f in [
            ("insufficient report quorum", {i: set() for i in range(4)}, 6, 1),
            ("wrong committee profile", {i: set() for i in range(3)}, 4, 1),
            ("nonmember substituted", {i: set() for i in [0, 1, 2, 3, 6]}, 6, 1),
        ]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    supported_dependencies(bad_reports, n, f)

    def test_readiness_and_closed_cycles(self):
        cases = [
            ("missing predecessor", {"B": {"A"}}, {"B"}, set(), ()),
            ("known but undecided", {"A": set(), "B": {"A"}}, {"B"}, set(), ()),
            ("dependency before consumer", {"A": {"B"}, "B": set()}, {"A", "B"}, set(), (("B",), ("A",))),
            ("independent block proceeds", {"B": {"A"}, "C": set()}, {"B", "C"}, set(), (("C",),)),
            ("cycle closes as one batch", {"A": {"B"}, "B": {"A"}}, {"A", "B"}, set(), (("A", "B"),)),
            ("cycle waits for outside predecessor", {"A": {"B", "C"}, "B": {"A"}}, {"A", "B"}, set(), ()),
            ("already executed is not repeated", {"A": set(), "B": {"A"}}, {"A", "B"}, {"A"}, (("B",),)),
        ]
        for name, deps, committed, executed, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(ready_batches(deps, committed, executed), expected)

    def test_cut_rejects_omitted_dependency_and_split_cycle(self):
        deps = {"A": {"B"}, "B": {"A"}, "C": set(), "D": {"C"}}
        for name, committed, selected, previous, expected in [
            ("closed cycle", set(deps), {"A", "B"}, set(), True),
            ("split cycle", set(deps), {"A"}, set(), False),
            ("missing predecessor", set(deps), {"D"}, set(), False),
            ("uncommitted member", {"C"}, {"C", "D"}, set(), False),
            ("canonical history dropped", set(deps), {"A", "B"}, {"C"}, False),
            ("extends prior cut", set(deps), {"C", "D"}, {"C"}, True),
        ]:
            with self.subTest(name=name):
                self.assertEqual(is_closed_cut(deps, committed, selected, previous), expected)

    def test_executed_state_cannot_have_missing_dependencies(self):
        with self.assertRaises(ValueError):
            ready_batches({"A": {"B"}}, {"A"}, {"A"})

    def test_deciding_each_block_does_not_close_an_extending_chain(self):
        previous = {}
        for length in range(1, 20):
            natural = list(range(length + 2))
            odd_swaps, even_swaps = natural[:], natural[:]
            for i in range(0, len(natural) - 1, 2):
                odd_swaps[i], odd_swaps[i + 1] = odd_swaps[i + 1], odd_swaps[i]
            for i in range(1, len(natural) - 1, 2):
                even_swaps[i], even_swaps[i + 1] = even_swaps[i + 1], even_swaps[i]
            deps = {}
            for block in range(length):
                reports = {0: {block + 1}}
                for validator, order in enumerate([odd_swaps, even_swaps, natural, natural], 1):
                    reports[validator] = set(order[:order.index(block)])
                deps[block] = supported_dependencies(reports, 6, 1)
                self.assertIn(block + 1, deps[block])
            for block, old_record in previous.items():
                self.assertEqual(deps[block], old_record)
            self.assertEqual(ready_batches(deps, set(deps)), ())
            self.assertFalse(is_closed_cut(deps, set(deps), set(deps)))
            previous = deps

    def test_cut_size_cap_can_exclude_every_nonempty_closed_selection(self):
        deps = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
        self.assertEqual(ready_batches(deps, set(deps)), (("A", "B", "C"),))
        for size in (1, 2):
            for selected in itertools.combinations(deps, size):
                self.assertFalse(is_closed_cut(deps, set(deps), set(selected)))

    def test_exhaustive_three_node_closed_execution(self):
        nodes = "ABC"
        edges = [(a, b) for a in nodes for b in nodes if a != b]
        checked = 0
        for mask in range(1 << len(edges)):
            deps = {a: set() for a in nodes}
            for i, (a, b) in enumerate(edges):
                if mask & (1 << i):
                    deps[a].add(b)
            for committed_mask in range(1 << len(nodes)):
                committed = {a for i, a in enumerate(nodes) if committed_mask & (1 << i)}
                batches = ready_batches(deps, committed)
                done = set()
                for batch in batches:
                    self.assertFalse(done.intersection(batch))
                    self.assertTrue(set(batch) <= committed)
                    for a in batch:
                        self.assertTrue(deps[a] <= done.union(batch))
                    done.update(batch)
                # Independent greatest-fixed-point oracle, not the SCC implementation.
                possible = set(committed)
                while any(not deps[a] <= possible for a in possible):
                    possible = {a for a in possible if deps[a] <= possible}
                self.assertEqual(done, possible)
                # A later node cannot change old dependency records or re-execute done.
                for late_mask in range(1 << len(nodes)):
                    extended = {a: set(d) for a, d in deps.items()}
                    extended["D"] = {a for i, a in enumerate(nodes) if late_mask & (1 << i)}
                    later = ready_batches(extended, committed | {"D"}, done)
                    later_nodes = {a for batch in later for a in batch}
                    self.assertFalse(done & later_nodes)
                    self.assertEqual(later_nodes & set(nodes), set())
                    self.assertEqual("D" in later_nodes, extended["D"] <= done)
                    checked += 1
        self.assertEqual(checked, 4096)


class CounterexampleTests(unittest.TestCase):
    def test_pairwise_votes_can_form_cycle(self):
        views = [("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B")]
        winners = {(a, b) for a, b in itertools.permutations("ABC", 2)
                   if sum(v.index(a) < v.index(b) for v in views) >= 2}
        self.assertEqual(winners, {("A", "B"), ("B", "C"), ("C", "A")})

    def test_relative_order_does_not_stop_late_predecessor(self):
        def execute(order):
            state = {"x": 0, "a": None, "b": None}
            for block in order:
                if block == "C":
                    state["x"] = 10
                elif block == "A":
                    state["a"] = state["x"] + 1
                else:
                    state["b"] = state["a"] + 1
            return state
        self.assertEqual(execute("AB")["b"], 2)
        self.assertEqual(execute("CAB")["b"], 12)

    def test_immutable_first_votes_can_deadlock_without_recovery(self):
        # n=6,f=1: five honest voters split 3/2; the Byzantine voter stays silent.
        assignments = ["P", "P", "P", "Q", "Q"]
        for quorum in (4, 5):
            self.assertLess(max(assignments.count("P"), assignments.count("Q")), quorum)

    def test_quorum_intersection_requires_more_than_honest_custody(self):
        for n, f, q, expected_minimum in [(6, 1, 4, 1), (6, 1, 5, 3), (11, 2, 7, 1), (11, 2, 9, 5)]:
            with self.subTest(n=n, f=f, q=q):
                quorums = list(map(set, itertools.combinations(range(n), q)))
                byzantine = set(range(f))
                minimum = min(len((a & b) - byzantine) for a in quorums for b in quorums)
                self.assertEqual(minimum, expected_minimum)
        self.assertEqual((set([0, 1]) & set([0, 2])) - {0}, set())

    def test_report_union_covers_every_conflicting_pair_in_small_committee(self):
        # Removing reports or requiring several votes per edge breaks this property.
        checked = 0
        for q in (4, 5):
            quorums = list(map(set, itertools.combinations(range(6), q)))
            for orders in itertools.product((False, True), repeat=5):
                a_first = {i + 1 for i, value in enumerate(orders) if value}
                b_first = set(range(1, 6)) - a_first
                for qa in quorums:
                    for qb in quorums:
                        a_depends_b = bool(qa & b_first)
                        b_depends_a = bool(qb & a_first)
                        self.assertTrue(a_depends_b or b_depends_a)
                        checked += 1
        self.assertEqual(checked, 8352)

    def test_per_edge_support_filter_can_drop_both_conflict_directions(self):
        a_first, b_first = {1, 2, 3}, {4, 5}
        qa, qb = {0, 1, 2, 3, 4}, {0, 2, 3, 4, 5}
        self.assertEqual((len(qa & b_first), len(qb & a_first)), (1, 2))
        self.assertFalse(len(qa & b_first) >= 3 or len(qb & a_first) >= 3)
        self.assertTrue(bool(qa & b_first) or bool(qb & a_first))

    def test_f_plus_one_edge_support_covers_conflicts_with_n_minus_f_reports(self):
        checked = 0
        for f in (1, 2):
            n, q = 5 * f + 1, 4 * f + 1
            honest = set(range(f, n))
            quorums = list(map(set, itertools.combinations(range(n), q)))
            for mask in range(1 << len(honest)):
                a_first = {node for i, node in enumerate(sorted(honest)) if mask & (1 << i)}
                b_first = honest - a_first
                counts_a = [len(reporters & b_first) for reporters in quorums]
                counts_b = [len(reporters & a_first) for reporters in quorums]
                for a_support in counts_a:
                    for b_support in counts_b:
                        self.assertTrue(a_support >= f + 1 or b_support >= f + 1)
                        checked += 1
        self.assertEqual(checked, 1_549_952)

    def test_f_plus_one_filter_is_unsafe_with_smaller_report_quorum(self):
        a_first, b_first = {1, 2, 3}, {4, 5}
        qa, qb = {0, 1, 2, 3}, {0, 3, 4, 5}
        self.assertEqual((len(qa & b_first), len(qb & a_first)), (0, 1))



if __name__ == "__main__":
    unittest.main()
