import threading
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup

from webscrapping.series_scrap import RIBScrapper

RESPONSE = {}
lock = threading.Lock()


class Scraper(threading.Thread):
    def __init__(self, input_df: pd.DataFrame, tag: str):
        threading.Thread.__init__(self)
        self.match_db = input_df
        self.browser = webdriver.Chrome()
        self.name = tag
        self.visited_ids = []

    def quit(self):
        self.browser.quit()

    def run(self):
        self.download_self_links()

    def show_visited_ids(self):
        print("[{}] visited {}".format(self.name, self.visited_ids))

    def download_self_links(self):
        for link in self.match_db.iterrows():
            match_link = link[1]["match_link"]
            self.export_single_link_using_selenium(match_link)
        self.quit()
        print("[{}] done!".format(self.name))

    def export_single_link_using_selenium(self, input_link: str):
        current_driver = self.browser
        lock.acquire()
        current_driver.get(input_link)
        html = self.browser.page_source
        lock.release()
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.findAll('script')
        content_filter = [i for i in scripts if len(i.attrs) == 0]
        match_tag = content_filter[1]
        match_script = match_tag.contents[0].string
        script = match_script[:match_script.find("?{}:")]
        output_index = self.scrap_match_link(input_link)
        print("Downloaded {}.json using {}".format(output_index, self.name))
        self.visited_ids.append(output_index)

        with open("matches/json/{}.json".format(output_index), "w", encoding='utf-8') as f:
            f.write(script)

    @staticmethod
    def scrap_match_link(link: str) -> str:
        return link.split("/")[-1].split("?")[-1].split("&")[0].split("=")[-1]


if __name__ == "__main__":
    urls = ["https://google.com", "https://stackoverflow.com", "https://yahoo.com", "https://msn.com"]
    # threads = []

    rbs = RIBScrapper()
    link_file = "na_links.csv"
    rbs.fix_current_folder()
    match_db = pd.read_csv("matches/events/{}".format(link_file))

# class LinkScrapper:
#     def __init__(self, input_db: pd.DataFrame):
#         self.link_db = input_db
#         print("Instantiated a data frame of length {}".format(len(self.link_db)))
#         self.thread_amount = 0
#
#     def reduce_size(self, amount: int):
#         self.link_db = self.link_db.head(amount)
#         print("Reduced data frame to length {}".format(len(self.link_db)))
#
#     def multi_thread_download(self, thread_amount: int):
#         split_db = [self.link_db[i::thread_amount] for i in range(thread_amount)]
#         thread_list = []
#
#         for i in range(thread_amount):
#             new_t = Scraper(split_db[i], "Thread-{}".format(i + 1))
#             thread_list.append(new_t)
#
#         for thread in thread_list:
#             thread.start()
#
#         for item in thread_list:
#             item.join()
#
#         for show in thread_list:
#             show.show_visited_ids()
#
#
# ls = LinkScrapper(match_db)
# ls.reduce_size(40)
# ls.multi_thread_download(4)

# Get the first 20 elements of match_db
# match_db = match_db.head(20)
#
# split_amount = 4
# # Split match_db into 4 parts
# split_db = [match_db[i::split_amount] for i in range(split_amount)]
#
# print("Creating scrapper!")
# # noinspection PyTypeChecker
# t1 = Scraper(split_db[0], "Thread-1")
# t2 = Scraper(split_db[3], "Thread-2")
# t1.start()
# t2.start()

# Create threads and give them piece of work each
# t1 = Scraper(1, urls[:2])
# t2 = Scraper(2, urls[2:])
#
# # Start new Threads
# t1.start()
# t2.start()
#
# # Add threads to thread list
# threads.append(t1)
# threads.append(t2)
#
# # Wait for all threads to complete
# for t in threads:
#     t.join()
#
# print(RESPONSE)
# print("Scraping done")
