from threading import Thread

import pandas as pd
from selenium import webdriver
from webscrapping.analyse_json import Analyser
from webscrapping.series_scrap import RIBScrapper
import os


class MatchScrapper:
    def __init__(self, filename: str):
        self.rbs = RIBScrapper()
        self.rib_csv = filename

    def generate_csv_table(self):
        print("File [{}] generated!".format("{}.csv".format(self.rib_csv)))
        return self.rbs.generate_link_table(self.rib_csv)

    def download_all_matches(self, **kwargs):
        os.chdir("../")
        csv_link = self.generate_csv_table()
        print("File [{}] generated!".format(csv_link))
        filename = kwargs["filename"]
        if "thread" in kwargs:
            threading = kwargs["thread"]
            if threading:
                self.rbs.selenium_threads(filename)
            else:
                self.rbs.download_links(filename)

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
        os.chdir("matches/json")
        print(os.getcwd())
        all_files = os.listdir()
        for file in all_files:
            print("Removing {}".format(file))
            os.remove(file)


if __name__ == "__main__":
    ms = MatchScrapper("na.csv")
    ms.generate_csv_table()
    # ms.download_all_matches(thread=False)
    # ms.rbs.fix_current_folder()
    # match_db = pd.read_csv("matches/events/{}".format("na_links.csv"))
    # path = os.getcwd()
    # # driver1 = webdriver.Firefox()
    # # driver1.get("https://www.google.com")
    # for link in match_db.iterrows():
    #     match_link = link[1]["match_link"]
        # ms.rbs.export_json_using_selenium(match_link, current_driver=placeholder_driver)
    #
    # l1 = "https://rib.gg/series/19407?match=41359&round=1&tab=round-stats"
    # t1 = Thread(target=ms.rbs.export_json_using_selenium, args=(l1, driver1,))
    # ms.merge_jsons_into_csv("na_merged.csv", delete_json=True)
