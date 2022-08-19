import unittest

from impact_score.json_analyser.core.analyser_file_loader import load_weapon_data, load_agent_data, load_map_data, \
    load_ability_data


class FileLoaderTest(unittest.TestCase):
    def setUp(self):
        self.index = "3"

    def test_weapon_data(self):
        data = load_weapon_data()
        actual = data[self.index]["name"].capitalize()
        expected = "Ares"
        self.assertEqual(actual, expected)  # add assertion here

    def test_agent_data(self):
        data = load_agent_data()
        actual = data[self.index]["name"].capitalize()
        expected = "Cypher"
        self.assertEqual(actual, expected)

    def test_map_data(self):
        data = load_map_data()
        actual = data[self.index]["name"].capitalize()
        expected = "Bind"
        self.assertEqual(actual, expected)

    def test_ability_data(self):
        data = load_ability_data()
        actual = data[self.index]["name"].capitalize()
        expected = "Blaze"
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
