import pandas as pd
import matplotlib.pyplot as plt

from impact_score.impact.match_analysis import RoundReplay


class ProbabilityCalibration:
    def __init__(self, match_id: int = 78746, round_number: int = 10, event_index: int = 0, side: str = "atk"):
        self.match_id = match_id
        self.round_number = round_number
        self.event_index = event_index
        self.rr = RoundReplay()
        self.rr.set_match(match_id)
        self.rr.choose_round(round_number)
        self.all_features = self.rr.model.feature_name_
        self.gamestate_df = self.rr.get_round_dataframe(self.round_number)
        self.sliced_gamestate = self.gamestate_df[self.all_features].copy()[event_index:event_index+1]
        self.side = side

    def create_multiple_gamestates(self, variable_name: str, variable_range: tuple[int, int, int])\
            -> pd.DataFrame:
        value_range = list(range(variable_range[0], variable_range[1], variable_range[2]))
        size = len(value_range)
        gamestate_df = pd.concat([self.sliced_gamestate] * size, ignore_index=True)
        if variable_name not in self.all_features:
            raise ValueError(f"{variable_name} is not a valid feature name")
        gamestate_df[variable_name] = value_range
        probs = self.rr.model.predict_proba(gamestate_df)
        current_probs = [item[0] for item in probs] if self.side == "atk" else [item[1] for item in probs]
        gamestate_df["Probability"] = current_probs
        gamestate_df["Feature"] = variable_name
        return gamestate_df

    @staticmethod
    def plot_probabilities(input_df: pd.DataFrame):
        variable_name = input_df["Feature"].unique()[0]
        plt.figure(figsize=(10, 5))
        plt.plot(input_df[variable_name], input_df["Probability"])
        plt.rcParams["figure.figsize"] = (10, 5)
        plt.grid(b=True, which='major', color='#666666', linestyle='-')
        plt.scatter(input_df[variable_name], input_df["Probability"], marker="o", color="red")
        plt.xlabel(variable_name)
        plt.ylabel("Probability")
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:.0%}".format(x)))
        plt.show()


def __main():
    pc = ProbabilityCalibration(match_id=79334, round_number=14, event_index=0, side="atk")
    aux = pc.create_multiple_gamestates("Loadout_diff", (-10000, 10000, 1000))
    pc.plot_probabilities(aux)
    return 0


if __name__ == '__main__':
    __main()
