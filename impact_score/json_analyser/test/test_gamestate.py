import unittest

from impact_score.json_analyser.core.analyser_gamestate import AnalyserGamestate
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_loader import get_analyser


class GameStateTest(unittest.TestCase):
    def setUp(self):
        a = get_analyser(74033)
        self.ag = AnalyserGamestate(a)
        event = {'round_number': 2, 'timing': 0, 'author': None, 'victim': None,
                 'event': 'start', 'damage_type': None, 'weapon_id': None, 'ability': None,
                 'probability_before': '0.12638844887808912', 'probability_after': '0.12638844887808912',
                 'impact': '0', 'kill_id': None, 'round_id': 1155527, 'bomb_id': None, 'res_id': None}
        self.ag.current_event = event
        self.ag.round_locations = [item for item in self.ag.a.location_data if item["roundNumber"] == 1]
        aux = self.ag.generate_single_event_values(timestamp=0, winner=0, plant=52502)

    @staticmethod
    def get_expected_output() -> dict:
        return {'RegularTime': 100, 'SpikeTime': 0, 'MapName': 'Bind', 'FinalWinner': 0, 'RoundID': 1154430,
                'MatchID': 74033, 'RoundNumber': 24, 'RoundTime': 0, 'ATK_loadoutValue': 26350,
                'ATK_weaponValue': 16600, 'ATK_shields': 250, 'ATK_remainingCreds': 6200, 'ATK_operators': 1,
                'ATK_kills': 0, 'ATK_Initiator': 4850, 'ATK_Duelist': 5050, 'ATK_Sentinel': 6500,
                'ATK_Controller': 9950, 'ATK_compaction': 246.17722208513464, 'DEF_loadoutValue': 21950,
                'DEF_weaponValue': 15300, 'DEF_shields': 175, 'DEF_remainingCreds': 700, 'DEF_operators': 1,
                'DEF_kills': 0, 'DEF_Initiator': 5300, 'DEF_Duelist': 4000, 'DEF_Sentinel': 6050,
                'DEF_Controller': 6600, 'DEF_compaction': 115.69437843892044}

    def test_something(self):
        actual = self.ag.generate_single_event_values(timestamp=0, winner=0, plant=52502)
        expected = self.get_expected_output()
        self.assertEqual(actual, expected)  # add assertion here


if __name__ == '__main__':
    unittest.main()
