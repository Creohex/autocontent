#!/Users/creohex/github/autocontent/.venv/bin/python

import click
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

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


@click.command()
def chunk(source):
    # 0:00 - Introduction
    # 1:38 - Starting a relationship
    # 5:37 - Couples therapy
    # 12:54 - Why relationships fail
    # 20:11 - Drama in relationships
    # 25:38 - Success in relationships
    # 32:03 - Dating
    # 40:39 - Sex
    # 42:32 - Cheating
    # 51:33 - Polyamory
    # 53:24 - Johnny Depp and Amber Heard trial
    # 1:22:02 - Forensic psychology
    # 1:32:12 - PTSD
    # 1:41:47 - Advice for young people
    # 1:44:38 - Love

    # provide a list of timestamps and its descriptions
    # output subs to separate files? specific file with a selected topic?

    pass


@click.command(help="...")
@click.option("-s", "--source", required=True, help="path to subs in json format")
@click.option(
    "-a",
    "--t1",
    type=float,
    # default=0.0,
    required=True,
    help="left time bracket in seconds",
)
@click.option(
    "-b",
    "--t2",
    type=float,
    # default=0.0,
    required=True,
    help="right time bracket in seconds",
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
def normalize(source, t1, t2, name, fmt, force, shift):
    """Extracts subtitles in selected time range and outputs in desired file format

    source (str): youtube subtitle JSON file
    t1 (float): left time bracket
    t2 (float): right time bracket
    name (str): override output file name
    fmt (str): output subtitle format
    force (bool): overwrite output file?
    """

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
            if padding is None:
                padding = record["start"]
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
    cli.add_command(normalize)

    cli()
