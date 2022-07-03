# import json
# from typing import Tuple
#
# import numpy as np
# import pandas as pd
# from scipy.spatial.distance import pdist
#
# from impact_score.imports.os_slash import get_slash_type
# from impact_score.json_analyser.core.api_consumer import get_match_info
# from impact_score.path_reference.folder_ref import valorant_model_reference
#
# sl = get_slash_type()
#
#
# def get_map_dict(input_data: dict, input_match_id: int) -> dict:
#     for match in input_data["series"]["seriesById"]["matches"]:
#         if match["id"] == input_match_id:
#             return match
#
#
# def get_round_events(input_data: dict, chosen_round: int):
#     """
#     Get the events of the round (kills, deaths, plants, defuses, etc)
#     :return:
#     """
#     return [
#         {
#             "round_number": m["roundNumber"],
#             "timing": m["roundTimeMillis"],
#             "author": m["playerId"],
#             "victim": m["referencePlayerId"],
#             "event": m["eventType"],
#             "damage_type": m["damageType"],
#             "weapon_id": m["weaponId"],
#             "ability": m["ability"],
#             "probability_before": m["attackingWinProbabilityBefore"],
#             "probability_after": m["attackingWinProbabilityAfter"],
#             "impact": m["impact"],
#             "kill_id": m["killId"],
#             "round_id": m["roundId"],
#             "bomb_id": m["bombId"],
#             "res_id": m["resId"]
#         }
#         for m in input_data["matches"]["matchDetails"]["events"]
#         if m["roundNumber"] == chosen_round
#     ]
#
#
# def create_player_table(input_data: dict, map_data: dict) -> dict:
#     ign_table = {
#         b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
#         for b in map_data["players"]
#     }
#
#     attacking_first_team = map_data["attackingFirstTeamNumber"]
#
#     player_dict = {}
#
#     for i in input_data["matches"]["matchDetails"]["economies"]:
#         if i["roundNumber"] == 1:
#             player_id = i["playerId"]
#             aux = {"name": ign_table[player_id],
#                    "agentId": i["agentId"],
#                    "combatScore": i["score"],
#                    "weaponId": i["weaponId"],
#                    "shieldId": i["armorId"],
#                    "loadoutValue": i["loadoutValue"],
#                    "spentCreds": i["spentCreds"],
#                    "remainingCreds": i["remainingCreds"],
#                    "attacking_side": ign_table[player_id]["team_number"] == attacking_first_team,
#                    "team_number": ign_table[player_id]["team_number"],
#                    "alive": True}
#             player_dict[player_id] = aux
#     return player_dict
#
#
# class Analyser:
#     def __init__(self):
#         print("Analyser created!")
#         self.data, self.raw_match_id, self.weapon_data, self.agent_data, self.attacking_first_team = [None] * 5
#         self.maps_data, self.best_of, self.current_status, self.chosen_map, self.chosen_round = [None] * 5
#         self.round_events, self.map_id, self.map_name, self.round_table, self.reverse_round_table = [None] * 5
#         self.match_id, self.series_id, self.team_a, self.team_b, self.series_by_id = [None] * 5
#         self.match_dict, self.defending_first_team, self.round_amount, self.current_round_sides = [None] * 4
#         self.match_link, self.round_number, self.team_number_dict, self.defuse_happened, self.event_type = [None] * 5
#         self.config_set = None
#
#     def set_match(self, input_index: int, **kwargs):
#         self.data = get_match_info(input_index)
#
#         self.raw_match_id = input_index
#         model_folder = valorant_model_reference()
#         weapon_file = open(f'{model_folder}{sl}weapon_table.json')
#         self.weapon_data = json.load(weapon_file)
#
#         agent_file = open(f'{model_folder}{sl}agent_table.json')
#         self.agent_data = json.load(agent_file)
#
#         maps_file = open(f'{model_folder}{sl}map_table.json')
#         self.maps_data = json.load(maps_file)
#         self.series_by_id = self.data["series"]["seriesById"]
#         self.best_of: int = self.series_by_id["bestOf"]
#
#         self.attacking_first_team, self.current_status, self.chosen_map, self.chosen_round, self.round_events = [
#                                                                                                                     None] * 5
#         self.map_id, self.map_name, self.round_table, self.reverse_round_table, self.match_id = [None] * 5
#         self.match_dict = self.series_by_id["matches"]
#         self.match_id = self.data["matches"]["matchDetails"]["id"]
#         self.series_id = self.series_by_id["id"]
#         self.match_link = f"https://rib.gg/series/{self.series_id}"
#
#         self.team_a = self.get_team_a()
#         self.team_b = self.get_team_b()
#
#     def set_config(self, **kwargs):
#         """
#         Set the many configurations of the analysis
#         :param kwargs: chosen_round → round id to be analysed
#         """
#         round_table = self.get_round_table()
#         self.round_number = kwargs["round"]
#         self.chosen_round = round_table[kwargs["round"]]
#         match_json = [item for item in self.match_dict if item["id"] == self.match_id][0]
#         self.chosen_map: str = match_json["seriesMatchNumber"]
#         self.attacking_first_team: int = match_json["attackingFirstTeamNumber"]
#         opposite_side = {1: 2, 2: 1}
#         self.defending_first_team: int = opposite_side[self.attacking_first_team]
#         self.round_events = self.get_round_events()
#         self.current_status: dict = self.generate_player_table()
#         self.map_id: int = match_json["mapId"]
#         self.map_name: str = self.maps_data[str(self.map_id)]
#         self.round_table: dict = self.get_round_table()
#         self.reverse_round_table: dict = self.get_reverse_round_table()
#         round_number = self.reverse_round_table[self.chosen_round]
#         self.round_amount = match_json["team1Score"] + match_json["team2Score"]
#         side_dict = self.handle_sides(self.round_amount)
#         mirror_dict = {"normal": {self.attacking_first_team: "attacking", self.defending_first_team: "defending"},
#                        "inverse": {self.attacking_first_team: "defending", self.defending_first_team: "attacking"}}
#         self.current_round_sides = mirror_dict[side_dict[round_number]]
#         old_attack = self.attacking_first_team
#         new_attack = 0
#         if old_attack == 1:
#             new_attack = 2
#         elif old_attack == 2:
#             new_attack = 1
#         if round_number >= 13:
#             self.attacking_first_team = new_attack
#
#         self.config_set = True
#
#     @staticmethod
#     def handle_sides(round_amount: int) -> dict:
#         side_pattern = ["normal"] * 12
#         if round_amount > 24:
#             side_pattern += ["inverse"] * 12
#             ot_rounds = round_amount - 24
#             for item in range(1, ot_rounds + 1):
#                 side_pattern += ["normal"] if item % 2 == 1 else ["inverse"]
#         else:
#             remaining = round_amount - 12
#             side_pattern += ["inverse"] * remaining
#
#         return {i: side for i, side in enumerate(side_pattern, 1)}
#
#     def get_player_sides(self) -> dict or None:
#         """
#         Get the sides of each player in the current round
#         :return:    {3340: 'defending',
#                     3894: 'defending',
#                     2810: 'defending',
#                     2125: 'attacking'}
#         """
#         if self.config_set is None:
#             print("You should use Analyser.set_config(round=x) beforehand!")
#             return None
#         raw_side_dict = self.current_round_sides
#         player_db = self.current_status
#         return {key: raw_side_dict[value["team_number"]] for key, value in player_db.items()}
#
#     def get_team_a(self) -> dict:
#         """
#         Get the team A of the current map
#         :return: {'id': 3975, 'name': 'Pioneers'}
#         """
#         aux = self.series_by_id
#         return {"id": aux["team1"]["id"], "name": aux["team1"]["name"]}
#
#     def get_team_b(self) -> dict:
#         """
#         Get the team B of the current map
#         :return: {'id': 588, 'name': 'Knights'}
#         """
#         aux = self.series_by_id
#         return {"id": aux["team2"]["id"], "name": aux["team2"]["name"]}
#
#     def get_plant_timestamp(self) -> float or None:
#         for h in self.round_events:
#             if h["event"] == "plant":
#                 return h["timing"]
#         return None
#
#     def get_series_by_id_match(self) -> dict:
#         for match in self.data["series"]["seriesById"]["matches"]:
#             if match["id"] == self.match_id:
#                 return match
#
#     def export_player_names(self):
#         """
#         Export the player names in format of a dictionary
#         :return:    {'ban': {'gained': 0, 'lost': 0, 'delta': 0},
#                     'Frosty': {'gained': 0, 'lost': 0, 'delta': 0},
#                     'Genghsta': {'gained': 0, 'lost': 0, 'delta': 0},
#                     'HUYNH': {'gained': 0, 'lost': 0, 'delta': 0},
#         """
#         self.set_config(round=1)
#         return {
#             value["name"]["ign"]: {"gained": 0, "lost": 0, "delta": 0} for item, value in self.current_status.items()
#         }
#
#     def get_last_round(self) -> int:
#         return self.round_amount
#
#     def generate_player_table(self) -> dict:
#         """
#         Generate a table of player IDs and their respective infos
#         :return: name, agentId, combatScore, weaponId, shieldId, loadoutValue, spent credits,
#                  remaining credits, side, team number, isAlive
#         """
#
#         ign_table = {
#             b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
#             for b in self.get_series_by_id_match()["players"]
#         }
#
#         player_dict = {}
#         if self.chosen_round is None:
#             self.chosen_round = self.get_round_table()[1]
#
#         for i in self.data["matches"]["matchDetails"]["economies"]:
#             if i["roundId"] == self.chosen_round:
#                 player_id = i["playerId"]
#                 aux = {"name": ign_table[player_id],
#                        "agentId": i["agentId"],
#                        "combatScore": i["score"],
#                        "weaponId": i["weaponId"],
#                        "shieldId": i["armorId"],
#                        "loadoutValue": i["loadoutValue"],
#                        "spentCreds": i["spentCreds"],
#                        "remainingCreds": i["remainingCreds"],
#                        "attacking_side": ign_table[player_id]["team_number"] == self.attacking_first_team,
#                        "team_number": ign_table[player_id]["team_number"],
#                        "alive": True}
#                 player_dict[player_id] = aux
#         return player_dict
#
#     def get_round_events(self):
#         """
#         Get the events of the round (kills, deaths, plants, defuses, etc)
#         :return:
#         """
#         return [
#             {
#                 "round_number": m["roundNumber"],
#                 "timing": m["roundTimeMillis"],
#                 "author": m["playerId"],
#                 "victim": m["referencePlayerId"],
#                 "event": m["eventType"],
#                 "damage_type": m["damageType"],
#                 "weapon_id": m["weaponId"],
#                 "ability": m["ability"],
#                 "probability_before": m["attackingWinProbabilityBefore"],
#                 "probability_after": m["attackingWinProbabilityAfter"],
#                 "impact": m["impact"],
#                 "kill_id": m["killId"],
#                 "round_id": m["roundId"],
#                 "bomb_id": m["bombId"],
#                 "res_id": m["resId"]
#             }
#             for m in self.data["matches"]["matchDetails"]["events"]
#             if m["roundId"] == self.chosen_round
#         ]
#
#     def get_round_winner(self) -> int:
#         for match in self.series_by_id["matches"]:
#             if match["id"] == self.raw_match_id:
#                 current_map = match
#                 for r in current_map["rounds"]:
#                     if r["id"] == self.chosen_round:
#                         return 1 if r["winningTeamNumber"] == self.attacking_first_team else 0
#
#     def generate_average_distance(self) -> pd.DataFrame:
#         self.set_config(round=1)
#         location_data = self.data["matches"]["matchDetails"]["locations"]
#         side_dict = {key: value["team_number"] for key, value in self.current_status.items()}
#
#         location_df = pd.DataFrame(location_data)
#         location_df['team'] = location_df['playerId'].map(side_dict)
#         location_df['index'] = range(1, len(location_df) + 1)
#
#         dfb = location_df.groupby(["roundNumber", "roundTimeMillis", "team"])
#         location_dict = {key: {} for key in range(1, self.round_amount+1)}
#         for group_name, df_group in dfb:
#             current_round = df_group["roundNumber"].iloc[0]
#             current_timestamp = df_group["roundTimeMillis"].iloc[0]
#             side = "atk" if self.current_status[df_group["playerId"].iloc[0]]["attacking_side"] is True else "def"
#             coord_zip = list(zip(df_group["locationX"], df_group["locationY"]))
#             avg_distance = np.mean(pdist(coord_zip))
#             aux = {"attack": 0, "defense": 0}
#             if current_timestamp not in location_dict[current_round]:
#                 location_dict[current_round][current_timestamp] = aux
#             if side == "atk":
#                 location_dict[current_round][current_timestamp]["attack"] = avg_distance
#             else:
#                 location_dict[current_round][current_timestamp]["defense"] = avg_distance
#
#         pre_df = {"roundNumber": [], "timestamp": [], "atkCompaction": [], "defCompaction": []}
#         for round_number, value in location_dict.items():
#             pre_df["roundNumber"].append(0)
#             pre_df["timestamp"].append(0)
#             pre_df["atkCompaction"].append(147)
#             pre_df["defCompaction"].append(184)
#             for timestamp, ts_data in value.items():
#                 pre_df["roundNumber"].append(round_number)
#                 pre_df["timestamp"].append(timestamp)
#                 pre_df["atkCompaction"].append(ts_data["attack"])
#                 pre_df["defCompaction"].append(ts_data["defense"])
#         final_df = pd.DataFrame(pre_df)[["atkCompaction", "defCompaction"]]
#         return final_df.fillna(0)
#
#     def generate_spike_timings(self, round_millis: int, plant_millis: int) -> Tuple:
#         if round_millis >= 100000 or self.defuse_happened:
#             regular_time = 0
#             spike_time = 0
#         elif round_millis == plant_millis:
#             regular_time = 0
#             spike_time = 45000
#         elif (
#                 plant_millis is not None
#                 and round_millis <= plant_millis
#                 or plant_millis is None
#         ):
#             regular_time = 100000 - round_millis
#             spike_time = 0
#         else:
#             regular_time = 0
#             spike_time = 45000 - (round_millis - plant_millis)
#
#         def round_func(x):
#             return int(round(x / 1000))
#
#         regular_time = round_func(regular_time)
#         spike_time = round_func(spike_time)
#         return regular_time, spike_time
#
#     def generate_single_event_values(self, **kwargs):
#         player_table: dict = self.current_status
#         team_variables = ["loadoutValue", "weaponValue", "shields", "remainingCreds", "operators", "kills"]
#         roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
#         features = team_variables + roles
#         atk_dict = {item: 0 for item in features}
#         def_dict = {item: 0 for item in features}
#         shield_table = {0: 0, 1: 25, 2: 50}
#
#         for value in player_table.values():
#             player_state = value["alive"]
#             if player_state:
#                 weapon_id = str(value["weaponId"])
#                 weapon_price = int(self.weapon_data[weapon_id]["price"]) if weapon_id != "None" else 0
#                 agent_id = str(value["agentId"])
#                 shield_id = str(value["shieldId"])
#                 shield_value = shield_table[int(shield_id)] if shield_id != "None" else 0
#                 agent_role = self.agent_data[agent_id]["role"]
#                 team_number = value["name"]["team_number"]
#                 team_side = self.current_round_sides[team_number]
#                 cont_dict = {"loadoutValue": value["loadoutValue"], "weaponValue": weapon_price,
#                              "remainingCreds": value["remainingCreds"], "operators": 1 if weapon_id == "15" else 0,
#                              "shields": shield_value, agent_role: 1}
#                 for feature, feature_value in cont_dict.items():
#                     if team_side == "attacking":
#                         atk_dict[feature] += feature_value
#                     else:
#                         def_dict[feature] += feature_value
#
#         round_time = kwargs["timestamp"]
#         regular_time, spike_time = self.generate_spike_timings(kwargs["timestamp"], kwargs["plant"])
#         round_winner = kwargs["winner"] if "winner" in kwargs else None
#         final_dict = {"RegularTime": regular_time, "SpikeTime": spike_time, "MapName": self.map_name["name"],
#                       "FinalWinner": round_winner, "RoundID": self.chosen_round, "MatchID": self.match_id,
#                       "RoundNumber": self.round_number, "RoundTime": round_time}
#         for key, value in atk_dict.items():
#             final_dict[f"ATK_{key}"] = value
#         for key, value in def_dict.items():
#             final_dict[f"DEF_{key}"] = value
#         return final_dict
#
#     def generate_single_event(self, **kwargs):
#         player_table: dict = self.current_status
#         atk_gun_price, def_gun_price, atk_alive, def_alive, def_has_operator, def_has_odin = (0, 0, 0, 0, 0, 0)
#         atk_bank, def_bank = (0, 0)
#         round_millis: int = kwargs["timestamp"]
#         plant_millis: int = kwargs["plant"]
#         agent_types = {'initiator': (1, 4, 13), 'duelist': (2, 7, 10, 12, 14),
#                        'sentinel': (3, 5, 9), 'controller': (6, 8, 11, 15)}
#         atk_agents = {'initiator': 0, 'duelist': 0, 'sentinel': 0, 'controller': 0}
#         def_agents = {'initiator': 0, 'duelist': 0, 'sentinel': 0, 'controller': 0}
#         atk_shields, def_shields = 0, 0
#         shield_table = {None: 0, 1: 25, 2: 50}
#
#         for key, value in player_table.items():
#             if value["alive"]:
#                 weapon_id: str = str(value["weaponId"])
#                 if weapon_id != 'None':
#                     weapon_price: str = self.weapon_data[weapon_id]["price"]
#                 else:
#                     weapon_price: str = '0'
#                 if value["attacking_side"]:
#                     atk_gun_price += int(weapon_price)
#                     atk_alive += 1
#                     atk_shields += shield_table[value['shieldId']]
#                     for archetype, agent_ids in agent_types.items():
#                         if value['agentId'] in agent_ids:
#                             atk_agents[archetype] += 1
#                 else:
#                     def_gun_price += int(weapon_price)
#                     def_alive += 1
#                     def_shields += shield_table[value['shieldId']]
#                     for archetype, agent_ids in agent_types.items():
#                         if value['agentId'] in agent_ids:
#                             def_agents[archetype] += 1
#                     if weapon_id == "15":
#                         def_has_operator = 1
#                     elif weapon_id == "2":
#                         def_has_odin = 1
#             if value["attacking_side"]:
#                 atk_bank += value["remainingCreds"]
#             else:
#                 def_bank += value["remainingCreds"]
#
#         regular_time, spike_time = self.generate_spike_timings(round_millis, plant_millis)
#
#         round_winner = kwargs["winner"] if "winner" in kwargs else None
#         return (self.chosen_round, self.reverse_round_table[self.chosen_round], round_millis, atk_gun_price,
#                 def_gun_price, atk_alive, def_alive, def_has_operator, def_has_odin,
#                 regular_time, spike_time, atk_bank, def_bank,
#                 atk_agents['initiator'], atk_agents['duelist'], atk_agents['sentinel'], atk_agents['controller'],
#                 def_agents['initiator'], def_agents['duelist'], def_agents['sentinel'], def_agents['controller'],
#                 atk_shields, def_shields,
#                 self.map_name["name"], self.match_id,
#                 self.series_id, self.best_of, round_winner)
#
#     @staticmethod
#     def evaluate_spike_beeps(current_stamp: int, spike_stamp: int) -> dict:
#         if spike_stamp is None:
#             return {"1beep": 0, "2beep": 0}
#         if current_stamp <= spike_stamp:
#             return {"1beep": 0, "2beep": 0}
#         running_time = current_stamp - spike_stamp
#         if 0 < running_time <= 25000:
#             return {"1beep": 1, "2beep": 0}
#         if running_time > 25000:
#             return {"1beep": 0, "2beep": 1}
#
#     def generate_full_round(self) -> list:
#         plant = self.get_plant_timestamp()
#         self.defuse_happened = False
#         self.event_type = "start"
#         self.current_status = self.generate_player_table()
#         round_winner = self.get_round_winner()
#         round_array = []
#         self.round_events = self.get_round_events()
#         re = self.round_events
#         sides = self.get_player_sides()
#         atk_kills = 0
#         def_kills = 0
#         for value in self.round_events:
#             event_type: str = value["event"]
#             timing: int = value["timing"]
#             self.event_type = event_type
#             situation = self.current_status
#             if event_type == "defuse":
#                 self.defuse_happened = True
#             elif event_type == "kill":
#                 self.current_status[value["victim"]]["alive"] = False
#                 player_side = sides[value["author"]]
#                 if player_side == "attacking":
#                     atk_kills += 1
#                 elif player_side == "defending":
#                     def_kills += 1
#             elif event_type == "revival":
#                 self.current_status[value["victim"]]["shieldId"] = None
#                 self.current_status[value["victim"]]["alive"] = True
#             event = self.generate_single_event_values(timestamp=timing, winner=round_winner, plant=plant)
#             event["ATK_kills"] = atk_kills
#             event["DEF_kills"] = def_kills
#             round_array.append(event)
#         return round_array
#
#     def get_round_table(self) -> dict:
#         """
#         Returns a dictionary of rounds raw order and their IDs
#         :return: round[6] = 509225
#         """
#         return {
#             round_data["roundNumber"]: round_data["roundId"]
#             for round_data in self.data["matches"]["matchDetails"]["events"]
#         }
#
#     def get_reverse_round_table(self) -> dict:
#         return {
#             round_data["roundId"]: round_data["roundNumber"]
#             for round_data in self.data["matches"]["matchDetails"]["events"]
#         }
#
#     def generate_map_metrics(self) -> list:
#         """
#         Generates the dataframe body. See get_feature_labels().
#         """
#         map_events = []
#         for i in range(1, self.round_amount + 1):
#             self.set_config(round=i)
#             map_events += self.generate_full_round()
#         return map_events
#
#     def export_df(self) -> pd.DataFrame:
#         self.set_config(round=1)
#         report = self.generate_map_metrics()
#         raw = pd.DataFrame(report)
#         raw = self.add_teams_to_df(raw)
#         raw["Loadout_diff"] = raw["ATK_loadoutValue"] - raw["DEF_loadoutValue"]
#         team_positions = self.generate_average_distance()
#         raw = raw.join(team_positions)
#         return raw
#
#     def add_teams_to_df(self, input_df: pd.DataFrame) -> pd.DataFrame:
#         new = input_df.copy()
#         dataframe_height = len(new["RoundID"])
#         team_a_id = [self.team_a["id"]] * dataframe_height
#         team_a_name = [self.team_a["name"]] * dataframe_height
#         team_b_id = [self.team_b["id"]] * dataframe_height
#         team_b_name = [self.team_b["name"]] * dataframe_height
#         new["Team_A_ID"] = team_a_id
#         new["Team_A_Name"] = team_a_name
#         new["Team_B_ID"] = team_b_id
#         new["Team_B_Name"] = team_b_name
#         return new
#
#     def get_map_table(self) -> dict:
#         aux = self.series_by_id["matches"]
#         return {aux[index]["id"]: index + 1 for index in range(len(aux))}
#
#     def check_if_player_is_in_match(self, player_name: str) -> bool:
#         player_names = self.export_player_names().keys()
#         return player_name in player_names
#
#     def export_round_events(self) -> dict:
#         self.set_config(round=1)
#         export_events = self.data["matches"]["matchDetails"]["events"]
#
#         for event in export_events:
#             killer_id = event["playerId"]
#             victim_id = event["referencePlayerId"]
#             killer_name = self.current_status[killer_id]["name"]["ign"]
#             killer_agent_id = self.current_status[killer_id]["agentId"]
#             killer_agent_name = self.agent_data[str(killer_agent_id)]["name"]
#
#             if event["eventType"] in ["kill", "revival"]:
#                 victim_name = self.current_status[victim_id]["name"]["ign"]
#                 victim_agent_id = self.current_status[victim_id]["agentId"]
#                 victim_agent_name = self.agent_data[str(victim_agent_id)]["name"]
#                 event["victim_agent_name"] = victim_agent_name
#                 event["victim_name"] = victim_name
#             else:
#                 event["victim_agent_name"] = "None"
#                 event["victim_name"] = "None"
#             if event["weaponId"] is not None:
#                 weapon = self.weapon_data[str(event["weaponId"])]
#             else:
#                 weapon = {"weaponId": "None", "name": event["ability"]}
#             event["killer_name"] = killer_name
#             event["killer_agent_name"] = killer_agent_name
#             event["weapon"] = weapon
#
#         return export_events
#
#     def export_player_agent_picks(self) -> dict:
#         self.set_config(round=1)
#         map_dict = self.get_series_by_id_match()
#         agent_pick_dict = {}
#         for item in map_dict["players"]:
#             player_name = item["player"]["ign"]
#             agent_id = item["agentId"]
#             agent_name = self.agent_data[str(agent_id)]["name"]
#             agent_pick_dict[player_name] = agent_name
#         return agent_pick_dict
#
#     def export_player_details(self) -> dict:
#         self.set_config(round=1)
#         map_dict = self.get_series_by_id_match()
#         details_dict = {}
#         for item in map_dict["players"]:
#             player_name = item["player"]["ign"]
#             agent_id = item["agentId"]
#             agent_name = self.agent_data[str(agent_id)]["name"]
#             player_id = item["playerId"]
#             details_dict[player_id] = {"agent_name": agent_name, "player_name": player_name}
#         return details_dict
#
#
# if __name__ == "__main__":
#     pass
#     # a = Analyser()
#     # a.set_match(65588)
#     # a.set_config(round=1)
#     # a.generate_average_distance()
#     # # a.get_player_sides()
#     # # r = a.export_player_details()
#     # q = a.export_df()
#     # print(q)
#     # # w = q.to_dict('list')
