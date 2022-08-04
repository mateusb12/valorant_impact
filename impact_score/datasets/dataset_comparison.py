import pandas as pd


class DatasetComparison:
    def __init__(self):
        self.old = pd.read_csv("4000.csv")
        self.new = pd.read_csv("merged.csv")
        common_cols = self.__get_common_columns()
        exclude_cols = ["RoundID"]
        self.old = self.old[common_cols]
        self.new = self.new[common_cols]
        self.old = self.old.drop(exclude_cols, axis=1)
        self.new = self.new.drop(exclude_cols, axis=1)
        self.current = pd.DataFrame()
        self.match_id = 0

    def set_match(self, match_id: int):
        self.match_id = match_id

    def __get_all_matches(self):
        return self.old["MatchID"].unique()

    def __get_common_columns(self) -> list[str]:
        old_columns = self.old.columns
        new_columns = self.new.columns
        return [col for col in old_columns if col in new_columns]

    def __filter(self) -> dict:
        current = self.current[self.current["MatchID"] == self.match_id]
        max_round = current["RoundNumber"].max()
        gamestate_dict = {key: [] for key in range(1, max_round + 1)}
        for index, row in current.iterrows():
            row_dict = row.to_dict()
            round_number = row_dict["RoundNumber"]
            gamestate_dict[round_number].append(row_dict)
        return gamestate_dict

    def __compare_dicts(self, old_dict: dict, new_dict: dict) -> list[int]:
        round_list = list(old_dict.keys())
        broken_rounds = []
        for round_number in round_list:
            old_round = old_dict[round_number]
            new_round = new_dict[round_number]
            broken_tags = []
            for old_gamestate, new_gamestate in zip(old_round, new_round):
                check = self.compare_gamestate(old_gamestate, new_gamestate)
                if check != 0:
                    broken_rounds.append(round_number)
                    broken_tags.append(check)
            print("ae")
        return broken_rounds

    @staticmethod
    def compare_gamestate(g1: dict, g2: dict) -> tuple or int:
        # sourcery skip: use-next
        for old, new in zip(g1.items(), g2.items()):
            if old != new:
                return old, new
        return 0

    def compare_both(self) -> list[int]:
        self.current = self.old
        old_dict = self.__filter()
        self.current = self.new
        new_dict = self.__filter()

        return self.__compare_dicts(old_dict, new_dict)

    def full_pipeline(self) -> dict:
        match_list = self.__get_all_matches()
        match_dict = {key: False for key in match_list}
        for match_id in match_list:
            self.set_match(match_id)
            result = self.compare_both()
            if len(result) > 0:
                match_dict[match_id] = True
        return {key: match_dict[key] for key in match_dict if match_dict[key]}


def __main():
    dc = DatasetComparison()
    dc.set_match(67207)
    aux = dc.compare_both()
    print(aux)
    print("done")


if __name__ == "__main__":
    __main()
