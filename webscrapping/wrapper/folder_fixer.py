import os


def fix_current_folder():
    path = os.getcwd()
    print(path)
    folder = path.split("\\")[-1]
    if folder in ("wrapper", "matches"):
        path_parent = os.path.dirname(os.getcwd())
        os.chdir(path_parent)
        new_path = os.getcwd()
        current_path = new_path

