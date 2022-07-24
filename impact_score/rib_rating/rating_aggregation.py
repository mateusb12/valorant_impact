import pandas as pd

from impact_score.model.progress_printer import time_metrics
from impact_score.rib_rating.rating_single_match import RatingAnalyser
from timeit import default_timer as timer


class RatingAggregator:
    def __init__(self):
        self.raw_id_list = pd.read_csv("id_list.csv")
        self.ra = RatingAnalyser()
        self.ids = self.raw_id_list["Match Id"].tolist()

    def aggregate(self) -> pd.DataFrame:
        aggregate_pot = []
        start = timer()
        self.ids = self.ids[:5]
        size = len(self.ids)
        for index, match_id in enumerate(self.ids):
            loop = timer()
            time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_id)
            self.ra.set_match(match_id)
            aggregate_pot.append(self.ra.export_player_performance())
        return pd.concat(aggregate_pot, axis=0, ignore_index=True)


if __name__ == '__main__':
    ra = RatingAggregator()
    champions = ra.aggregate()
    print(champions)
