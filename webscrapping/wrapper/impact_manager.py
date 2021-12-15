import os
from typing import List
from random import choice as random_choice
import pandas as pd

from webscrapping.match_analysis import RoundReplay, train_model
from webscrapping.wrapper.csv_manager import CsvCreator, CsvSplitter
from webscrapping.wrapper.scrap_matches import download_run


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

    @staticmethod
    def download_missing_matches(filename: str):
        suffix = filename.split(".")[0]
        ccr = CsvCreator(filename)
        ccr.generate_link_table()

        ccp = CsvSplitter(f"{suffix}_links.csv", file_amount=2)
        ccp.split()

        full_name = f"{suffix}_links"

        download_run(full_name, "a")
        download_run(full_name, "b")

    def export_single_impact(self, input_match: int):
        rr = RoundReplay(input_match, self.available[input_match], self.model)
        rr.choose_round(1)
        return rr.get_map_impact_dataframe()

    def get_player_impact_throughout_all_matches(self, player_name: str) -> pd.DataFrame:
        raw_impact = self.export_full_impact()
        raw_dfs_concat = pd.concat(raw_impact)
        player_df = raw_dfs_concat[raw_dfs_concat["Name"] == f"{player_name}"]
        player_df = player_df.sort_values("Delta", ascending=False)
        return player_df

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


def analyse_tourney(file_output: str):
    match_csv = pd.read_csv('..\\matches\\analysis\\search_list.csv', index_col=False)
    matches = match_csv["MatchID"].tolist()

    pimp = PlayerImpact(matches)
    # pimp.download_missing_matches("championsmatches.csv")
    q = pimp.analyse_full_impact()
    q.to_csv(f"matches\\analysis\\{file_output}", index=False)
    print(f"{file_output} generated!")


if __name__ == "__main__":
    # gmd_matches = ["43119", "43118", "43093", "43092", "43091", "42906", "42905", "41261", "41260", "41259", "39940",
    #                "39939", "39439", "39438", "39437", "33683", "33682", "33672", "33671", "33670", "33112", "33111",
    #                "33110", "30507", "30506", "30409", "30408", "30407", "29826", "29825", "29824", "29394", "29393",
    #                "29392", "29242", "29241", "29240", "29139", "29138", "28992", "28991", "21859", "21858", "21842",
    #                "21841", "21840", "21782", "21781", "21780", "21631", "21630", "21622", "21621", "18667", "18666",
    #                "18579", "18578", "18355", "18354", "18358", "18357", "16363", "16362", "16267", "16266", "16265",
    #                "16133", "16132", "15597", "15596", "15474", "15473", "15472", "14973", "14972", "14971", "14963",
    #                "14962", "14715", "14714", "13874", "13873", "12291", "12290", "11216", "11215", "10785", "10784",
    #                "10783", "10755", "10754", "10753", "10736", "10735", "10494", "10493", "10479", "10478", "9688",
    #                "9687", "9686", "9379", "9378", "8756", "8755", "8277", "8276", "8262", "8261", "8211", "8210",
    #                "8792", "8791", "8028", "8027"]
    # pi = PlayerImpact(gmd_matches)
    # pi.analyse_full_impact()
    analyse_tourney("champions_berlin.csv")
    # analyse_tourney("berlim.csv")
    # match_csv = pd.read_csv('..\\matches\\analysis\\search_list.csv', index_col=False)
    # matches = match_csv["MatchID"].tolist()
    #
    # pi = PlayerImpact(matches)
    # q = pi.analyse_full_impact()
    # q.to_csv("matches\\analysis\\full_impact.csv", index=False)
    # print("Full impact.csv generated!")

    # apple = 5 + 1
