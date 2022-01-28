import pandas as pd
import os

from termcolor import colored

from impact_score.json_analyser.analyse_json import Analyser
from webscrapping.wrapper.folder_fixer import fix_current_folder


# read DataFrame
# os.chdir("..\\matches\\events")
# data = pd.read_csv("na_links.csv")


class CsvCreator:
    def __init__(self, filename: str):
        self.filename = filename

    def generate_link_table(self) -> str:
        """
        Get a RIB .csv file and convert it to a list of match links.
        You should get that RIB file from the RIB bot discord.
        :return: generate a CSV file containing all matches links
        """
        event_id = self.filename.split('.')[0]
        print("Reading file [{}.csv] from [matches/events/{}.csv]".format(event_id, event_id))
        fix_current_folder()
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


class CsvSplitter:
    def __init__(self, filename: str, **kwargs):
        self.filename = filename.split(".")[0]
        os.chdir("matches\\events")
        self.data = pd.read_csv(filename)
        self.k = kwargs["file_amount"]
        self.size = len(self.data) // self.k
        self.files = []

    @staticmethod
    def convert_to_letter(number: int) -> str:
        return chr(number + 96)

    def split(self):
        """
        Split the CSV file into multiple smaller files.
        :return: Small csv files ordered alphabetically.
        """
        k = self.k
        size = self.size

        for i in range(k):
            index = i + 1
            letter = self.convert_to_letter(index)
            df = self.data[size * i:size * (i + 1)]
            export = "{}_{}.csv".format(self.filename, letter)
            df.to_csv(export, index=False)
            self.files.append(export)

    def cleanup(self):
        """
        Delete all CSV files except the last one.
        """
        for file in os.listdir():
            if self.filename in file and file != "{}.csv".format(self.filename):
                os.remove(file)


class CsvMerger:
    def __init__(self, output_name: str, **kwargs):
        self.output_name = output_name
        self.delete_jsons = kwargs["delete_jsons"]

    def merge(self):
        """
        Merge all csv files into one.
        """
        self.merge_all_csv(self.output_name)
        if self.delete_jsons:
            self.delete_jsons()

    @staticmethod
    def merge_all_csv(csv_name: str):
        file_list = os.listdir('../matches/json')
        match_list = [int(x[:-5]) for x in file_list]
        size = len(match_list)

        df_list = []
        error_list = []

        for index, i in enumerate(match_list):
            completion = round(index / size * 100, 2)
            print(f"{index}/{size} ({completion}%)")
            a = Analyser("{}.json".format(i))
            try:
                df_list.append(a.export_df(i))
            except KeyError:
                error_list.append(i)

        print("Append done")
        print(os.getcwd())
        merged = pd.concat(df_list)
        merged.to_csv(r'{}\matches\rounds\{}'.format(os.getcwd(), csv_name), index=False)
        print(colored(f'Error in {df_list}', 'red'))

    @staticmethod
    def delete_jsons():
        os.chdir("matches/json")
        print(os.getcwd())
        all_files = os.listdir()
        for file in all_files:
            print("Removing {}".format(file))
            os.remove(file)


class CsvConverter:
    def __init__(self):
        pass

    @staticmethod
    def get_current_folder():
        return os.getcwd().split("\\")[-1]

    def go_to_json_folder(self):
        current_folder = self.get_current_folder()
        if current_folder == "wrapper":
            os.chdir("..\\matches\\json")
        elif current_folder == "exports":
            os.chdir("..\\json")
        elif current_folder == "webscrapping":
            os.chdir("matches\\json")

    def go_to_csv_folder(self):
        current_folder = self.get_current_folder()
        if current_folder == "wrapper":
            os.chdir("..\\matches\\exports")
        elif current_folder == "json":
            os.chdir("..\\exports")
        elif current_folder == "webscrapping":
            os.chdir("matches\\exports")

    def get_json_list(self):
        self.go_to_json_folder()
        all_jsons = [i.split(".")[0] for i in os.listdir()]
        self.go_to_csv_folder()
        all_csvs = [i.split(".")[0] for i in os.listdir()]
        not_downloaded = [i for i in all_jsons if i not in all_csvs]
        os.chdir("..\\..\\wrapper")
        for index, item in enumerate(not_downloaded):
            a = Analyser("{}.json".format(item))
            print(f"Loading {item}.json. Series: {a.series_id}"
                  f" Progress: {index}/{len(not_downloaded)} %: {(index/len(not_downloaded))*100}")
            new_match_frame = a.export_df(int(item))
            self.go_to_csv_folder()
            new_match_frame.to_csv(r'{}.csv'.format(item), index=False)
        # print(not_downloaded)


if __name__ == "__main__":
    ccv = CsvConverter()
    cm = CsvMerger("vct_merged.csv", delete_jsons=False)
    cm.merge()
    # ccv.get_json_list()

    # cc = CsvCreator("na.csv")
    # cc.generate_link_table()
    #
    # cp = CsvSplitter("na_links.csv", file_amount=15)
    # cp.split()

    # cm = CsvMerger("na_merged.csv", delete_jsons=False)
    # cm.merge()
