import os
import time
from time import sleep

from selenium import webdriver
import selenium.webdriver.firefox.webdriver as FirefoxWebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import requests
from bs4 import BeautifulSoup
import pandas as pd

# page = requests.get("https://runitback.gg/series/12728?match=25608&round=3&tab=round-stats")
from selenium.webdriver.support.wait import WebDriverWait

from webscrapping.wrapper.folder_fixer import fix_current_folder


def create_link(series_id: int, match_id: int):
    return "https://runitback.gg/series/{}?match={}&round=1&tab=replay".format(series_id, match_id)


class RIBScrapper:
    def __init__(self, **kwargs):
        if "open" in kwargs and not kwargs["open"]:
            self.driver = None
        else:
            self.driver: FirefoxWebDriver = webdriver.Firefox()
        self.current_path = os.getcwd()

    def late_open(self):
        """
        Open the driver if it is not already open
        """
        if self.driver is None:
            self.driver = webdriver.Firefox()

    def close_driver(self):
        if self.driver is not None:
            self.driver.close()

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]

    @staticmethod
    def existing_file(filename: str, foldername: str):
        """
        Check if a given file exists in the current folder
        :param foldername: folder name
        :param filename
        :return: True or False
        """
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")
        elif current_folder == "wrapper":
            os.chdir("..")
        os.chdir("matches/{}".format(foldername))
        file_list = os.listdir()
        os.chdir("../../")
        return filename in file_list

    @staticmethod
    def generate_single_link(series_id: int, match_id: int) -> str:
        """
        Generate a single link to a match, based on the series ID and the match ID.
        :param series_id:
        :param match_id:
        :return: Full link string
        """
        return "https://runitback.gg/series/{}?match={}&round=1&tab=round-stats".format(
            series_id, match_id)

    @staticmethod
    def seconds_to_time(time_in_seconds: int) -> str:
        """
        Convert seconds to a string
        :param time_in_seconds:
        :return: String formatted as "HH:MM:SS"
        """
        hours = time_in_seconds // 3600
        minutes = (time_in_seconds % 3600) // 60
        seconds = time_in_seconds % 60
        return "{}:{}:{}".format(hours, minutes, seconds)

    def fix_current_folder(self):
        path = os.getcwd()
        folder = path.split("\\")[-1]
        if folder == "wrapper":
            path_parent = os.path.dirname(os.getcwd())
            os.chdir(path_parent)
            new_path = os.getcwd()
            self.current_path = new_path

    def download_links(self, link_table: str):
        """
        Get a .csv file containing all matches links and download all matches json files.
        If you don't want to download a given match, you should change its ID in the .csv file to "none" or "null".
        :param link_table: .csv file containing all matches links
        """
        print("Reading links from [{}]".format(link_table))
        fix_current_folder()
        match_db = pd.read_csv("matches/events/{}".format(link_table))
        size = len(match_db)
        total_time_seconds = int(size * 131 / 50)
        for index, i in enumerate(match_db.iterrows(), start=1):
            remaining_seconds = int(total_time_seconds - (index * 131 / 50))
            total_time_date = self.seconds_to_time(remaining_seconds)
            match_id = i[1]["match_ID"]
            print("Downloading match ID → {}      ({}/{})   → [Remaining time: {}]"
                  .format(match_id, index, size, total_time_date))
            if match_id not in ["none", "null"]:
                match_link = i[1]["match_link"]
                exist = self.existing_file("{}.json".format(match_id), "json")
                # t = Thread(target=self.export_json_using_selenium, args=(match_link,))
                # t.start()
                if not exist:
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

    def handle_map_buttons(self) -> dict:
        """
        :return: Returns a dict with all clickable map buttons across the series.
        """
        button_mapping = {}
        current_driver = self.driver
        best_of_text = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div[1]/div["
                                                            "2]/div[2]").text
        best_of = int(best_of_text.split(" ")[-1])
        first_map_button = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div["
                                                                "2]/div/div[2]/div/div[2]")
        button_mapping[1] = first_map_button
        if best_of > 1:
            second_map_button = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div["
                                                                     "2]/div/div[3]")
            button_mapping[2] = second_map_button
            try:
                third_map_button = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div["
                                                                        "2]/div/div[4]")
                button_mapping[3] = third_map_button
            except NoSuchElementException:
                print("BO3 but 3rd map does not exist")
        if best_of > 3:
            try:
                fourth_map_button = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div["
                                                                         "2]/div/div[5]/div")
                button_mapping[4] = fourth_map_button
            except NoSuchElementException:
                print("BO5 but 4th map does not exist")
            try:
                fifth_map_button = current_driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div["
                                                                        "2]/div/div[6]/div")
                button_mapping[5] = fifth_map_button
            except NoSuchElementException:
                print("BO5 but 5th map does not exist")
        button_mapping["best_of"] = best_of
        return button_mapping

    def handle_single_html_source_code(self) -> str:
        """
        :return: Returns a single string with a json containing all the data from 2D Replay of that link
        """
        current_driver = self.driver

        html = current_driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.findAll('script')
        content_filter = [i for i in scripts if len(i.attrs) == 0]
        match_tag = content_filter[1]
        match_script = match_tag.contents[0].string
        script = match_script[:match_script.find("?{}:")]
        trash_script = 'window.__INITIAL_STATE__="undefined"==typeof '
        return script[45:]

    def handle_whole_series(self) -> dict:
        """
        :return: Returns a dict containing the 2D Replay JSON for all maps in the series
        """
        start = time.time()
        all_maps = self.handle_map_buttons()
        map_jsons = {}
        map_ids = {}
        id_to_json = {}

        for i in range(1, all_maps["best_of"] + 1):
            if i in all_maps:
                all_maps[i].click()
                self.driver.refresh()
                all_maps = self.handle_map_buttons()
                map_jsons[i] = self.handle_single_html_source_code()
                map_ids[i] = int(self.driver.current_url.split("=")[-1])
            else:
                break

        end = time.time()
        running_time = end - start
        print("That series took {} to scrap".format(running_time))

        return {value: map_jsons[key] for key, value in map_ids.items()}

    def export_json_using_selenium(self, input_link: str, current_driver=None, **kwargs):
        if current_driver is None:
            current_driver = self.driver
        current_driver.get(input_link)
        script = self.handle_single_html_source_code()
        output_index = self.scrap_match_link(input_link)

        if "folder_location" in kwargs:
            output_location = "matches/{}/{}.json".format(kwargs["folder_location"], output_index)
        else:
            output_location = "matches/json/{}.json".format(output_index)

        with open(output_location, "w", encoding='utf-8') as f:
            f.write(script)
            print("File downloaded at {}".format(output_location))

    def export_json_of_whole_series(self, input_link: str, current_driver=None, **kwargs):
        if current_driver is None:
            current_driver = self.driver
        current_driver.get(input_link)
        script_dict = self.handle_whole_series()

        current_folder = os.getcwd()

        for key, value in script_dict.items():
            json_name = "{}.json".format(key)
            if "folder_location" in kwargs:
                output_location = "matches/json/{}".format(json_name)
            else:
                output_location = "matches/{}/{}.json".format(kwargs["folder_location"], json_name)

            with open(output_location, "w", encoding='utf-8') as f:
                f.write(value)
                print("File downloaded at {}".format(output_location))
                f.close()


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
