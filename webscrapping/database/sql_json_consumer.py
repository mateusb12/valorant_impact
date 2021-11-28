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

    def get_team_table_data(self) -> dict:
        team_table_data = self.data["series"]["seriesById"]
        return {1: team_table_data["team1Id"], 2: team_table_data["team2Id"]}

    def get_player_data(self) -> dict:
        match_data = self.data["series"]["seriesById"]["matches"]
        return match_data[0]["players"]

    def get_valid_maps(self):
        return [item for item in self.data["series"]["seriesById"]["matches"] if item["riotId"] is not None]

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
        players_data = self.get_player_data()
        team_table_data = self.get_team_table_data()

        for player in players_data:
            aux = player["player"]
            player_id = aux["id"]
            player_name = aux["ign"]
            team_id = team_table_data[player["teamNumber"]]
            country_id = aux["countryId"]
            try:
                self.db.insert_player(player_id, player_name, team_id, country_id)
            except psycopg2.DatabaseError as dbe:
                print(colored(f'{dbe}', 'red'))

    def add_maps(self):
        for key, value in self.maps_data.items():
            if value["name"] != "NA":
                try:
                    self.db.insert_map(int(key), value["name"])
                except psycopg2.DatabaseError as dbe:
                    print(colored(f'{dbe}', 'red'))

    def add_matches(self):
        maps_data = self.get_valid_maps()
        team_table_data = self.get_team_table_data()
        for map_played in maps_data:
            match_id = map_played["id"]
            series_id = map_played["seriesId"]
            series_order = map_played["seriesMatchNumber"]
            map_id = map_played["mapId"]
            map_name = self.maps_data[f"{map_id}"]["name"]
            start_date = map_played["startDate"]
            length_millis = map_played["lengthMillis"]
            attacking_first_team = team_table_data[map_played["attackingFirstTeamNumber"]]
            red_team = team_table_data[map_played["redTeamNumber"]]
            winning_team = team_table_data[map_played["winningTeamNumber"]]
            team_a_score = map_played["team1Score"]
            team_b_score = map_played["team2Score"]
            try:
                self.db.insert_match(match_id, series_id, series_order, map_id, map_name, start_date, length_millis,
                                     attacking_first_team, red_team, winning_team, team_a_score, team_b_score)
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
    vc.add_players()
    vc.add_maps()
    vc.add_matches()
    print("")
    print(vc.db.select_from_table("events"))
    print(vc.db.select_from_table("series"))
    print(vc.db.select_from_table("teams"))
    print(vc.db.select_from_table("players"))
    print(vc.db.select_from_table("maps"))
    print(vc.db.select_from_table("matches"))
    # vc.add_series()
    # vc.add_players()
