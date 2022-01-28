import os
from typing import List, Tuple

import lightgbm
import optuna
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.metrics import brier_score_loss, log_loss, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import variance_inflation_factor
from timeit import default_timer as timer
import joblib

import pandas as pd
from pathlib import Path

from termcolor import colored

from impact_score.json_analyser.analyse_json import Analyser
from impact_score.imports.os_slash import get_slash_type

sl = get_slash_type()


def get_impact_score_reference() -> Path or None:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name in ("api", "datasets", "impact", "imports", "json_analyser", "model", "valorant_model"):
        return current_folder.parent
    Exception("Can't find impact_score folder")
    return None


def get_webscrapping_reference() -> Path or None:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name in ("model", "api", "impact"):
        webscrapping_p = current_folder.parent
    elif current_folder_name == "model_improvement":
        webscrapping_p = current_folder.parent.parent
    else:
        Exception("Can't find webscrapping folder")
        return None
    return webscrapping_p


def get_dataset_reference() -> Path:
    return Path(get_impact_score_reference(), "datasets")


class ValorantLGBM:
    def __init__(self, filename: str = None):
        if filename:
            self.df = pd.read_csv(f"{get_dataset_reference()}{sl}{filename}")
            self.old_df = self.df.copy()
        else:
            self.df = None
        self.old_df_name = filename
        self.features: List[str] = []
        self.target = ""
        self.model = None
        self.X, self.Y, self.X_train, self.Y_train, self.X_test, self.Y_test = [None] * 6
        self.pred_proba, self.pred_proba_test = [None] * 2
        self.from_file = False
        self.from_scratch = False
        self.df_prepared = False
        self.do_optuna = False

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

    def get_default_features(self, **kwargs) -> List[str]:
        global_features = ["RegularTime", "SpikeTime", "DEF_operators", "Loadout_diff"]
        raw_features = ["weaponValue", "shields", "remainingCreds", "kills"]
        roles = ["Initiator", "Duelist", "Sentinel", "Controller"]
        team_features = raw_features + roles
        prefix_team_features = self.generate_atk_def_prefix(team_features)
        trimmed = global_features + prefix_team_features
        if "delete" in kwargs:
            trimmed = [item for item in trimmed if item not in kwargs["delete"]]
        return trimmed

    def handle_dummy_column_names(self) -> Tuple[str] or None:
        first_map_index = 0
        df_columns = tuple(self.df.columns)
        for index, column_name in enumerate(df_columns):
            if column_name == "Team_B_Name":
                first_map_index = index + 1
                break
        if first_map_index != 0:
            return df_columns[first_map_index:]
        else:
            return None

    @staticmethod
    def generate_atk_def_prefix(variable_list: List[str]) -> List[str]:
        atk_p = [f"ATK_{item}" for item in variable_list]
        def_p = [f"DEF_{item}" for item in variable_list]
        return atk_p + def_p

    def set_default_features_without_multicollinearity(self):
        raw_list = ["weaponValue", "shields", "remainingCreds"]
        # raw_list = ["loadoutValue", "remainingCreds"]
        delete_list = self.generate_atk_def_prefix(raw_list)
        self.set_features(self.get_default_features(delete=delete_list))
        self.set_target("FinalWinner")
        self.df = self.df[self.features + [self.target]]

    def set_delta_setup(self):
        self.set_delta_features()
        self.set_features(["delta_loadoutValue", "delta_operators", "delta_Initiator", "delta_Duelist",
                           "delta_Sentinel", "delta_Controller", "SpikeTime", "RegularTime"])
        self.set_target("FinalWinner")
        self.trim_df()

    def set_delta_features(self):
        delta_features = ["loadoutValue", "operators", "Initiator", "Duelist", "Sentinel", "Controller"]
        for feature in delta_features:
            self.df[f"delta_{feature}"] = self.df[f"ATK_{feature}"] - self.df[f"DEF_{feature}"]

    def trim_df(self):
        combined = self.features + [self.target]
        self.df = self.df[combined]

    def prepare_df(self):
        if not self.df_prepared:
            if self.df is None:
                self.df = pd.read_csv(f"{get_dataset_reference()}{sl}{'4500.csv'}")
            self.X = self.df.drop([self.target], axis='columns')
            self.Y = self.df[self.target]
            self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(self.X, self.Y,
                                                                                    train_size=0.8, test_size=0.2,
                                                                                    random_state=15)
            self.df_prepared = True

    def train_model(self):
        current_path = Path(os.getcwd())
        current_folder = current_path.name
        webscrapping_path = current_path.parent if current_folder != "webscrapping" else current_path
        model_path = f"{webscrapping_path}{sl}model{sl}model.pkl"
        if os.path.isfile(model_path):
            self.import_model_from_file()
            self.from_file = True
        else:
            print(colored(f"[model.pkl] not found at {model_path}.", "yellow"))
            print(colored('Training model with 20 optuna iterations', "yellow"))
            self.pandas_tasks(optuna=True)
            self.from_scratch = True

    def pandas_tasks(self, **kwargs):
        self.set_default_features_without_multicollinearity()
        self.prepare_df()
        optuna_study = kwargs["optuna"]
        if optuna_study:
            self.do_optuna = True
        self.train_model_from_scratch()

    def train_model_from_scratch(self):
        if self.do_optuna:
            self.optuna_study(trials=20)
        optuna_dict = self.get_optuna_parameters()
        self.model = lightgbm.LGBMClassifier(bagging_freq=optuna_dict["bagging_freq"],
                                             min_data_in_leaf=optuna_dict["min_data_in_leaf"],
                                             max_depth=optuna_dict["max_depth"],
                                             learning_rate=optuna_dict["learning_rate"],
                                             num_leaves=optuna_dict["num_leaves"],
                                             num_threads=optuna_dict["num_threads"],
                                             min_sum_hessian_in_leaf=optuna_dict["min_sum_hessian_in_leaf"])
        self.model.fit(self.X_train, self.Y_train)
        joblib.dump(self.model, 'model.pkl')

    def import_model_from_file(self):
        webscrapping_folder = get_webscrapping_reference()
        model_folder = Path(webscrapping_folder, "model")
        os.chdir(model_folder)
        self.model: lightgbm.LGBMClassifier = joblib.load('model.pkl')

    def get_optuna_parameters(self):
        ref = self.get_optuna_reference()
        optuna_df: pd.DataFrame = pd.read_csv(f"{ref}{sl}model_params.csv")
        optuna_dict = optuna_df.to_dict(orient="list")
        return {key: value[0] for key, value in optuna_dict.items()}

    def optuna_study(self, **kwargs):
        study = optuna.create_study()
        study_trials = kwargs["trials"] if "trials" in kwargs else 10
        study.optimize(self.objective, n_trials=study_trials)
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
        if self.from_file:
            print(colored("Impossible to show metrics. You should instantiate this class with a csv dataset", "red"))
        self.pandas_tasks(optuna=False)
        self.get_feature_importance()
        self.get_model_precision()
        self.get_brier_score()
        self.get_confusion_matrix()
        self.get_f1_score()

    @staticmethod
    def get_optuna_reference() -> Path:
        current_folder = Path(os.getcwd())
        current_folder_name = current_folder.name
        if current_folder_name in ("impact", "api"):
            webscrapping = current_folder.parent
            return Path(webscrapping, "model")
        elif current_folder_name == "model":
            return current_folder
        elif current_folder_name == "model_improvement":
            return current_folder.parent

    def get_importance_dict(self) -> dict:
        return dict(zip(self.model.feature_name_, self.model.feature_importances_))

    def get_model_features(self) -> List[str]:
        return self.model.feature_name_

    def test_probability(self, example: dict = None) -> float:
        if example is None:
            aux_df = pd.DataFrame([self.get_probability_input_example()])
        else:
            aux_df = pd.DataFrame([example])
        return self.model.predict_proba(aux_df)[0][1]

    @staticmethod
    def get_probability_input_example() -> dict:
        return {"RegularTime": 0, "SpikeTime": 0, "ATK_loadoutValue": 20750, "ATK_Initiator": 2,
                "ATK_Duelist": 1, "ATK_Sentinel": 1, "ATK_Controller": 1, "ATK_kills": 1,
                "DEF_loadoutValue": 23700, "DEF_operators": 0, "DEF_kills": 1,
                "DEF_Initiator": 2, "DEF_Duelist": 1, "DEF_Sentinel": 1, "DEF_Controller": 1}

    def query_example(self, **kwargs) -> dict:
        match = kwargs["match"]
        round_ = kwargs["round_"]
        timing = kwargs["timing"]
        a = Analyser()
        a.set_match(match)
        df = a.export_df()
        match_query = df[df["MatchID"] == match]
        round_query = match_query[match_query["RoundNumber"] == round_]
        timing_query = round_query[round_query["RegularTime"] == timing]
        trim = timing_query[self.get_model_features()]
        return trim.to_dict(orient="records")[0]


def get_trained_model() -> ValorantLGBM:
    dataset = "4500.csv"
    start = timer()
    v = ValorantLGBM(dataset)
    v.train_model()
    end = timer()
    print(colored(f"Model loading time: {end - start}", "green"))
    return v


def get_dataset() -> pd.DataFrame:
    return pd.read_csv(f"{get_dataset_reference()}{sl}5000.csv")


if __name__ == "__main__":
    vm = get_trained_model()
    vm.show_all_metrics()
