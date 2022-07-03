import time

# Check the run time of a function
import warnings

from impact_score.deprecated.analyse_json import Analyser
from impact_score.json_analyser.pool.analyser_pool import analyser_pool
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper


def get_run_time(func):
    start = time.time()
    result = func()
    end = time.time()
    print(f"{func.__name__} took {end - start} seconds")


def default_analyser_func():
    start = time.time()
    a = Analyser()
    a.set_match(65588)
    a.set_config(round=1)
    res = a.export_df()
    end = time.time()
    # print(f"Default analyser took {end - start} seconds")
    return end - start


def refactored_analyser_func():
    start = time.time()
    a = analyser_pool.acquire()
    a.set_match(65588)
    aw = AnalyserWrapper(a)
    res = aw.export_df()
    end = time.time()
    # print(f"Refactored analyser took {end - start} seconds")
    return end - start


def __main():
    warnings.filterwarnings('ignore')
    default_pot = []
    refactored_pot = []
    for i in range(100):
        default_pot.append(default_analyser_func())
        refactored_pot.append(refactored_analyser_func())
        print(i)
    print(f"Default analyser average time: {sum(default_pot) / len(default_pot)}")
    print(f"Refactored analyser average time: {sum(refactored_pot) / len(refactored_pot)}")


if __name__ == "__main__":
    __main()
