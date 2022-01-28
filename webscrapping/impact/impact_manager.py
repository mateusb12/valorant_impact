import os
from pathlib import Path
from typing import List
from random import choice as random_choice
import pandas as pd

from impact_score.impact.match_analysis import RoundReplay, train_model
from timeit import default_timer as timer

from impact_score.json_analyser.analyse_json import Analyser
from impact_score.model.time_analyser import time_metrics
from webscrapping.wrapper.csv_manager import CsvCreator, CsvSplitter, CsvConverter
from webscrapping.wrapper.scrap_matches import download_run


class PlayerImpact:
    def __init__(self, match_db: List[int] = None):
        self.fix_current_folder()
        self.search_player = ""
        self.match_db = get_match_db_reference() if match_db is None else match_db
        print(os.getcwd())
        self.model = train_model()
        self.rr = RoundReplay(self.model)
        self.analyser = Analyser()
        self.available = self.existing_matches()
        self.failed_matches = []
        self.analysis_type = None

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
    def existing_matches() -> List[int]:
        current_folder = Path(os.getcwd())
        webscrapping = current_folder.parent
        json = Path(webscrapping, "matches", "json")
        json_list = os.listdir(json)
        return [int(item.split(".")[0]) for item in json_list]

    @staticmethod
    def existing_match(input_match_id: int):
        current_folder = Path(os.getcwd())
        webscrapping = current_folder.parent
        json = Path(webscrapping, "matches", "json")
        try:
            analysis_df = pd.read_csv(f'{json}\\{input_match_id}.json'.format(input_match_id), index_col=False)
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
        """
        Downloads missing matches from the database.
        :param filename: championsmatches.csv (example)
        :return: download all necessary files
        """
        suffix = filename.split(".")[0]
        ccr = CsvCreator(filename)
        ccr.generate_link_table()

        ccp = CsvSplitter(f"{suffix}_links.csv", file_amount=2)
        ccp.split()

        full_name = f"{suffix}_links"
        download_run(full_name, "a")
        download_run(full_name, "b")

        ccv = CsvConverter()
        ccv.get_json_list()

    def export_single_impact(self, input_match: int):
        rr = RoundReplay(input_match, self.available[input_match], self.model)
        rr.choose_round(1)
        return rr.get_map_impact_dataframe()

    def get_player_impact_throughout_all_matches(self, player_name: str) -> pd.DataFrame:
        self.search_player = player_name
        raw_impact = self.export_player_impact()
        raw_dfs_concat = pd.concat(raw_impact)
        player_df = raw_dfs_concat[raw_dfs_concat["Name"] == f"{player_name}"]
        player_df = player_df.sort_values("Delta", ascending=False)
        return player_df

    def export_full_impact(self) -> List[pd.DataFrame]:
        impacts = []
        total_len = len(self.match_db)
        start = timer()
        rr = self.rr
        for index, key in enumerate(self.match_db):
            if key != 0:
                rr.set_match(key)
                self.analyser.set_match(key)
                rr.choose_round(1)
                loop = timer()
                time_metrics(start=start, end=loop, index=index, size=total_len, tag="match", element=key)
                try:
                    impact = [5]
                    if self.analysis_type == "player":
                        impact = rr.get_map_impact_dataframe()
                    elif self.analysis_type == "agent":
                        impact = rr.get_map_impact_dataframe(agents=True)
                    impacts.append(impact)
                except KeyError:
                    print("→ → → Match {} failed!".format(key))
                    self.failed_matches.append(key)
        return impacts

    def export_player_impact(self):
        impacts = []
        total_len = len(self.match_db)
        start = timer()
        rr = self.rr
        player_name = self.search_player
        for index, key in enumerate(self.match_db):
            if key != 0:
                rr.set_match(key)
                self.analyser.set_match(key)
                rr.choose_round(1)
                existing_player = self.analyser.check_if_player_is_in_match(player_name)
                if existing_player:
                    loop = timer()
                    time_metrics(start=start, end=loop, index=index, size=total_len, tag="match", element=key)
                    try:
                        impact = rr.get_map_impact_dataframe()
                        impacts.append(impact)
                    except KeyError:
                        print("→ → → Match {} failed!".format(key))
                        self.failed_matches.append(key)
        return impacts

    def analyse_full_impact(self, **kwargs) -> pd.DataFrame:
        self.analysis_type = kwargs["type"]
        raw_dfs = self.export_full_impact()
        raw_dfs_concat = pd.concat(raw_dfs)
        raw_dfs_concat = raw_dfs_concat.drop(["MatchID"], axis=1)
        analysis_dict = {"agent": "Agent", "player": "Name"}
        bias = analysis_dict[self.analysis_type]
        aux = raw_dfs_concat.groupby(bias).agg({'Delta': ['sum', 'count'], "Gain": "sum", "Lost": "sum"})
        aux.columns = aux.columns.map("_".join)
        aux[bias] = aux.index
        aux = aux.reset_index(drop=True)
        aux = aux[[bias, "Gain_sum", "Lost_sum", "Delta_sum", "Delta_count"]]
        aux = aux.rename(columns={"Delta_count": "Matches"})
        aux = aux.sort_values("Delta_sum", ascending=False)
        aux['Delta_avg'] = aux['Delta_sum'] / aux['Matches']
        return aux


def get_match_db_reference():
    current_folder = Path(os.getcwd())
    match_csv = pd.read_csv(f'{current_folder}\\search_list.csv', index_col=False)
    return match_csv["MatchID"].tolist()


def analyse_tourney(file_output: str, **kwargs):
    analysis_type = kwargs["type"]
    current_folder = Path(os.getcwd())
    export_folder = Path(current_folder, "impact_exports")
    matches = get_match_db_reference()

    pimp = PlayerImpact(matches)
    # pimp.download_missing_matches("championsmatches.csv")
    q = pimp.analyse_full_impact(type=analysis_type)
    q.to_csv(f"{export_folder}\\{file_output}", index=False)
    print(f"{file_output} generated!")


if __name__ == "__main__":
    analyse_tourney("champions_impact.csv", type="agent")
    # pi = PlayerImpact()
    # pi.get_player_impact_throughout_all_matches("chronicle")
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
    # analyse_tourney("berlim.csv")
    # match_csv = pd.read_csv('..\\matches\\analysis\\search_list.csv', index_col=False)
    # matches = match_csv["MatchID"].tolist()
    #
    # pi = PlayerImpact(matches)
    # q = pi.analyse_full_impact()
    # q.to_csv("matches\\analysis\\full_impact.csv", index=False)
    # print("Full impact.csv generated!")

    # apple = 5 + 1
