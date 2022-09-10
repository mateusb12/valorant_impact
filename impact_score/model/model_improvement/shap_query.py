import lightgbm
import pandas as pd

from impact_score.json_analyser.wrap.analyser_wrapper import get_match_df
from impact_score.model.lgbm_model import get_trained_model_from_csv


def query_shap_situation(match_id: int, round_number: int, event_index: int):
    match_data = get_match_df(match_id)
    round_data = match_data[match_data["RoundNumber"] == round_number]
    gamestate = round_data.iloc[event_index]
    return pd.DataFrame(gamestate)


def raw_shap_situation(match_id: int, round_number: int, event_index: int):
    match_data = get_match_df(match_id)
    round_data = match_data[match_data["RoundNumber"] == round_number]
    return round_data.iloc[event_index]


def __main():
    aux = query_shap_situation(match_id=78746, round_number=12, event_index=7)
    df = pd.DataFrame()


if __name__ == "__main__":
    __main()
