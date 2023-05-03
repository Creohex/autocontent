#!pytest -s

import pytest
from pathlib import Path

from .. import utils
from .. import exceptions


@pytest.mark.parametrize(
    ("time_string", "expected"),
    [
        (0, 0.0),
        (0.0, 0.0),
        (123, 123.0),
        (.012321312, 0.012321312),
        (0x123, 291.0),
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
    assert utils.parse_time_value(time_string) == expected


@pytest.mark.parametrize(
    "time_string",
    ["", "gibberish", "123.123", "1.1.1", "0.999", "00:" "00:00:00:00", "0b123"],
)
def test_parse_time_input_negative(time_string):
    with pytest.raises(Exception):
        utils.parse_time_value(time_string)


@pytest.mark.parametrize(
    ("path", "raises"),
    [
        ("~", None),
        ("~/", None),
        ("~/blabla", None),
        ("~/bla/blabla/bla.txt", None),
        ("/", exceptions.InvalidFilePath),
        ("/bla", exceptions.InvalidFilePath),
        ("/bla.txt", exceptions.InvalidFilePath),
        (utils.HOME_DIR.parent, exceptions.InvalidFilePath),
    ],
)
def test_ensure_inside_home(path, raises):
    if raises:
        with pytest.raises(exceptions.InvalidFilePath):
            utils.ensure_inside_home(path)
    else:
        utils.ensure_inside_home(path)
