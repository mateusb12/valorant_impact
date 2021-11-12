import pandas as pd

from webscrapping.analyse_json import Analyser
from webscrapping.series_scrap import RIBScrapper
import os


class MatchScrapper:
    def __init__(self, filename: str):
        self.rbs = RIBScrapper()
        self.rib_csv = filename

    def download_all_matches(self):
        os.chdir("../")
        csv_link = self.rbs.generate_links(self.rib_csv)
        print("File [{}] generated!".format(csv_link))
        self.rbs.async_download_run(csv_link)

    def merge_jsons_into_csv(self, filename_output: str, **kwargs):
        self.merge_all_csv(filename_output)
        if kwargs["delete_json"]:
            self.delete_jsons()

    @staticmethod
    def merge_all_csv(csv_name: str):
        file_list = os.listdir('../matches/json')
        match_list = [int(x[:-5]) for x in file_list]

        df_list = []

        for i in match_list:
            print(i)
            a = Analyser("{}.json".format(i))
            df_list.append(a.export_df(i))

        print("Append done")
        print(os.getcwd())
        merged = pd.concat(df_list)
        merged.to_csv(r'{}\matches\rounds\{}'.format(os.getcwd(), csv_name), index=False)

    @staticmethod
    def delete_jsons():
        current_dir = os.getcwd()
        os.chdir("matches/json")
        print(os.getcwd())
        all_files = os.listdir()
        for file in all_files:
            print("Removing {}".format(file))
            os.remove(file)


if __name__ == "__main__":
    ms = MatchScrapper("na.csv")
    ms.download_all_matches()
    ms.merge_jsons_into_csv("na_merged.csv", delete_json=True)

