from random import sample

from termcolor import colored

from webscrapping.database.sql_queries import ValorantQueries


class ValorantLBGM:
    def __init__(self):
        self.vq = ValorantQueries()
        self.match_list = self.vq.query_match_db()
        self.dataset_index = []
        self.dataset_list = []

    def create_dataset(self, size: int):
        self.set_random_sample(size)
        for index, match_index in enumerate(self.dataset_index):
            print(colored(f'{index}/{len(self.dataset_index)}', 'magenta'))
            match_df = self.vq.export_df(match_index)
            self.dataset_list.append(match_df)

    def get_random_sample(self, amount: int):
        return sample(self.match_list, amount)

    def set_random_sample(self, amount):
        self.dataset_index = self.get_random_sample(amount)


if __name__ == "__main__":
    vm = ValorantLBGM()
    vm.create_dataset(1000)
