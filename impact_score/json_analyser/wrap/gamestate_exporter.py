from impact_score.json_analyser.pool.analyser_pool import analyser_pool
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper


def export_gamestate(**kwargs) -> dict:
    match_id = kwargs.get("match_id")
    round_number = kwargs.get("round_number")
    event_index = kwargs.get("event_index")
    feature_names = ['RegularTime', 'SpikeTime', 'ATK_operators', 'ATK_kills',
                     'ATK_Initiator', 'ATK_Duelist', 'ATK_Sentinel', 'ATK_Controller',
                     'DEF_operators', 'DEF_kills', 'DEF_Initiator', 'DEF_Duelist',
                     'DEF_Sentinel', 'DEF_Controller', 'Loadout_diff', 'atkCompaction', 'defCompaction']
    a = analyser_pool.acquire()
    a.set_match(match_id)
    aw = AnalyserWrapper(a)
    df = aw.export_df()
    query = df[df["RoundNumber"] == round_number]
    query = query[feature_names]
    single_event = query.iloc[[event_index]]
    return single_event.to_dict('records')[0]


def __main():
    aux = export_gamestate(match_id=65588, round_number=1, event_index=3)
    print(aux)


if __name__ == "__main__":
    __main()
