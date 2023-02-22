from typing import Tuple, Any, List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import shap


def load_data(filepath: str):
    data = pd.read_csv(filepath)
    y = (data['Man of the Match'] == "Yes")
    feature_names = [i for i in data.columns if data[i].dtype in [np.int64, np.int64]]
    X = data[feature_names]
    return X, y


def split_training_data(x: pd.DataFrame, y: pd.Series, random_state=0):
    return train_test_split(x, y, random_state=random_state)


def train_model(train_x, train_y, random_state=0) -> RandomForestClassifier:
    return RandomForestClassifier(random_state=random_state).fit(train_x, train_y)


def predict(model: RandomForestClassifier, data_for_prediction: pd.Series):
    data_for_prediction_array = data_for_prediction.values.reshape(1, -1)
    return model.predict_proba(data_for_prediction_array)


def force_plot_visualization(model, sample: pd.Series):
    shap.initjs()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)
    shap.force_plot(explainer.expected_value[1], shap_values[1], sample, matplotlib=True)
    plt.show()


def decision_plot_visualization(model, sample: pd.Series):
    shap.initjs()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)
    feature_names = list(sample.index.values)
    class_names = ['Not Man of the Match', 'Man of the Match']
    shap.decision_plot(explainer.expected_value[1], shap_values[1], feature_names=feature_names,
                       show=False)
    plt.show()


def __main():
    x, y = load_data('FIFA 2018 Statistics.csv')
    train_x, val_x, train_y, val_y = split_training_data(x, y, random_state=1)
    model = train_model(train_x, train_y, random_state=0)
    sample = val_x.iloc[5]
    # pred = predict(model, sample)
    decision_plot_visualization(model, sample)


if __name__ == "__main__":
    __main()
