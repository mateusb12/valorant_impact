import pytest

from impact_score.json_analyser.core.analyser_round_aggregator import AnalyserRound
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


@pytest.fixture(scope="module")
def gamestate():
    a = analyser_pool.acquire()
    a.set_match(74099)
    ar = AnalyserRound(a)
    ar.pick_round(2)
    pot = ar.generate_full_round()
    index = 4
    return pot[index]


def test_regular_time(gamestate: dict):
    actual = gamestate["RegularTime"]
    expected = 64
    assert actual == expected


def test_spike_time(gamestate: dict):
    actual = gamestate["SpikeTime"]
    expected = 0
    assert actual == expected


def test_final_winner(gamestate: dict):
    actual = gamestate["FinalWinner"]
    expected = 0
    assert actual == expected


def test_round_time(gamestate: dict):
    actual = gamestate["RoundTime"]
    expected = 36009
    assert actual == expected


def test_atk_loadout_value(gamestate: dict):
    actual = gamestate["ATK_loadoutValue"]
    expected = 900
    assert actual == expected


def test_atk_shields(gamestate: dict):
    actual = gamestate["ATK_shields"]
    expected = 0
    assert actual == expected


def test_atk_remaining_creds(gamestate: dict):
    actual = gamestate["ATK_remainingCreds"]
    expected = 5850
    assert actual == expected


def test_atk_kills(gamestate: dict):
    actual = gamestate["ATK_kills"]
    expected = 2
    assert actual == expected


def test_def_loadout_value(gamestate: dict):
    actual = gamestate["DEF_loadoutValue"]
    expected = 9400
    assert actual == expected


def test_def_shields(gamestate: dict):
    actual = gamestate["DEF_shields"]
    expected = 150
    assert actual == expected


def test_def_remaining_creds(gamestate: dict):
    actual = gamestate["DEF_remainingCreds"]
    expected = 1700
    assert actual == expected


def test_def_kills(gamestate: dict):
    actual = gamestate["DEF_kills"]
    expected = 2
    assert actual == expected


if __name__ == '__main__':
    pytest.main()
