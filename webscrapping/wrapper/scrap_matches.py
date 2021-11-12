from webscrapping.series_scrap import RIBScrapper
import os


class MatchScrapper:
    def __init__(self, filename: str):
        self.rbs = RIBScrapper()
        os.chdir("../")
        csv_link = self.rbs.generate_links(filename)
        print("File [{}] generated!".format(csv_link))
        self.rbs.download_links(csv_link)

    def get_matches(self):
        pass


ms = MatchScrapper("br.csv")
