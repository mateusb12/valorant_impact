from typing import List

import pandas as pd


def export_vct_events() -> str:
    df_events = pd.read_csv('all_events.csv')
    vct_events = df_events[df_events['Name'].str.contains('VCT')][~df_events['Name'].str.contains('Game Changers')]
    vct_event_int = vct_events["Id"].tolist()
    empty_string = "".join(f"{str(event)} " for event in vct_event_int)
    return f"!rib matches -e {empty_string} -csv"


if __name__ == '__main__':
    vct = export_vct_events()
    print(vct)

