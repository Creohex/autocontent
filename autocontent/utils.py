import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path


TIME_FMT = r"%H:%M:%S"
# TIME_FMT_MS = r"%H:%M:%S,%f"
FMT_TXT = "txt"
FMT_SRT = "srt"
FORMATS = [FMT_TXT, FMT_SRT]


def format_time_ms(seconds):
    """Formats seconds to HH:MM:SS:MS format.

    seconds (float): _description_

    Returns:
        _type_: _description_
    """

    formatted_td = str(timedelta(seconds=seconds)).split(".")[0]
    formatted_time = datetime.strptime(formatted_td, TIME_FMT)
    ms = int(seconds % 1 * 1000)
    formatted_time_str = formatted_time.strftime(TIME_FMT)
    formatted_str = f"{formatted_time_str},{ms:03d}"
    return formatted_str


def format_txt(records):
    text = ""
    for record in records:
        start = time.strftime(TIME_FMT, time.gmtime(record["start"]))
        end = time.strftime(TIME_FMT, time.gmtime(record["start"] + record["duration"]))
        text += f"[{start} - {end}] {record['text']}\n"
    return text


def format_srt(records):
    text = ""
    for i, record in enumerate(records):
        start = format_time_ms(record["start"])
        end = format_time_ms(record["start"] + record["duration"])
        text += f"{i + 1}\n{start} --> {end}\n{record['text']}\n\n"
    return text


def format_subs(records, format):
    """Formats subtitles (JSON -> txt/srt/...)

    records (list): subtitles in JSON format
    format (str): prefered output format
    """

    formatter = format_txt if format == FMT_TXT else format_srt
    return formatter(records)


def ensure_folder(file_path):
    """Ensures that all folders leading to the provided file path exist."""

    if not isinstance(file_path, (str, Path)):
        raise Exception("Incorrect file_path: 'Path' or 'str' expected")
    if isinstance(file_path, str):
        file_path = Path(file_path)

    for directory in reversed(list(file_path.parents)):
        if not directory.exists():
            directory.mkdir()


def check_existing_file(file, force):
    """Checks if file exists and deletes it when forced to."""

    if file.exists():
        if force:
            file.unlink()
        else:
            raise Exception("output file already exists")


def write_to_file(file, contents):
    """Writes contents to file.

    file (Path):
    contents (): _description_
    """

    if not isinstance(file, Path):
        raise Exception(f"'file' must be a Path object ({type(file)} was provided)")

    try:
        with open(file, "w") as target_file:
            target_file.write(contents)
    except:
        file.unlink()
        raise


def load_subtitiles(file):
    """Read JSON from file."""

    s = Path(file).absolute()
    if not s.exists():
        raise Exception("File not found")
    if not s.suffix == ".json":
        raise Exception("Incorrect file format")

    with open(s) as file:
        # subs = json.load(file)[0]
        subs = json.load(file)

    return subs


def parse_time_input(time_string):
    """Converts HH:MM:SS time format to float value."""

    if not re.match(r"^\d{1,2}:\d{1,2}:\d{1,2}$", time_string):
        raise Exception(f"Incorrect time format: {time_string}")

    h, m, s = time_string.split(":")
    return 1.0 * int(h) * 3600 + int(m) * 60 + int(s)
