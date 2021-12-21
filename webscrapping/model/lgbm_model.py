import datetime
from random import sample
from timeit import default_timer as timer
from termcolor import colored

from webscrapping.analyse_json import Analyser
from webscrapping.database.sql_queries import ValorantQueries
from webscrapping.model.time_analyser import time_metrics


class ValorantLBGM:
    def __init__(self):
        self.vq = ValorantQueries()
        self.a = Analyser("43621.json")
        self.match_list = self.vq.query_match_db()
        self.dataset_index = []
        self.dataset_list = []

    def create_dataset(self, size: int):
        self.set_random_sample(size)
        start = timer()
        for index, match_index in enumerate(self.dataset_index):
            loop = timer()
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_index)
            self.a.implicit_set_config(round=1)
            # match_df = self.vq.export_df(match_index)
            match_df = self.a.export_df(match_index)
            self.dataset_list.append(match_df)

    def get_random_sample(self, amount: int):
        return sample(self.match_list, amount)

    def set_random_sample(self, amount):
        self.dataset_index = self.get_random_sample(amount)


if __name__ == "__main__":
    vm = ValorantLBGM()
    vm.create_dataset(1000)
