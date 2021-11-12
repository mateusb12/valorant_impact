import os

import requests
from bs4 import BeautifulSoup
import pandas as pd


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

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]

    @staticmethod
    def generate_links(filename: str) -> str:
        event_id = filename.split('.')[0]
        print("Reading file [{}.csv] from [matches/events/{}.csv]".format(event_id, event_id))
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

    @staticmethod
    def seconds_to_time(time_in_seconds: int) -> str:
        hours = time_in_seconds // 3600
        minutes = (time_in_seconds % 3600) // 60
        seconds = time_in_seconds % 60
        return "{}:{}:{}".format(hours, minutes, seconds)

    def download_links(self, link_file: str):
        print("Reading links from [{}]".format(link_file))
        match_db = pd.read_csv("matches/events/{}".format(link_file))
        size = len(match_db)
        total_time_seconds = int(size * 7/3)
        for index, i in enumerate(match_db.iterrows(), start=1):
            remaining_seconds = int(total_time_seconds - (index * 7/3))
            total_time_date = self.seconds_to_time(remaining_seconds)
            match_id = i[1]["match_ID"]
            match_link = i[1]["match_link"]

            print("Downloading match ID → {}      ({}/{})   → [Remaining time: {}]"
                  .format(match_id, index, size, total_time_date))
            self.export_json(match_link)


if __name__ == '__main__':
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
