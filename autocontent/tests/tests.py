import pytest

from .. import utils


@pytest.mark.parametrize(
    ("time_string", "expected"),
    [
        ("0", 0.0),
        ("0.0", 0.0),
        ("0.1", 0.1),
        ("007.07", 7.07),
        ("123.55", 123.55),
        ("00:00", 0.0),
        ("00:01", 1.0),
        ("00:00:00", 0.0),
        ("00:00:01", 1.0),
        ("99:99:99", 362439.0),
    ],
)
def test_parse_time_input(time_string, expected):
    assert utils.parse_time_input(time_string) == expected


@pytest.mark.parametrize(
    "time_string",
    ["", "gibberish", "123.123", "1.1.1", "0.999", "00:" "00:00:00:00"],
)
def test_parse_time_input_negative(time_string):
    with pytest.raises(Exception):
        utils.parse_time_input(time_string)
