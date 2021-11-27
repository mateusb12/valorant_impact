import os
from typing import List, Optional

import pandas as pd

from webscrapping.series_scrap import RIBScrapper
from webscrapping.analyse_json import Analyser


class SingleMatchDownloader:
    def __init__(self, series_id: int, **kwargs):
        self.match_id = kwargs["match_id"] if "match_id" in kwargs else 0
        self.series_id = series_id
        self.rb = RIBScrapper(open=False)
        self.series_table = self.get_series_table()
        self.existing_json = self.rb.existing_file("{}.json".format(self.match_id), "json")
        self.existing_csv = self.rb.existing_file("{}.csv".format(self.match_id), "exports")

    @staticmethod
    def get_series_table() -> pd.DataFrame:
        current_folder = os.getcwd().split("\\")[-1]
        output = None
        if current_folder == "wrapper":
            os.chdir("..\\matches\\events\\")
        if current_folder == "webscrapping":
            os.chdir("matches\\events\\")
        output = pd.read_csv('na.csv', index_col=False)
        os.chdir("..\\..")
        return output

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

    def get_match_id_by_series(self) -> List[int]:
        an = Analyser("{}.json".format(self.match_id))
        return an.all_matches
        # sliced_series = self.series_table[["Match Id", "Series Id"]]
        # query = sliced_series.query('`Series Id`=={}'.format(self.series_id))
        # return list(query["Match Id"])

    def download_full_series(self, **kwargs):
        match_id_list = self.get_match_id_by_series()
        if not match_id_list:
            Exception("No matches found for series {}".format(self.series_id))
        json_download = False
        csv_download = False
        for i in match_id_list:
            existing_json = self.rb.existing_file("{}.json".format(i), "json")
            if not existing_json:
                json_download = True
            existing_csv = self.rb.existing_file("{}.csv".format(i), "exports")
            if not existing_csv:
                csv_download = True
            if json_download and csv_download:
                break

        if json_download:
            self.download_jsons()

        if csv_download:
            self.download_csvs(match_id_list)

    def download_jsons(self):
        download_link = "https://rib.gg/series/{}".format(self.series_id)
        self.rb.late_open()
        self.rb.export_json_of_whole_series(download_link, folder_location="exports")
        self.rb.close_driver()
        print("JSONs successfully downloaded!")

    @staticmethod
    def download_csvs(input_id_list: List[int]):
        for m in input_id_list:
            anl = Analyser("{}.json".format(m))
            new_match_frame = anl.export_df(m)
            new_match_frame.to_csv(r'matches\exports\{}.csv'.format(m), index=False)
            print("CSV downloaded at matches\\exports\\{}.csv".format(m))


if __name__ == "__main__":
    a = Analyser("{}.json".format(42038))
    csv_list = a.all_matches
    print(csv_list)
    match = 42041
    series = 19728
    smd = SingleMatchDownloader(series, match_id=42041)
    smd.download_csvs(csv_list)
    # match = int(input("Enter match number: "))
    # series = int(input("Enter series number: "))
    # smd = SingleMatchDownloader(match, series)
    # smd.download()
