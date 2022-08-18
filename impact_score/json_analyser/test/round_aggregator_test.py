import unittest

from impact_score.json_analyser.core.analyser_round_aggregator import AnalyserRound
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


class RoundAggregatorTest(unittest.TestCase):
    def setUp(self) -> None:
        a = analyser_pool.acquire()
        a.set_match(74099)
        self.ar = AnalyserRound(a)
        self.ar.pick_round(2)

    def test_generate_full_round(self):
        actual = self.ar.generate_full_round()
        expected = 1
        self.assertEqual(actual, expected)  # add assertion here


if __name__ == '__main__':
    unittest.main()
