import pandas as pd

from impact_score.json_analyser.pool.analyser_pool import analyser_pool, CoreAnalyser
from impact_score.json_analyser.core.analyser_round_aggregator import AnalyserRound
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.model.features.model_features import generate_role_diff


class AnalyserWrapper:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        self.ar = AnalyserRound(input_core_analyser)
        self.tools = AnalyserTools(input_core_analyser)

    def generate_map_metrics(self) -> list:
        """
        Generates the dataframe body. See get_feature_labels().
        """
        map_events = []
        for i in range(1, self.a.round_amount + 1):
            self.ar.pick_round(i)
            map_events += self.ar.generate_full_round()
        return map_events

    def __add_teams_to_df(self, input_df: pd.DataFrame) -> pd.DataFrame:
        new = input_df.copy()
        dataframe_height = len(new["RoundID"])
        team_a = self.tools.get_team_a()
        team_b = self.tools.get_team_b()
        team_a_id = [team_a["id"]] * dataframe_height
        team_a_name = [team_a["name"]] * dataframe_height
        team_b_id = [team_b["id"]] * dataframe_height
        team_b_name = [team_b["name"]] * dataframe_height
        new["Team_A_ID"] = team_a_id
        new["Team_A_Name"] = team_a_name
        new["Team_B_ID"] = team_b_id
        new["Team_B_Name"] = team_b_name
        generate_role_diff(new)
        return new

    def export_df(self) -> pd.DataFrame:
        report = self.generate_map_metrics()
        raw = pd.DataFrame(report)
        raw = self.__add_teams_to_df(raw)
        raw["Loadout_diff"] = raw["ATK_loadoutValue"] - raw["DEF_loadoutValue"]
        # team_positions = self.ar.generate_average_distance()
        # raw = raw.join(team_positions)
        return raw

    def set_match(self, input_match_id: int):
        self.a.set_match(input_match_id)


def get_match_df(input_match_id: int) -> pd.DataFrame:
    a = analyser_pool.acquire()
    a.set_match(input_match_id)
    aw = AnalyserWrapper(a)
    return aw.export_df()


def __main():
    a = analyser_pool.acquire()
    a.set_match(78746)
    aw = AnalyserWrapper(a)
    aux = aw.export_df()
    query = aux[aux["RoundNumber"] == 12]
    master_query = query[["RegularTime", "SpikeTime", "RoundNumber", "RoundTime",
                          "ATK_loadoutValue", "ATK_kills", "ATK_Initiator", "ATK_Duelist", "ATK_Sentinel",
                          "ATK_Controller", "DEF_loadoutValue", "DEF_kills", "DEF_Initiator", "DEF_Duelist",
                          "DEF_Sentinel", "DEF_Controller", "Loadout_diff", "FinalWinner"]]
    print(aux)


if __name__ == "__main__":
    __main()
