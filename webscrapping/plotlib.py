import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
import lightgbm
from matplotlib import pyplot as plt
import seaborn as sns

path = 'D:\\Documents\\GitHub\\Classification_datascience\\webscrapping\\matches\\rounds\\'
df = pd.read_csv('{}combined_csv.csv'.format(path))
df = pd.get_dummies(df, columns=['MapName'])

X = df.drop(['FinalWinner'], axis='columns')
Y = df.FinalWinner
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, train_size=0.8, test_size=0.2, random_state=15)

params = pd.read_csv('model_params.csv', index_col=False)
params = params.to_dict('records')[0]

model = lightgbm.LGBMClassifier(bagging_freq=params["bagging_freq"], min_data_in_leaf=params["min_data_in_leaf"],
                                max_depth=params["max_depth"],
                                learning_rate=params["learning_rate"], num_leaves=params["num_leaves"],
                                num_threads=params["num_threads"],
                                min_sum_hessian_in_leaf=params["min_sum_hessian_in_leaf"])
model.fit(X_train, Y_train)

df = pd.read_csv('{}combined_csv.csv'.format(path))


class RoundReplay:
    def __init__(self, match_id: int):
        self.match_id = match_id
        self.query = df.query('MatchID == {}'.format(match_id))
        self.round_table = self.get_round_table()

    def get_round_table(self) -> dict:
        g = self.query[["RoundNumber", "RoundID"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.RoundID))

    def get_round_id(self, round_index: int) -> int:
        return self.round_table[round_index]

    def get_round_dataframe(self, round_index: int):
        return df.query('RoundID == {}'.format(self.get_round_id(round_index)))

    def get_attacking_probabilities(self):
        old_table = self.get_round_dataframe(19)
        table = old_table.drop(['bestOF', 'RoundNumber', 'SeriesID', 'MatchID',
                                'RoundID', 'RoundTime', 'FinalWinner'],
                               axis=1)
        current_map = table.MapName.max()
        map_names = ["Ascent", "Bind", "Breeze", "Haven", "Icebox", "Split"]
        map_names.remove(current_map)
        table = pd.get_dummies(table, columns=['MapName'])
        for item in map_names:
            table['MapName_{}'.format(item)] = 0
        features = list(table.columns)

        attack_pred = [round(i[1] * 100, 2) for i in model.predict_proba(table)]
        table["Attack_win_probability"] = attack_pred
        raw_timings = [int(round(x / 1000, 0)) for x in old_table.RoundTime]
        table["Round time"] = raw_timings
        return table[["Round time", "Attack_win_probability"]]

    def plot_attacking_round(self):
        plt.figure(figsize=(12, 5))
        final_table = self.get_attacking_probabilities()

        sns.set_context(rc={'patch.linewidth': 2.0})
        sns.set(font_scale=1.3)
        ax = sns.lineplot(x="Round time", y="Attack_win_probability", data=final_table,
                          linewidth=2.0, zorder=3,
                          palette=sns.color_palette("deep"))
        ax.set(xlabel='Round time (s)', ylabel='Win probability (%)')
        ax.xaxis.labelpad = 10
        ax.grid(linewidth=1, color='white', zorder=0)
        plt.title("Attacking win probability over time")


rr = RoundReplay(25645)
print(rr.get_attacking_probabilities())
