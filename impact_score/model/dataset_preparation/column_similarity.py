import dataclasses
import math
import pprint
from collections import Counter
from pathlib import Path

import pandas as pd
from pandas import Index

from impact_score.path_reference.folder_ref import datasets_reference


@dataclasses.dataclass
class ColumnSimilarity:
    old_df: pd.DataFrame
    new_df: pd.DataFrame
    current_column: str = None

    @staticmethod
    def __counter_cosine_similarity(c1, c2):
        terms = set(c1).union(c2)
        dot_prod = sum(c1.get(k, 0) * c2.get(k, 0) for k in terms)
        magA = math.sqrt(sum(c1.get(k, 0) ** 2 for k in terms))
        magB = math.sqrt(sum(c2.get(k, 0) ** 2 for k in terms))
        return dot_prod / (magA * magB)

    @staticmethod
    def __raw_similarity(c1, c2):
        pot = [1 for x, y in zip(c1, c2) if x == y]
        return len(pot) / len(c1)

    def __column_similarity(self, column_name: str) -> float:
        counterA = Counter(self.old_df[column_name].tolist())
        counterB = Counter(self.new_df[column_name].tolist())

        return self.__counter_cosine_similarity(counterA, counterB)

    def __raw_column_similarity(self, column_name: str) -> float:
        self.current_column = column_name
        ca = self.old_df[column_name].tolist()
        cb = self.new_df[column_name].tolist()
        return self.__raw_similarity(ca, cb)

    def __get_common_cols(self) -> Index:
        return self.old_df.columns.intersection(self.new_df.columns)

    def get_similar_cols(self) -> dict:
        common_cols = self.__get_common_cols()
        return {column: self.__raw_column_similarity(column) for column in common_cols}


def __main():
    df_a = pd.read_csv(Path(datasets_reference(), "4000.csv"))
    df_b = pd.read_csv(Path(datasets_reference(), "merged.csv"))
    cs = ColumnSimilarity(df_a, df_b)
    similarity = cs.get_similar_cols()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(similarity)
    # print(similarity)


if __name__ == "__main__":
    __main()
