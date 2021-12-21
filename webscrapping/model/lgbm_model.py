import datetime
import os
from pathlib import Path
from random import sample
from timeit import default_timer as timer
from typing import List

import pandas as pd
from termcolor import colored

from webscrapping.analyse_json import Analyser
from webscrapping.database.sql_queries import ValorantQueries
from webscrapping.model.time_analyser import time_metrics


class ValorantLBGM:
    def __init__(self):
        self.vq = ValorantQueries()
        self.a = Analyser()
        self.match_list = self.get_match_list()
        self.dataset_index = []

    def create_dataset(self, size: int):
        dataset_list = []
        self.set_random_sample(size)
        start = timer()
        for index, match_index in enumerate(self.dataset_index):
            loop = timer()
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_index)
            self.a.set_match(match_index)
            match_df = self.a.export_df()
            dataset_list.append(match_df)
        return pd.concat(dataset_list)

    def export_dataset(self, **kwargs):
        dataset_size = kwargs["size"]
        dataset_name = kwargs["name"]
        matches = self.get_matches_folder_reference()
        datasets = Path(matches, "datasets")
        huge_df = self.create_dataset(size=dataset_size)
        huge_df.to_csv(Path(datasets, f"{dataset_name}.csv"), index=False)
        print(colored(f"Dataset {dataset_name}.csv exported", "green"))

    def get_random_sample(self, amount: int):
        return sample(self.match_list, amount)

    def set_random_sample(self, amount):
        self.dataset_index = self.get_random_sample(amount)

    @staticmethod
    def get_json_folder_reference() -> Path:
        current_folder = Path(os.getcwd())
        current_folder_name = current_folder.name
        if current_folder_name == "model":
            webscrapping = current_folder.parent
            return Path(webscrapping, "matches", "json")

    @staticmethod
    def get_matches_folder_reference() -> Path:
        current_folder = Path(os.getcwd())
        current_folder_name = current_folder.name
        if current_folder_name == "model":
            webscrapping = current_folder.parent
            return Path(webscrapping, "matches")

    def get_match_list(self) -> List[int]:
        jsons = os.listdir(self.get_json_folder_reference())
        return [int(x.split(".")[0]) for x in jsons]


if __name__ == "__main__":
    vm = ValorantLBGM()
    vm.export_dataset(size=10, name="test")
