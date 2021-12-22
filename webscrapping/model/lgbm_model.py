import os
from typing import List

import lightgbm
import optuna
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.metrics import brier_score_loss, log_loss, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import variance_inflation_factor

import pandas as pd
from pathlib import Path

from termcolor import colored


class ValorantLGBM:
    def __init__(self, filename: str):
        self.df = pd.read_csv(f"{self.get_dataset_reference()}\\{filename}")
        self.old_df = self.df.copy()
        self.features: List[str] = []
        self.target = ""
        self.model = None
        self.X, self.Y, self.X_train, self.Y_train, self.X_test, self.Y_test = [None] * 6
        self.pred_proba, self.pred_proba_test = [None] * 2

    def check_multicollinearity(self) -> pd.DataFrame:
        X_variables = self.df[self.features]
        vif_data = pd.DataFrame()
        vif_data["feature"] = X_variables.columns
        vif_data["VIF"] = [variance_inflation_factor(X_variables.values, i) for i in range(X_variables.shape[1])]
        return vif_data

    def set_features(self, features: List[str]):
        self.features = features

    def set_target(self, target: str):
        self.target = target

    def trim_df(self):
        combined = self.features + [self.target]
        self.df = self.df[combined]

    def set_delta_setup(self):
        self.set_delta_features()
        self.set_features(["delta_loadoutValue", "delta_operators", "delta_Initiator", "delta_Duelist",
                           "delta_Sentinel", "delta_Controller", "SpikeTime", "RegularTime"])
        self.set_target("FinalWinner")
        self.trim_df()

    @staticmethod
    def get_default_features(**kwargs) -> List[str]:
        default = ["RegularTime", "SpikeTime", "ATK_loadoutValue", "ATK_weaponValue", "ATK_shields",
                   "ATK_remainingCreds", "ATK_operators", "ATK_Initiator", "ATK_Duelist", "ATK_Sentinel",
                   "ATK_Controller", "DEF_loadoutValue", "DEF_weaponValue", "DEF_shields", "DEF_remainingCreds",
                   "DEF_operators", "DEF_Initiator", "DEF_Duelist", "DEF_Sentinel", "DEF_Controller"]
        if "delete" in kwargs:
            return [item for item in default if item not in kwargs["delete"]]
        else:
            return default

    def set_default_features_without_multicollinearity(self):
        raw_list = ["weaponValue", "shields", "remainingCreds"]
        atk_list = [f"ATK_{item}" for item in raw_list]
        def_list = [f"DEF_{item}" for item in raw_list]
        delete_list = atk_list + def_list
        self.set_features(self.get_default_features(delete=delete_list))
        self.set_target("FinalWinner")
        self.df = self.df[self.features + [self.target]]

    def set_delta_features(self):
        delta_features = ["loadoutValue", "operators", "Initiator", "Duelist", "Sentinel", "Controller"]
        for feature in delta_features:
            self.df[f"delta_{feature}"] = self.df[f"ATK_{feature}"] - self.df[f"DEF_{feature}"]

    def train_model(self, **kwargs):
        self.X = self.df.drop([self.target], axis='columns')
        self.Y = self.df[self.target]
        self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(self.X, self.Y,
                                                                                train_size=0.8, test_size=0.2,
                                                                                random_state=15)
        X_train, X_valid, Y_train, Y_valid = train_test_split(self.X_train, self.Y_train,
                                                              train_size=0.9, test_size=0.1, random_state=15)
        if "optuna" in kwargs:
            self.optuna_study()

        optuna_dict = self.get_optuna_parameters()
        self.model = lightgbm.LGBMClassifier(bagging_freq=optuna_dict["bagging_freq"],
                                             min_data_in_leaf=optuna_dict["min_data_in_leaf"],
                                             max_depth=optuna_dict["max_depth"],
                                             learning_rate=optuna_dict["learning_rate"],
                                             num_leaves=optuna_dict["num_leaves"],
                                             num_threads=optuna_dict["num_threads"],
                                             min_sum_hessian_in_leaf=optuna_dict["min_sum_hessian_in_leaf"])
        self.model.fit(X_train, Y_train)

    def get_optuna_parameters(self):
        ref = self.get_optuna_reference()
        optuna_df: pd.DataFrame = pd.read_csv(f"{ref}\\model_params.csv")
        optuna_dict = optuna_df.to_dict(orient="list")
        return {key: value[0] for key, value in optuna_dict.items()}

    def optuna_study(self):
        study = optuna.create_study()
        study.optimize(self.objective, n_trials=20)
        trial = study.best_trial
        print(colored(f"Best trial: Value: {trial.value}", "green"))
        print(colored(f"Params: {trial.params}", "green"))
        pd_param = pd.DataFrame([trial.params])
        pd_param.to_csv('model_params.csv', index=False)

    def objective(self, trial):
        bagging_freq = trial.suggest_int('bagging_freq', 1, 10),
        min_data_in_leaf = trial.suggest_int('min_data_in_leaf', 2, 100),
        max_depth = trial.suggest_int('max_depth', 1, 20),
        learning_rate = trial.suggest_loguniform('learning_rate', 0.001, 0.1),
        num_leaves = trial.suggest_int('num_leaves', 2, 70),
        num_threads = trial.suggest_int('num_threads', 1, 10),
        min_sum_hessian_in_leaf = trial.suggest_int('min_sum_hessian_in_leaf', 1, 10),

        model = lightgbm.LGBMClassifier(bagging_freq=bagging_freq,
                                        min_data_in_leaf=min_data_in_leaf,
                                        max_depth=max_depth,
                                        learning_rate=learning_rate,
                                        num_leaves=num_leaves,
                                        num_threads=num_threads,
                                        min_sum_hessian_in_leaf=min_sum_hessian_in_leaf)
        model.fit(self.X_train, self.Y_train)
        pred_proba_test = model.predict_proba(self.X_test)
        return brier_score_loss(self.Y_test, pd.DataFrame(pred_proba_test)[1])

    def get_feature_importance(self):
        feature_imp = pd.DataFrame(sorted(zip(self.model.feature_importances_, self.X.columns)),
                                   columns=['Value', 'Feature'])
        plt.figure(figsize=(10, 10))
        sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value", ascending=False))
        sns.set(font_scale=1)
        plt.title('Features')
        plt.tight_layout()
        plt.show()

    def get_model_precision(self):
        plt.figure(figsize=(10, 5))
        pred_proba = self.model.predict_proba(self.X_train)
        pred_proba_test = self.model.predict_proba(self.X_test)
        self.pred_proba = pred_proba
        self.pred_proba_test = pred_proba_test

        gmt = ["accuracy train", "accuracy test", "log loss train", "log loss test", "brier score train",
               "brier score test"]
        metrics = {'Labels': gmt,
                   'Value': [self.model.score(self.X_train, self.Y_train), self.model.score(self.X_test, self.Y_test),
                             log_loss(self.Y_train, pred_proba), log_loss(self.Y_test, pred_proba_test),
                             brier_score_loss(self.Y_train, pd.DataFrame(pred_proba)[1]),
                             brier_score_loss(self.Y_test, pd.DataFrame(pred_proba_test)[1])]
                   }
        sns.set_context(rc={'patch.linewidth': 2.0})
        sns.set(font_scale=1.3)
        ax = sns.barplot(x='Labels', y='Value', data=metrics, linewidth=2.0, edgecolor=".2", zorder=3,
                         palette=sns.color_palette("deep"))

        plt.ylabel('%')
        ax.grid(linewidth=1, color='white', zorder=0)
        ax.set_facecolor("#d7d7e0")
        plt.title("Model performance metrics")
        plt.show()

    def get_brier_score(self):
        print("Brier score → {}".format(brier_score_loss(self.Y_test, pd.DataFrame(self.pred_proba_test)[1])))

    def get_confusion_matrix(self):
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(self.Y_test, self.model.predict(self.X_test, num_iteration=50))
        cm = (cm / cm.sum(axis=1).reshape(-1, 1))

        sns.heatmap(cm, cmap="YlGnBu", vmin=0., vmax=1., annot=True, annot_kws={'size': 45})
        plt.title("wa", fontsize=5)
        plt.ylabel('Predicted label')
        plt.xlabel('True label')
        plt.show()

    def get_f1_score(self):
        Y_pred = self.model.predict(self.X_test)
        f1 = classification_report(self.Y_test, Y_pred, output_dict=True)["weighted avg"]["f1-score"]
        print(f"F1 score → {f1}")

    def show_all_metrics(self):
        self.get_feature_importance()
        self.get_model_precision()
        self.get_brier_score()
        self.get_confusion_matrix()
        self.get_f1_score()

    @staticmethod
    def get_dataset_reference() -> Path:
        current_folder = Path(os.getcwd())
        webscrapping = current_folder.parent
        return Path(webscrapping, "matches", "datasets")

    @staticmethod
    def get_optuna_reference() -> Path:
        current_folder = Path(os.getcwd())
        current_folder_name = current_folder.name
        if current_folder_name == "impact":
            webscrapping = current_folder.parent
            return Path(webscrapping, "model")
        elif current_folder_name == "model":
            return current_folder


if __name__ == "__main__":
    vm = ValorantLGBM("500.csv")
    vm.set_default_features_without_multicollinearity()
    # vm.set_delta_setup()
    # vm.set_delta_features()
    # vm.set_features(["delta_loadoutValue", "delta_operators", "delta_Initiator", "delta_Duelist",
    #                  "delta_Sentinel", "delta_Controller"])
    # vm.set_target("RoundWinner")
    # vm.trim_df()
    vm.train_model()
    vm.show_all_metrics()
