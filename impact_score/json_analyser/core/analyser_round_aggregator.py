from typing import Dict, Union

from impact_score.json_analyser.core.analyser_gamestate import AnalyserGamestate
from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser, analyser_pool
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist


class AnalyserRound:
    """This class aggregates the multiple gamestates that a given round may have.
    It loops through a list of events (kill, plant, defuse, sage ult) and generates a gamestate for each of them.
    The core method of this class is generate_full_round, which returns a list of gamestates for a given round."""
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a: CoreAnalyser = input_core_analyser
        self.tools = AnalyserTools(input_core_analyser)
        self.ag = AnalyserGamestate(input_core_analyser)
        self.sides = {}
        self.atk_kills = 0
        self.def_kills = 0
        self.round_winner, self.plant, self.current_round_locations = None, None, None

    def pick_round(self, round_number: int):
        self.a.choose_round(round_number)
        self.a.defuse_happened = False
        self.a.event_type = "start"
        self.round_winner = self.tools.get_round_winner()
        self.plant = self.tools.get_plant_timestamp()
        self.sides = self.tools.get_player_sides()
        self.current_round_locations = [item for item in self.a.location_data if item["roundNumber"] == round_number]
        self.ag.set_round_locations(self.current_round_locations)

    def __generate_single_gamestate(self, event: dict) -> Dict[str, Union[int, str]]:
        timing: int = event["timing"]
        self.ag.current_event = event
        event_type: str = event["event"]
        if event_type == "defuse":
            self.a.defuse_happened = True
        elif event_type == "kill":
            self.a.current_status[event["victim"]]["alive"] = False
            damage_type = event["damage_type"]
            if damage_type != "bomb":
                player_side = self.sides[event["author"]]
                if player_side == "attacking":
                    self.atk_kills += 1
                elif player_side == "defending":
                    self.def_kills += 1
        elif event_type == "revival":
            self.a.current_status[event["victim"]]["shieldId"] = None
            self.a.current_status[event["victim"]]["alive"] = True
        gamestate = self.ag.generate_single_event_values(timestamp=timing, plant=self.plant, winner=self.round_winner)
        gamestate["ATK_kills"] = self.atk_kills
        gamestate["DEF_kills"] = self.def_kills
        return gamestate

    def generate_full_round(self) -> list:
        round_array = []
        for event in self.a.round_events:
            gamestate = self.__generate_single_gamestate(event)
            round_array.append(gamestate)
        self.atk_kills, self.def_kills = 0, 0
        return round_array

    def generate_average_distance(self) -> pd.DataFrame:
        location_data = self.a.data["matches"]["matchDetails"]["locations"]
        side_dict = {key: value["team_number"] for key, value in self.a.current_status.items()}

        location_df = pd.DataFrame(location_data)
        location_df['team'] = location_df['playerId'].map(side_dict)
        location_df['index'] = range(1, len(location_df) + 1)

        dfb = location_df.groupby(["roundNumber", "roundTimeMillis", "team"])
        location_dict = {key: {} for key in range(1, self.a.round_amount + 1)}
        for group_name, df_group in dfb:
            current_round = df_group["roundNumber"].iloc[0]
            current_timestamp = df_group["roundTimeMillis"].iloc[0]
            side = "atk" if self.a.current_status[df_group["playerId"].iloc[0]]["attacking_side"] is True else "def"
            coord_zip = list(zip(df_group["locationX"], df_group["locationY"]))
            avg_distance = np.mean(pdist(coord_zip))
            aux = {"attack": 0, "defense": 0}
            if current_timestamp not in location_dict[current_round]:
                location_dict[current_round][current_timestamp] = aux
            if side == "atk":
                location_dict[current_round][current_timestamp]["attack"] = avg_distance
            else:
                location_dict[current_round][current_timestamp]["defense"] = avg_distance

        pre_df = {"roundNumber": [], "timestamp": [], "atkCompaction": [], "defCompaction": []}
        for round_number, value in location_dict.items():
            pre_df["roundNumber"].append(0)
            pre_df["timestamp"].append(0)
            pre_df["atkCompaction"].append(147)
            pre_df["defCompaction"].append(184)
            for timestamp, ts_data in value.items():
                pre_df["roundNumber"].append(round_number)
                pre_df["timestamp"].append(timestamp)
                pre_df["atkCompaction"].append(ts_data["attack"])
                pre_df["defCompaction"].append(ts_data["defense"])
        final_df = pd.DataFrame(pre_df)[["atkCompaction", "defCompaction"]]
        return final_df.fillna(0)


def __main():
    a = analyser_pool.acquire()
    a.set_match(74033)
    ar = AnalyserRound(a)
    ar.pick_round(2)
    aux = ar.generate_full_round()
    print(aux)


if __name__ == "__main__":
    __main()
