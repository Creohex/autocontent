#!/Users/creohex/github/autocontent/.venv/bin/python


import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import click
from youtube_transcript_api import YouTubeTranscriptApi


TIME_FMT = r"%H:%M:%S"
# TIME_FMT_MS = r"%H:%M:%S,%f"
FMT_TXT = "txt"
FMT_SRT = "srt"
FORMATS = [FMT_TXT, FMT_SRT]


def format_time_ms(seconds):
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
    if file.exists():
        if force:
            file.unlink()
        else:
            raise Exception("output file already exists")


def write_to_file(file, contents):
    """..."""

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
    return 1.0 * (int(h) * 3600 + int(m) * 60 + int(s))


@click.command()
@click.option("-i", "--video_id", required=True, type=str, help="Youtube video ID")
@click.option(
    "-n", "--name", required=False, type=str, default="", help="output file name"
)
@click.option(
    "-f",
    "--force",
    default=False,
    is_flag=True,
    show_default=True,
    help="override target file if exists?",
)
def pull(video_id, name, force):
    """Downloads youtube video subtitles

    video_id (str): youtube video ID
    name (str): override name for output file
    force (bool): overwrite output file if exists?
    """

    target_name = f"{name or video_id}.json"
    target = Path(__file__).parent / "subs" / target_name

    check_existing_file(target, force)
    ensure_folder(target)

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_transcript(["en"]).fetch()

    write_to_file(target, json.dumps(transcript))

    click.echo("Done.")


@click.command()
@click.option("-s", "--source", required=True, help="path to subs in json format")
@click.option(
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS, case_sensitive=True),
    help=f"output format ({','.join(FORMATS)})",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    show_default=True,
    default=False,
    help="override target file if exists?",
)
def convert(source, fmt, force):
    """Converts youtube video JSON transcription into readable text with timestamps.

    source (str): path to .json file
    fmt (str): output file format (txt, srt)
    force (bool): override output file if exists
    """

    s = Path(source).absolute()
    target = s.parent / f"{s.stem}.{fmt}"
    subs = load_subtitiles(s)

    click.echo(f"Source file: {s}\nTarget file: {target}")

    check_existing_file(target, force)
    ensure_folder(target)

    formatter = format_txt if fmt == FMT_TXT else format_srt
    write_to_file(target, formatter(subs))

    click.echo("Done.")


@click.command(help="Cuts subtitles into a chunk with possible time shift")
@click.option("-s", "--source", required=True, help="path to subs in json format")
@click.option(
    "-a",
    "--t1",
    # type=(float, str),
    required=True,
    help="left time bracket in seconds or hh:mm:ss format",
)
@click.option(
    "-b",
    "--t2",
    # type=(float, str),
    required=True,
    help="right time bracket in seconds or hh:mm:ss format",
)
@click.option(
    "-n",
    "--name",
    required=False,
    type=str,
    default="",
    help="output file name",
)
@click.option(
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS, case_sensitive=True),
    help=f"output format ({','.join(FORMATS)})",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    show_default=True,
    default=False,
    help="override target file if exists?",
)
@click.option(
    "--shift",
    is_flag=True,
    show_default=True,
    default=False,
    help="shifts timestamps to 0",
)
def chunk(source, t1, t2, name, fmt, force, shift):
    """Extracts subtitles in selected time range and outputs in desired file format

    source (str): youtube subtitle JSON file
    t1 (float): left time bracket
    t2 (float): right time bracket
    name (str): override output file name
    fmt (str): output subtitle format
    force (bool): overwrite output file?
    shift (bool): shifts subtitle timestamps to the left
    """

    if isinstance(t1, str):
        t1 = parse_time_input(t1)
    if isinstance(t2, str):
        t2 = parse_time_input(t2)
    if t1 >= t2:
        raise Exception("Incorrect timeframes selected")

    s = Path(source).absolute()
    target = s.parent / f"{name or s.stem}_chunk_{int(t1)}_{int(t2)}.{fmt}"
    subs = load_subtitiles(s)

    check_existing_file(target, force)
    ensure_folder(target)

    filtered = []
    padding = None

    for record in subs:
        end = record["start"] + record["duration"]
        if record["start"] >= t1 and end < (t2 + record["duration"]):
            if shift and padding is None:
                padding = record["start"]
            if shift:
                record["start"] -= padding
            filtered.append(record)

    formatter = format_txt if fmt == FMT_TXT else format_srt
    write_to_file(target, formatter(filtered))

    click.echo(f"Wrote to: {target}\nDone.")


if __name__ == "__main__":

    @click.group
    def cli():
        pass

    cli.add_command(pull)
    cli.add_command(convert)
    cli.add_command(chunk)

    cli()
