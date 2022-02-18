from impact_score.json_analyser.api_consumer import get_match_info
import pandas as pd


class RatingAnalyser:
    def __init__(self, match_id: int):
        self.match_id = match_id
        self.data = get_match_info(match_id)
        self.current_map = self.get_current_map()
        self.player_data = self.get_player_dict()
        self.player_names = {player["player"]["id"]: player["player"]["ign"] for player in self.current_map["players"]}

    def get_current_map(self) -> dict:
        series_by_id = self.data["series"]["seriesById"]
        matches = series_by_id["matches"]
        return [match for match in matches if match["id"] == self.match_id][0]

    def get_player_dict(self) -> dict:
        return {player["player"]["id"]: player for player in self.current_map["players"]}

    def get_player_performance(self):
        player_stats = self.current_map["stats"]
        return [(self.player_names[stat["playerId"]],
                 round(stat["score"] / stat["roundsPlayed"], 2),
                 round(float(stat["impact"]), 2))
                for stat in player_stats]

    def export_player_performance(self) -> pd.DataFrame:
        raw_dict = self.get_player_performance()
        return pd.DataFrame(raw_dict, columns=["Player", "Score", "Impact"])


if __name__ == "__main__":
    ra = RatingAnalyser(55500)
    print(ra.export_player_performance())
