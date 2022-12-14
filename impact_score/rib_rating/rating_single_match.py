from impact_score.json_analyser.core.api_consumer import request_http_match_data
import pandas as pd


class RatingAnalyser:
    def __init__(self):
        self.match_id = None
        self.data = None
        self.current_map = None
        self.player_data = None
        self.player_names = None

    def set_match(self, match_id: int):
        self.match_id = match_id
        self.data = request_http_match_data(match_id)
        self.current_map = self.get_current_map()
        self.player_data = self.get_player_dict()
        self.player_names = {player["player"]["id"]: player["player"]["ign"] for player in self.current_map["players"]}

    def get_current_map(self) -> dict:
        series_by_id = self.data["series"]["seriesById"]
        matches = series_by_id["matches"]
        return [match for match in matches if match["id"] == self.match_id][0]

    def get_player_dict(self) -> dict:
        return {player["player"]["id"]: player for player in self.current_map["players"]}

    def export_player_performance(self) -> pd.DataFrame:
        player_stats = self.current_map["stats"]
        raw_list = [(self.player_names[stat["playerId"]],
                     round(float(stat["impact"]), 2),
                     round(stat["score"] / stat["roundsPlayed"], 2))
                    for stat in player_stats]
        pre_df = pd.DataFrame(raw_list, columns=["Player", "Impact", "Score"])
        df_types = pre_df.dtypes
        return pre_df


if __name__ == "__main__":
    ra = RatingAnalyser()
    ra.set_match(54900)
    ex = ra.export_player_performance()
    print(ex)
