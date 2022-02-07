from pathlib import Path
import os

from termcolor import colored

from impact_score.imports.os_slash import get_slash_type
from impact_score.model.lgbm_model import ValorantLGBM
from timeit import default_timer as timer

sl = get_slash_type()


def lgbm_get_model_path() -> Path:
    current_path = Path(os.getcwd())
    parent_path = current_path.parent
    parent_name = parent_path.name
    if parent_name == "impact_score":
        return Path(parent_path, "model", "model.pkl")
    elif parent_name == "model":
        return Path(parent_path, "model.pkl")
    else:
        model_path = Path(parent_path, "model", "model.pkl")
        print(colored(f"Model file not found: {model_path}", "red"))
        Exception(f"Model file not found at {model_path}")


def load_lgbm() -> ValorantLGBM:  # sourcery skip: use-named-expression
    start = timer()
    model_path = lgbm_get_model_path()
    print(colored(f"Model path: {model_path}", "green"))
    existing_pkl = model_path.is_file()
    if existing_pkl:
        vm = ValorantLGBM()
        vm.import_model_from_file()
        end = timer()
        print(colored(f"Model loading time: {end - start}", "green"))
        return vm
    else:
        Exception(f"Model file not found at {model_path}")


if __name__ == "__main__":
    load_lgbm()
