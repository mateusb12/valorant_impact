import time
import pandas as pd
from selenium import webdriver
from webscrapping.analyse_json import Analyser
from webscrapping.series_scrap import RIBScrapper
import os
from webscrapping.wrapper.folder_fixer import fix_current_folder


class MatchScrapper:
    def __init__(self, filename: str):
        self.rbs = RIBScrapper()
        self.rib_csv = filename

    def generate_csv_table(self):
        print("File [{}] generated!".format("{}.csv".format(self.rib_csv)))
        return self.rbs.generate_link_table(self.rib_csv)

    def close_firefox(self):
        self.rbs.driver.close()

    def download_all_matches(self, **kwargs):
        os.chdir("../")
        # csv_link = self.generate_csv_table()
        # print("File [{}] generated!".format(csv_link))
        self.rbs.fix_current_folder()
        filename = kwargs["filename"]
        if "thread" in kwargs:
            threading = kwargs["thread"]
            if threading:
                self.rbs.selenium_threads(filename)
            else:
                self.rbs.download_links(filename)

    # def merge_jsons_into_csv(self, filename_output: str, **kwargs):
    #     self.merge_all_csv(filename_output)
    #     if kwargs["delete_json"]:
    #         self.delete_jsons()
    #
    # @staticmethod
    # def merge_all_csv(csv_name: str):
    #     file_list = os.listdir('../matches/json')
    #     match_list = [int(x[:-5]) for x in file_list]
    #
    #     df_list = []
    #
    #     for i in match_list:
    #         print(i)
    #         a = Analyser("{}.json".format(i))
    #         df_list.append(a.export_df(i))
    #
    #     print("Append done")
    #     print(os.getcwd())
    #     merged = pd.concat(df_list)
    #     merged.to_csv(r'{}\matches\rounds\{}'.format(os.getcwd(), csv_name), index=False)
    #
    # @staticmethod
    # def delete_jsons():
    #     os.chdir("matches/json")
    #     print(os.getcwd())
    #     all_files = os.listdir()
    #     for file in all_files:
    #         print("Removing {}".format(file))
    #         os.remove(file)


def download_run(filename: str, tag: str):
    ms = MatchScrapper(filename)
    start_time = time.time()
    ms.download_all_matches(filename="{}_{}.csv".format(filename, tag), thread=False)
    print("--- %s seconds ---" % (time.time() - start_time))
    ms.close_firefox()
    fix_current_folder()
    os.chdir("matches/events")
    os.remove("{}_{}.csv".format(filename, tag))


if __name__ == "__main__":
    download_run("na_links", "t")
    # os.remove("../matches/rounds/na_links_a.csv")
    # ms = MatchScrapper("na.csv")
    # ms.generate_csv_table()
    # ms = MatchScrapper("na.csv")
    # start_time = time.time()
    # ms.download_all_matches(filename="na_links_e.csv", thread=False)
    # print("--- %s seconds ---" % (time.time() - start_time))
    # ms.close_firefox()

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