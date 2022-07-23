from typing import Tuple

import numpy as np
from scipy.spatial.distance import pdist

from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser, analyser_pool
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_loader import get_analyser


class AnalyserGamestate:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        self.tools = AnalyserTools(input_core_analyser)
        self.current_round_sides = self.tools.get_current_sides()
        self.round_info: dict = self.tools.generate_round_info()
        self.round_table = self.tools.get_round_table()
        self.shield_table = {0: 0, 1: 25, 2: 50}
        self.current_event: dict = {}
        self.round_locations: dict = {}

    def __get_weapon_price(self, weapon_id: int) -> int:
        new_id = str(weapon_id)
        return int(self.a.weapon_data[new_id]["price"]) if new_id != "None" else 0

    def __get_agent_role(self, agent_id: int) -> str:
        new_id = str(agent_id)
        return self.a.agent_data[new_id]["role"]

    def __get_shield_value(self, shield_id: int) -> int:
        new_id = str(shield_id)
        return self.shield_table[int(new_id)] if new_id != "None" else 0

    @staticmethod
    def __is_alive(player_dict: dict) -> bool:
        return player_dict["alive"]

    def __get_player_gamestate_dict(self, player_dict: dict) -> dict:
        weapon_price = self.__get_weapon_price(player_dict["weaponId"])
        agent_role = self.__get_agent_role(player_dict["agentId"])
        shield_value = self.__get_shield_value(player_dict["shieldId"])
        return {"loadoutValue": player_dict["loadoutValue"],
                "weaponValue": weapon_price,
                "remainingCreds": player_dict["remainingCreds"],
                "operators": 1 if player_dict["weaponId"] == "15" else 0,
                "shields": shield_value,
                agent_role: player_dict["loadoutValue"]}

    def __get_match_state_dict(self, timestamp: int, plant: int, round_winner: int) -> dict:
        regular_time, spike_time = self.tools.generate_spike_timings(timestamp, plant)
        return {"RegularTime": regular_time, "SpikeTime": spike_time, "MapName": self.a.map_name,
                "FinalWinner": round_winner, "RoundID": self.round_table[self.a.chosen_round],
                "MatchID": self.a.match_id, "RoundNumber": self.a.chosen_round, "RoundTime": timestamp}

    def set_round_locations(self, new_round_locations: list):
        self.round_locations = new_round_locations

    def __get_location_pot(self) -> list:
        timing = self.current_event["timing"]
        if timing != 0:
            return [item for item in self.round_locations if item["roundTimeMillis"] == timing]
        first_timing = self.round_locations[0]["roundTimeMillis"]
        return [item for item in self.round_locations if item["roundTimeMillis"] == first_timing]

    @staticmethod
    def __get_player_exact_location(location_pot: list[dict], player_id: int) -> dict:
        potential_locations: list[dict] = [item for item in location_pot if item["playerId"] == player_id]
        if not potential_locations:
            return {"locationX": 165, "locationY": 165}
        return potential_locations[0]

    @staticmethod
    def evaluate_team_compaction(input_locations: list[Tuple[any, any]]) -> float:
        if not input_locations:
            return 0
        return 165 if len(input_locations) == 1 else np.mean(pdist(input_locations))

    def generate_single_event_values(self, **kwargs) -> dict:
        team_variables = ["loadoutValue", "weaponValue", "shields", "remainingCreds", "operators", "kills"]
        roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
        features = team_variables + roles
        atk_dict = {item: 0 for item in features}
        def_dict = {item: 0 for item in features}

        player_table: dict = self.a.current_status
        round_info: dict = self.round_info[self.a.chosen_round]
        attacking_team = round_info["attacking"]["id"]
        locations = self.__get_location_pot()
        atk_locations = []
        def_locations = []

        for value in player_table.values():
            if self.__is_alive(value):
                team_number = value["name"]["team_number"]
                team_side = "attacking" if team_number == attacking_team else "defending"
                player_id = value["playerId"]
                player_state = self.__get_player_gamestate_dict(value)
                player_locations: dict = self.__get_player_exact_location(locations, player_id)
                x, y = player_locations["locationX"], player_locations["locationY"]
                if team_side == "attacking":
                    atk_locations.append((x, y))
                elif team_side == "defending":
                    def_locations.append((x, y))

                for feature, feature_value in player_state.items():
                    if team_side == "attacking":
                        atk_dict[feature] += feature_value
                    else:
                        def_dict[feature] += feature_value

        round_winner = kwargs["winner"] if "winner" in kwargs else None
        atk_dict["compaction"] = self.evaluate_team_compaction(atk_locations)
        def_dict["compaction"] = self.evaluate_team_compaction(def_locations)
        final_dict = self.__get_match_state_dict(kwargs["timestamp"], kwargs["plant"], round_winner)
        for key, value in atk_dict.items():
            final_dict[f"ATK_{key}"] = value
        for key, value in def_dict.items():
            final_dict[f"DEF_{key}"] = value
        return final_dict


def __main():
    a = get_analyser(74033)
    ag = AnalyserGamestate(a)
    aux = ag.generate_single_event_values(timestamp=0, winner=1, plant=91990)
    print(aux)


if __name__ == "__main__":
    __main()
