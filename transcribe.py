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

    if target.exists():
        if force:
            target.unlink()
        else:
            raise Exception("output file already exists")

    ensure_folder(target)

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_transcript(["en"]).fetch()

    try:
        with open(target, "w") as target_file:
            target_file.write(json.dumps(transcript))
    except:
        target.unlink()
        raise

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
    if not s.exists():
        raise Exception("File not found")
    if not s.suffix == ".json":
        raise Exception("Incorrect file format")

    target = s.parent / f"{s.stem}.{fmt}"
    click.echo(f"Source file: {s}\nTarget file: {target}")

    with open(s) as file:
        # subs = json.load(file)[0]
        subs = json.load(file)

    if target.exists():
        if force:
            target.unlink()
        else:
            raise Exception("output file already exists")

    try:
        with open(target, "w") as target_file:
            formatter = format_txt if fmt == FMT_TXT else format_srt
            target_file.write(formatter(subs))
    except:
        target.unlink()
        raise

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


if __name__ == "__main__":

    @click.group
    def cli():
        pass

    cli.add_command(pull)
    cli.add_command(convert)
    cli.add_command(chunk)

    cli()
