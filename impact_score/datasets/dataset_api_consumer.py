import requests


def _generate_dataset_api_link():
    return "https://backend-dev.rib.gg/v1/matches/ml-ids"


class ValorantDatasetConsumer:
    def __init__(self):
        self.api_link = _generate_dataset_api_link()

    def call_api(self):
        input_json = {"includedEventWords": ["vct", "challengers"],
                      "excludedEventWords": ["open", "qualifiers"],
                      "limit": 2000}

        response = requests.post(self.api_link, data=input_json)
        return response.json()

    def convert_api_call_into_list(self):
        api_call = self.call_api()
        matches = api_call["matches"]
        return [match["id"] for match in matches]

    def export_id_list(self):
        id_list = self.convert_api_call_into_list()
        with open("dataset_matches.csv", "w") as f:
            for match_id in id_list:
                f.write(str(match_id) + "\n")


if __name__ == "__main__":
    consumer = ValorantDatasetConsumer()
    consumer.export_id_list()
