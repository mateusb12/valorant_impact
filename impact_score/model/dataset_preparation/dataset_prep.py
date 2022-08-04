import pandas as pd


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
