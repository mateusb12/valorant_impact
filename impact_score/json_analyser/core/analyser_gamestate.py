from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser, analyser_pool
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_loader import get_analyser


class AnalyserGamestate:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        self.tools = AnalyserTools(input_core_analyser)
        self.current_round_sides = self.tools.get_current_sides()
        self.round_table = self.tools.get_round_table()
        self.shield_table = {0: 0, 1: 25, 2: 50}

    def get_weapon_price(self, weapon_id: int):
        new_id = str(weapon_id)
        return int(self.a.weapon_data[new_id]["price"]) if new_id != "None" else 0

    def get_agent_role(self, agent_id: int):
        new_id = str(agent_id)
        return self.a.agent_data[new_id]["role"]

    def get_shield_value(self, shield_id: int):
        new_id = str(shield_id)
        return self.shield_table[int(new_id)] if new_id != "None" else 0

    def get_team_side(self, team_number: int):
        return self.current_round_sides[team_number]

    def get_player_gamestate_dict(self, player_dict: dict):
        weapon_price = self.get_weapon_price(player_dict["weaponId"])
        agent_role = self.get_agent_role(player_dict["agentId"])
        shield_value = self.get_shield_value(player_dict["shieldId"])
        return {"loadoutValue": player_dict["loadoutValue"], "weaponValue": weapon_price,
                "remainingCreds": player_dict["remainingCreds"],
                "operators": 1 if player_dict["weaponId"] == "15" else 0,
                "shields": shield_value, agent_role: 1}

    def generate_single_event_values(self, **kwargs):
        player_table: dict = self.a.current_status
        team_variables = ["loadoutValue", "weaponValue", "shields", "remainingCreds", "operators", "kills"]
        roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
        features = team_variables + roles
        atk_dict = {item: 0 for item in features}
        def_dict = {item: 0 for item in features}

        for value in player_table.values():
            if player_state := value["alive"]:
                team_side = self.get_team_side(value["name"]["team_number"])
                cont_dict = self.get_player_gamestate_dict(value)
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
    a = get_analyser(68821)
    ag = AnalyserGamestate(a)
    ag.generate_single_event_values(timestamp=0, winner=1, plant=91990)


if __name__ == "__main__":
    __main()
