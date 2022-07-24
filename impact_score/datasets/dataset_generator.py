from pathlib import Path
from random import sample
from timeit import default_timer as timer
from typing import List

import numpy as np
import pandas as pd
import os
from termcolor import colored

from impact_score.json_analyser.pool.analyser_pool import analyser_pool, CoreAnalyser
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper
from impact_score.model.time_analyser import time_metrics
from impact_score.path_reference.folder_ref import datasets_reference


def get_match_list(filename: str) -> List[int]:
    dataset_reference = Path(datasets_reference(), "split", filename)
    matches_csv = pd.read_csv(dataset_reference)
    return matches_csv["Match Id"].tolist()


class ValorantDatasetGenerator:
    def __init__(self):
        self.a: CoreAnalyser = analyser_pool.acquire()
        self.a.set_match(74099)
        self.wrapper: AnalyserWrapper = AnalyserWrapper(self.a)
        self.current_file = ""
        self.match_list = []
        self.match_pot = self.__get_all_files()
        self.dataset_index = []
        self.broken_matches = []

    @staticmethod
    def __split_dataset(amount: int) -> None:
        dataset_ref = Path(datasets_reference(), "matches", "all_matches.csv")
        raw_dataset = pd.read_csv(dataset_ref)
        dataset = pd.DataFrame(raw_dataset["Match Id"].unique(), columns=["Match Id"])
        output_ref = Path(datasets_reference(), "split")
        splits = np.array_split(dataset, amount)
        stamps = [chr(i) for i in range(65, 65 + amount)]
        for split, stamp in zip(splits, stamps):
            ref = Path(output_ref, f"{stamp}.csv")
            split.to_csv(Path(output_ref, ref), index=False)

    def __set_file(self, filename: str):
        self.current_file = filename
        dataset_reference = Path(datasets_reference(), "split", filename)
        matches_csv = pd.read_csv(dataset_reference)
        self.match_list = matches_csv["Match Id"].tolist()

    @staticmethod
    def __get_all_files():
        return [f.name for f in Path(datasets_reference(), "split").iterdir() if f.name != "__init__.py"]

    def __consume_dataset(self) -> pd.DataFrame:
        df_ref = Path(datasets_reference(), "split", self.current_file)
        df = pd.read_csv(df_ref)
        size = len(df)
        dataset_list = []
        start = timer()
        for index, match_index in enumerate(self.match_list):
            loop = timer()
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_index)
            self.a.set_match(match_index)
            try:
                match_df = self.wrapper.export_df()
            except KeyError:
                print(colored(f"Match #{match_index} is broken", "red"))
                self.broken_matches.append(match_index)
                continue
            dataset_list.append(match_df)
        print(colored(f"Slice {self.current_file}.csv exported", "green"))
        os.remove(df_ref)
        return pd.concat(dataset_list)

    def __export_dataset(self):
        huge_df = self.__consume_dataset()
        map_name_dummy = pd.get_dummies(huge_df["MapName"], prefix="MapName")
        huge_df = pd.concat([huge_df, map_name_dummy], axis=1)
        output_ref = Path(datasets_reference(), f"Split_{self.current_file}.csv")
        huge_df.to_csv(output_ref, index=False)
        print(colored(f"Dataset {self.current_file}.csv exported", "green"))

    def run_pipeline(self, amount: int):
        self.__split_dataset(amount=amount)
        for file in self.__get_all_files():
            self.__set_file(file)
            self.__export_dataset()


if __name__ == "__main__":
    vdg = ValorantDatasetGenerator()
    vdg.run_pipeline(amount=5)
    # vdg.export_dataset()
    # print(vm.broken_matches)
