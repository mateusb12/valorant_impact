import unittest
import pytest

from impact_score.json_analyser.core.analyser_gamestate import AnalyserGamestate, get_event_example
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_loader import get_analyser


@pytest.fixture
def ag():
    a = get_analyser(74033)
    ag = AnalyserGamestate(a)
    event = get_event_example()
    ag.current_event = event
    ag.round_locations = [item for item in ag.a.location_data if item["roundNumber"] == 1]
    return ag


def get_expected_output() -> dict:
    return {'RegularTime': 100, 'SpikeTime': 0, 'MapName': 'Bind', 'FinalWinner': 0, 'RoundID': 1154430,
            'MatchID': 74033, 'RoundNumber': 24, 'RoundTime': 0, 'ATK_loadoutValue': 26350,
            'ATK_weaponValue': 16600, 'ATK_shields': 250, 'ATK_remainingCreds': 6200, 'ATK_operators': 1,
            'ATK_kills': 0, 'ATK_Initiator': 4850, 'ATK_Duelist': 5050, 'ATK_Sentinel': 6500,
            'ATK_Controller': 9950, 'ATK_compaction': 246.17722208513464, 'DEF_loadoutValue': 21950,
            'DEF_weaponValue': 15300, 'DEF_shields': 175, 'DEF_remainingCreds': 700, 'DEF_operators': 1,
            'DEF_kills': 0, 'DEF_Initiator': 5300, 'DEF_Duelist': 4000, 'DEF_Sentinel': 6050,
            'DEF_Controller': 6600, 'DEF_compaction': 115.69437843892044}


def test_get_weapon_price_returns_expected_result(ag):
    test_cases = [
        (1, 3200),  # weapon ID of 1 has a price of 3200
        (15, 5000),  # weapon ID of 2 has a price of 5000
        (None, 0),  # Edge case where input is None
        (0, KeyError),  # Edge case where input is 0
        (-1, KeyError),  # Edge case where input is negative
    ]
    for weapon_id, expected_output in test_cases:
        if expected_output == KeyError:
            with pytest.raises(KeyError):
                ag._get_weapon_price(weapon_id)
        else:
            assert ag._get_weapon_price(weapon_id) == expected_output


def test_get_agent_role_returns_expected_result(ag):
    test_cases = [
        ('1', 'Initiator'),  # agent ID of 1 has a role of "Initiator"
        ('11', 'Controller'),  # agent ID of 2 has a role of "Duelist"
        (None, KeyError),  # Edge case where input is None
        (0, KeyError),  # Edge case where input is 0
        (-1, KeyError),  # Edge case where input is negative
    ]
    for agent_id, expected_output in test_cases:
        if expected_output == KeyError:
            with pytest.raises(KeyError):
                ag._get_agent_role(agent_id)
        else:
            true_output = ag._get_agent_role(agent_id)
            assert true_output == expected_output


def test_get_player_gamestate_dict_returns_expected_result(ag):
    test_cases = [
        (1,
         {'name': {'ign': 'dimasick', 'team_number': 2}, 'agentId': 11, 'combatScore': 250,
          'weaponId': 12, 'shieldId': None, 'loadoutValue': 900, 'spentCreds': 750, 'remainingCreds': 50,
          'attacking_side': True, 'team_number': 2, 'timing': 4136, 'playerId': 750, 'alive': True},
         {'loadoutValue': 900, 'weaponValue': 500, 'remainingCreds': 50, 'operators': 0, 'shields': 0,
          'Controller': 900}
         ),
        (2,
         {'name': {'ign': 'ScreaM', 'team_number': 2}, 'agentId': 7, 'combatScore': 88,
          'weaponId': 10, 'shieldId': None, 'loadoutValue': 700, 'spentCreds': 700, 'remainingCreds': 100,
          'attacking_side': True, 'team_number': 2, 'timing': 4136, 'playerId': 1690, 'alive': True},
         {'loadoutValue': 700, 'weaponValue': 500, 'remainingCreds': 100, 'operators': 0, 'shields': 0,
          'Duelist': 700}
         ),
        (3,
         {'name': {'ign': 'soulcas', 'team_number': 2}, 'agentId': 19, 'combatScore': 25, 'weaponId': 12,
          'shieldId': None, 'loadoutValue': 750, 'spentCreds': 750, 'remainingCreds': 50, 'attacking_side': True,
          'team_number': 2, 'timing': 4136, 'playerId': 2056, 'alive': True},
         {'loadoutValue': 750, 'weaponValue': 500, 'remainingCreds': 50, 'operators': 0, 'shields': 0,
          'Initiator': 750}
         )
    ]
    for single_test in test_cases:
        test_number, input_dict, expected_output = single_test
        true_output = ag._get_player_gamestate_dict(input_dict)
        assert true_output == expected_output


def test_get_match_state_dict_returns_expected_result(ag):
    inputs = {"timestamp": 0, "plant": 52502, "round_winner": 0}
    true_output = ag._get_match_state_dict(**inputs)
    expected_output = {'RegularTime': 100, 'SpikeTime': 0, 'MapName': 'Bind', 'FinalWinner': 0, 'RoundID': 1154430,
                       'MatchID': 74033, 'RoundNumber': 24, 'RoundTime': 0}
    assert true_output == expected_output


def test_something(ag):
    actual = ag.generate_single_event_values(timestamp=0, winner=0, plant=52502)
    expected = get_expected_output()
    assert actual == expected


if __name__ == '__main__':
    pytest.main()
