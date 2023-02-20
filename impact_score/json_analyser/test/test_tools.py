import random
import unittest
from typing import Tuple

import pytest

from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool, CoreAnalyser


@pytest.fixture(scope="module")
def analyzer_tuple() -> Tuple[CoreAnalyser, AnalyserTools]:
    a = analyser_pool.acquire()
    a.set_match(74099)
    a.choose_round(5)
    return a, AnalyserTools(a)


def test_get_plant_timestamp(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_plant_timestamp()
    expected = 23707
    assert actual == expected


def test_get_round_winner(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_round_winner()
    expected = 0
    assert actual == expected


def test_get_current_sides(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_current_sides()
    expected = {1: "attacking", 2: "defending"}
    assert actual == expected


def test_get_player_sides(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_player_sides()
    expected = {76: 'attacking', 718: 'attacking', 2011: 'attacking', 2937: 'attacking', 3421: 'defending',
                3531: 'defending', 3532: 'defending', 6414: 'defending', 14543: 'attacking', 21588: 'defending'}
    assert actual == expected


def test_generate_spike_timings(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    aw.a.choose_round(5)
    spike_event = [item for item in aw.a.round_events if item["event"] == "plant"][0]
    spike_timing = spike_event["timing"]
    random_event = random.choice(aw.a.round_events)
    timing = random_event["timing"]
    actual = aw.generate_spike_timings(spike_timing, timing)
    expected = (76, 0)
    assert actual == expected


def test_get_team_a(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_team_a()
    expected = {'id': 1625, 'name': 'FNATIC'}
    assert actual == expected


def test_get_team_b(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_team_b()
    expected = {'id': 738, 'name': 'Leviatán'}
    assert actual == expected


def test_get_round_table(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.get_round_table()
    expected = {1: 1155526, 2: 1155527, 3: 1155528, 4: 1155529, 5: 1155530, 6: 1155531, 7: 1155532,
                8: 1155533, 9: 1155534, 10: 1155535, 11: 1155536, 12: 1155537, 13: 1155538, 14: 1155539,
                15: 1155540, 16: 1155541, 17: 1155542, 18: 1155543, 19: 1155544, 20: 1155545, 21: 1155546,
                22: 1155547, 23: 1155548, 24: 1155549, 25: 1155550, 26: 1155551, 27: 1155552, 28: 1155553,
                29: 1155554, 30: 1155555, 31: 1155556, 32: 1155557}
    assert actual == expected


def test_generate_round_info(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    pot = aw.generate_round_info()
    actual = pot[5]
    expected = {'id': 1155530, 'matchId': 74099, 'number': 5, 'winCondition': 'defuse',
                'winningTeamNumber': 2, 'ceremony': 'closer', 'team1LoadoutTier': 4, 'team2LoadoutTier': 3,
                'attacking': {'name': 'FNATIC', 'id': 1},
                'defending': {'name': 'Leviatán', 'id': 2}, 'finalWinner': 0}
    assert actual == expected


def test_generate_side_dict(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    a.choose_round(5)
    actual = aw.generate_side_outcomes_dict()
    expected = {1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 0, 7: 1, 8: 0, 9: 1, 10: 1, 11: 1, 12: 0, 13: 0, 14: 0,
                15: 1, 16: 0, 17: 0, 18: 1, 19: 0, 20: 0, 21: 1, 22: 0, 23: 1, 24: 1, 25: 0, 26: 0, 27: 0,
                28: 0, 29: 1, 30: 1, 31: 1, 32: 0}
    assert actual == expected


def test_get_side_dict(analyzer_tuple: tuple):
    a, aw = analyzer_tuple
    aw.a.choose_round(5)
    original_dict = aw.get_side_dict()
    slim_dict = {
        k: {
            "attacking": v1["Leviatán"]["name"] if v1["Leviatán"]["side"] == "attack" else v1["FNATIC"]["name"],
            "defending": v1["Leviatán"]["name"] if v1["Leviatán"]["side"] == "defense" else v1["FNATIC"]["name"],
            "outcome": "attackers" if v1["Leviatán"]["outcome"] == "win" else "defenders"
        }
        for k, v1 in original_dict.items()
    }
    side_list = [
        "Default" if d["attacking"] == "FNATIC" else "Mirrored"
        for d in slim_dict.values()
    ]
    outcome_list = [
        "A" if d["outcome"] == "attackers" else "D"
        for d in slim_dict.values()
    ]
    expected_side_list = ['Default', 'Default', 'Default', 'Default', 'Default', 'Default', 'Default', 'Default',
                          'Default', 'Default', 'Default', 'Default', 'Mirrored', 'Mirrored', 'Mirrored',
                          'Mirrored', 'Mirrored', 'Mirrored', 'Mirrored', 'Mirrored', 'Mirrored', 'Mirrored',
                          'Mirrored', 'Mirrored', 'Default', 'Mirrored', 'Default', 'Mirrored', 'Default',
                          'Mirrored', 'Default', 'Mirrored']
    expected_outcome_list = ['A', 'A', 'D', 'A', 'A', 'A', 'D', 'A', 'D', 'D', 'D', 'A', 'D', 'D', 'A', 'D', 'D',
                             'A', 'D', 'D', 'A', 'D', 'A', 'A', 'A', 'D', 'A', 'D', 'D', 'A', 'D', 'D']
    assert side_list == expected_side_list
    assert outcome_list == expected_outcome_list


if __name__ == '__main__':
    pytest.main()
