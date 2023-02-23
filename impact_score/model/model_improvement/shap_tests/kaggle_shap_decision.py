import warnings
from typing import Tuple, Any, List

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from shap import maskers
import shap


def load_data(filepath: str):
    data = pd.read_csv(filepath)
    y = (data['Man of the Match'] == "Yes")
    feature_names = [i for i in data.columns if data[i].dtype in [np.int64, np.int64]]
    X = data[feature_names]
    return X, y


def split_training_data(x: pd.DataFrame, y: pd.Series, random_state=0):
    return train_test_split(x, y, random_state=random_state)


def train_model(train_x, train_y, random_state=0) -> LGBMClassifier:
    # return RandomForestClassifier(random_state=random_state).fit(train_x, train_y)
    return LGBMClassifier(random_state=random_state).fit(train_x, train_y)
    # return XGBClassifier(random_state=random_state).fit(train_x, train_y)


def predict(model: RandomForestClassifier, data_for_prediction: pd.Series):
    data_for_prediction_array = data_for_prediction.values.reshape(1, -1)
    return model.predict_proba(data_for_prediction_array)


def get_explainer(model, sample):
    sample_df = sample.to_frame().T
    return shap.TreeExplainer(model)
    # return shap.Explainer(model.predict_proba, sample_df)


def y_axis_break_long_labels(fig: plt.Figure):
    ax = fig.get_axes()[0]
    y_tick_labels = [label.get_text() for label in ax.get_yticklabels()]
    replace_dict = {"RegularTime": "Regular_Time", "Loadout_diff": "Loadout_Diff", "ATK_kills": "ATK_Kills",
                    "DEF_kills": "DEF_Kills", "ATK_compaction": "ATK_Compaction", "DEF_compaction": "DEF_Compaction",
                    "ATK_operators": "ATK_Operators", "DEF_operators": "DEF_Operators", "Goal Scored": "Goal_Scored",
                    "Possession %": "Possession%", "Yellow Card": "Yellow_Card", "Pass Accuracy %": "Pass Accuracy_%"}
    y_tick_labels = [replace_dict.get(label, label) for label in y_tick_labels]
    wrapped_y_tick_labels = []
    for label in y_tick_labels:
        if '_' in label:
            wrapped_lines = label.split('_')
            wrapped_label = '\n'.join(wrapped_lines)
            wrapped_y_tick_labels.append(wrapped_label)
        else:
            wrapped_y_tick_labels.append(label)
    ax.set_yticklabels(wrapped_y_tick_labels)


def model_summary_plot(model, sample: pd.Series):
    explainer = get_explainer(model, sample)
    sample_df = sample.to_frame().T
    shap_values = explainer.shap_values(sample_df)
    shap.summary_plot(shap_values, sample_df, show=False)
    plt.show()


def force_plot_visualization(model, sample: pd.Series):
    shap.initjs()
    explainer = shap.TreeExplainer(model)
    sample_df = sample.to_frame().T
    shap_values_array = explainer.shap_values(sample_df)
    expected_values_array = explainer.expected_value
    shap_value = shap_values_array[1]
    expected_value = expected_values_array[1]
    shap.force_plot(expected_value, shap_value, sample, matplotlib=True)
    plt.show()


def decision_plot_visualization(model, sample: pd.Series):
    # shap.initjs()
    explainer = get_explainer(model, sample)
    sample_df = sample.to_frame().T
    all_shap_values = explainer.shap_values(sample_df)
    all_expected_values = explainer.expected_value
    shap_value = all_shap_values[1]
    expected_value = all_expected_values[1]
    prediction = predict(model, sample)
    prediction_diff = prediction[0][1] - expected_value
    shap_sum = np.sum(shap_value)
    normalized_shap_values = [prediction_diff*item/shap_sum for item in shap_value][0]
    final_probability = np.sum(normalized_shap_values) + expected_value
    feature_names = list(sample.index.values)
    fig = plt.figure()
    shap.decision_plot(expected_value, normalized_shap_values, sample, feature_names=feature_names, highlight=0,
                       show=False)
    y_axis_break_long_labels(fig)
    plt.xlabel("Attackers winning probability")
    plt.gcf().set_size_inches(14, 8)
    # plt.tick_params(axis='y', labelsize=12)
    plt.show()


def __main():
    x, y = load_data('FIFA 2018 Statistics.csv')
    train_x, val_x, train_y, val_y = split_training_data(x, y, random_state=1)
    model = train_model(train_x, train_y, random_state=0)
    sample = val_x.iloc[5]
    # pred = predict(model, sample)
    # force_plot_visualization(model, sample)
    decision_plot_visualization(model, sample)
    # model_summary_plot(model, sample)


if __name__ == "__main__":
    __main()
