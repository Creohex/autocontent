from __future__ import annotations
from __future__ import unicode_literals

import re
from abc import ABC, abstractmethod, abstractclassmethod
from pathlib import Path

from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip
from pytube import exceptions as pytube_exc, YouTube
from pytube.cli import on_progress
from yt_dlp import YoutubeDL as ytdlp
from yt_dlp.utils import DownloadError

from . import exceptions, utils
from .utils import DEBUG, Spinner


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

AUDIO_CODEC_MP4A = "mp4a.40.2"
AUDIO_CODEC_OPUS = "opus"
AUDIO_CODECS = [AUDIO_CODEC_MP4A, AUDIO_CODEC_OPUS]
"""Audio codecs."""

AUDIO_BITRATE_DEFAULT = 192
"""Default audio bitrate value."""

AUDIO_FMT_MP3 = "mp3"
"""Audio format constants."""

MIME_TYPE_MHTML = "video/" + FMT_MHTML
MIME_TYPE_3GPP = "video/" + FMT_3GPP
MIME_TYPE_WEBM = "video/" + FMT_WEBM
MIME_TYPE_MP4 = "video/" + FMT_MP4
MIME_TYPES = [MIME_TYPE_MHTML, MIME_TYPE_3GPP, MIME_TYPE_WEBM, MIME_TYPE_MP4]
"""Video MIME types."""

MIME_FMT_MAP = {
    MIME_TYPE_MP4: FMT_MP4,
    MIME_TYPE_3GPP: FMT_3GPP,
    MIME_TYPE_WEBM: FMT_WEBM,
    MIME_TYPE_MHTML: FMT_MHTML,
}
FMT_MIME_MAP = {v: k for k, v in MIME_FMT_MAP.items()}
"""MIME type <-> format mappings."""

DEFAULT_DIR = utils.ROOT_DIR / "sources/"
"""Default directory for video file management."""


class VideoImporter(ABC):
    """Youtube video importer base class."""

    DEFAULT_RES_HEIGHT = 360
    DEFAULT_MIME_TYPE = MIME_TYPE_MP4
    DEFAULT_FORMAT = FMT_MP4

    def __init__(self, video_id=None, url=None) -> None:
        if not bool(video_id) ^ bool(url):
            raise Exception("Either video_id or url must be provided")

        self.video_id = Video.validate_video_id(video_id or Video.extract_video_id(url))
        self.url = Video.video_id_to_url(self.video_id)

    def default_filepath(self, fmt=FMT_MP4):
        """Generate default filepath for the video."""

        return DEFAULT_DIR / f"{self.video_id}.{fmt}"

    def validate_filename(self, filename: Path, fmt: str | None = None):
        """Validates/fixes video filename.

        - filename (_type_): suggested video filename
        - fmt (str | None, optional (None)): video format
        """

        fmt = fmt or self.DEFAULT_FORMAT

        return filename

    def derive_filepath(self, path: Path | str | None, fmt: str, force: bool) -> Path:
        """Form absolute resulting filename for video (or audio) file.

        - path (Path | str | None): Path predicate
        - fmt (str): File format
        - force (bool): overwrite existing file
        """

        vpath = (
            (self.default_filepath(fmt) if not path else Path(path))
            .expanduser()
            .absolute()
        )

        if vpath.is_dir():
            vpath = vpath / f"{self.video_id}.{fmt}"
        else:
            suff = vpath.suffix
            if not suff:
                vpath = Path(f"{vpath}.{fmt}")
            elif suff[1:] not in FORMATS_VID:
                raise exceptions.InvalidFileName(msg=f"Invalid format provided: {path}")

        if not re.match(r"^[\d\w\-_]{1,20}\.[\d\w]{2,5}$", vpath.name):
            raise exceptions.InvalidFileName(msg=f"Invalid name for video file: {path}")

        utils.ensure_inside_home(vpath)
        utils.ensure_folder(vpath)
        # FIXME: not needed? 'overwrites' would work better perhaps?
        utils.check_existing_file(vpath, force=force)

        return vpath

    @staticmethod
    def resolution_to_height(res: str) -> int:
        """Transform resolution to video frame height.

        - res (str): resolution in "XXXp" format
        """

        return int(res.strip("p"))

    @staticmethod
    def mime_type_to_format(mime_type: str) -> str:
        """Transform MIME type to video format."""

        if mime_type not in MIME_TYPES:
            raise exceptions.ValidationError(msg=f"Invalid MIME type: {mime_type}")

        return MIME_FMT_MAP[mime_type]

    @staticmethod
    def format_to_mime_type(fmt: str) -> str:
        """Transform video format to MIME type."""

        if fmt not in FORMATS_VID:
            raise exceptions.ValidationError(msg=f"Invalid video format: {fmt}")

        return FMT_MIME_MAP[fmt]

    @abstractmethod
    def download(self):
        raise NotImplementedError()

    @abstractmethod
    def download_audio(self):
        raise NotImplementedError


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
            and stream.audio_codec == AUDIO_CODEC_MP4A
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

    # TODO: download speed appears to be very slow, appears to be better in yt-dlp
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

        # ydl_opts = {
        #     "format": "bestaudio/best",
        #     "postprocessors": [
        #         {
        #             "key": "FFmpegExtractAudio",
        #             "preferredcodec": "mp3",
        #             "preferredquality": "192",
        #         }
        #     ],
        #     "progress_hooks": [my_hook],
        # }
        # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        #     ydl.download([self.url])

        raise NotImplementedError()


