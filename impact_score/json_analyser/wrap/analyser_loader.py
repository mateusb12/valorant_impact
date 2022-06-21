from impact_score.json_analyser.pool.analyser_pool import analyser_pool, CoreAnalyser


def get_analyser(input_match_id: int) -> CoreAnalyser:
    a: CoreAnalyser = analyser_pool.acquire()
    a.set_match(input_match_id)
    return a
