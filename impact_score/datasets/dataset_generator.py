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


def get_json_folder_reference() -> Path:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name == "model":
        webscrapping = current_folder.parent
        return Path(webscrapping, "matches", "json")


def get_matches_folder_reference() -> Path:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name == "model":
        webscrapping = current_folder.parent
        return Path(webscrapping, "matches")


def get_datasets_folder_reference() -> Path:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name == "model":
        webscrapping = current_folder.parent
        return Path(webscrapping, "matches", "events")
    elif current_folder_name == "datasets":
        return current_folder


def get_match_list() -> List[int]:
    dataset_reference = Path(get_datasets_folder_reference(), "dataset_matches.csv")
    matches_csv = pd.read_csv(dataset_reference)
    nested_list = matches_csv.values.tolist()
    return list(chain(*nested_list))


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
        dataset_size = kwargs["size"]
        dataset_name = kwargs["name"]
        matches = get_matches_folder_reference()
        datasets = Path(matches, "datasets")
        huge_df = self.create_dataset(size=dataset_size)
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
    vm.export_dataset(size=2000, name="2000")
    print(vm.broken_matches)
