import os
from selenium import webdriver
import selenium.webdriver.firefox.webdriver as FirefoxWebDriver

import requests
from bs4 import BeautifulSoup
import pandas as pd


# page = requests.get("https://runitback.gg/series/12728?match=25608&round=3&tab=round-stats")

def create_link(series_id: int, match_id: int):
    return "https://runitback.gg/series/{}?match={}&round=1&tab=replay".format(series_id, match_id)


class RIBScrapper:
    def __init__(self):
        self.driver: FirefoxWebDriver = webdriver.Firefox()

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]

    @staticmethod
    def existing_file(filename: str):
        """
        Check if a given file exists in the current folder
        :param filename
        :return: True or False
        """
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")
        os.chdir("matches/exports")
        file_list = os.listdir()
        os.chdir("../../")
        return filename in file_list

    @staticmethod
    def generate_single_link(series_id: int, match_id: int) -> str:
        return "https://runitback.gg/series/{}?match={}&round=1&tab=round-stats".format(
            series_id, match_id)

    @staticmethod
    def seconds_to_time(time_in_seconds: int) -> str:
        hours = time_in_seconds // 3600
        minutes = (time_in_seconds % 3600) // 60
        seconds = time_in_seconds % 60
        return "{}:{}:{}".format(hours, minutes, seconds)

    @staticmethod
    def fix_current_folder():
        path = os.getcwd()
        folder = path.split("\\")[-1]
        if folder == "wrapper":
            path_parent = os.path.dirname(os.getcwd())
            os.chdir(path_parent)
            new_path = os.getcwd()

    def generate_links(self, filename: str) -> str:
        """
        Get a RIB .csv file and convert it to a list of match links.
        You should get that RIB file from the RIB bot discord.
        :param filename: RIB file
        :return: generate a CSV file containing all matches links
        """
        event_id = filename.split('.')[0]
        print("Reading file [{}.csv] from [matches/events/{}.csv]".format(event_id, event_id))
        self.fix_current_folder()
        df = pd.read_csv('matches/events/{}.csv'.format(event_id))
        df_ids = df[["Series Id", "Match Id"]]
        link_dict = {}
        for i in df_ids.iterrows():
            series_id = i[1]["Series Id"]
            match_id = i[1]["Match Id"]
            final_link = "https://rib.gg/series/{}?match={}&round=1&tab=round-stats".format(
                series_id, match_id)
            link_dict[match_id] = final_link
        with open('matches/events/{}_links.csv'.format(event_id), 'w') as f:
            f.write("match_ID,match_link\n")
            [f.write('{0},{1}\n'.format(key, value)) for key, value in link_dict.items()]
        return "{}_links.csv".format(event_id)

    def download_links(self, link_table: str):
        """
        Get a .csv file containing all matches links and download all matches json files.
        :param link_table: .csv file containing all matches links
        """
        print("Reading links from [{}]".format(link_table))
        self.fix_current_folder()
        match_db = pd.read_csv("matches/events/{}".format(link_table))
        size = len(match_db)
        total_time_seconds = int(size * 131 / 50)
        for index, i in enumerate(match_db.iterrows(), start=1):
            remaining_seconds = int(total_time_seconds - (index * 131 / 50))
            total_time_date = self.seconds_to_time(remaining_seconds)
            match_id = i[1]["match_ID"]
            match_link = i[1]["match_link"]

            print("Downloading match ID → {}      ({}/{})   → [Remaining time: {}]"
                  .format(match_id, index, size, total_time_date))
            # t = Thread(target=self.export_json_using_selenium, args=(match_link,))
            # t.start()
            self.export_json_using_selenium(match_link)

    def export_json(self, input_link: str, input_session: requests.Session):
        """
        Get a https://runitback.gg/ link and convert it to a json file.
        Link example: https://runitback.gg/series/12728?match=25608&round=3&tab=round-stats
        :param input_link: run it back link
        :param input_session: the session to use for the request.
        :return: JSON file
        """
        page = input_session.get(input_link)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')
        content_filter = [i for i in scripts if len(i.attrs) == 0]
        match_tag = content_filter[1]
        match_script = match_tag.contents[0].string
        match_script = match_script[45:]
        first_half = match_script[:match_script.find("?{}:")]
        output_index = self.scrap_match_link(input_link)
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")
        output_location = "matches/json/{}.json".format(output_index)
        with open(output_location, 'w', encoding='utf-8') as fp:
            fp.write(first_half)
        return output_location

    def export_json_using_selenium(self, input_link: str, current_driver=None):
        if current_driver is None:
            current_driver = self.driver
        current_driver.get(input_link)
        html = current_driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.findAll('script')
        content_filter = [i for i in scripts if len(i.attrs) == 0]
        match_tag = content_filter[1]
        match_script = match_tag.contents[0].string
        script = match_script[:match_script.find("?{}:")]
        output_index = self.scrap_match_link(input_link)

        with open("matches/json/{}.json".format(output_index), "w", encoding='utf-8') as f:
            f.write(script)

    def selenium_threads(self, link_table: str):
        match_db = pd.read_csv("matches/events/{}".format(link_table))
        # thread_driver_a = webdriver.Firefox()
        # thread_driver_b = webdriver.Firefox()
        # for link in match_db.iterrows():
        #     match_link = link[1]["match_link"]
        #     self.export_json_using_selenium(match_link, current_driver=thread_driver_a)
            # t = Thread(target=self.export_json_using_selenium, args=(link, thread_driver_a,))
            # t.start()


if __name__ == '__main__':
    rb = RIBScrapper()

    # start = time.time()
    # rb.download_links("na_links.csv")
    # loop = asyncio.get_event_loop()
    # link_table = "na_links.csv"
    # match_db = pd.read_csv("matches/events/{}".format(link_table))
    # future = asyncio.ensure_future(rb.async_download_links(match_db))
    # r = loop.run_until_complete(future)
    # print(r)
    # end = time.time()
    # print("Time was {}".format(end - start))
