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
        self.round_table = {}

        self.match_id = 0
        self.broken_json = set()

    def extract_full_json(self):
        existing = self.existing_match(self.match_id)
        if not existing:
            self.add_event()
            self.add_all_teams()
            self.add_series()
            self.add_players()
            self.add_maps()
            self.add_matches()
            self.add_rounds()
            self.add_rounds_economies()
            self.add_round_events()
            self.add_round_locations()
            self.add_player_instances()

    def setup_json(self, filename: str):
        data_file = open('..\\matches\\json\\{}'.format(filename), encoding="utf-8")
        body_txt = data_file.read()
        clean_txt = self.trim_trash_code(body_txt)
        self.data = json.loads(clean_txt)
        self.match_id = int(filename.split(".")[0])

    @staticmethod
    def trim_trash_code(code_string: str):
        """
        Trim the trash code from the json file, making the json readable
        """
        first_segment = code_string[0:24]
        if first_segment == "window.__INITIAL_STATE__":
            return code_string[45:]
        else:
            return code_string

    def existing_match(self, input_match_id: int) -> bool:
        instruction = (
            f"""select exists(select 1 from Matches where match_id={input_match_id});"""
        )
        self.db.cursor.execute(instruction)
        return self.db.cursor.fetchall()[0][0]

    def get_team_table_data(self) -> dict:
        team_table_data = self.data["series"]["seriesById"]
        return {1: team_table_data["team1Id"], 2: team_table_data["team2Id"]}

    def get_player_data(self) -> dict:
        match_data = self.data["series"]["seriesById"]["matches"]
        return match_data[0]["players"]

    def get_valid_maps(self):
        return [item for item in self.data["series"]["seriesById"]["matches"] if item["riotId"] is not None]

    def handle_postgres_exception(self, input_exception: psycopg2):
        error_tag = input_exception.diag.source_function
        if error_tag != "_bt_check_unique":
            print(colored(f'{input_exception}', 'red'))
            self.broken_json.add(self.match_id)

    def export_broken_matches(self):
        export_table = list(self.broken_json)
        with open("broken_matches.txt", "w") as outfile:
            outfile.write("\n".join(str(item) for item in export_table))

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
        # print("Adding events")
        event_data = self.data["series"]["seriesById"]
        event_id = event_data["eventId"]
        try:
            self.db.insert_event(event_data["eventId"], event_data["eventName"], event_data["startDate"],
                                 event_data["stage"], event_data["bracket"])
        except psycopg2.IntegrityError as dbe:
            self.handle_postgres_exception(dbe)

    def add_series(self):
        # print("Adding series")
        series_data = self.data["series"]["seriesById"]
        try:
            self.db.insert_series(series_data["id"], series_data["eventId"], series_data["bestOf"],
                                  series_data["team1Id"], series_data["team2Id"])
        except psycopg2.DatabaseError as dbe:
            self.handle_postgres_exception(dbe)

    def add_all_teams(self):
        # print("Adding teams")
        teams_data = self.data["series"]["seriesById"]
        teams = [teams_data["team1"], teams_data["team2"]]
        for team in teams:
            try:
                team_id = team["id"]
                team_name = team["name"] if team["name"] is not None else "Unknown"
                team_logo = team["logoUrl"] if team["logoUrl"] is not None else "No logo"
                team_country_id = team["countryId"] if team["countryId"] is not None else 0
                team_region_id = team["regionId"] if team["regionId"] is not None else 0
                team_rank = team["rank"] if team["rank"] is not None else 0
                team_region_rank = team["regionRank"] if team["regionRank"] is not None else 0
                self.db.insert_team(team_id, team_name, team_logo, team_country_id, team_region_id,
                                    team_rank, team_region_rank)
            except psycopg2.DatabaseError as dbe:
                error_tag = dbe.diag.source_function
                if error_tag != "_bt_check_unique":
                    print(colored(f'{dbe}', 'red'))

        try:
            self.db.insert_team(0, "None", "None", 0, 0, 0, 0)
        except psycopg2.IntegrityError as dbe:
            pass

    def get_player_instance_source(self, input_match_id: int) -> dict:
        data_source = self.data["series"]["seriesById"]["matches"]
        chosen_data = None
        for match in data_source:
            if match["id"] == input_match_id:
                chosen_data = {"players": match["players"], "stats": match["stats"], "rounds": match["rounds"]}
                break

        round_amount = len(chosen_data["rounds"])
        output_players = {}
        for player in chosen_data["players"]:
            if player["playerId"] not in output_players:
                output_players[player["playerId"]] = {}
            output_players[player["playerId"]]["player"] = player

        for stat in chosen_data["stats"]:
            output_players[stat["playerId"]]["stats"] = stat
            output_players[stat["playerId"]]["rounds"] = round_amount
        return output_players

    def add_players(self):
        # print("Adding players")
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
                self.handle_postgres_exception(dbe)
        try:
            self.db.insert_player(0, "None", 0, 0)
        except psycopg2.IntegrityError as dbe:
            pass

    def add_maps(self):
        # print("Adding maps")
        for key, value in self.maps_data.items():
            if value["name"] != "NA":
                try:
                    self.db.insert_map(int(key), value["name"])
                except psycopg2.DatabaseError as dbe:
                    self.handle_postgres_exception(dbe)

    def add_matches(self):
        # print("Adding matches")
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
                self.handle_postgres_exception(dbe)
        self.attack_first_table = attack_first_table

    def add_rounds(self):
        # print("Adding rounds")
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
                        self.handle_postgres_exception(dbe)

    def add_rounds_economies(self):
        # print("Adding round economies")
        economies_data = self.data["matches"]["matchDetails"]["economies"]
        for economy in economies_data:
            round_id = economy["roundId"]
            round_number = economy["roundNumber"]
            self.round_table[round_number] = round_id
            player_id = economy["playerId"]
            agent_id = economy["agentId"]
            score = economy["score"]
            weapon_id = economy["weaponId"] if economy["weaponId"] is not None else 0
            armor_id = 0 if economy["armorId"] is None else economy["armorId"]
            remaining_creds = economy["remainingCreds"]
            spent_creds = economy["spentCreds"]
            loadout_value = economy["loadoutValue"]
            pot = (round_id, round_number, player_id, agent_id, score, weapon_id, armor_id, remaining_creds,
                   spent_creds, loadout_value)
            try:
                self.db.insert_round_economy(round_id, round_number, player_id, agent_id, score, weapon_id, armor_id,
                                             remaining_creds, spent_creds, loadout_value)
            except psycopg2.DatabaseError as dbe:
                self.handle_postgres_exception(dbe)

    def add_round_locations(self):
        # print("Adding round locations")
        location_data = self.data["matches"]["matchDetails"]["locations"]
        for location in location_data:
            round_number = location["roundNumber"]
            round_id = self.round_table[round_number]
            round_time_millis = location["roundTimeMillis"]
            player_id = location["playerId"]
            location_x = location["locationX"]
            location_y = location["locationY"]
            view_radians = location["viewRadians"]
            try:
                self.db.insert_round_location(round_id, round_number, round_time_millis, player_id, location_x,
                                              location_y, view_radians)
            except psycopg2.DatabaseError as dbe:
                self.handle_postgres_exception(dbe)

    def add_round_events(self):
        # print("Adding round events")
        event_data = self.data["matches"]["matchDetails"]["events"]
        for event in event_data:
            round_id = event["roundId"]
            round_number = event["roundNumber"]
            round_time_millis = event["roundTimeMillis"]
            player_id = event["playerId"]
            victim_id = 0 if event["referencePlayerId"] is None else event["referencePlayerId"]
            event_type = event["eventType"]
            damage_type = event["damageType"]
            weapon_id = 0 if event["weaponId"] is None else event["weaponId"]
            ability = 0 if event["ability"] is None else event["ability"]
            attacking_team = event["attackingTeamNumber"]
            assists = event["assists"]
            try:
                self.db.insert_round_event(round_id, round_number, round_time_millis, player_id, victim_id,
                                           event_type, damage_type, weapon_id, ability, attacking_team)
            except psycopg2.DatabaseError as dbe:
                self.handle_postgres_exception(dbe)

            if assists:
                instruction = "Select currval(pg_get_serial_sequence('roundevents', 'round_event_id')) as new_id;"
                self.db.cursor.execute(instruction)
                current_primary_key = self.db.cursor.fetchall()[0][0]
                for assist in assists:
                    actor_id = assist["assistantId"]
                    damage = assist["damage"]
                    try:
                        self.db.insert_assist(current_primary_key, actor_id, damage)
                    except psycopg2.DatabaseError as dbe:
                        self.handle_postgres_exception(dbe)

    def add_player_instances(self):
        # print("Adding player instances")
        raw_data = self.get_player_instance_source(self.match_id)

        for key, value in raw_data.items():
            player_data = value["player"]
            stats_data = value["stats"]
            player_id = key
            agent_id = player_data["agentId"]
            score = stats_data["score"]
            map_played = self.match_id
            rounds_played = value["rounds"]
            try:
                self.db.insert_player_map_instance(player_id, agent_id, map_played, score, rounds_played)
            except psycopg2.DatabaseError as dbe:
                self.handle_postgres_exception(dbe)


if __name__ == "__main__":
    vc = ValorantConsumer()
    # vc.db.rebuild_database()
    vc.setup_json('37853.json')
    q = vc.existing_match(37853)
    apple = 5 + 1

    # vc.extract_full_json()
    # vc.setup_json('37854.json')
    # vc.extract_full_json()
