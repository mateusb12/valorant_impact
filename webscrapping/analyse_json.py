import json
import os
from pathlib import Path
from typing import Tuple, List
import pandas as pd
from line_profiler_pycharm import profile


class Analyser:
    def __init__(self, input_file: str):
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")
        elif current_folder == "wrapper":
            os.chdir("..")
        elif current_folder == "exports":
            os.chdir("..\\..")
        json_folder = self.get_json_folder()
        data_file = open(f'{json_folder}/{input_file}', encoding="utf-8")
        body_txt = data_file.read()
        self.data = {}
        self.trim_trash_code(body_txt)

        self.raw_match_id = int(input_file.split(".")[0])
        model_folder = Path(self.get_matches_folder(), "model")
        weapon_file = open(f'{model_folder}/weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        agent_file = open(f'{model_folder}/agent_table.json')
        self.agent_data = json.load(agent_file)

        maps_file = open(f'{model_folder}/map_table.json')
        self.maps_data = json.load(maps_file)
        self.best_of: int = self.data["series"]["seriesById"]["bestOf"]

        self.attacking_team = None
        self.current_status = None
        self.chosen_map = None
        self.chosen_round = None
        self.round_events = None
        self.map_id = None
        self.map_name = None
        self.round_table = None
        self.reverse_round_table = None
        self.match_id = None
        self.series_id = self.data["series"]["seriesById"]["id"]
        self.all_matches = self.get_all_matches_ids()

        self.team_a = self.get_team_a()
        self.team_b = self.get_team_b()

    @staticmethod
    def get_matches_folder():
        current_folder = Path(os.getcwd())
        webscrapping = current_folder.parent
        return Path(webscrapping, "matches")

    def get_json_folder(self) -> Path:
        return Path(self.get_matches_folder(), "json")

    def get_all_matches_ids(self) -> List[int]:
        matches = self.data["series"]["seriesById"]["matches"]
        return [match["id"] for match in matches if "id" in match and match["riotId"] is not None]

    def implicit_set_config(self, **kwargs):
        map_index = self.get_valid_maps()[self.raw_match_id]
        round_table = self.get_round_table()
        round_index = round_table[kwargs["round"]]
        self.set_config(map=map_index, round=round_index)

    def set_config(self, **kwargs):
        """
        Set the many configurations of the analysis
        :param kwargs: chosen_map → map id to be analysed
                       chosen_round → round id to be analysed
        """
        self.chosen_map: str = kwargs["map"]
        match_json = self.get_series_by_id_match()
        self.chosen_round: int = kwargs["round"]
        self.attacking_team: int = match_json["attackingFirstTeamNumber"]
        self.round_events = self.get_round_events()
        self.current_status: dict = self.generate_player_table()
        self.map_id: int = match_json["mapId"]
        self.match_id: int = match_json["id"]
        self.series_id: int = self.data["series"]["seriesById"]["id"]
        self.map_name: str = self.maps_data[str(self.map_id)]
        self.round_table: dict = self.get_round_table()
        self.reverse_round_table: dict = self.get_reverse_round_table()

        round_pos = self.reverse_round_table[self.chosen_round]
        old_attack = self.attacking_team
        new_attack = 0
        if old_attack == 1:
            new_attack = 2
        elif old_attack == 2:
            new_attack = 1
        if round_pos >= 13:
            self.attacking_team = new_attack

    def trim_trash_code(self, code_string: str):
        """
        Trim the trash code from the json file, making the json readable
        """
        first_segment = code_string[0:24]
        if first_segment == "window.__INITIAL_STATE__":
            new_format = code_string[45:]
            self.data = json.loads(new_format)
        else:
            self.data = json.loads(code_string)

    def get_team_a(self):
        aux = self.data["series"]["seriesById"]
        return {"id": aux["team1"]["id"], "name": aux["team1"]["name"]}

    def get_team_b(self):
        aux = self.data["series"]["seriesById"]
        return {"id": aux["team2"]["id"], "name": aux["team2"]["name"]}

    def get_plant_timestamp(self):
        for h in self.round_events.values():
            if h["event"] == "plant":
                return h["timing"]
        return None

    def get_series_by_id_match(self):
        for match in self.data["series"]["seriesById"]["matches"]:
            if match["seriesMatchNumber"] == self.chosen_map:
                return match

    def generate_player_table(self) -> dict:
        """
        Generate a table of player IDs and their respective infos
        :return: name, agentId, combatScore, weaponId, shieldId, loadoutValue, spent credits,
                 remaining credits, side, team number, isAlive
        """

        ign_table = {
            b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
            for b in self.get_series_by_id_match()["players"]
        }  # for b in self.data["series"]["seriesById"]["matches"][self.chosen_map]["players"]

        player_dict = {}

        for i in self.data["matches"]["matchDetails"]["economies"]:
            if i["roundId"] == self.chosen_round:
                player_id = i["playerId"]
                aux = {"name": ign_table[player_id],
                       "agentId": i["agentId"],
                       "combatScore": i["score"],
                       "weaponId": i["weaponId"],
                       "shieldId": i["armorId"],
                       "loadoutValue": i["loadoutValue"],
                       "spentCreds": i["spentCreds"],
                       "remainingCreds": i["remainingCreds"],
                       "attacking_side": ign_table[player_id]["team_number"] == self.attacking_team,
                       "team_number": ign_table[player_id]["team_number"],
                       "alive": True}
                player_dict[player_id] = aux
        return player_dict

    def get_round_events(self) -> dict:
        """
        Get the events of the round (kills, deaths, plants, defuses, etc)
        :return:
        """
        return {
            m["roundTimeMillis"]: {
                "round_number": m["roundNumber"],
                "victim": m["referencePlayerId"],
                "event": m["eventType"],
                "timing": m["roundTimeMillis"],
            }
            for m in self.data["matches"]["matchDetails"]["events"]
            if m["roundId"] == self.chosen_round
        }

    def get_round_winner(self) -> int:
        for match in self.data["series"]["seriesById"]["matches"]:
            if match["id"] == self.raw_match_id:
                current_map = match
                for r in current_map["rounds"]:
                    if r["id"] == self.chosen_round:
                        if r["winningTeamNumber"] == self.attacking_team:
                            return 1
                        else:
                            return 0

    def get_valid_maps(self) -> dict:
        match_list = self.data["series"]["seriesById"]["matches"]
        return {i["id"]: i["seriesMatchNumber"] for i in match_list if i["riotId"] is not None}

        # return {j["id"]: i for i, j in match_list if j["riotId"] is not None}

    @staticmethod
    def generate_spike_timings(round_millis: int, plant_millis: int) -> Tuple:
        if (
                plant_millis is not None
                and round_millis <= plant_millis
                or plant_millis is None
        ):
            regular_time = round_millis
            spike_time = 0
        else:
            regular_time = 0
            spike_time = round_millis - plant_millis

        def round_func(x):
            return int(round(x / 1000))

        regular_time = round_func(regular_time)
        spike_time = round_func(spike_time)
        return regular_time, spike_time

    @profile
    def generate_single_event(self, **kwargs):
        player_table: dict = self.current_status
        atk_gun_price, def_gun_price, atk_alive, def_alive, def_has_operator, def_has_odin = (0, 0, 0, 0, 0, 0)
        atk_bank, def_bank = (0, 0)
        round_millis: int = kwargs["timestamp"]
        plant_millis: int = kwargs["plant"]
        agent_types = {'initiator': (1, 4, 13), 'duelist': (2, 7, 10, 12, 14),
                       'sentinel': (3, 5, 9), 'controller': (6, 8, 11, 15)}
        atk_agents = {'initiator': 0, 'duelist': 0, 'sentinel': 0, 'controller': 0}
        def_agents = {'initiator': 0, 'duelist': 0, 'sentinel': 0, 'controller': 0}
        atk_shields, def_shields = 0, 0
        shield_table = {None: 0, 1: 25, 2: 50}

        for key, value in player_table.items():
            if value["alive"]:
                weapon_id: str = str(value["weaponId"])
                if weapon_id != 'None':
                    weapon_price: str = self.weapon_data[weapon_id]["price"]
                else:
                    weapon_price: str = '0'
                if value["attacking_side"]:
                    atk_gun_price += int(weapon_price)
                    atk_alive += 1
                    atk_shields += shield_table[value['shieldId']]
                    for archetype, agent_ids in agent_types.items():
                        if value['agentId'] in agent_ids:
                            atk_agents[archetype] += 1
                else:
                    def_gun_price += int(weapon_price)
                    def_alive += 1
                    def_shields += shield_table[value['shieldId']]
                    for archetype, agent_ids in agent_types.items():
                        if value['agentId'] in agent_ids:
                            def_agents[archetype] += 1
                    if weapon_id == "15":
                        def_has_operator = 1
                    elif weapon_id == "2":
                        def_has_odin = 1
            if value["attacking_side"]:
                atk_bank += value["remainingCreds"]
            else:
                def_bank += value["remainingCreds"]

        regular_time, spike_time = self.generate_spike_timings(round_millis, plant_millis)

        round_winner = None
        if "winner" in kwargs:
            round_winner = kwargs["winner"]

        return (self.chosen_round, self.reverse_round_table[self.chosen_round], round_millis, atk_gun_price,
                def_gun_price, atk_alive, def_alive, def_has_operator, def_has_odin,
                regular_time, spike_time, atk_bank, def_bank,
                atk_agents['initiator'], atk_agents['duelist'], atk_agents['sentinel'], atk_agents['controller'],
                def_agents['initiator'], def_agents['duelist'], def_agents['sentinel'], def_agents['controller'],
                atk_shields, def_shields,
                self.map_name["name"], self.match_id,
                self.series_id, self.best_of, round_winner)

    @staticmethod
    def evaluate_spike_beeps(current_stamp: int, spike_stamp: int) -> dict:
        if spike_stamp is None:
            return {"1beep": 0, "2beep": 0}
        if current_stamp <= spike_stamp:
            return {"1beep": 0, "2beep": 0}
        running_time = current_stamp - spike_stamp
        if 0 < running_time <= 25000:
            return {"1beep": 1, "2beep": 0}
        if running_time > 25000:
            return {"1beep": 0, "2beep": 1}

    def generate_full_round(self) -> list:
        plant = self.get_plant_timestamp()
        self.current_status = self.generate_player_table()
        round_winner = self.get_round_winner()
        first_round = self.generate_single_event(timestamp=0, winner=round_winner, plant=plant)
        round_array = [first_round]
        self.round_events = self.get_round_events()
        for key, value in self.round_events.items():
            timestamp = value["timing"]
            situation = self.current_status
            if value["victim"] is not None:
                self.current_status[value["victim"]]["alive"] = False
            if value["event"] == "revival":
                self.current_status[value["victim"]]["shieldId"] = None
                self.current_status[value["victim"]]["alive"] = True
            beep_table = self.evaluate_spike_beeps(timestamp, plant)
            event = self.generate_single_event(timestamp=key, winner=round_winner,
                                               beeps=beep_table, plant=plant)
            round_array.append(event)
        return round_array

    def get_round_table(self) -> dict:
        """
        Returns a dictionary of rounds raw order and their IDs
        :return: round[6] = 509225
        """
        return {
            round_data["roundNumber"]: round_data["roundId"]
            for round_data in self.data["matches"]["matchDetails"]["events"]
        }

    def get_reverse_round_table(self) -> dict:
        return {
            round_data["roundId"]: round_data["roundNumber"]
            for round_data in self.data["matches"]["matchDetails"]["events"]
        }

    def get_map_table(self) -> dict:
        aux = self.data["series"]["seriesById"]["matches"]
        return {aux[index]["id"]: index + 1 for index in range(len(aux))}

    def generate_map_metrics(self) -> list:
        """
        Generates the dataframe body. See get_feature_labels().
        """
        map_events = []
        round_table = self.get_round_table()
        for i in round_table.values():
            self.set_config(map=self.chosen_map, round=i)
            map_events += self.generate_full_round()
        return map_events

    def get_first_round(self) -> list:
        return self.data["matches"]["matchDetails"]["economies"][0]["roundId"]

    def get_last_round(self) -> int:
        return self.data["matches"]["matchDetails"]["economies"][-1]["roundNumber"]

    def get_feature_labels(self) -> List[str]:
        """
        Returns a list of all the features used in the model
        """
        return ['RoundID', 'RoundNumber', 'RoundTime', 'ATK_wealth', 'DEF_wealth',
                'ATK_alive', 'DEF_alive', 'DEF_has_OP', 'Def_has_Odin',
                'RegularTime', 'SpikeTime', 'ATK_bank', 'DEF_bank',
                'ATK_initiators', 'ATK_duelists', 'ATK_sentinels', 'ATK_controllers',
                'DEF_initiators', 'DEF_duelists', 'DEF_sentinels', 'DEF_controllers',
                'ATK_Shields', 'DEF_Shields',
                'MapName', 'MatchID', 'SeriesID', 'bestOF',
                'FinalWinner']

    def export_single_map(self, input_match_id: int):
        vm = self.get_valid_maps()
        map_index = vm[input_match_id]
        r = self.get_first_round()
        self.set_config(map=map_index, round=r)
        report = self.generate_map_metrics()
        df = pd.DataFrame(report, columns=self.get_feature_labels())
        df.to_csv(r'matches\exports\{}.csv'.format(input_match_id), index=False)

    @profile
    def export_df(self, input_match_id: int):
        vm = self.get_valid_maps()
        map_index = vm[input_match_id]
        r = self.get_first_round()
        self.set_config(map=map_index, round=r)
        features = self.get_feature_labels()
        report = self.generate_map_metrics()
        raw = pd.DataFrame(report, columns=features)
        raw = self.add_teams_to_df(raw)
        return raw

    def add_teams_to_df(self, input_df: pd.DataFrame) -> pd.DataFrame:
        new = input_df.copy()
        dataframe_height = len(new["RoundID"])
        team_a_id = [self.team_a["id"]] * dataframe_height
        team_a_name = [self.team_a["name"]] * dataframe_height
        team_b_id = [self.team_b["id"]] * dataframe_height
        team_b_name = [self.team_b["name"]] * dataframe_height
        new["Team_A_ID"] = team_a_id
        new["Team_A_Name"] = team_a_name
        new["Team_B_ID"] = team_b_id
        new["Team_B_Name"] = team_b_name
        return new

    def export_player_names(self) -> dict:
        self.implicit_set_config(round=1)
        return {
            value["name"]["ign"]: {"gained": 0, "lost": 0, "delta": 0} for item, value in self.current_status.items()
        }

    def export_round_events(self) -> dict:
        self.chosen_map = self.get_map_table()[self.raw_match_id]
        self.chosen_round = self.get_round_table()[1]
        self.set_config(map=self.chosen_map, round=self.chosen_round)
        export_events = self.data["matches"]["matchDetails"]["events"]

        for event in export_events:
            killer_id = event["playerId"]
            victim_id = event["referencePlayerId"]
            killer_name = self.current_status[killer_id]["name"]["ign"]
            killer_agent_id = self.current_status[killer_id]["agentId"]
            killer_agent_name = self.agent_data[str(killer_agent_id)]["name"]

            if event["eventType"] in ["kill", "revival"]:
                victim_name = self.current_status[victim_id]["name"]["ign"]
                victim_agent_id = self.current_status[victim_id]["agentId"]
                victim_agent_name = self.agent_data[str(victim_agent_id)]["name"]
                event["victim_agent_name"] = victim_agent_name
                event["victim_name"] = victim_name
            else:
                event["victim_agent_name"] = "None"
                event["victim_name"] = "None"
            if event["weaponId"] is not None:
                weapon = self.weapon_data[str(event["weaponId"])]
            else:
                weapon = {"weaponId": "None", "name": event["ability"]}
            event["killer_name"] = killer_name
            event["killer_agent_name"] = killer_agent_name
            event["weapon"] = weapon

        return export_events


if __name__ == "__main__":
    a = Analyser("43621.json")
    a.implicit_set_config(round=1)
    q = a.export_df(43621)
    apple = 5 + 1
    # q = a.generate_full_round()
    # dm = a.export_round_events()

# a.set_config(map=1, round=414368)
# a.get_round_positions()
# q = a.generate_full_round()
# a.export_df(a.match_id)
# a.export_single_map(26426)
# w = a.export_df(26426)
# print(w.columns)
# apple = 5 + 3
