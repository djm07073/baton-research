import unittest

import experiment as e


class ExperimentTests(unittest.TestCase):
    def test_unit_worker_scheduler(self):
        self.assertTrue(hasattr(e, "schedule_time"), "worker timing not implemented")
        rows = [
            ("serial", ("A", "B"), (("A", "B"),), ("A", "B"), 2, 2),
            ("parallel", ("A", "B"), (), ("A", "B"), 2, 1),
            ("one worker", ("A", "B"), (), ("A", "B"), 1, 2),
            ("cache hit", ("A", "B"), (("A", "B"),), (), 2, 0),
            ("cached descendant", ("A", "B", "C"), (("A", "B"), ("B", "C")),
             ("A", "C"), 2, 2),
        ]
        for name, nodes, edges, dirty, workers, expected in rows:
            with self.subTest(name=name):
                self.assertEqual(e.schedule_time(nodes, edges, dirty, workers), expected)

    def test_trial_is_reproducible_and_checks_actual_reuse(self):
        self.assertTrue(hasattr(e, "trial"), "experiment not implemented")
        a, b = e.trial(1, 0.7), e.trial(1, 0.7)
        self.assertEqual(a, b)
        self.assertEqual(len(a["modes"]), 5)
        for row in a["modes"].values():
            self.assertTrue(row["same_result"])
            self.assertLessEqual(row["mean_reexecuted"], 6)
            self.assertLessEqual(row["quorum_work_rounds"], 6)


if __name__ == "__main__":
    unittest.main()
