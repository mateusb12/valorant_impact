from pathlib import Path

import numpy as np
import pandas as pd
import shap
from matplotlib import pyplot as plt
from numpy import ndarray
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import warnings
import textwrap

from impact_score.model.features.model_features import prepare_dataset
from impact_score.model.lgbm_model import get_trained_model_from_csv
from impact_score.path_reference.folder_ref import datasets_reference


class DatasetClass:
    def __init__(self):
        self.model, self.X_display, self.y_display = None, None, None
        self.X_train, self.X_test, self.y_train, self.y_test = None, None, None, None
        self.X, self.y = None, None
        self.random_state = 7

    def add_dataset(self, x_dataset, y_dataset):
        self.X, self.y = x_dataset, y_dataset

    def run(self):
        self.model = self.train()
        self.set_display()

    def split_train_test(self) -> tuple[lgb.basic.Dataset, lgb.basic.Dataset]:
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2,
                                                                                random_state=self.random_state)
        return lgb.Dataset(self.X_train, label=self.y_train), lgb.Dataset(self.X_test, label=self.y_test)

    def set_display(self):
        # self.X_display, self.y_display = shap.datasets.adult(display=True)
        self.X_display, self.y_display = self.X, self.y

    def train(self) -> lgb.basic.Booster:
        params = {
            "max_bin": 512,
            "learning_rate": 0.05,
            "boosting_type": "gbdt",
            "objective": "binary",
            "metric": "binary_logloss",
            "num_leaves": 10,
            "verbose": -1,
            "min_data": 100,
            "boost_from_average": True,
            "random_state": self.random_state
        }
        callbacks = [lgb.early_stopping(50, verbose=False)]
        d_train, d_test = self.split_train_test()
        return lgb.train(params, d_train, 10000, valid_sets=[d_test], callbacks=callbacks)


def y_axis_break_long_labels(fig: plt.Figure):
    ax = fig.get_axes()[0]
    y_tick_labels = [label.get_text() for label in ax.get_yticklabels()]
    replace_dict = {"RegularTime": "Regular_Time", "Loadout_diff": "Loadout_Diff", "ATK_kills": "ATK_Kills",
                    "DEF_kills": "DEF_Kills", "ATK_compaction": "ATK_Compaction", "DEF_compaction": "DEF_Compaction"
        , "ATK_operators": "ATK_Operators", "DEF_operators": "DEF_Operators"}
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


