import pandas as pd
import os

# read DataFrame
os.chdir("..\\matches\\events")
data = pd.read_csv("na_links.csv")


class CsvSplitter:
    def __init__(self, filename: str, **kwargs):
        self.filename = filename.split(".")[0]
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
            df = data[size * i:size * (i + 1)]
            export = "{}_{}.csv".format(self.filename, letter)
            df.to_csv(export, index=False)
            self.files.append(export)

    def cleanup(self):
        for file in os.listdir():
            if self.filename in file and file != "{}.csv".format(self.filename):
                os.remove(file)


cp = CsvSplitter("na_links.csv", file_amount=3)
cp.cleanup()
# cp.split()
# cp.cleanup()
# cp.cleanup()