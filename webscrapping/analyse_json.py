import datetime
import glob
import json
import os

import pandas as pd

agent_table = {1: "Breach", 2: "Raze", 3: "Cypher", 4: "Sova", 5: "Killjoy", 6: "Viper",
               7: "Phoenix", 8: "Brimstone", 9: "Sage", 10: "Reyna", 11: "Omen", 12: "Jett",
               13: "Skye", 14: "Yoru", 15: "Astra"}

begin_time = datetime.datetime.now()


class Analyser:
    def __init__(self, input_file: str):
        data_file = open('matches/json/{}'.format(input_file))
        self.data = json.load(data_file)

        weapon_file = open('matches/model/weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        maps_file = open('matches/model/map_table.json')
        self.maps_data = json.load(maps_file)

        self.match_id = self.data["series"]["seriesById"]["id"]
        self.event_id = self.data["series"]["seriesById"]["eventId"]
        self.best_of = self.data["series"]["seriesById"]["bestOf"]

        self.attacking_team = None
        self.current_status = None
        self.chosen_map = None
        self.chosen_round = None
        self.round_events = None
        self.map_id = None
        self.map_name = None
        self.round_table = None
        self.reverse_round_table = None

    def set_config(self, **kwargs):
        self.chosen_map = kwargs["map"]
        self.chosen_round = kwargs["round"]
        self.attacking_team = self.data["series"]["seriesById"]["matches"][self.chosen_map]["attackingFirstTeamNumber"]
        self.round_events = self.get_round_events()
        self.current_status = self.generate_player_table()
        self.map_id = self.data["series"]["seriesById"]["matches"][self.chosen_map]["mapId"]
        self.map_name = self.maps_data[str(self.map_id)]
        self.round_table = self.get_round_table()
        self.reverse_round_table = self.get_reverse_round_table()

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
                       "attacking_side": ign_table[player_id]["team_number"] == self.attacking_team,
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

    def generate_single_event(self, **kwargs):
        player_table = self.current_status

        atk_gun_price = 0
        def_gun_price = 0
        atk_alive = 0
        def_alive = 0
        def_has_operator = 0
        def_has_odin = 0
        round_millis = kwargs["timestamp"]

        for key, value in player_table.items():
            if value["alive"]:
                weapon_id = str(value["weaponId"])
                if weapon_id != 'None':
                    weapon_tuple = self.weapon_data[weapon_id]
                else:
                    weapon_tuple = {'name': 'None', 'price': 0}
                weapon_price = weapon_tuple["price"]
                if value["attacking_side"]:
                    atk_gun_price += int(weapon_price)
                    atk_alive += 1
                else:
                    def_gun_price += int(weapon_price)
                    def_alive += 1
                    if weapon_id == "15":
                        def_has_operator = 1
                    elif weapon_id == "2":
                        def_has_odin = 1

        atk_gun_price /= 5
        def_gun_price /= 5

        spike_1beep = 0
        spike_2beep = 0

        round_winner = None

        if "beeps" in kwargs:
            beep_dict = kwargs["beeps"]
            spike_1beep = beep_dict["1beep"]
            spike_2beep = beep_dict["2beep"]

        if "winner" in kwargs:
            round_winner = kwargs["winner"]

        return (self.chosen_round, self.reverse_round_table[self.chosen_round], round_millis, atk_gun_price,
                def_gun_price, atk_alive, def_alive, def_has_operator, def_has_odin, spike_1beep, spike_2beep,
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
        round_winner = self.get_round_winner()
        first_round = self.generate_single_event(timestamp=0, winner=round_winner, first=True)
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
            event = self.generate_single_event(timestamp=key, winner=round_winner, beeps=beep_table)
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

    def export_single_map(self, input_match_id: int):
        vm = self.get_valid_maps()
        map_index = vm[input_match_id]
        r = self.get_first_round()
        self.set_config(map=map_index, round=r)
        report = self.generate_map_metrics()
        df = pd.DataFrame(report, columns=['RoundID', 'RoundNumber', 'RoundTime', 'ATK_wealth', 'DEF_wealth',
                                           'ATK_alive', 'DEF_alive', 'DEF_has_OP', 'Def_has_Odin',
                                           'Spike_1_beep', 'Spike_2_beep',
                                           'MapName', 'MatchID', 'SeriesID', 'bestOF',
                                           'FinalWinner'])
        df.to_csv(r'matches\exports\{}.csv'.format(input_match_id), index=False)


# file_list = os.listdir('matches/json')
# match_list = [int(x[:-5]) for x in file_list]
#
# for i in match_list:
#     print(i)
#     a = Analyser("{}.json".format(i))
#     a.export_single_map(i)


def merge_csv():
    folder = "matches/exports"
    os.chdir(folder)
    extension = 'csv'
    all_filenames = [file for file in glob.glob('*.{}'.format(extension))]
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
    combined_csv.to_csv("combined_csv.csv", index=False, encoding='utf-8-sig')
    print('done!')

merge_csv()
