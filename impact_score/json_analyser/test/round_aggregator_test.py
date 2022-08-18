import unittest

from impact_score.json_analyser.core.analyser_round_aggregator import AnalyserRound
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


class RoundAggregatorTest(unittest.TestCase):
    ar = None

    def setUp(self) -> None:
        pass

    @classmethod
    def setUpClass(cls) -> None:
        a = analyser_pool.acquire()
        a.set_match(74099)
        cls.ar = AnalyserRound(a)
        cls.ar.pick_round(2)
        cls.pot = cls.ar.generate_full_round()
        cls.index = 4

    def test_regular_time(self):
        gamestate = self.pot[self.index]
        actual = gamestate["RegularTime"]
        expected = 64
        self.assertEqual(actual, expected)

    def test_spike_time(self):
        gamestate = self.pot[self.index]
        actual = gamestate["SpikeTime"]
        expected = 0
        self.assertEqual(actual, expected)

    def test_final_winner(self):
        gamestate = self.pot[self.index]
        actual = gamestate["FinalWinner"]
        expected = 0
        self.assertEqual(actual, expected)

    def test_round_time(self):
        gamestate = self.pot[self.index]
        actual = gamestate["RoundTime"]
        expected = 36009
        self.assertEqual(actual, expected)

    def test_atk_loadout_value(self):
        gamestate = self.pot[self.index]
        actual = gamestate["ATK_loadoutValue"]
        expected = 900
        self.assertEqual(actual, expected)

    def test_atk_shields(self):
        gamestate = self.pot[self.index]
        actual = gamestate["ATK_shields"]
        expected = 0
        self.assertEqual(actual, expected)

    def test_atk_remaining_creds(self):
        gamestate = self.pot[self.index]
        actual = gamestate["ATK_remainingCreds"]
        expected = 5850
        self.assertEqual(actual, expected)

    def test_atk_kills(self):
        gamestate = self.pot[self.index]
        actual = gamestate["ATK_kills"]
        expected = 2
        self.assertEqual(actual, expected)

    def test_def_loadout_value(self):
        gamestate = self.pot[self.index]
        actual = gamestate["DEF_loadoutValue"]
        expected = 9400
        self.assertEqual(actual, expected)

    def test_def_shields(self):
        gamestate = self.pot[self.index]
        actual = gamestate["DEF_shields"]
        expected = 150
        self.assertEqual(actual, expected)

    def test_def_remaining_creds(self):
        gamestate = self.pot[self.index]
        actual = gamestate["DEF_remainingCreds"]
        expected = 1700
        self.assertEqual(actual, expected)

    def test_def_kills(self):
        gamestate = self.pot[self.index]
        actual = gamestate["DEF_kills"]
        expected = 2
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
