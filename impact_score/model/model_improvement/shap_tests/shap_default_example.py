import pandas as pd
import shap
from numpy import ndarray
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import warnings


class AdultModel:
    def __init__(self, display=False):
        self.model, self.X_display, self.y_display = None, None, None
        self.X_train, self.X_test, self.y_train, self.y_test = None, None, None, None
        self.X, self.y = shap.datasets.adult(display=display)
        self.random_state = 7

    def run(self):
        self.model = self.train()

    def split_train_test(self) -> tuple[lgb.basic.Dataset, lgb.basic.Dataset]:
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2,
                                                                                random_state=self.random_state)
        self.X_display, self.y_display = shap.datasets.adult(display=True)
        return lgb.Dataset(self.X_train, label=self.y_train), lgb.Dataset(self.X_test, label=self.y_test)

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


class AdultShapValues:
    def __init__(self, model_object: AdultModel):
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

    def _compute_predictions(self, shap_values, expected_value, select):
        """ y_pred → predicted class labels
            misclassified → array indicating whether each example is misclassified or not"""
        y_pred = (shap_values.sum(1) + expected_value) > 0
        misclassified = y_pred != self.y_test[select]
        return y_pred, misclassified

    def _get_features(self, select) -> pd.DataFrame:
        """It contains the features for which we want to compute SHAP values"""
        return self.X_test.iloc[select]

    def _get_features_display(self, features) -> pd.DataFrame:
        """It contains the features that will be highlighted in the SHAP decision plot"""
        return self.X_display.loc[features.index]

    def explain(self):
        """Displays the SHAP decision plot with highlighted features"""
        explainer = shap.TreeExplainer(self.model)
        expected_value = self._get_expected_value(explainer)
        select = range(20)
        features = self._get_features(select)
        features_display = self._get_features_display(features)
        shap_values, shap_interaction_values = self._compute_shap_values(explainer, features)
        y_pred, misclassified = self._compute_predictions(shap_values, expected_value, select)
        shap.decision_plot(expected_value, shap_values[misclassified], features_display[misclassified],
                           link='logit', highlight=0)


def __main():
    am = AdultModel()
    am.run()
    ash = AdultShapValues(am)
    ash.explain()
    return


if __name__ == "__main__":
    __main()
