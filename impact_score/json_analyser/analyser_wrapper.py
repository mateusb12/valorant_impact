import pandas as pd

from impact_score.json_analyser.analyser_pool import analyser_pool, CoreAnalyser


class AnalyserWrapper:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser

    def generate_map_metrics(self) -> list:
        """
        Generates the dataframe body. See get_feature_labels().
        """
        map_events = []
        for i in range(1, self.a.round_amount + 1):
            self.set_config(round=i)
            map_events += self.generate_full_round()
        return map_events

    def export_df(self) -> pd.DataFrame:
        self.set_config(round=1)
        report = self.generate_map_metrics()
        raw = pd.DataFrame(report)
        raw = self.add_teams_to_df(raw)
        raw["Loadout_diff"] = raw["ATK_loadoutValue"] - raw["DEF_loadoutValue"]
        team_positions = self.generate_average_distance()
        raw = raw.join(team_positions)
        return raw


def __main():
    a = analyser_pool.acquire()
    a.set_match(65588)
    aw = AnalyserWrapper(a)


if __name__ == "__main__":
    __main()
