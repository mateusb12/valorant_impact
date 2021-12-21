import os
from typing import List

import pandas as pd
from termcolor import colored

from webscrapping.database.sql_populator import ValorantPopulator
from webscrapping.wrapper.csv_manager import CsvCreator, CsvSplitter
from webscrapping.wrapper.scrap_matches import download_run


class ValorantScrapper:
    def __init__(self, filename: str):
        self.filename = filename
        self.suffix = filename.split(".")[0]
        self.match_list = self.get_match_list()

    def start_scrapping_pipeline(self):
        self.create_links()
        self.split_links()
        self.download_links()
        self.populate_sql()
        print(colored("Pipeline finished", "magenta"))

    def half_pipeline(self, split_size: int):
        self.create_links()
        self.split_links_with_size(split_size)

    def manually_download_parts(self, part_letter: str):
        full_name = f"{self.suffix}_links"
        print(colored(f"Download {part_letter} part...", "cyan"))
        download_run(full_name, part_letter)

    @staticmethod
    def navigate_to_events_folder():
        current_path = os.getcwd()
        current_folder = current_path.split("\\")[-1]
        if current_folder == "database":
            os.chdir("..\\matches\\events")

    def get_match_list(self) -> List[int]:
        self.navigate_to_events_folder()
        match_pd = pd.read_csv(self.filename)
        return list(match_pd["Match Id"])

    def create_links(self):
        print(colored("Creating links...", "cyan"))
        ccr = CsvCreator(self.filename)
        ccr.generate_link_table()
        print(colored('Links created!', 'green'))

    def split_links(self):
        print(colored("Splitting links...", "cyan"))
        ccp = CsvSplitter(f"{self.suffix}_links.csv", file_amount=2)
        ccp.split()
        print(colored('Links split!', 'green'))

    def split_links_with_size(self, size: int):
        print(colored("Splitting links...", "cyan"))
        ccp = CsvSplitter(f"{self.suffix}_links.csv", file_amount=size)
        ccp.split()
        print(colored('Links split!', 'green'))

    def download_links(self):
        full_name = f"{self.suffix}_links"
        print(colored("Download A part...", "cyan"))
        download_run(full_name, "a")
        print(colored("A part downloaded!", "green"))
        print(colored("Download B part...", "cyan"))
        download_run(full_name, "b")
        print(colored("B part downloaded!", "green"))

    def populate_sql(self):
        print(colored("Populating SQL", "cyan"))
        vp = ValorantPopulator(match_list=self.match_list)
        vp.populate(rebuild=False)
        print(colored("SQL Populated!", "green"))


if __name__ == "__main__":
    vs = ValorantScrapper("vct_matches.csv")
    vs.manually_download_parts("n")