class ModelExplainer:
    def __init__(self, model_object: DatasetClass):
        self.model: lgb.basic.Booster = model_object.model
        self.X_test = model_object.X_test
        self.y_test = model_object.y_test
        self.verbose_dataframe = model_object.X_display

    @staticmethod
    def _get_expected_value(explainer: shap.explainers):
        """Returns the average output of the model across all the samples in the dataset"""
        expected_value = explainer.expected_value
        if isinstance(expected_value, list):
            expected_value = expected_value[1]
        print(f"Explainer expected value: {expected_value}")
        return expected_value

    @staticmethod
    def _compute_shap_values(explainer: shap.explainers, features: pd.DataFrame):
        """Computes the SHAP values and SHAP interaction values for the desired features using the given explainer"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shap_values = explainer.shap_values(features)[1]
            shap_interaction_values = explainer.shap_interaction_values(features)
        if isinstance(shap_interaction_values, list):
            shap_interaction_values = shap_interaction_values[1]
        return shap_values

    def _compute_predictions(self, shap_values: ndarray, expected_value: ndarray, select) -> ndarray:
        """ y_pred → predicted class labels
            misclassified → array indicating whether each example is misclassified or not"""
        y_pred = (shap_values.sum(1) + expected_value) > 0
        selected = self.y_test[select]
        return y_pred != selected

    def _get_raw_features(self, select: range) -> pd.DataFrame:
        """Returns the raw features of the examples in the dataset specified by the indices in the 'select' parameter"""
        return self.X_test.iloc[select].reset_index(drop=True)

    def _get_verbose_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Returns the verbose features of the examples in the dataset specified by the 'features' parameter"""
        index = features.index
        valid_indices = index[index.isin(self.verbose_dataframe.index)]
        return self.verbose_dataframe.loc[valid_indices]

    def shap_force_plot(self):
        explainer = shap.TreeExplainer(self.model)
        expected_value = self._get_expected_value(explainer)
        sample = np.expand_dims(self.X_test.iloc[0], axis=0)
        shap_values = explainer.shap_values(sample)
        shap.force_plot(expected_value, shap_values[0], sample[0], matplotlib=True)
        plt.show()

    def explain(self):
        """Displays the SHAP decision plot with highlighted features"""
        explainer = shap.TreeExplainer(self.model)
        expected_value = self._get_expected_value(explainer)
        select = range(13)
        raw_features = self._get_raw_features(select)
        verbose_features = self._get_verbose_features(raw_features)
        shap_values = self._compute_shap_values(explainer, raw_features)
        # sliced_shap_values, sliced_verbose_features = self._get_misclassified_samples(expected_value, select,
        #                                                                               shap_values, verbose_features)
        sliced_shap_values, sliced_verbose_features = self.get_single_sample(shap_values, 0)
        self.plot_explanation(expected_value, sliced_shap_values, sliced_verbose_features)

    def get_single_sample(self, shap_values: ndarray, row_index: int):
        """Returns a single example from the dataset, along with its SHAP values and verbose features"""
        sample_verbose_features = self.verbose_dataframe.loc[row_index]
        predicted_probability = self.model.predict(sample_verbose_features)[0]
        sample_shap_values = shap_values[row_index, :]
        return sample_shap_values, sample_verbose_features

    def _get_misclassified_samples(self, expected_value: ndarray, select: range, shap_values: ndarray,
                                   verbose_features: pd.DataFrame):
        """Returns a sample of misclassified examples from the dataset, along with their
        SHAP values and verbose features"""
        misclassified = self._compute_predictions(shap_values, expected_value, select)
        misclassified_shap_values = shap_values[misclassified]
        misclassified_verbose_features = verbose_features[misclassified]
        sample_amount = 1
        sliced_shap_values = misclassified_shap_values[:sample_amount]
        sliced_verbose_features = misclassified_verbose_features[:sample_amount]
        return sliced_shap_values, sliced_verbose_features

    @staticmethod
    def plot_explanation(expected_value: ndarray, sliced_shap_values, sliced_verbose_features):
        fig = plt.figure()
        shap.decision_plot(expected_value, sliced_shap_values, sliced_verbose_features,
                           link='logit', highlight=0, feature_display_range=slice(None, -31, -1), show=False)
        y_axis_break_long_labels(fig)
        plt.xlabel("Attackers winning probability")
        plt.gcf().set_size_inches(9, 6)
        plt.tick_params(axis='y', labelsize=12)
        plt.show()


def __get_adult_dataset() -> tuple[pd.DataFrame, pd.Series]:
    return shap.datasets.adult(display=False)


def __get_valorant_dataset() -> tuple[pd.DataFrame, pd.Series]:
    raw_csv = prepare_dataset("merged.csv")
    df_size = raw_csv.shape[0]
    reduced_size = 32561
    reduced_df = raw_csv.head(reduced_size)
    y = reduced_df['FinalWinner'].replace({0: False, 1: True}).transpose().to_numpy()
    X = reduced_df.drop(columns=['FinalWinner'])
    return X, y


def __main():
    X, y = __get_adult_dataset()
    # X, y = __get_valorant_dataset()
    # X2, y2 = __get_valorant_dataset()
    dc = DatasetClass()
    dc.add_dataset(X, y)
    dc.run()
    de = ModelExplainer(dc)
    de.explain()
    return


if __name__ == "__main__":
    __main()