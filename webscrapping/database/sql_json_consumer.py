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

        self.attack_first_table = {}
        self.map_side_table = {}

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

    @staticmethod
    def generate_attacking_round_format(**kwargs) -> dict:
        attacking_first = kwargs["attackers"]
        defending_first = kwargs["defenders"]
        round_amount = kwargs["round_amount"]
        ot_rounds = round_amount - 24
        round_indexes = [i for i in range(1, 25)]
        side_indexes = [attacking_first for _ in range(1, 13)] + [defending_first for _ in range(12, 24)]
        if ot_rounds > 0:
            ot_round_indexes = [i for i in range(25, 25 + ot_rounds)]
            ot_round_teams = [f(x) for x in range(ot_rounds // 2) for f in
                              (lambda x: attacking_first, lambda x: defending_first)]
            round_indexes += ot_round_indexes
            side_indexes += ot_round_teams
        return dict(zip(round_indexes, side_indexes))

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
        convert_side_table = {1: 2, 2: 1}
        attack_first_table = {}
        for map_played in maps_data:
            match_id = map_played["id"]
            series_id = map_played["seriesId"]
            series_order = map_played["seriesMatchNumber"]
            map_id = map_played["mapId"]
            map_name = self.maps_data[f"{map_id}"]["name"]
            start_date = map_played["startDate"]
            length_millis = map_played["lengthMillis"]
            atk_first = map_played["attackingFirstTeamNumber"]
            def_first = convert_side_table[atk_first]
            attacking_first_team = team_table_data[map_played["attackingFirstTeamNumber"]]
            defending_first_team = team_table_data[def_first]
            attack_first_table[match_id] = attacking_first_team
            red_team = team_table_data[map_played["redTeamNumber"]]
            winning_team = team_table_data[map_played["winningTeamNumber"]]
            team_a_score = map_played["team1Score"]
            team_b_score = map_played["team2Score"]
            total_rounds = team_a_score + team_b_score
            self.map_side_table[match_id] = {"attacking_first": attacking_first_team,
                                             "defending_first": defending_first_team,
                                             "round_amount": total_rounds}
            try:
                self.db.insert_match(match_id, series_id, series_order, map_id, map_name, start_date, length_millis,
                                     attacking_first_team, red_team, winning_team, team_a_score, team_b_score)
            except psycopg2.DatabaseError as dbe:
                print(colored(f'{dbe}', 'red'))
        self.attack_first_table = attack_first_table

    def add_rounds(self):
        matches_data = self.data["series"]["seriesById"]["matches"]
        team_table_data = self.get_team_table_data()
        for match in matches_data:
            if match["riotId"] is not None:
                match_id = match["id"]
                rounds_data = match["rounds"]
                current_map_data = self.map_side_table[match_id]
                round_format = self.generate_attacking_round_format(attackers=current_map_data["attacking_first"],
                                                                    defenders=current_map_data["defending_first"],
                                                                    round_amount=current_map_data["round_amount"])
                for round_ in rounds_data:
                    round_id = round_["id"]
                    round_number = round_["number"]
                    attacking_team = round_format[round_number]
                    winning_team_index = round_["winningTeamNumber"]
                    winning_team = team_table_data[winning_team_index]
                    if round_["team1LoadoutTier"] is None:
                        team_a_economy = 0
                    else:
                        team_a_economy = round_["team1LoadoutTier"]
                    if round_["team2LoadoutTier"] is None:
                        team_b_economy = 0
                    else:
                        team_b_economy = round_["team2LoadoutTier"]
                    win_condition = round_["winCondition"]
                    ceremony = round_["ceremony"]
                    try:
                        self.db.insert_round(round_id, match_id, round_number, attacking_team, winning_team,
                                             team_a_economy, team_b_economy, win_condition, ceremony)
                    except psycopg2.DatabaseError as dbe:
                        print(colored(f'Round #{round_id}', 'red'))
                        print(colored(f'{dbe}', 'red'))


if __name__ == "__main__":
    vc = ValorantConsumer()
    vc.setup_json('37853.json')
    q = vc.generate_attacking_round_format(attackers=255, defenders=75, round_amount=28)
    print("")
    vc.db.rebuild_database()
    print("")
    vc.add_event()
    vc.add_all_teams()
    vc.add_series()
    vc.add_players()
    vc.add_maps()
    vc.add_matches()
    vc.add_rounds()
    apple = 5 + 1
    print("")
    print(vc.db.select_from_table("events"))
    print(vc.db.select_from_table("series"))
    print(vc.db.select_from_table("teams"))
    print(vc.db.select_from_table("players"))
    print(vc.db.select_from_table("maps"))
    print(vc.db.select_from_table("matches"))
    print(vc.db.select_from_table("rounds"))
    # vc.add_series()
    # vc.add_players()
