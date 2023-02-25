import random
import warnings
from functools import reduce
from typing import Tuple, Any, List

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from matplotlib import pyplot as plt
from numpy import ndarray
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from shap import maskers
import shap
import matplotlib.ticker as mtick

from impact_score.model.lgbm_model import get_trained_model_from_csv
from impact_score.model.model_improvement.shap_tests.old_shap_decision_plot import DatasetClass, get_valorant_dataset


def load_data(filepath: str):
    data = pd.read_csv(filepath)
    y = (data['Man of the Match'] == "Yes")
    feature_names = [i for i in data.columns if data[i].dtype in [np.int64, np.int64]]
    X = data[feature_names]
    return X, y


def split_training_data(x: pd.DataFrame, y: pd.Series, random_state=0):
    return train_test_split(x, y, random_state=random_state)


def train_model(train_x, train_y, random_state=0) -> LGBMClassifier:
    return RandomForestClassifier(random_state=random_state).fit(train_x, train_y)
    # return LGBMClassifier(random_state=random_state).fit(train_x, train_y)
    # return XGBClassifier(random_state=random_state).fit(train_x, train_y)


def predict(model: RandomForestClassifier, data_for_prediction: pd.Series):
    feature_names = model.feature_names_in_
    data_for_prediction_with_names = pd.DataFrame([data_for_prediction.values], columns=feature_names)
    return model.predict_proba(data_for_prediction_with_names)


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


def _get_normalized_shap_values(baseline_probability: float, model, sample: pd.Series, shap_value: ndarray):
    sample_features = list(sample.index)
    prediction_pair = predict(model, sample)
    prediction = prediction_pair[0][1]
    prediction_diff = prediction - baseline_probability
    shap_sum = np.sum(shap_value)
    return [prediction_diff * item / shap_sum for item in shap_value][0]


def _get_probability_ticks(normalized_shap_values) -> np.ndarray:
    raw_proba_ticks = reduce(lambda x, y: x + [x[-1] + y], normalized_shap_values[1:], [normalized_shap_values[0]])
    min_tick = min(raw_proba_ticks)
    max_tick = max(raw_proba_ticks)
    step = 0.1
    return np.arange(min_tick, max_tick + step, step)


def _get_aggregated_probabilities(normalized_shap_values: ndarray, baseline_probability: float):
    shap_list = list(normalized_shap_values)
    proba_list = [baseline_probability]
    proba_list.extend(proba_list[-1] + shap_value for shap_value in shap_list)
    return proba_list


def get_probability_progression(model, sample: pd.Series):
    explainer = get_explainer(model, sample)
    sample_df = sample.to_frame().T
    all_shap_values = explainer.shap_values(sample_df)
    all_expected_values = explainer.expected_value
    shap_value = all_shap_values[1]
    baseline_probability = all_expected_values[1]
    normalized_shap_values = _get_normalized_shap_values(baseline_probability, model, sample, shap_value)
    return _get_aggregated_probabilities(normalized_shap_values, baseline_probability)


# def decision_plot_visualization(model, sample: pd.Series):
#     # shap.initjs()
#     explainer = get_explainer(model, sample)
#     sample_df = sample.to_frame().T
#     all_shap_values = explainer.shap_values(sample_df)
#     all_expected_values = explainer.expected_value
#     shap_value = all_shap_values[1]
#     baseline_probability = all_expected_values[1]
#     normalized_shap_values = _get_normalized_shap_values(baseline_probability, model, sample, shap_value)
#     probability_progression = _get_aggregated_probabilities(normalized_shap_values, baseline_probability)

#     shap_sum = sum(list(shap_value[0]))
#     normalized_sum = sum(list(normalized_shap_values))
#
#     final_probability = np.sum(normalized_shap_values) + baseline_probability
#     true_prediction = predict(model, sample)[0][1]
#     feature_names = list(sample.index.values)
#     feature_values = list(sample.values)
#     probability_ticks = _get_probability_ticks(normalized_shap_values)
#     fig, ax = plt.subplots()
#     shap.decision_plot(baseline_probability, normalized_shap_values, sample, feature_names=feature_names, highlight=0,
#                    show=False)
#     y_axis_break_long_labels(fig)
#     plt.xlabel("Attackers winning probability")
#     plt.gcf().set_size_inches(14, 8)
#     plt.show()

def get_fifa_example(sample_index: int = -1):
    x, y = load_data('FIFA 2018 Statistics.csv')
    train_x, val_x, train_y, val_y = split_training_data(x, y, random_state=1)
    model = train_model(train_x, train_y, random_state=0)
    if sample_index == -1:
        size = len(val_x)
        sample_index = random.randint(0, size - 1)
        print(f"Index: {sample_index}")
    sample = val_x.iloc[sample_index]
    probabilities = get_probability_progression(model, sample)
    return sample, probabilities


def get_valorant_example():
    valorant_model = get_trained_model_from_csv()
    x, y = valorant_model.X, valorant_model.Y
    train_x, val_x, train_y, val_y = valorant_model.X_train, valorant_model.X_test, valorant_model.Y_train, \
        valorant_model.Y_test
    model = valorant_model.model
    sample = val_x.iloc[572]
    probabilities = get_probability_progression(model, sample)
    return sample, probabilities


def __main():
    # valorant_model = get_trained_model_from_csv()
    # x, y = valorant_model.X, valorant_model.Y
    # train_x, val_x, train_y, val_y = valorant_model.X_train, valorant_model.X_test, valorant_model.Y_train,\
    #     valorant_model.Y_test
    # model = valorant_model.model
    # sample = val_x.iloc[572]
    # # force_plot_visualization(model, sample)
    # decision_plot_visualization(model, sample)
    # # model_summary_plot(model, sample)
    # return

    # custom_decision_plot()

    # pred = predict(model, sample)
    # force_plot_visualization(model, sample)

    decision_plot_visualization(model, sample)

    # model_summary_plot(model, sample)


if __name__ == "__main__":
    __main()
