from pathlib import Path

import pandas as pd

from impact_score.path_reference.folder_ref import datasets_reference


def prepare_dataset(filename: str = "4000.csv") -> pd.DataFrame:
    dataset_folder = Path(datasets_reference(), filename)
    df = pd.read_csv(dataset_folder)
    dataset_columns = list(df.columns)
    generate_role_diff(df)
    index_f = __get_index_features()
    map_f = __get_map_features()
    red_f = __get_redundant_side_features()
    weak_f = __get_weak_features()
    features_to_remove = index_f + map_f + red_f + weak_f
    all_features = [feature for feature in features_to_remove if feature in dataset_columns]
    df = df.drop(all_features, axis=1)
    df = df.fillna(0)
    final_features = list(df.columns)
    return df


def __get_index_features() -> list[str]:
    return ["RoundID", "MatchID", "RoundNumber", "Team_A_ID", "Team_A_Name", "Team_B_ID", "Team_B_Name",
            "MapName", "RoundTime"]


def __get_map_features() -> list[str]:
    return [f"MapName_{item}" for item in ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Split"]]


def __get_redundant_side_features() -> list[str]:
    redundant_features = ["weaponValue", "shields", "remainingCreds", "loadoutValue",
                          "Sentinel", "Initiator", "Controller", "Duelist"]
    redundant_features_atk = [f"ATK_{item}" for item in redundant_features]
    redundant_features_def = [f"DEF_{item}" for item in redundant_features]
    return redundant_features_atk + redundant_features_def


def __get_weak_features() -> list[str]:
    return ["Loadout_diff"]


def generate_role_diff(input_df: pd.DataFrame) -> None:
    roles = ["Sentinel", "Initiator", "Controller", "Duelist"]
    for role in roles:
        input_df[f"{role}_loadout_diff"] = input_df[f"ATK_{role}"] - input_df[f"DEF_{role}"]


def __main():
    df = prepare_dataset("merged.csv")
    print(df.columns)


if __name__ == "__main__":
    __main()
