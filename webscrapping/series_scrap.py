import os

import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv


# page = requests.get("https://runitback.gg/series/12728?match=25608&round=3&tab=round-stats")

def create_link(series_id: int, match_id: int):
    return "https://runitback.gg/series/{}?match={}&round=1&tab=replay".format(series_id, match_id)


class RIBScrapper:
    def __init__(self):
        pass

    def export_json(self, input_link: str):
        page = requests.get(input_link)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')
        match_tag = scripts[5]
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

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]

    @staticmethod
    def generate_links(filename: str):
        event_id = filename.split('.')[0]
        df = pd.read_csv('matches/events/{}.csv'.format(event_id))
        df_ids = df[["Series Id", "Match Id"]]
        link_dict = {}
        for i in df_ids.iterrows():
            series_id = i[1]["Series Id"]
            match_id = i[1]["Match Id"]
            final_link = "https://runitback.gg/series/{}?match={}&round=1&tab=round-stats".format(
                series_id, match_id)
            link_dict[match_id] = final_link
        with open('matches/events/{}_links.csv'.format(event_id), 'w') as f:
            f.write("match_ID,match_link\n")
            [f.write('{0},{1}\n'.format(key, value)) for key, value in link_dict.items()]

    @staticmethod
    def generate_single_link(series_id: int, match_id: int) -> str:
        return "https://runitback.gg/series/{}?match={}&round=1&tab=round-stats".format(
            series_id, match_id)

    @staticmethod
    def existing_file(filename: str):
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "Classification_datascience":
            os.chdir("webscrapping")
        os.chdir("matches/exports")
        file_list = os.listdir()
        os.chdir("../../")
        return filename in file_list

    def download_links(self, link_file: str):
        match_db = pd.read_csv("matches/events/{}".format(link_file))
        for i in match_db.iterrows():
            match_id = i[1]["match_ID"]
            match_link = i[1]["match_link"]
            print("ID → {}".format(match_id))
            self.export_json(match_link)


# il = "https://runitback.gg/series/12728?match=25609&round=1&tab=replay"
# il = "https://runitback.gg/series/12751?match=25661&round=1&tab=replay"
rb = RIBScrapper()

# rb.export_json("https://runitback.gg/series/12751?match=25661&round=18&tab=replay")
# print(rb.existing_file("15593.csv"))

# rb.generate_links("br.csv")
rb.download_links('br_links.csv')

# match_db = pd.read_csv("matches/events/br_links.csv")
# for i in match_db.iterrows():
#     match_id = i[1]["match_ID"]
#     match_link = i[1]["match_link"]
#     print("ID → {}".format(match_id))
#     rb.export_json(match_link)
