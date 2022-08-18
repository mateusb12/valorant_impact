import random
import unittest

from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


class ToolsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        a = analyser_pool.acquire()
        a.set_match(74099)
        a.choose_round(5)
        cls.aw = AnalyserTools(a)

    def test_get_plant_timestamp(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_plant_timestamp()
        expected = 23707
        self.assertEqual(actual, expected)

    def test_get_round_winner(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_round_winner()
        expected = 0
        self.assertEqual(actual, expected)

    def test_get_current_sides(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_current_sides()
        expected = {1: "attacking", 2: "defending"}
        self.assertEqual(actual, expected)

    def test_get_player_sides(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_player_sides()
        expected = {76: 'attacking', 718: 'attacking', 2011: 'attacking', 2937: 'attacking', 3421: 'defending',
                    3531: 'defending', 3532: 'defending', 6414: 'defending', 14543: 'attacking', 21588: 'defending'}
        self.assertEqual(actual, expected)

    def test_generate_spike_timings(self):
        self.aw.a.choose_round(5)
        spike_event = [item for item in self.aw.a.round_events if item["event"] == "plant"][0]
        spike_timing = spike_event["timing"]
        random_event = random.choice(self.aw.a.round_events)
        timing = random_event["timing"]
        actual = self.aw.generate_spike_timings(spike_timing, timing)
        expected = (76, 0)
        self.assertEqual(actual, expected)

    def test_get_team_a(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_team_a()
        expected = {'id': 1625, 'name': 'FNATIC'}
        self.assertEqual(actual, expected)

    def test_get_team_b(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_team_b()
        expected = {'id': 738, 'name': 'Leviatán'}
        self.assertEqual(actual, expected)

    def test_get_round_table(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_round_table()
        expected = {1: 1155526, 2: 1155527, 3: 1155528, 4: 1155529, 5: 1155530, 6: 1155531, 7: 1155532,
                    8: 1155533, 9: 1155534, 10: 1155535, 11: 1155536, 12: 1155537, 13: 1155538, 14: 1155539,
                    15: 1155540, 16: 1155541, 17: 1155542, 18: 1155543, 19: 1155544, 20: 1155545, 21: 1155546,
                    22: 1155547, 23: 1155548, 24: 1155549, 25: 1155550, 26: 1155551, 27: 1155552, 28: 1155553,
                    29: 1155554, 30: 1155555, 31: 1155556, 32: 1155557}
        self.assertEqual(actual, expected)

    def test_generate_round_info(self):
        self.aw.a.choose_round(5)
        pot = self.aw.generate_round_info()
        actual = pot[5]
        expected = {'id': 1155530, 'matchId': 74099, 'number': 5, 'winCondition': 'defuse',
                    'winningTeamNumber': 2, 'ceremony': 'closer', 'team1LoadoutTier': 4, 'team2LoadoutTier': 3,
                    'attacking': {'name': 'FNATIC', 'id': 1},
                    'defending': {'name': 'Leviatán', 'id': 2}, 'finalWinner': 0}
        self.assertEqual(actual, expected)

    def test_generate_side_dict(self):
        self.aw.a.choose_round(5)
        actual = self.aw.generate_side_dict()
        expected = {1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 0, 7: 1, 8: 0, 9: 1, 10: 1, 11: 1, 12: 0, 13: 0, 14: 0,
                    15: 1, 16: 0, 17: 0, 18: 1, 19: 0, 20: 0, 21: 1, 22: 0, 23: 1, 24: 1, 25: 0, 26: 0, 27: 0,
                    28: 0, 29: 1, 30: 1, 31: 1, 32: 0}
        self.assertEqual(actual, expected)

    def test_get_side_dict(self):
        self.aw.a.choose_round(5)
        actual = self.aw.get_side_dict()
        expected = {1: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    2: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    3: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    4: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    5: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    6: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    7: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    8: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    9: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    10: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    11: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    12: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    13: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    14: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    15: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    16: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    17: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    18: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    19: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    20: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    21: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    22: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    23: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    24: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    25: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    26: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    27: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    28: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1},
                    29: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    30: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    31: {'name': 'FNATIC', 'id': 1625, 'team_id': 1, 'side': 'attack', 'finalWinner': 1},
                    32: {'name': 'Leviatán', 'id': 738, 'team_id': 2, 'side': 'attack', 'finalWinner': 1}}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
