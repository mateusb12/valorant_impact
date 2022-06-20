import pandas as pd


class AnalyserWrapper:
    def __init__(self, analyser):
        self.analyser = analyser

    def generate_map_metrics(self) -> list:
        """
        Generates the dataframe body. See get_feature_labels().
        """
        map_events = []
        for i in range(1, self.round_amount + 1):
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
    pass


if __name__ == "__main__":
    __main()
