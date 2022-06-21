from impact_score.json_analyser.analyser_gamestate import AnalyserGamestate
from impact_score.json_analyser.analyser_pool import CoreAnalyser, analyser_pool
from impact_score.json_analyser.analyser_tools import AnalyserTools
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist


class AnalyserRound:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        self.tools = AnalyserTools(input_core_analyser)
        self.ag = AnalyserGamestate(input_core_analyser)

    def pick_round(self, round_number: int):
        self.a.choose_round(round_number)

    def generate_full_round(self) -> list:
        plant = self.tools.get_plant_timestamp()
        self.a.defuse_happened = False
        self.a.event_type = "start"
        round_winner = self.tools.get_round_winner()
        round_array = []
        sides = self.tools.get_player_sides()
        atk_kills = 0
        def_kills = 0
        for value in self.a.round_events:
            event_type: str = value["event"]
            timing: int = value["timing"]
            if event_type == "defuse":
                self.a.defuse_happened = True
            elif event_type == "kill":
                self.a.current_status[value["victim"]]["alive"] = False
                player_side = sides[value["author"]]
                if player_side == "attacking":
                    atk_kills += 1
                elif player_side == "defending":
                    def_kills += 1
            elif event_type == "revival":
                self.a.current_status[value["victim"]]["shieldId"] = None
                self.a.current_status[value["victim"]]["alive"] = True
            event = self.ag.generate_single_event_values(timestamp=timing, winner=round_winner, plant=plant)
            event["ATK_kills"] = atk_kills
            event["DEF_kills"] = def_kills
            round_array.append(event)
        return round_array

    def generate_average_distance(self) -> pd.DataFrame:
        location_data = self.a.data["matches"]["matchDetails"]["locations"]
        side_dict = {key: value["team_number"] for key, value in self.a.current_status.items()}

        location_df = pd.DataFrame(location_data)
        location_df['team'] = location_df['playerId'].map(side_dict)
        location_df['index'] = range(1, len(location_df) + 1)

        dfb = location_df.groupby(["roundNumber", "roundTimeMillis", "team"])
        location_dict = {key: {} for key in range(1, self.a.round_amount+1)}
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
    a.set_match(68821)
    ar = AnalyserRound(a)
    ar.pick_round(2)
    aux = ar.generate_full_round()
    print(aux)


if __name__ == "__main__":
    __main()
