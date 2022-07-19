import os
from typing import List

import lightgbm
import optuna
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split
import joblib

import pandas as pd
from pathlib import Path

from termcolor import colored

from impact_score.imports.os_slash import get_slash_type
from impact_score.model.dataset_preparation.dataset_prep import prepare_dataset
from impact_score.path_reference.folder_ref import model_reference

sl = get_slash_type()


def get_impact_score_reference() -> Path or None:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name in ("api", "datasets", "impact", "imports", "json_analyser", "model", "valorant_model"):
        return current_folder.parent
    Exception("Can't find impact_score folder")
    return None


def get_impact_score_folder_reference() -> Path or None:
    current_folder = Path(os.getcwd())
    current_folder_name = current_folder.name
    if current_folder_name in ("model", "api", "impact"):
        folder_p = current_folder.parent
    elif current_folder_name == "model_improvement":
        folder_p = current_folder.parent.parent
    else:
        Exception("Can't find webscrapping folder")
        return None
    return folder_p


def get_dataset_reference() -> Path:
    return Path(get_impact_score_reference(), "datasets")


class ValorantLGBM:
    def __init__(self, filename: str = None):
        self.df = None
        self.old_df = None
        self.filename = filename
        self.features: List[str] = []
        self.target = ""
        self.model: lightgbm = None
        self.X, self.Y, self.X_train, self.Y_train, self.X_test, self.Y_test = [None] * 6
        self.df_prepared = False
        self.do_optuna = False

    def setup_dataframe(self, filename: str):
        self.df = prepare_dataset(filename)

    def setup_features_and_target(self):
        self.old_df = self.df.copy()
        self.set_target("FinalWinner")
        self.features = [col for col in self.df.columns if col != self.target]

    def set_target(self, target: str):
        self.target = target

    def train_model(self, **kwargs):
        self.do_optuna = kwargs.get("optuna_study", False)
        self.prepare_df()
        self.fit_model()
        # self.export_model()

    def prepare_df(self):
        if not self.df_prepared:
            if self.df is None:
                self.df = prepare_dataset(self.filename)
            self.X = self.df.drop([self.target], axis='columns')
            self.Y = self.df[self.target]
            self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(self.X, self.Y,
                                                                                    train_size=0.8, test_size=0.2,
                                                                                    random_state=15)
            self.df_prepared = True

    def fit_model(self):
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
        # joblib.dump(self.model, 'model.pkl')

    def import_model_from_file(self):
        # model_folder = Path(impact_folder, "model")
        model_folder = model_reference()
        pkl_path = Path(model_folder, "model.pkl")
        self.model: lightgbm.LGBMClassifier = joblib.load(pkl_path)

    def export_model_to_pkl(self):
        joblib.dump(self.model, 'model.pkl')

    @staticmethod
    def get_optuna_parameters():
        ref = model_reference()
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

    # def query_example(self, **kwargs) -> dict:
    #     match = kwargs["match"]
    #     round_ = kwargs["round_"]
    #     timing = kwargs["timing"]
    #     a = Analyser()
    #     a.set_match(match)
    #     df = a.export_df()
    #     match_query = df[df["MatchID"] == match]
    #     round_query = match_query[match_query["RoundNumber"] == round_]
    #     timing_query = round_query[round_query["RegularTime"] == timing]
    #     trim = timing_query[self.get_model_features()]
    #     return trim.to_dict(orient="records")[0]


def get_dataset() -> pd.DataFrame:
    return pd.read_csv(f"{get_dataset_reference()}{sl}5000.csv")


def get_trained_model_from_csv() -> ValorantLGBM:
    model_obj = ValorantLGBM()
    model_obj.setup_dataframe("4000.csv")
    model_obj.setup_features_and_target()
    model_obj.train_model(optuna_study=False)
    return model_obj


def get_trained_model_from_pkl() -> ValorantLGBM:
    model_obj = ValorantLGBM()
    model_obj.import_model_from_file()
    return model_obj


def get_pkl_model() -> ValorantLGBM:
    model_obj = ValorantLGBM()
    model_obj.import_model_from_file()
    return model_obj


def existing_pkl() -> bool:
    model_folder = model_reference()
    pkl_ref = Path(model_folder, "model.pkl")
    return pkl_ref.exists()


if __name__ == "__main__":
    vm = get_trained_model_from_csv()
    print(vm.model.feature_name_)
    # # vm.import_model_from_file()
    # vm.setup_dataframe("4000.csv")
    # vm.setup_features_target()
    # vm.train_model(optuna_study=False)
    # vm.show_all_metrics()
