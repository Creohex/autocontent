from __future__ import annotations
from __future__ import unicode_literals

import json
import re
import uuid
from abc import ABC, abstractmethod, abstractclassmethod
from pathlib import Path
from pprint import pprint as pp
from urllib3.util import parse_url

import moviepy.editor
import pytube
import youtube_dl
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pytube import exceptions as pytube_exc, YouTube
from pytube.cli import on_progress
from yt_dlp import YoutubeDL as ytdlp

from . import utils


DEBUG = False
"""Debug flag."""

VIDEO_URL_BASE = "https://youtu.be/"
"""YouTube base URL."""

VIDEO_ID_PATTERN = r"[0-9A-Za-z_-]{11}"
"""YouTube video ID regex pattern."""

FMT_MHTML = "mhtml"
FMT_3GPP = "3gpp"
FMT_WEBM = "webm"
FMT_MP4 = "mp4"
FORMATS_VID = [FMT_MP4, FMT_MHTML, FMT_3GPP, FMT_WEBM]
"""Video formats."""

RESOLUTION_144 = "144p"
RESOLUTION_240 = "240p"
RESOLUTION_360 = "360p"
RESOLUTION_480 = "480p"
RESOLUTION_720 = "720p"
RESOLUTION_1080 = "1080p"
RESOLUTIONS = [
    RESOLUTION_144,
    RESOLUTION_240,
    RESOLUTION_360,
    RESOLUTION_480,
    RESOLUTION_720,
    RESOLUTION_1080,
]
RESOLUTION_MAP = {r: i for i, r in enumerate(RESOLUTIONS)}
"""Video resolutions."""

AUDIO_CODEC_MP4 = "mp4a.40.2"
AUDIO_CODEC_OPUS = "opus"
AUDIO_CODECS = [AUDIO_CODEC_MP4, AUDIO_CODEC_OPUS]
"""Audio codecs."""

MIME_TYPE_3GPP = "video/" + FMT_3GPP
MIME_TYPE_WEBM = "video/" + FMT_WEBM
MIME_TYPE_MP4 = "video/" + FMT_MP4
MIME_TYPES = [MIME_TYPE_3GPP, MIME_TYPE_WEBM, MIME_TYPE_MP4]
"""Video MIME types."""

DEFAULT_DIR = utils.ROOT_DIR / "sources/"
"""Default directory for video file management."""


class VideoImporter(ABC):
    """Youtube video importer base class."""

    @property
    def success(self):
        return self.filepath is not None

    def __init__(self, video_id=None, url=None) -> None:
        if not bool(video_id) ^ bool(url):
            raise Exception("Either video_id or url must be provided")

        self._downloader = None

        self.video_id = Video.validate_video_id(
            video_id or Video.url_to_video_id(video_id)
        )
        self.url = Video.video_id_to_url(self.video_id)
        self.filepath = None

    def default_filepath(self, fmt=FMT_MP4):
        """Generate default filepath for the video."""

        return DEFAULT_DIR / f"{self.video_id}.{fmt}"

    @abstractmethod
    def download(self):
        raise NotImplementedError()


class PytubeImporter(VideoImporter):
    """Youtube video importer via pytube."""

    def download(
        self,
        max_resolution: str | None = RESOLUTION_360,
        mime_type: str | None = MIME_TYPE_MP4,
        exact_resolution: bool | None = True,
        output_file: Path | str | None = None,
        force: bool | None = False,
    ) -> str:
        if mime_type not in MIME_TYPES:
            raise Exception(f"Invalid mime_type: {mime_type}")

        try:
            vid = YouTube(self.url, on_progress_callback=on_progress)
        # except pytube_exc as exc1:
        # raise Exception(f"Invalid video link: {url} ({str(exc1)})")
        except pytube_exc.PytubeError as exc2:
            raise Exception(f"Failed to load video ({str(exc2)})")

        # FIXME: for resolutions >360p we must manually merge audio and video streams
        if RESOLUTION_MAP[max_resolution] > RESOLUTION_MAP[RESOLUTION_360]:
            raise Exception(
                "Audio for resolutions higher than 360p is not currently supported"
            )

        # streams = sorted(
        streams = [
            stream
            for stream in vid.streams
            if stream.resolution == max_resolution
            and stream.audio_codec == AUDIO_CODEC_MP4
            and stream.mime_type == mime_type
            and stream.type == "video"
            # and stream.is_progressive
        ]
        # key=lambda s: -bool(s.is_progressive),
        # )

        if not len(streams):
            if exact_resolution:
                raise Exception("Video streams with specified parameters not found")
            # TODO: retry lower quality streams (exact_resolution = False)

        self.filepath = (
            Path(output_file).absolute() if output_file else self.default_filepath()
        )
        utils.check_existing_file(self.filepath, force=force)
        utils.ensure_folder(self.filepath)
        streams[0].download(output_path=str(DEFAULT_DIR), filename=str(self.filepath))


class YoutubeDlImporter(VideoImporter):
    """Youtube video importer via youtube-dl."""

    def download(
        self,
        max_resolution: str | None = RESOLUTION_360,
        mime_type: str | None = MIME_TYPE_MP4,
        exact_resolution: bool | None = True,
        output_file: Path | str | None = None,
        force: bool | None = False,
    ):
        def my_hook(d):
            if d["status"] == "finished":
                print("Done downloading, now converting ...")

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "progress_hooks": [my_hook],
        }
        print(">>> ", self.url)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])


class YtDlpImporter(VideoImporter):
    """Youtube cideo importer via yt-dlp"""

    @staticmethod
    def construct_options(
        format_id: str,
        name: str | None = None,
    ) -> dict:
        """Prepares options dictionary for ytdlp context."""

        # TODO: parametrize destination folder path as well?
        return {
            "format": format_id,
            "outtmpl": str(
                DEFAULT_DIR / f"{(Path(name).stem if name else '%(id)s')}.%(ext)s"
            ),
            "noplaylist": True,
        }

    def extract_info(self):
        """Fetches information JSON for video."""

        with ytdlp() as ydl:
            return ydl.extract_info(self.url, download=False)

    def appropriate_format(self):
        """..."""

        # TODO: parametrize video params
        # TODO: implement video/audio merge for higher-resolution streams

        info = self.extract_info()
        resolutions = ["640x360", "426x240"]
        exts = [FMT_MP4, FMT_WEBM]
        with_audio = True
        format_ids = []

        for f in info["formats"]:
            if (
                f["resolution"] in resolutions
                and f["ext"] in exts
                and (
                    ("audio_channels" in f and f["audio_channels"] != "none")
                    if with_audio
                    else True
                )
                and f["acodec"] == AUDIO_CODEC_MP4
                and re.match(r"^\d+$", f["format_id"])
            ):
                pp(f"Found appropriate format ID: {f['format']}")
                format_ids.append(f["format_id"])

                if DEBUG:
                    with open(f"./sources/{f['format_id']}.json", "w") as fil:
                        json.dump(f, fil)

        if not len(format_ids):
            raise Exception("No appropriate formats found to download")

        return sorted(format_ids, key=lambda f: -int(f))[0]

    def download(self):
        options = self.construct_options(self.appropriate_format())

        with ytdlp(options) as ydl:
            ydl.download(self.url)

        # FIXME: derive video filepath from ydl obj?
        return DEFAULT_DIR / f"{self.video_id}.{FMT_MP4}"
