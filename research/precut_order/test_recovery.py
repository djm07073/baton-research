import itertools
import unittest

from recovery import Replica, Reply, recovery_choice


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.nodes = [Replica("block-B", i, 1, {"D1", "D2"}) for i in range(6)]

    def test_first_vote_same_view_equivocation_and_invalid_record(self):
        node = self.nodes[1]
        self.assertFalse(node.accept(0, "invalid"))
        self.assertTrue(node.accept(0, "D1"))
        self.assertFalse(node.accept(0, "D2"))
        self.assertTrue(node.accept(0, "D1"))

    def test_hidden_old_certificate_survives_every_recovery_report_set(self):
        for i in [1, 2, 3, 4]:
            self.assertTrue(self.nodes[i].accept(0, "D1"))
        # Byzantine node 0 signed D1 too: the old five-vote result exists but is hidden.
        replies = {i: self.nodes[i].query(1) for i in range(1, 6)}
        for liar_value in [None, "D2"]:
            reports = dict(replies)
            reports[0] = Reply("block-B", 1, 0, liar_value)
            for ids in itertools.combinations(range(6), 5):
                with self.subTest(liar=liar_value, ids=ids):
                    certificate = [reports[i] for i in ids]
                    self.assertEqual(recovery_choice("block-B", 1, certificate, 1), "D1")
                    self.assertFalse(self.nodes[5].accept(1, "D2", certificate))
        self.assertTrue(self.nodes[5].accept(1, "D1", list(replies.values())))

    def test_split_votes_can_recover_without_erasing_first_view_history(self):
        for i, value in [(1, "D1"), (2, "D1"), (3, "D1"), (4, "D2"), (5, "D2")]:
            self.assertTrue(self.nodes[i].accept(0, value))
        certificate = [self.nodes[i].query(1) for i in range(1, 6)]
        self.assertEqual(recovery_choice("block-B", 1, certificate, 1), "D1")
        self.assertTrue(all(self.nodes[i].accept(1, "D1", certificate) for i in range(1, 6)))
        next_certificate = [self.nodes[i].query(2) for i in range(1, 6)]
        self.assertEqual(recovery_choice("block-B", 2, next_certificate, 1), "D1")

    def test_query_fences_old_votes_and_same_view_reply_is_stable(self):
        node = self.nodes[1]
        self.assertTrue(node.accept(0, "D1"))
        first = node.query(1)
        self.assertEqual(first.accepted, "D1")
        self.assertFalse(node.accept(0, "D1"))
        certificate = [first] + [self.nodes[i].query(1) for i in [2, 3, 4, 5]]
        self.assertIsNone(recovery_choice("block-B", 1, certificate, 1))
        self.assertTrue(node.accept(1, "D2", certificate))
        self.assertEqual(node.query(1), first)
        self.assertEqual(node.query(2).accepted, "D2")
        with self.assertRaises(ValueError):
            node.query(1)

    def test_recovery_evidence_rejects_replay_and_nonquorum(self):
        valid = [self.nodes[i].query(1) for i in range(1, 6)]
        cases = [
            ("old view", "block-B", 2, valid),
            ("another instance", "block-C", 1, valid),
            ("too few", "block-B", 1, valid[:4]),
            ("duplicate sender", "block-B", 1, valid[:4] + valid[:1]),
            ("nonmember", "block-B", 1, valid[:4] + [Reply("block-B", 1, 6, None)]),
            ("not a selected quorum", "block-B", 1, valid + [Reply("block-B", 1, 0, None)]),
        ]
        for name, instance, view, certificate in cases:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    recovery_choice(instance, view, certificate, 1)

    def test_single_byzantine_reply_cannot_force_an_invalid_value(self):
        certificate = [self.nodes[i].query(1) for i in [1, 2, 3, 4]]
        certificate.append(Reply("block-B", 1, 0, "invalid"))
        self.assertIsNone(recovery_choice("block-B", 1, certificate, 1))
        self.assertFalse(self.nodes[5].accept(1, "invalid", certificate))
        self.assertTrue(self.nodes[5].accept(1, "D2", certificate))


if __name__ == "__main__":
    unittest.main()
