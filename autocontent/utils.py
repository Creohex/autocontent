import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from moviepy.editor import VideoFileClip


TIME_FMT = r"%H:%M:%S"
# TIME_FMT_MS = r"%H:%M:%S,%f"

FMT_MP4 = "mp4"
FORMATS_VID = [FMT_MP4]
"""Video formats."""


def format_time_ms(seconds):
    """Formats seconds to HH:MM:SS:MS format."""

    formatted_td = str(timedelta(seconds=seconds)).split(".")[0]
    formatted_time = datetime.strptime(formatted_td, TIME_FMT)
    ms = int(seconds % 1 * 1000)
    formatted_time_str = formatted_time.strftime(TIME_FMT)
    formatted_str = f"{formatted_time_str},{ms:03d}"
    return formatted_str


def ensure_folder(file_path):
    """Ensures that all folders leading to the provided file path exist."""

    if not isinstance(file_path, (str, Path)):
        raise Exception("Incorrect file_path: 'Path' or 'str' expected")
    if isinstance(file_path, str):
        file_path = Path(file_path)

    for directory in reversed(list(file_path.parents)):
        if not directory.exists():
            directory.mkdir()


def check_existing_file(file, force=False):
    """Checks if file exists and deletes it when forced to."""

    if file.is_file() and file.exists():
        if force:
            file.unlink()
        else:
            raise Exception(f"file already exists: {file}")


def write_to_file(file, contents):
    """Writes contents to file.

    file (Path):
    contents (): _description_
    """

    file = Path(file)

    if file.exists():
        raise Exception(f"Couldn't write to {file}: already exists.")

    try:
        with open(file, "w") as target_file:
            target_file.write(contents)
    except:
        file.unlink()
        raise


def parse_time_value(predicate):
    """Parses time input in various forms."""

    match predicate:
        case float():
            return predicate
        case int():
            return float(predicate)
        case str():
            h = m = s = 0
            if re.match(r"^\d+(\.(0?[0-9]|[0-9]{1,2}))?$", predicate):
                return float(predicate)
            elif re.match(r"^\d{1,2}:\d{1,2}$", predicate):
                m, s = predicate.split(":")
            elif re.match(r"^\d{1,2}:\d{1,2}:\d{1,2}$", predicate):
                h, m, s = predicate.split(":")
            else:
                raise Exception(f"Incorrect time format: {predicate}")

            return 1.0 * (int(h) * 3600 + int(m) * 60 + int(s))
        case _:
            raise Exception(
                f"Invalid time argument type ({predicate}, {type(predicate)})"
            )


def check_video_extension(file):
    """Checks if provided video file type is supported."""

    return Path(file).suffix[1:] in FORMATS_VID


def check_video_file(file) -> VideoFileClip:
    """Checks if video file exists and in correct ."""

    file = Path(file).absolute()
    if not file.exists():
        raise Exception("File not found")
    if not check_video_extension(file):
        raise Exception(f"Incorrect file format (supported: {','.join(FORMATS_VID)})")

    return str(file)
    # return VideoFileClip(str(s))


def clip_video(source_file, t1, t2, target_file=None, strip_sound=False, force=False):
    """Cut clip from a video file."""

    t1 = parse_time_value(t1)
    t2 = parse_time_value(t2)
    if t1 >= t2:
        raise Exception(f"Incorrect time range provided ({t1} - {t2})")

    source_file = Path(source_file).absolute()
    video_path = check_video_file(source_file)
    target_file = source_file.parent / Path(
        target_file or f"{source_file.stem}-clip-{str(t1)}-{str(t2)}.{FMT_MP4}"
    )
    check_existing_file(target_file, force=force)

    with VideoFileClip(video_path) as vid:
        subclip = vid.subclip(t1, t2)
        if strip_sound:
            subclip = subclip.without_audio()
        subclip.write_videofile(str(target_file))
