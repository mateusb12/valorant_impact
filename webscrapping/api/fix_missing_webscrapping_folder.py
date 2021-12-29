import sys
from pathlib import Path
import os


def webscrapping_fix():
    current_folder = Path(os.getcwd())
    webscrapping_folder = current_folder.parent
    root_folder = webscrapping_folder.parent
    aux = str(root_folder)
    return str(root_folder)
    # sys.path.append("E:\\Python\\Classification_datascience")


sys.path.append(webscrapping_fix())
