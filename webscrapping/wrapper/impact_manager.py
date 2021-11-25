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

    def export_full_impact(self):
        impacts = []
        for key in self.available:
            rr = RoundReplay(key, self.available[key], self.model)
            rr.choose_round(1)
            print(f"appendind key {key}")
            impacts.append(rr.get_map_impact_dataframe())
        return impacts


if __name__ == "__main__":
    matches = [41930, 41929, 41872, 41870, 41868, 39658, 39657, 39656, 39617, 39616, 39587, 39491, 39431, 37854,
               37853, 37852, 37829, 37828, 37818, 37817, 37816, 37726, 37725, 37610, 37609, 37608, 37460, 37459,
               35950, 35949, 35948, 35947, 35945, 35944, 35943, 35942, 35835, 35834, 35833, 35589, 35588, 35587,
               35245, 35244, 35243, 35083, 35082, 33879, 33880, 33877, 33875, 33866, 33861, 33746, 33745, 33744,
               33868, 33867, 30495, 30494, 30493, 30235, 30234, 30151, 30150, 29808, 29807, 28830, 28829, 28622,
               28621, 23633, 23632, 23562, 23561, 22878, 22877, 22339, 22338, 22115, 22109, 22108, 22107, 21829,
               21828, 21291, 21290, 21016, 21015, 20940, 20939, 20938, 21163, 21162, 20889, 20888, 19333, 19332,
               19197, 19196, 19182, 19181, 18534, 18533, 18531, 18530, 16287, 16286, 16285, 16277, 16276, 15775,
               15774, 15553, 15552, 14282, 14281, 12434, 12433, 12369, 12368, 11135, 11134, 11068, 11067, 11071,
               11070, 11047, 7446, 7439, 7427, 7403]
    pi = PlayerImpact(matches)
    q = pi.export_full_impact()
    apple = 5 + 1
