import pytest

from impact_score.json_analyser.core.analyser_file_loader import load_weapon_data, load_agent_data, load_map_data, \
    load_ability_data


class TestFileLoader(object):
    @pytest.fixture
    def index(self):
        return "3"

    def test_weapon_data(self, index: str):
        data = load_weapon_data()
        actual = data[index]["name"].capitalize()
        expected = "Ares"
        assert actual == expected

    def test_agent_data(self, index: str):
        data = load_agent_data()
        actual = data[index]["name"].capitalize()
        expected = "Cypher"
        assert actual == expected

    def test_map_data(self, index: str):
        data = load_map_data()
        actual = data[index]["name"].capitalize()
        expected = "Bind"
        assert actual == expected

    def test_ability_data(self, index: str):
        data = load_ability_data()
        actual = data[index]["name"].capitalize()
        expected = "Blaze"
        assert actual == expected


if __name__ == '__main__':
    pytest.main()
