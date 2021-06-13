import json
import requests
from bs4 import BeautifulSoup


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
        output_location = "matches/{}.json".format(output_index)

        with open(output_location, 'w', encoding='utf-8') as fp:
            fp.write(first_half)

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]


# il = "https://runitback.gg/series/12728?match=25609&round=1&tab=replay"
il = "https://runitback.gg/series/12751?match=25661&round=1&tab=replay"
rb = RIBScrapper()
rb.export_json(il)
