from pathlib import Path
import os

from termcolor import colored

from impact_score.imports.os_slash import get_slash_type
from impact_score.model.lgbm_model import ValorantLGBM
from timeit import default_timer as timer

sl = get_slash_type()


def load_lgbm():  # sourcery skip: use-named-expression
    start = timer()
    current_path = Path(os.getcwd())
    parent_path = current_path.parent
    parent_name = parent_path.name
    if parent_name == "impact_score":
        model_path = Path(parent_path, "model", "model.pkl")
        existing_pkl = model_path.is_file()
        if existing_pkl:
            vm = ValorantLGBM()
            vm.import_model_from_file()
            end = timer()
            print(colored(f"Model loading time: {end - start}", "green"))
            return vm
        else:
            Exception(f"Model file not found at {model_path}")
    else:
        Exception(f"Model file not found at {current_path}")


if __name__ == "__main__":
    load_lgbm()
