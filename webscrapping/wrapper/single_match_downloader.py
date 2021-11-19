import pandas as pd

from webscrapping.series_scrap import RIBScrapper
from webscrapping.analyse_json import Analyser


class SingleMatchDownloader:
    def __init__(self, match_id: int, series_id: int):
        self.match_id = match_id
        self.series_id = series_id
        self.rb = RIBScrapper(open=False)
        self.existing_json = self.rb.existing_file("{}.json".format(match_id), "json")
        self.existing_csv = self.rb.existing_file("{}.csv".format(match_id), "exports")

    def download(self):
        if not self.existing_json:
            download_link = self.rb.generate_single_link(self.series_id, self.match_id)
            self.rb.late_open()
            self.rb.export_json_using_selenium(download_link, folder_location="exports")
            self.rb.close_driver()

        if not self.existing_csv:
            a = Analyser("{}.json".format(self.match_id))
            new_match_frame = a.export_df(self.match_id)
            new_match_frame.to_csv(r'matches\exports\{}.csv'.format(self.match_id), index=False)
            print("CSV downloaded at matches\\exports\\{}.csv".format(self.match_id))
            return

        if self.existing_json:
            print("Match {} was already downloaded!".format(self.match_id))

    def get_csv(self) -> pd.DataFrame:
        if self.existing_csv:
            return pd.read_csv(r'matches\exports\{}.csv'.format(self.match_id))


if __name__ == "__main__":
    match = int(input("Enter match number: "))
    series = int(input("Enter series number: "))
    smd = SingleMatchDownloader(match, series)
    smd.download()
