from pathlib import Path

import pandas as pd

from impact_score.path_reference.folder_ref import datasets_reference


def prepare_dataset(filename: str = "4000.csv") -> pd.DataFrame:
    dataset_folder = Path(datasets_reference(), filename)
    df = pd.read_csv(dataset_folder)
    dataset_columns = list(df.columns)
    index_f = get_index_features()
    map_f = get_map_features()
    red_f = get_redundant_side_features()
    weak_f = get_weak_features()
    features_to_remove = index_f + map_f + red_f + weak_f
    final_features = [feature for feature in features_to_remove if feature in dataset_columns]
    df = df.drop(final_features, axis=1)
    df = df.fillna(0)
    return df


def get_index_features() -> list[str]:
    return ["RoundID", "MatchID", "RoundNumber", "Team_A_ID", "Team_A_Name", "Team_B_ID", "Team_B_Name",
            "MapName", "RoundTime"]


def get_map_features() -> list[str]:
    return [f"MapName_{item}" for item in ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Split"]]


def get_redundant_side_features() -> list[str]:
    redundant_features = ["weaponValue", "shields", "remainingCreds", "loadoutValue",
                          "Duelist", "Sentinel", "Initiator", "Controller"]
    redundant_features_atk = [f"ATK_{item}" for item in redundant_features]
    redundant_features_def = [f"DEF_{item}" for item in redundant_features]
    return redundant_features_atk + redundant_features_def


def get_weak_features() -> list[str]:
    return []


def __main():
    df = prepare_dataset("5000.csv")
    print(df.columns)


if __name__ == "__main__":
    __main()