class YtDlpImporter(VideoImporter):
    """Youtube cideo importer via yt-dlp"""

    @classmethod
    def construct_options(
        cls,
        height: int,
        exact: bool,
        fmt: str,
        output_file: str,
        additional_options: dict,
    ) -> dict:
        """Prepares options dictionary for ytdlp context.

        - height (int): resolution in horizontal line count
        - exact (bool): attempt to download ^this specific resolution, not closest to it
        - fmt (str): video format
        - output_file (str): output location
        - additional_options (dict): extra YoutubeDL options
        """

        # TODO: add progress hooks

        cmpr = "=" if exact else "<="
        res_str = f"[height{cmpr}{height}]"

        options = {
            "format": f"bestvideo{res_str}+bestaudio/best{res_str}",
            "merge_output_format": fmt or cls.DEFAULT_FORMAT,
            "outtmpl": str(output_file),
            "noplaylist": True,
            "forcejson": False,
            "quiet": True,  # suppress downloading messages
            # "postprocessor_hooks": ... # video postprocessing hooks
            # "overwrites": True,  # handle 'force' here?
            # "simulate": True,  # for testing?
        }
        options.update(additional_options or {})

        return options

    def extract_info(self):
        """Fetches information JSON for video."""

        with ytdlp() as ydl:
            try:
                return ydl.extract_info(self.url, download=False)
            except DownloadError:
                raise exceptions.VideoUnavailable()

    def download_audio(
        self,
        output_file: Path | str | None = None,
        bitrate: int | None = None,
        force: bool | None = None,
        additional_options: dict(str, str) | None = None,
    ):
        bitrate = str(bitrate or AUDIO_BITRATE_DEFAULT)
        force = False if force is None else force

        output_file = self.validate_filename(
            Path(output_file)
            if output_file
            else self.default_filepath(fmt=AUDIO_FMT_MP3),
            fmt=AUDIO_FMT_MP3,
        )
        utils.ensure_folder(output_file)
        utils.check_existing_file(output_file, force=force)

        options = {
            "format": "bestaudio/best",
            "audioformat": AUDIO_FMT_MP3,
            "merge_output_format": AUDIO_FMT_MP3,
            # FIXME: outtmpl: for some reason extension is duplicated otherwise
            "outtmpl": str(output_file.parent / output_file.stem),
            "noplaylist": True,
            "forcejson": False,
            "quiet": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": AUDIO_FMT_MP3,
                    "preferredquality": bitrate,
                }
            ],
            "postprocessor_hooks": [
                Spinner(title_former=lambda x: f"{x['postprocessor']} ({x['status']})")
            ],
        }
        options.update(additional_options or {})

        with ytdlp(options) as ydl:
            try:
                ydl.download(self.url)
            except DownloadError as e:
                raise exceptions.VideoUnavailable(str(e))

        return output_file

    def download(
        self,
        max_resolution: str | None = RESOLUTION_360,
        mime_type: str | None = MIME_TYPE_MP4,
        exact_resolution: bool | None = False,
        output_file: Path | str | None = None,
        force: bool | None = False,
        additional_options: dict(str, str) | None = None,
    ):
        """Download from best video stream according to provided parameters.

        - max_resolution (str | None, optional (RESOLUTION_360)): maximum resolution
        - mime_type (str | None, optional (MIME_TYPE_MP4)): video format
        - exact_resolution (bool | None, optional (False)): aim for specific resolution
        - output_file (Path | str | None, optional (None)): override output location
        - force (bool | None (False)): overwrite flag
        - additional options (dict): extra YoutubeDL options
        """

        mime_type = mime_type or MIME_TYPE_MP4
        fmt = self.mime_type_to_format(mime_type)
        force = False if force is None else force

        options = self.construct_options(
            height=self.resolution_to_height(max_resolution or RESOLUTION_360),
            exact=False if exact_resolution is None else exact_resolution,
            fmt=fmt,
            output_file=self.derive_filepath(output_file, fmt, force),
            additional_options=additional_options or {},
        )

        with ytdlp(options) as ydl:
            try:
                ydl.download(self.url)
            except DownloadError as e:
                raise exceptions.VideoUnavailable(str(e))

        return output_file


