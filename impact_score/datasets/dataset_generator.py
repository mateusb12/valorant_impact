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
from impact_score.model.progress_printer import time_metrics
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
        self.match_pot = self.__get_all_split_files()
        self.dataset_index = []
        self.broken_matches = []

    def __split_dataset(self, amount: int) -> None:
        dataset_ref = Path(datasets_reference(), "matches", "all_matches.csv")
        raw_dataset = pd.read_csv(dataset_ref)
        dataset = pd.DataFrame(raw_dataset["Match Id"].unique(), columns=["Match Id"])
        output_ref = Path(datasets_reference(), "split")
        output_files = self.__get_all_split_files()
        splits = np.array_split(dataset, amount)
        stamps = [chr(i) for i in range(65, 65 + amount)]
        if len(output_files) == 0:
            for split, stamp in zip(splits, stamps):
                current_stamp = f"{stamp}.csv"
                existing = output_files.__contains__(current_stamp)
                if not existing:
                    ref = Path(output_ref, f"{stamp}.csv")
                    split.to_csv(ref, index=False)

    def __set_file(self, filename: str):
        self.current_file = filename
        dataset_reference = Path(datasets_reference(), "split", filename)
        matches_csv = pd.read_csv(dataset_reference)
        self.match_list = matches_csv["Match Id"].tolist()

    @staticmethod
    def __get_all_split_files():
        file_list = Path(datasets_reference(), "split").iterdir()
        return [f.name for f in file_list if f.name != "__init__.py"]

    @staticmethod
    def __get_all_dataset_files():
        return [f.name for f in Path(datasets_reference()).iterdir() if f.name[:6] == "Split_"]

    def __consume_dataset(self) -> pd.DataFrame:
        df_ref = Path(datasets_reference(), "split", self.current_file)
        df = pd.read_csv(df_ref)
        size = len(df)
        dataset_list = []
        start = timer()
        for index, match_index in enumerate(self.match_list):
            loop = timer()
            print(colored(f"File: {self.current_file}"))
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_index)
            self.a.set_match(match_index)
            try:
                match_df = self.wrapper.export_df()
            except KeyError:
                print(colored(f"Match #{match_index} is broken", "red"))
                self.broken_matches.append(match_index)
                continue
            dataset_list.append(match_df)
        print(colored(f"Slice {self.current_file} concluded", "green"))
        os.remove(df_ref)
        return pd.concat(dataset_list)

    def __export_dataset(self):
        huge_df = self.__consume_dataset()
        map_name_dummy = pd.get_dummies(huge_df["MapName"], prefix="MapName")
        huge_df = pd.concat([huge_df, map_name_dummy], axis=1)
        output_ref = Path(datasets_reference(), f"Split_{self.current_file}")
        huge_df.to_csv(output_ref, index=False)
        print(colored(f"Dataset {self.current_file} exported", "green"))

    def merge_datasets(self, output_file: str):
        files = self.__get_all_dataset_files()
        df_pot = []
        ref_pot = []
        for file in files:
            df_ref = Path(datasets_reference(), f"{file}")
            ref_pot.append(df_ref)
            df = pd.read_csv(df_ref)
            df_pot.append(df)
        merged_df = pd.concat(df_pot, ignore_index=True)
        output_ref = Path(datasets_reference(), f"{output_file}")
        merged_df.to_csv(output_ref, index=False)
        for ref in ref_pot:
            os.remove(ref)

    def run_pipeline(self, split_amount: int, filename: str):
        self.__split_dataset(amount=split_amount)
        split_files = self.__get_all_split_files()
        for file in split_files:
            self.__set_file(file)
            self.__export_dataset()
        dat = self.__get_all_dataset_files()
        self.merge_datasets(output_file=filename)
        print(dat)


if __name__ == "__main__":
    vdg = ValorantDatasetGenerator()
    vdg.run_pipeline(split_amount=5, filename="100.csv")
    # vdg.export_dataset()
    # print(vm.broken_matches)
