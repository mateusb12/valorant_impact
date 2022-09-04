import lightgbm

from impact_score.json_analyser.wrap.analyser_wrapper import get_match_df
from impact_score.model.lgbm_model import get_trained_model_from_csv


def query_shap_situation(match_id: int, round_number: int, event_index: int):
    match_data = get_match_df(match_id)
    round_data = match_data[match_data["RoundNumber"] == round_number]
    gamestate = round_data.iloc[event_index]
    vm = get_trained_model_from_csv()
    model: lightgbm.LGBMClassifier = vm.model
    features = model.feature_name_
    return gamestate[features]


def __main():
    query_shap_situation(match_id=78746, round_number=12, event_index=7)


if __name__ == "__main__":
    __main()
