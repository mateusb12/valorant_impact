from impact_score.json_analyser.analyse_json import get_map_dict, create_player_table, get_round_events
from impact_score.json_analyser.analyser_file_loader import get_agent_data, get_weapon_data


class AnalyserGamestate:
    def __init__(self, json_data: dict, input_match_id: int):
        self.data = json_data
        self.chosen_round = 1
        self.map_dict = get_map_dict(json_data, input_match_id)
        self.attacking_first_team: int = self.map_dict["attackingFirstTeamNumber"]
        self.defending_first_team: int = 1 if self.attacking_first_team == 2 else 2
        self.current_status = create_player_table(json_data, self.map_dict)
        self.round_events = None
        self.agent_data = get_agent_data()
        self.weapon_data = get_weapon_data()

    def choose_round(self, desired_round: int):
        self.chosen_round = desired_round
        self.round_events = get_round_events(self.data, self.chosen_round)

    def create_player_gamestate_dict(self, input_value: dict, input_shield_table: dict):
        weapon_id = str(input_value["weaponId"])
        weapon_price = int(self.weapon_data[weapon_id]["price"]) if weapon_id != "None" else 0
        agent_id = str(input_value["agentId"])
        shield_id = str(input_value["shieldId"])
        shield_value = input_shield_table[int(shield_id)] if shield_id != "None" else 0
        agent_role = self.agent_data[agent_id]["role"]
        team_number = input_value["name"]["team_number"]
        team_side = self.current_round_sides[team_number]
        cont_dict = {"loadoutValue": input_value["loadoutValue"], "weaponValue": weapon_price,
                     "remainingCreds": input_value["remainingCreds"], "operators": 1 if weapon_id == "15" else 0,
                     "shields": shield_value, agent_role: 1}

    def generate_single_event_values(self, **kwargs):
        player_table: dict = self.current_status
        team_variables = ["loadoutValue", "weaponValue", "shields", "remainingCreds", "operators", "kills"]
        roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
        features = team_variables + roles
        atk_dict = {item: 0 for item in features}
        def_dict = {item: 0 for item in features}
        shield_table = {0: 0, 1: 25, 2: 50}

        for value in player_table.values():
            if player_state := value["alive"]:
                weapon_id = str(value["weaponId"])
                weapon_price = int(self.weapon_data[weapon_id]["price"]) if weapon_id != "None" else 0
                agent_id = str(value["agentId"])
                shield_id = str(value["shieldId"])
                shield_value = shield_table[int(shield_id)] if shield_id != "None" else 0
                agent_role = self.agent_data[agent_id]["role"]
                team_number = value["name"]["team_number"]
                team_side = self.current_round_sides[team_number]
                cont_dict = {"loadoutValue": value["loadoutValue"], "weaponValue": weapon_price,
                             "remainingCreds": value["remainingCreds"], "operators": 1 if weapon_id == "15" else 0,
                             "shields": shield_value, agent_role: 1}
                for feature, feature_value in cont_dict.items():
                    if team_side == "attacking":
                        atk_dict[feature] += feature_value
                    else:
                        def_dict[feature] += feature_value

        round_time = kwargs["timestamp"]
        regular_time, spike_time = self.generate_spike_timings(kwargs["timestamp"], kwargs["plant"])
        round_winner = kwargs["winner"] if "winner" in kwargs else None
        final_dict = {"RegularTime": regular_time, "SpikeTime": spike_time, "MapName": self.map_name["name"],
                      "FinalWinner": round_winner, "RoundID": self.chosen_round, "MatchID": self.match_id,
                      "RoundNumber": self.round_number, "RoundTime": round_time}
        for key, value in atk_dict.items():
            final_dict[f"ATK_{key}"] = value
        for key, value in def_dict.items():
            final_dict[f"DEF_{key}"] = value
        return final_dict
