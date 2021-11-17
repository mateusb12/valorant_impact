import pandas as pd
import os
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
        os.chdir("..\\matches\\events")
        self.data = pd.read_csv(filename)
        self.k = kwargs["file_amount"]
        self.size = len(self.data) // self.k
        self.files = []

    @staticmethod
    def convert_to_letter(number: int) -> str:
        return chr(number + 96)

    def split(self):
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
        for file in os.listdir():
            if self.filename in file and file != "{}.csv".format(self.filename):
                os.remove(file)


if __name__ == "__main__":
    # cc = CsvCreator("na.csv")
    # cc.generate_link_table()

    cp = CsvSplitter("na_links.csv", file_amount=20)
    cp.split()
