from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.webdriver.firefox.webdriver as FirefoxWebDriver

matches = []
match_links = [
    "https://rib.gg/series/19407?match=41359&round=1&tab=round-stats",
    "https://rib.gg/series/19407?match=41358&round=1&tab=round-stats",
    "https://rib.gg/series/19407?match=41357&round=1&tab=round-stats",
    "https://rib.gg/series/19408?match=41364&round=1&tab=round-stats",
    "https://rib.gg/series/19408?match=41363&round=1&tab=round-stats",
    "https://rib.gg/series/19408?match=41362&round=1&tab=round-stats",
    "https://rib.gg/series/19404?match=41347&round=1&tab=round-stats",
    "https://rib.gg/series/19404?match=41346&round=1&tab=round-stats",
    "https://rib.gg/series/18674?match=39944&round=1&tab=round-stats"
]


# class RibScrapper:
#     def __init__(self):
#         self.driver: FirefoxWebDriver = webdriver.Firefox()
#
#     @staticmethod
#     def scrap_match_link(link: str) -> str:
#         return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]
#
#     def save_link_html(self, input_link: str):
#         self.driver.get(input_link)
#         html = self.driver.page_source
#         soup = BeautifulSoup(html, "html.parser")
#         scripts = soup.findAll('script')
#         content_filter = [i for i in scripts if len(i.attrs) == 0]
#         match_tag = content_filter[1]
#         match_script = match_tag.contents[0].string
#         script = match_script[:match_script.find("?{}:")]
#         output_index = self.scrap_match_link(input_link)
#         # trimmed_half = first_half.split("{")
#         # json_txt = trimmed_half[1:]
#
#         with open("../matches/json/{}.json".format(output_index), "w", encoding='utf-8') as f:
#             f.write(script)
#
#     def save_all_links(self):
#         for link in match_links:
#             self.save_link_html(link)
#
#
# rs = RibScrapper()
# rs.save_link_html(match_links[0])
#
