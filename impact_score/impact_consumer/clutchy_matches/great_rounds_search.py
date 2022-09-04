import pandas as pd

from impact_score.impact.match_analysis import RoundReplay


def query_great_rounds() -> None:
    tourney = pd.read_csv("tourney.csv")
    match_pool = tourney["Match Id"].to_list()
    rr = RoundReplay()
    great_rounds = rr.most_difficult_rounds_multiple_matches(match_pool)
    great_rounds.to_csv("great_rounds.csv", index=False)


def __main():
    query_great_rounds()


if __name__ == "__main__":
    __main()
