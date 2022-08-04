import datetime

from termcolor import colored


def convert_seconds_to_time(seconds: int) -> str:
    raw = str(datetime.timedelta(seconds=seconds)).split(".")[0]
    raw_list = raw.split(":")
    return f"{raw_list[0]}h {raw_list[1]}m {raw_list[2]}s"


def print_progress_bar(iteration: int, total: int, prefix='', suffix='', decimals: int = 1, length: int = 100,
                       fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    return fill * filledLength + '-' * (length - filledLength)
    # full_string = f'\r{prefix} |{bar}| {percent}% {suffix}'
    # print(colored(full_string, "yellow"), end=print_end)
    # # Print New Line on Complete
    # if iteration == total:
    #     print()


def time_metrics(**kwargs):
    a = "->"
    start = kwargs["start"]
    end = kwargs["end"]
    current_index = kwargs["index"]
    size = kwargs["size"]
    element_name = kwargs["tag"]
    current_element = kwargs["element"]
    elapsed = end - start
    round_elapsed = datetime.timedelta(seconds=elapsed).seconds
    round_elapsed = convert_seconds_to_time(round_elapsed)
    time_per_element = elapsed / current_index if current_index != 0 else 0
    remaining_elements = size - current_index
    remaining_seconds = round(time_per_element * remaining_elements, 2)
    remaining_minutes = str(datetime.timedelta(seconds=remaining_seconds)).split(".")[0]
    progress = f"{current_index}/{size}"
    ratio = f"{round((current_index / size) * 100, 2)}%"
    progress_str = f"Analysing {element_name} #{current_element}, {progress} so far." \
                   f" Ratio {a} [{ratio}]"
    current_time = datetime.datetime.now()
    seconds_added = datetime.timedelta(seconds=remaining_seconds)
    future_date_and_time = current_time + seconds_added
    future_date_and_time_str = future_date_and_time.strftime("%H:%M:%S")
    details_str = f"Elapsed {a} {round_elapsed} | Time per match {a} {round(time_per_element, 2)}s" \
                  f" | Remaining time {a} {remaining_minutes} | ETA {a} {future_date_and_time_str}"
    print(colored(progress_str, "green"))
    print(colored(details_str, "magenta"))
    print(print_progress_bar(current_index, size, prefix='Progress:', suffix='Complete', length=100))
    print("")
