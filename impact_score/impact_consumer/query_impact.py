from impact_score.impact_consumer.impact_consumer import merge_impacts


def query_clutch_situations(match_id: int):
    df = merge_impacts(match_id)
    player_pool = [item for item in list(set(df["author"]).intersection(df["victim"])) if isinstance(item, str)]
    max_round = df["round_number"].max()
    round_book = {f"Round_{i}": None for i in range(1, max_round + 1)}
    for round_number in range(1, max_round + 1):
        query_string = f"round_number == {round_number}"
        query = df.query(query_string)
        round_book[f"Round_{round_number}"] = query
    print("nice")


def __main():
    query_clutch_situations(76730)


if __name__ == "__main__":
    __main()
