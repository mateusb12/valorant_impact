from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser, analyser_pool
from impact_score.json_analyser.core.analyser_tools import AnalyserTools


class AnalyserGamestate:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        self.tools = AnalyserTools(input_core_analyser)
        self.current_round_sides = self.tools.get_current_sides()
        self.round_table = self.tools.get_round_table()

    def create_player_gamestate_dict(self, input_value: dict, input_shield_table: dict):
        weapon_id = str(input_value["weaponId"])
        weapon_price = int(self.a.weapon_data[weapon_id]["price"]) if weapon_id != "None" else 0
        agent_id = str(input_value["agentId"])
        shield_id = str(input_value["shieldId"])
        shield_value = input_shield_table[int(shield_id)] if shield_id != "None" else 0
        agent_role = self.a.agent_data[agent_id]["role"]
        team_number = input_value["name"]["team_number"]
        team_side = self.current_round_sides[team_number]
        cont_dict = {"loadoutValue": input_value["loadoutValue"], "weaponValue": weapon_price,
                     "remainingCreds": input_value["remainingCreds"], "operators": 1 if weapon_id == "15" else 0,
                     "shields": shield_value, agent_role: 1}

    def generate_single_event_values(self, **kwargs):
        player_table: dict = self.a.current_status
        team_variables = ["loadoutValue", "weaponValue", "shields", "remainingCreds", "operators", "kills"]
        roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
        features = team_variables + roles
        atk_dict = {item: 0 for item in features}
        def_dict = {item: 0 for item in features}
        shield_table = {0: 0, 1: 25, 2: 50}

        for value in player_table.values():
            if player_state := value["alive"]:
                weapon_id = str(value["weaponId"])
                weapon_price = int(self.a.weapon_data[weapon_id]["price"]) if weapon_id != "None" else 0
                agent_id = str(value["agentId"])
                shield_id = str(value["shieldId"])
                shield_value = shield_table[int(shield_id)] if shield_id != "None" else 0
                agent_role = self.a.agent_data[agent_id]["role"]
                team_number = value["name"]["team_number"]
                round_sides = self.current_round_sides
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
        regular_time, spike_time = self.tools.generate_spike_timings(kwargs["timestamp"], kwargs["plant"])
        round_winner = kwargs["winner"] if "winner" in kwargs else None
        final_dict = {"RegularTime": regular_time, "SpikeTime": spike_time, "MapName": self.a.map_name,
                      "FinalWinner": round_winner, "RoundID": self.round_table[self.a.chosen_round],
                      "MatchID": self.a.match_id, "RoundNumber": self.a.chosen_round, "RoundTime": round_time}
        for key, value in atk_dict.items():
            final_dict[f"ATK_{key}"] = value
        for key, value in def_dict.items():
            final_dict[f"DEF_{key}"] = value
        return final_dict


def __main():
    a = analyser_pool.acquire()
    a.set_match(68821)
    ag = AnalyserGamestate(a)


if __name__ == "__main__":
    __main()
