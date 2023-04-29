#!pytest -s

from __future__ import annotations

import functools
import pytest
from mock import MagicMock, patch
from pathlib import Path

from .. import exceptions, utils, video
from ..video import Video


video.DEFAULT_DIR = utils.ROOT_DIR / "test_videos/"
"""Override default directgitory for video files for isolation purposes."""

TEST_VIDEO_ID = "EngW7tLk6R8"
"""Small youtube video ID perfect for use in tests."""

# TODO: extensive tests with parameters, alternative naming, etc:
#       simple test
#       different parameter combinations
#       audio only
#       high res (audio merge)


# --- Tooling: ---
@pytest.fixture()
def use_dir():
    """Fixture that manages temporary directory."""

    prepare()
    print()
    yield True
    cleanup()


def cleanup():
    """Delete temp files in (updated) video.DEFAULT_DIR."""

    files = [f for f in video.DEFAULT_DIR.glob("*") if f.is_file]
    if not files:
        return

    if utils.DEBUG:
        files_str = "\t\n".join(map(str, files))
        print(f"found files:\n{files_str}")
        if not utils.dialog_confirm(message="Delete mentioned files?"):
            return

    for f in files:
        f.unlink()


def prepare():
    """Preparations for test cases that use local directory to store files and such."""

    cleanup()
    utils.ensure_folder(video.DEFAULT_DIR)


class VideoMock(Video):
    def __init__(self, video_id):
        self.video_id = video_id


# --- Cases: ---
def test_download_video(use_dir):
    vid = Video(video_id=TEST_VIDEO_ID)
    # TODO: assertions...


@pytest.mark.parametrize(
    ("invalid_video_id", "expected"),
    [
        ("", Exception),
        ("gibberish", Exception),
        (123, TypeError),
        ("0" * 11, exceptions.VideoUnavailable),
    ],
)
def test_download_video_negative(invalid_video_id, expected):
    with pytest.raises(expected):
        Video(video_id=invalid_video_id)


@pytest.mark.parametrize(
    ("max_resolution", "mime_type", "exact_resolution", "output_file"),
    [
        # (None, None, None, None),
        (None, None, None, video.DEFAULT_DIR / "specific.mp4"),
        (video.RESOLUTION_144, None, False, video.DEFAULT_DIR / "specific.mp4"),
    ],
)
def test_download_video_combinations(
    use_dir, max_resolution, mime_type, exact_resolution, output_file
):
    # TODO: pass 'writeinfojson', load it and make assertions against args
    # other options: quiet,
    vid = VideoMock(video_id=TEST_VIDEO_ID)
    vid.download_video(
        max_resolution=max_resolution,
        mime_type=mime_type,
        exact_resolution=exact_resolution,
        output_file=output_file,
    )

    # asserts..
    assert vid.filepath == output_file
    assert Path(vid.filepath).is_file()
    # import pdb; pdb.set_trace()
