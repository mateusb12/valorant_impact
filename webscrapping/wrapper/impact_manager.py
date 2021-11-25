import os
from typing import List
from random import choice as random_choice
import pandas as pd

from webscrapping.match_analysis import RoundReplay, train_model


class PlayerImpact:
    def __init__(self, match_db: List[int]):
        self.fix_current_folder()
        self.match_db = match_db
        print(os.getcwd())
        self.model = train_model()
        self.available = self.create_queue()
        self.failed_matches = []

    @staticmethod
    def fix_current_folder():
        folder = os.getcwd().split("\\")[-1]
        if folder == "Classification_datascience":
            os.chdir("webscrapping")
            print("Path updated!")
        elif folder == "wrapper":
            os.chdir("..")

    def random_pick(self):
        return random_choice(list(self.available.keys()))

    @staticmethod
    def existing_match(input_match_id: int):
        try:
            analysis_df = pd.read_csv('matches\\exports\\{}.csv'.format(input_match_id), index_col=False)
            return True, analysis_df
        except FileNotFoundError:
            return False, None

    def create_queue(self) -> dict:
        match_queue = {}
        for i in self.match_db:
            aux = self.existing_match(i)
            existing = aux[0]
            if existing:
                content = aux[1]
                match_queue[i] = content
        return match_queue

    def export_single_impact(self, input_match: int):
        rr = RoundReplay(input_match, self.available[input_match], self.model)
        rr.choose_round(1)
        return rr.get_map_impact_dataframe()

    def export_full_impact(self) -> List[pd.DataFrame]:
        impacts = []
        total_len = len(self.available)
        for index, key in enumerate(self.available):
            if key != 0:
                rr = RoundReplay(key, self.available[key], self.model)
                rr.choose_round(1)
                percentage = round((index + 1) / total_len * 100, 2)
                print(f"Analysing match {key}. Total: #{index}/{total_len}.    {percentage}%")
                try:
                    impacts.append(rr.get_map_impact_dataframe())
                except KeyError:
                    print("→ → → Match {} failed!".format(key))
                    self.failed_matches.append(key)
        return impacts

    def analyse_full_impact(self) -> pd.DataFrame:
        raw_dfs = self.export_full_impact()
        raw_dfs_concat = pd.concat(raw_dfs)
        raw_dfs_concat = raw_dfs_concat.drop(["MatchID"], axis=1)
        aux = raw_dfs_concat.groupby('Name').agg({'Delta': ['sum', 'count'], "Gain": "sum", "Lost": "sum"})
        aux.columns = aux.columns.map("_".join)
        aux["Name"] = aux.index
        aux = aux.reset_index(drop=True)
        aux = aux[["Name", "Gain_sum", "Lost_sum", "Delta_sum", "Delta_count"]]
        aux = aux.rename(columns={"Delta_count": "Matches"})
        aux = aux.sort_values("Delta_sum", ascending=False)
        aux['Delta_avg'] = aux['Delta_sum'] / aux['Matches']
        return aux


if __name__ == "__main__":
    match_csv = pd.read_csv('..\\matches\\analysis\\search_list.csv', index_col=False)
    matches = match_csv["MatchID"].tolist()

    pi = PlayerImpact(matches)
    q = pi.analyse_full_impact()
    q.to_csv("matches\\analysis\\full_impact.csv", index=False)
    print("Full impact.csv generated!")

    # apple = 5 + 1
