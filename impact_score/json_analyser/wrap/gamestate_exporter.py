import dataclasses

from impact_score.json_analyser.pool.analyser_pool import analyser_pool
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper
from impact_score.model.lgbm_model import get_trained_model_from_csv, ValorantLGBM


def export_gamestate(match_id: int, round_number: int, event_index: int, feature_names: list[str]) -> dict:
    a = analyser_pool.acquire()
    a.set_match(match_id)
    aw = AnalyserWrapper(a)
    df = aw.export_df()
    query = df[df["RoundNumber"] == round_number]
    query = query[feature_names]
    single_event = query.iloc[[event_index]]
    return single_event.to_dict('records')[0]


@dataclasses.dataclass
class ProbabilityTester:
    lgbm: ValorantLGBM = None
    gamestate: dict = None

    def __post_init__(self):
        self.lgbm = get_trained_model_from_csv()

    def import_gamestate(self, **kwargs):
        match_id = kwargs.get("match_id")
        round_number = kwargs.get("round_number")
        event_index = kwargs.get("event_index")
        feature_names = self.lgbm.model.feature_name_
        self.gamestate = export_gamestate(match_id, round_number, event_index, feature_names)

    def import_gamestate_example(self):
        self.import_gamestate(match_id=65588, round_number=1, event_index=3)

    def set_custom_gamestate(self, input_dict: dict):
        self.gamestate = input_dict

    def test_probability(self):
        return self.lgbm.test_probability(self.gamestate)


def __main():
    pt = ProbabilityTester()
    pt.import_gamestate_example()
    print(pt.test_probability())


if __name__ == "__main__":
    __main()
