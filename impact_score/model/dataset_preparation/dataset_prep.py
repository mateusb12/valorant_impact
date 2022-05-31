from pathlib import Path
from impact_score.path_reference.folder_ref import datasets_reference
import pandas as pd


def prepare_dataset(filename: str = "4000.csv") -> pd.DataFrame:
    dataset_folder = Path(datasets_reference(), filename)
    index_features = ["RoundID", "MatchID", "RoundNumber", "Team_A_ID", "Team_A_Name", "Team_B_ID", "Team_B_Name",
                      "MapName", "RoundTime"]
    map_features = [f"MapName_{item}" for item in ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Split"]]
    redundant_features = ["weaponValue", "shields", "remainingCreds", "loadoutValue"]
    redundant_features_atk = [f"ATK_{item}" for item in redundant_features]
    redundant_features_def = [f"DEF_{item}" for item in redundant_features]
    useless_features = index_features + map_features + redundant_features_atk + redundant_features_def
    df = pd.read_csv(dataset_folder)
    df = df.drop(useless_features, axis=1)
    df = df.fillna(0)
    return df


def check_multicollinearity(input_df: pd.DataFrame) -> pd.DataFrame:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif = pd.DataFrame()
    vif["VIF"] = [variance_inflation_factor(input_df.values, i) for i in range(input_df.shape[1])]
    vif["features"] = input_df.columns
    return vif


def plot_correlation_matrix(input_df: pd.DataFrame) -> None:
    import seaborn as sns
    import matplotlib.pyplot as plt
    plt.figure(figsize=(17, 10))
    sns.heatmap(input_df.corr(), annot=True)
    plt.show()
