import os
from pathlib import Path
from random import sample
from timeit import default_timer as timer
from typing import List
from itertools import chain

import pandas as pd
from termcolor import colored

from impact_score.json_analyser.analyse_json import Analyser
from impact_score.model.time_analyser import time_metrics
from impact_score.path_reference.folder_ref import datasets_reference


def get_match_list() -> List[int]:
    dataset_reference = Path(datasets_reference(), "dataset_matches.csv")
    matches_csv = pd.read_csv(dataset_reference)
    return matches_csv["Match Id"].tolist()


class ValorantDatasetGenerator:
    def __init__(self):
        self.a = Analyser()
        self.match_list = get_match_list()
        self.dataset_index = []
        self.broken_matches = []

    def create_dataset(self, size: int):
        dataset_list = []
        self.set_random_sample(size)
        start = timer()
        for index, match_index in enumerate(self.dataset_index):
            loop = timer()
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_index)
            self.a.set_match(match_index)
            try:
                match_df = self.a.export_df()
            except KeyError:
                print(colored(f"Match #{match_index} is broken", "red"))
                self.broken_matches.append(match_index)
                continue
            dataset_list.append(match_df)
        return pd.concat(dataset_list)

    def export_dataset(self, **kwargs):
        dataset_size = (kwargs["size"]) - 1
        dataset_name = kwargs["name"]
        datasets = datasets_reference()
        huge_df = self.create_dataset(size=dataset_size)
        map_name_dummy = pd.get_dummies(huge_df["MapName"], prefix="MapName")
        huge_df = pd.concat([huge_df, map_name_dummy], axis=1)
        huge_df.to_csv(Path(datasets, f"{dataset_name}.csv"), index=False)
        print(colored(f"Dataset {dataset_name}.csv exported", "green"))

    def get_random_sample(self, amount: int):
        dataset_size = len(self.match_list)
        if amount > dataset_size:
            raise ValueError(f"Dataset size [{dataset_size}] is smaller than the requested sample size [{amount}]")
        else:
            return sample(self.match_list, amount)

    def set_random_sample(self, amount):
        self.dataset_index = self.get_random_sample(amount)


if __name__ == "__main__":
    vm = ValorantDatasetGenerator()
    vm.export_dataset(size=100, name="100")
    print(vm.broken_matches)
