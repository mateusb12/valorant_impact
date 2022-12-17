import pandas as pd
import pytest

from impact_score.json_analyser.wrap.analyser_wrapper import get_match_df


def compare_floats(float_a: float, float_b: float):
    return abs(float_a - float_b) < 0.00001


def compare_dfs(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    a_dict = a.to_dict("records")
    b_dict = b.to_dict("records")
    for a_output, b_output in zip(a_dict, b_dict):
        if len(a_output) != len(b_output):
            return False
        for a_pair, b_pair in zip(a_output.items(), b_output.items()):
            a_value = a_pair[1]
            b_value = b_pair[1]
            test = False
            if isinstance(a_value, float):
                test = compare_floats(a_value, b_value)
            elif isinstance(a_value, (str, int)):
                test = a_value == b_value
            if test is False:
                key = a_pair[0]
                print(f"key = {key}")
                return False
    return True


def test_wrapper():
    test_df = pd.read_csv("test.csv")
    cols = test_df.columns.values
    wrapper_df = get_match_df(89765)
    trimmed_wrapper_df = wrapper_df[cols]
    comparison = compare_dfs(test_df, trimmed_wrapper_df)
    assert comparison is True


if __name__ == '__main__':
    pytest.main()
