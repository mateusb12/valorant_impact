import json
import os
from termcolor import colored

import psycopg2

from webscrapping.database.sql_creator import ValorantCreator


class ValorantConsumer:
    def __init__(self):
        self.db = ValorantCreator("valorant")
        self.data = {}
        weapon_file = open('..\\matches\\model\\weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        agent_file = open('..\\matches\\model\\agent_table.json')
        self.agent_data = json.load(agent_file)

        maps_file = open('..\\matches\\model\\map_table.json')
        self.maps_data = json.load(maps_file)

    def setup_json(self, filename: str):
        data_file = open('..\\matches\\json\\{}'.format(filename), encoding="utf-8")
        body_txt = data_file.read()
        self.data = json.loads(body_txt)
        apple = 5 + 1

    def add_event(self):
        event_data = self.data["series"]["seriesById"]
        event_id = event_data["eventId"]
        try:
            self.db.insert_event(event_data["eventId"], event_data["eventName"], event_data["startDate"],
                                 event_data["stage"], event_data["bracket"])
        except psycopg2.DatabaseError as dbe:
            print(colored(f'{dbe}', 'red'))

    def add_series(self):
        series_data = self.data["series"]["seriesById"]
        try:
            self.db.insert_series(series_data["id"], series_data["eventId"], series_data["bestOf"],
                                  series_data["team1Id"], series_data["team2Id"])
        except psycopg2.DatabaseError as dbe:
            print(colored(f'{dbe}', 'red'))

    def add_all_teams(self):
        teams_data = self.data["series"]["seriesById"]
        teams = [teams_data["team1"], teams_data["team2"]]
        for team in teams:
            try:
                self.db.insert_team(team["id"], team["name"], team["logoUrl"], team["countryId"], team["regionId"],
                                    team["rank"], team["regionRank"])
            except psycopg2.DatabaseError as dbe:
                print(colored(f'{dbe}', 'red'))

    def add_players(self):
        series_data = self.data["series"]["seriesById"]
        players_data = series_data["matches"][0]["players"]
        for player in players_data:
            player_id = player["player"]["id"]
            player_name = player["player"]["ign"]
            country_id = player["player"]["countryId"]
            try:
                self.db.insert_player(player_id, player_name, country_id)
            except psycopg2.DatabaseError as dbe:
                print(colored(f'{dbe}', 'red'))


if __name__ == "__main__":
    vc = ValorantConsumer()
    vc.setup_json('37853.json')
    print("")
    vc.db.rebuild_database()
    print("")
    vc.add_event()
    vc.add_all_teams()
    vc.add_series()
    # vc.add_players()
    print("")
    print(vc.db.select_from_table("events"))
    print(vc.db.select_from_table("series"))
    print(vc.db.select_from_table("teams"))
    print(vc.db.select_from_table("players"))
    # vc.add_series()
    # vc.add_players()