class Video:
    """Video model."""

    # TODO: cycle through importers on fail?
    importers = {
        "pytube": PytubeImporter,
        "youtube-dl": YoutubeDlImporter,
        "yt-dlp": YtDlpImporter,
    }
    default_importer = YtDlpImporter

    def __init__(
        self,
        filepath: str = None,
        video_id: str = None,
        url: str = None,
        audio_only: bool | None = None,
        download_kwargs: dict[str, str] | None = None,
    ) -> Video:
        if sum(map(bool, (filepath, video_id, url))) != 1:
            raise Exception("Either filepath, video_id or url must be provided")

        download_kwargs = download_kwargs or {}
        self.filepath = None
        self.video_id = None

        if filepath:
            self.filepath = self.check_video_file(filepath)
            self.video_id = self.extract_video_id(self.filepath)
        else:
            self.video_id = video_id or self.extract_video_id(url)
            if audio_only:
                self.download_audio(**download_kwargs)
            else:
                self.download_video(**download_kwargs)

    def download_video(
        self,
        max_resolution: str | None = RESOLUTION_360,
        mime_type: str | None = MIME_TYPE_MP4,
        exact_resolution: bool | None = False,
        output_file: Path | str | None = None,
        force: bool | None = False,
        additional_options: dict(str, str) | None = None,
    ) -> None:
        """Download video.

        - max_resolution (str | None, optional (RESOLUTION_360)): maximum resolution
            to probe for
        - mime_type (str | None, optional (MIME_TYPE_MP4)): Video format
        - exact_resolution (bool | None, optional (False)): attempt to
            download exclusively provided resolution or none at all
        - output_file (Path | str | None, optional (None)): override output location
        - force (bool | None, optional (False)): overwrite if exists
        - additional_options (dict): additional downloader options
        """

        self.filepath = self.default_importer(self.video_id).download(
            max_resolution=max_resolution or RESOLUTION_360,
            mime_type=mime_type or MIME_TYPE_MP4,
            exact_resolution=False if exact_resolution is None else exact_resolution,
            output_file=output_file,
            force=False if force is None else force,
            additional_options=additional_options or {},
        )

    def download_audio(
        self,
        output_file: Path | str | None = None,
        bitrate: int | None = None,
        force: bool | None = False,
        additional_options: dict(str, str) | None = None,
    ) -> None:
        """Download audio track.

        - output_file (Path | str | None, optional (None)): override output location
        - bitrate (int | None, optional (None)): desired audio bitrate
        - force (bool | None, optional (False)): overwrite if exists
        - additional_options (dict, optional (None)): additional importer options
        """

        self.filepath = self.default_importer(self.video_id).download_audio(
            output_file=output_file,
            bitrate=bitrate,
            force=force,
            additional_options=additional_options,
        )

    @classmethod
    def video_id_to_url(cls, video_id: str) -> str:
        """Validate and transform youtube video ID to valid url."""

        return VIDEO_URL_BASE + cls.validate_video_id(video_id)

    @staticmethod
    def extract_video_id(url: str) -> str:
        try:
            return re.search(VIDEO_ID_PATTERN, url).group()
        except AttributeError:
            raise Exception(f"Unable to derive video ID from string: {url}")

    @staticmethod
    def validate_video_id(video_id: str) -> str:
        """Youtube video ID validator."""

        if not re.match(f"^{VIDEO_ID_PATTERN}$", video_id):
            raise Exception(f"Invalid video ID provided: {video_id}")

        return video_id

    @classmethod
    def check_video_file(cls, filepath: str) -> str:
        """Check if video file exists and in correct format."""

        filepath = Path(filepath).absolute()

        if filepath.suffix[1:] not in FORMATS_VID:
            formats = ",".join(FORMATS_VID)
            raise Exception(f"Incorrect file format (supported: {formats})")
        if not filepath.is_file():
            raise Exception("File not found")

        return filepath

    def clip(
        self,
        t1: str | int | float,
        t2: str | int | float,
        output_file: Path | str | None = None,
        strip_sound: bool | None = False,
        force: bool | None = False,
    ) -> Video:
        """Cut clip from a video file."""

        force = False if force is None else force
        t1 = utils.parse_time_value(t1)
        t2 = utils.parse_time_value(t2)
        if t1 >= t2:
            raise Exception(f"Incorrect time range provided ({t1} - {t2})")

        output_file = (
            Path(output_file)
            if output_file
            else DEFAULT_DIR / f"{self.video_id}-clip-{float(t1)}-{float(t2)}.{FMT_MP4}"
        )
        utils.check_existing_file(output_file, force=force)
        utils.ensure_folder(output_file)

        with VideoFileClip(self.filepath) as vid:
            subclip = vid.subclip(t1, t2)
            if strip_sound:
                subclip = subclip.without_audio()
            subclip.write_videofile(str(output_file))

        return Video(filepath=str(output_file))

    def modify_speed(self, factor: int | None = None):
        """..."""

        if not factor:
            raise exceptions.ValidationError(value=factor)

        raise NotImplementedError()
