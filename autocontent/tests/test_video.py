#!pytest -s

from __future__ import annotations

import json
import pytest
from pathlib import Path

from .. import exceptions, utils, video
from ..video import Video, YtDlpImporter


video.DEFAULT_DIR = utils.ROOT_DIR / "test_videos/"
"""Override default directgitory for video files for isolation purposes."""

TEST_VIDEO_ID = "EngW7tLk6R8"  # 5-second
TEST_VIDEO_ID_LONG = "0nTEfx44pws"  # 15-minute
"""Small youtube video ID perfect for use in tests."""


# --- Tooling: ---
@pytest.fixture()
def vid() -> VideoMock:
    """Video mock obj fixture."""

    return VideoMock(TEST_VIDEO_ID)


@pytest.fixture()
def use_dir():
    """Fixture that manages temporary directory."""

    prepare()
    print()
    yield True
    cleanup()


@pytest.fixture()
def debug_json_opts():
    return {
        "writeinfojson": True,
    }


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
    """
    Video mock class, with altered initialization and
    additional helper methods for testing purposes.
    """

    def __init__(self, video_id):
        self.video_id = video_id

    def info_json(self):
        if not self.filepath:
            raise Exception("File hasn't been downloaded yet!")
        fp = Path(self.filepath)
        info_json_path = fp.parent / f"{fp.name.split('.')[0]}.info.json"

        with open(info_json_path, "r") as f:
            info_json = json.loads(f.read())

        return info_json


# TODO: audio-only case
# --- Cases: ---
def test_download_video(use_dir):
    v = VideoMock(video_id=TEST_VIDEO_ID)
    v.download_video()

    info = v.info_json()
    assert isinstance(v.filepath, Path)
    assert TEST_VIDEO_ID in v.filepath
    assert v.filepath.is_file()
    assert v.filepath.suffix.split(".")[-1] == YtDlpImporter.DEFAULT_FORMAT
    assert info["ext"] == YtDlpImporter.DEFAULT_FORMAT
    assert info["height"] == YtDlpImporter.DEFAULT_RES_HEIGHT
    assert info["acodec"] == video.AUDIO_CODEC_MP4A


@pytest.mark.parametrize(
    ("invalid_video_id", "max_resolution", "expected"),
    [
        ("", None, Exception),
        ("gibberish", None, Exception),
        (123, None, TypeError),
        ("0" * 11, None, exceptions.VideoUnavailable),
        (TEST_VIDEO_ID, "145p", Exception),
    ],
)
def test_download_video_negative(use_dir, invalid_video_id, max_resolution, expected):
    with pytest.raises(expected):
        vid = VideoMock(video_id=invalid_video_id)
        vid.download_video(max_resolution=max_resolution)


@pytest.mark.parametrize(
    ("max_resolution", "mime_type", "exact_resolution", "output_file"),
    [
        (video.RESOLUTION_144, None, False, video.DEFAULT_DIR / "specific.mp4"),
        (video.RESOLUTION_144, None, False, None),
        # (video.RESOLUTION_360, video.MIME_TYPE_WEBM, False, None),
        (video.RESOLUTION_240, None, True, None),
    ],
)
def test_download_video_combinations(
    use_dir,
    debug_json_opts,
    max_resolution,
    mime_type,
    exact_resolution,
    output_file,
):
    """Test video download parameter compliance."""

    vid = VideoMock(video_id=TEST_VIDEO_ID)
    vid.download_video(
        max_resolution=max_resolution,
        mime_type=mime_type,
        exact_resolution=exact_resolution,
        output_file=output_file,
        force=False,
        additional_options=debug_json_opts,
    )

    info = vid.info_json()

    assert vid.video_id == info["id"]
    assert Path(vid.filepath).is_file()
    assert info["acodec"] == video.AUDIO_CODEC_MP4A
    assert info["ext"] == YtDlpImporter.mime_type_to_format(
        mime_type or video.MIME_TYPE_MP4
    )
    assert info["height"] == YtDlpImporter.resolution_to_height(max_resolution)

    if output_file:
        assert vid.filepath == output_file


def test_download_audio(use_dir, debug_json_opts):
    vid = VideoMock(TEST_VIDEO_ID_LONG)
    vid.download_audio(additional_options=debug_json_opts)
    info = vid.info_json()

    assert vid.filepath.is_file()
    assert info["id"] == TEST_VIDEO_ID
    assert info["vcodec"] == "none"
    assert info["acodec"] == video.AUDIO_CODEC_MP4A
    assert bool(info["audio_channels"])
