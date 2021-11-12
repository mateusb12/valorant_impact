import datetime
import glob
import json
import os
from typing import Tuple, List

import pandas as pd

agent_table = {1: "Breach", 2: "Raze", 3: "Cypher", 4: "Sova", 5: "Killjoy", 6: "Viper",
               7: "Phoenix", 8: "Brimstone", 9: "Sage", 10: "Reyna", 11: "Omen", 12: "Jett",
               13: "Skye", 14: "Yoru", 15: "Astra"}

begin_time = datetime.datetime.now()


class Analyser:
    def __init__(self, input_file: str):

        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")

        data_file = open('matches/json/{}'.format(input_file), encoding="utf-8")
        self.data = json.load(data_file)

        weapon_file = open('matches/model/weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        maps_file = open('matches/model/map_table.json')
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
        self.event_id = None

    def set_config(self, **kwargs):
        self.chosen_map: str = kwargs["map"]
        self.chosen_round: int = kwargs["round"]
        self.attacking_team: int = self.data["series"]["seriesById"]["matches"][self.chosen_map][
            "attackingFirstTeamNumber"]
        self.round_events = self.get_round_events()
        self.current_status: dict = self.generate_player_table()
        self.map_id: int = self.data["series"]["seriesById"]["matches"][self.chosen_map]["mapId"]
        self.match_id: int = self.data["series"]["seriesById"]["matches"][self.chosen_map]["id"]
        self.event_id: int = self.data["series"]["seriesById"]["id"]
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

    def get_plant_timestamp(self):
        for h in self.round_events.values():
            if h["event"] == "plant":
                return h["timing"]
        return None

    def generate_player_table(self) -> dict:
        ign_table = {
            b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
            for b in self.data["series"]["seriesById"]["matches"][self.chosen_map]["players"]
        }

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
        for q in self.data["series"]["seriesById"]["matches"][self.chosen_map]["rounds"]:
            if q["id"] == self.chosen_round:
                if q["winningTeamNumber"] == self.attacking_team:
                    return 1
                else:
                    return 0

    def get_valid_maps(self) -> dict:
        match_list = enumerate(self.data["series"]["seriesById"]["matches"])

        return {j["id"]: i for i, j in match_list if j["riotId"] is not None}

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
                self.event_id, self.best_of, round_winner)


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
                self.current_status[value["victim"]]["alive"] = True
            beep_table = self.evaluate_spike_beeps(timestamp, plant)
            event = self.generate_single_event(timestamp=key, winner=round_winner,
                                               beeps=beep_table, plant=plant)
            round_array.append(event)
        return round_array

    def get_round_table(self) -> dict:
        return {
            round_data["number"]: round_data["id"]
            for round_data in self.data["series"]["seriesById"]["matches"][
                self.chosen_map
            ]["rounds"]
        }

    def get_reverse_round_table(self) -> dict:
        return {
            round_data["id"]: round_data["number"]
            for round_data in self.data["series"]["seriesById"]["matches"][
                self.chosen_map
            ]["rounds"]
        }

    def generate_map_metrics(self) -> list:
        map_events = []
        round_table = self.get_round_table()
        for i in round_table.values():
            self.set_config(map=self.chosen_map, round=i)
            map_events += self.generate_full_round()
        return map_events

    def get_first_round(self) -> list:
        return self.data["matches"]["matchDetails"]["economies"][0]["roundId"]

    def get_feature_labels(self) -> List[str]:
        comparison_test = self.generate_map_metrics()
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

    def export_df(self, input_match_id: int):
        vm = self.get_valid_maps()
        map_index = vm[input_match_id]
        r = self.get_first_round()
        self.set_config(map=map_index, round=r)
        features = self.get_feature_labels()
        report = self.generate_map_metrics()
        return pd.DataFrame(report, columns=features)


# a = Analyser("26426.json")
# a.set_config(map=1, round=414368)
# a.get_round_positions()
# q = a.generate_full_round()
# a.export_df(a.match_id)
# a.export_single_map(26426)
# w = a.export_df(26426)
# print(w.columns)
# apple = 5 + 3


def merge_all_csv(csv_name: str):
    file_list = os.listdir('matches/json')
    match_list = [int(x[:-5]) for x in file_list]

    df_list = []

    for i in match_list:
        print(i)
        a = Analyser("{}.json".format(i))
        df_list.append(a.export_df(i))

    print("Append done")
    print(os.getcwd())
    merged = pd.concat(df_list)
    merged.to_csv(r'{}\matches\rounds\{}'.format(os.getcwd(), csv_name), index=False)


merge_all_csv('combined_br.csv')
