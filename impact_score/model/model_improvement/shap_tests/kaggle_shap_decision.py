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


def _get_normalized_shap_values(baseline_probability: float, model, sample: pd.Series, shap_value: ndarray):
    prediction = predict(model, sample)
    prediction_diff = prediction[0][1] - baseline_probability
    shap_sum = np.sum(shap_value)
    return [prediction_diff * item / shap_sum for item in shap_value][0]


def _get_probability_ticks(normalized_shap_values) -> np.ndarray:
    raw_proba_ticks = reduce(lambda x, y: x + [x[-1] + y], normalized_shap_values[1:], [normalized_shap_values[0]])
    min_tick = min(raw_proba_ticks)
    max_tick = max(raw_proba_ticks)
    step = 0.1
    return np.arange(min_tick, max_tick + step, step)


def decision_plot_visualization(model, sample: pd.Series):
    # shap.initjs()
    explainer = get_explainer(model, sample)
    sample_df = sample.to_frame().T
    all_shap_values = explainer.shap_values(sample_df)
    all_expected_values = explainer.expected_value
    shap_value = all_shap_values[1]
    baseline_probability = all_expected_values[1]
    normalized_shap_values = _get_normalized_shap_values(baseline_probability, model, sample, shap_value)
    final_probability = np.sum(normalized_shap_values) + baseline_probability
    true_prediction = predict(model, sample)[0][1]
    feature_names = list(sample.index.values)
    feature_values = list(sample.values)
    probability_ticks = _get_probability_ticks(normalized_shap_values)
    fig, ax = plt.subplots()
    shap.decision_plot(baseline_probability, normalized_shap_values, sample, feature_names=feature_names, highlight=0,
                       show=False)
    # ax.set_xticklabels(probability_ticks)
    y_axis_break_long_labels(fig)
    plt.xlabel("Attackers winning probability")
    plt.gcf().set_size_inches(14, 8)
    # plt.tick_params(axis='y', labelsize=12)
    plt.show()


def custom_decision_plot():
    probabilities = [0.5, 0.1, 0.67, 0.88, 0.35, 0.12]
    feature_values = [70, 100, 120, 150, 170, 200]
    feature_names = [" ", "feature1", "feature2", "feature3", "feature4", "feature5"]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax2 = ax.twiny()

    previous_x, previous_y, previous_probability = None, None, None
    for i, (feature_name, probability) in enumerate(zip(feature_names, probabilities)):
        new_x = probability - 0.5
        new_y = i if i != 0 else i + 0.05

        # Plot the point
        ax.scatter(new_x, new_y, color='blue')

        if previous_x is not None and previous_y is not None:
            ax.plot([previous_x, new_x], [previous_y, new_y], color='gray', linestyle='--', linewidth=1)

        # Label the point with the feature name and probability
        if i != 0:
            probability_shift = (probability - previous_probability)
            ax.annotate(f"{feature_values[i]} ({probability_shift:.2%})", (new_x, new_y), xytext=(10, -2),
                        textcoords='offset pixels', ha='left', va='top', fontsize=12, color='black')

        previous_x, previous_y = new_x, new_y
        previous_probability = probability

    x = probabilities
    y = feature_values
    for i in range(len(x) - 1):
        ax.plot([x[i], x[i + 1]], [y[i], y[i + 1]], color='blue', linewidth=2)

    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels(feature_names)
    ax.set_xlabel('Impact on Probability', fontsize=14)
    ax.set_ylim([0, len(feature_names)])  # set the y-axis limits
    ax_labels = ax.get_xticklabels()

    ax2.set_xticks(ax.get_xticks())
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xlabel('Probability', fontsize=14)
    ax.axvline(x=0, color='black')
    # ax2.axvline(x=0, color='red')

    plt.show()


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

    custom_decision_plot()

    x, y = load_data('FIFA 2018 Statistics.csv')
    train_x, val_x, train_y, val_y = split_training_data(x, y, random_state=1)
    model = train_model(train_x, train_y, random_state=0)
    sample = val_x.iloc[7]
    # pred = predict(model, sample)
    # force_plot_visualization(model, sample)

    decision_plot_visualization(model, sample)

    # model_summary_plot(model, sample)


if __name__ == "__main__":
    __main()
