from webscrapping.database.sql_creator import ValorantCreator


class ValorantTest:
    def __init__(self):
        self.v = ValorantCreator("valorant")

    def insert_all(self):
        self.insert_event()
        self.insert_players()
        self.insert_teams()
        self.insert_maps()
        self.insert_series()
        self.insert_matches()
        self.insert_round()
        self.insert_round_events()
        self.insert_locations()
        self.insert_economy()

    def refresh_tables(self):
        self.v.drop_all_tables()
        self.v.create_all_tables()

    def insert_event(self):
        self.v.insert_event(779, "VCT North America 2021 - Last Chance Qualifier", "2020-06-01", 4, "losers")

    def insert_players(self):
        self.v.insert_player(3187, "b0i", 226)
        self.v.insert_player(355, "Hiko", 226)
        self.v.insert_player(1132, "nitr0", 226)
        self.v.insert_player(763, "Asuna", 226)
        self.v.insert_player(10253, "Ethan", 226)
        self.v.insert_player(1961, "xeta", 113)
        self.v.insert_player(13591, "Xeppaa", 226)
        self.v.insert_player(3599, "leaf", 226)
        self.v.insert_player(2213, "mitch", 226)
        self.v.insert_player(4639, "vanity", 226)

    def insert_teams(self):
        self.v.insert_team(305, "100 Thieves", "https://i.imgur.com/xQvJdtJ.png", 226, 2, 6, 3, 3187, 355,
                           1132, 763, 10253)
        self.v.insert_team(141, "Cloud9 Blue", "https://i.imgur.com/xQvJdtJ.png", 226, 2, 30, 8, 1961, 13591,
                           3599, 2213, 4639)

    def insert_maps(self):
        self.v.insert_map(4, "Bind")

    def insert_series(self):
        self.v.insert_series(19408, 779, 3, 305, 141)

    def insert_matches(self):
        self.v.insert_match(41362, 19408, 1, 4, "2020-06-01", 4607106, 1, 1, 1, 14, 12)

    def insert_round(self):
        self.v.insert_round(642213, 41362, 5, 1, 4, 4, "kills", "default")

    def insert_round_events(self):
        self.v.insert_round_event(642213, 5, 7969, 763, 13591, "kill", "weapon", 4, "", 1)
        self.v.insert_round_event(642213, 5, 12565, 10253, 3599, "kill", "weapon", 4, "", 1)
        self.v.insert_round_event(642213, 5, 19170, 4639, 3187, "kill", "weapon", 6, "", 1)
        self.v.insert_round_event(642213, 5, 21132, 763, 1961, "kill", "weapon", 4, "", 1)

    def insert_locations(self):
        self.v.insert_round_location(642213, 5, 7969, 10253, 272.895999, 363.958857, "0.06773489")

    def insert_economy(self):
        self.v.insert_round_economy(642213, 5, 1961, 4, 80, 4, 2, 600, 4050, 4600)


if __name__ == "__main__":
    vt = ValorantTest()
