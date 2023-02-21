from pathlib import Path

import pandas as pd
import shap
from numpy import ndarray
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import warnings

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


class ModelExplainer:
    def __init__(self, model_object: DatasetClass):
        self.model: lgb.basic.Booster = model_object.model
        self.X_test = model_object.X_test
        self.y_test = model_object.y_test
        self.X_display = model_object.X_display

    @staticmethod
    def _get_expected_value(explainer: shap.explainers):
        """Returns the average output of the model across all the samples in the dataset"""
        expected_value = explainer.expected_value
        if isinstance(expected_value, list):
            expected_value = expected_value[1]
        print(f"Explainer expected value: {expected_value}")
        return expected_value

    @staticmethod
    def _compute_shap_values(explainer, features):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shap_values = explainer.shap_values(features)[1]
            shap_interaction_values = explainer.shap_interaction_values(features)
        if isinstance(shap_interaction_values, list):
            shap_interaction_values = shap_interaction_values[1]
        return shap_values, shap_interaction_values

    def _compute_predictions(self, shap_values, expected_value, select) -> tuple[ndarray, ndarray]:
        """ y_pred → predicted class labels
            misclassified → array indicating whether each example is misclassified or not"""
        y_pred = (shap_values.sum(1) + expected_value) > 0
        selected = self.y_test[select]
        misclassified = y_pred != selected
        return y_pred, misclassified

    def _get_raw_features(self, select) -> pd.DataFrame:
        """It contains the features for which we want to compute SHAP values"""
        return self.X_test.iloc[select].reset_index(drop=True)

    def _get_verbose_features(self, features) -> pd.DataFrame:
        """It contains the features that will be highlighted in the SHAP decision plot"""
        index = features.index
        valid_indices = index[index.isin(self.X_display.index)]
        return self.X_display.loc[valid_indices]

    def explain(self):
        """Displays the SHAP decision plot with highlighted features"""
        explainer = shap.TreeExplainer(self.model)
        expected_value = self._get_expected_value(explainer)
        select = range(13)
        raw_features = self._get_raw_features(select)
        verbose_features = self._get_verbose_features(raw_features)
        shap_values, shap_interaction_values = self._compute_shap_values(explainer, raw_features)
        y_pred, misclassified = self._compute_predictions(shap_values, expected_value, select)
        misclassified_shap_values = shap_values[misclassified]
        misclassified_verbose_features = verbose_features[misclassified]
        shap.decision_plot(expected_value, misclassified_shap_values, misclassified_verbose_features,
                           link='logit', highlight=0, feature_display_range=slice(None, -31, -1))


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
    # X, y = __get_adult_dataset()
    X, y = __get_valorant_dataset()
    # X2, y2 = __get_valorant_dataset()
    dc = DatasetClass()
    dc.add_dataset(X, y)
    dc.run()
    de = ModelExplainer(dc)
    de.explain()
    return


if __name__ == "__main__":
    __main()
