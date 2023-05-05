#!pytest -s

import pytest
from pathlib import Path

from .. import exceptions
from .. import utils
from ..video import FMT_MP4


TEST_DIR = utils.ROOT_DIR / "test_videos"
"""Default directory for test entities."""

TEST_ENTITY_ID = "EngW7tLk6R8"
"""Test entity ID (video)."""


@pytest.mark.parametrize(
    ("time_string", "expected"),
    [
        (0, 0.0),
        (0.0, 0.0),
        (123, 123.0),
        (0.012321312, 0.012321312),
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


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        # empty:
        (None, TEST_DIR / f"{TEST_ENTITY_ID}.{FMT_MP4}"),
        ("", TEST_DIR / f"{TEST_ENTITY_ID}.{FMT_MP4}"),
        # home:
        ("~", utils.HOME_DIR / f"{TEST_ENTITY_ID}.mp4"),
        ("~/", utils.HOME_DIR / f"{TEST_ENTITY_ID}.mp4"),
        ("~/bla", utils.HOME_DIR / f"bla.mp4"),
        ("~/bla.mp4", utils.HOME_DIR / f"bla.mp4"),
        # relative:  # FIXME: depends on run dir..
        (".", utils.ROOT_DIR / f"{TEST_ENTITY_ID}.mp4"),
        ("./", utils.ROOT_DIR / f"{TEST_ENTITY_ID}.mp4"),
        ("./bla", utils.ROOT_DIR / f"bla.mp4"),
        ("bla.webm", utils.ROOT_DIR / "bla.webm"),
        # invalid:
        ("/", exceptions.InvalidFilePath),
        ("/gibberish", exceptions.InvalidFilePath),
        ("/gibberish/gibberish/bla.mp4", exceptions.InvalidFilePath),
        (utils.HOME_DIR.parent / "bla.mp4", exceptions.InvalidFilePath),
        # ("bla.xxx", exceptions.InvalidFileName),  # TODO: decide on limitations
        # (".x", exceptions.InvalidFileName),
        # ("bla.x", exceptions.InvalidFileName),
    ],
)
def test_importer_derive_filepath(path, expected):
    if isinstance(expected, type):
        with pytest.raises(expected):
            utils.derive_filepath(
                path,
                TEST_ENTITY_ID,
                FMT_MP4,
                TEST_DIR / f"{TEST_ENTITY_ID}.{FMT_MP4}",
                False,
            )
    else:
        assert utils.derive_filepath(
            path,
            TEST_ENTITY_ID,
            FMT_MP4,
            TEST_DIR / f"{TEST_ENTITY_ID}.{FMT_MP4}",
            False,
        ) == expected
