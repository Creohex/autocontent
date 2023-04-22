#!/Users/creohex/github/autocontent/.venv/bin/python

import json
from pathlib import Path

import click
from youtube_transcript_api import YouTubeTranscriptApi

import utils
from utils import FMT_TXT, FMT_SRT, FORMATS


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

    utils.check_existing_file(target, force)
    utils.ensure_folder(target)

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_transcript(["en"]).fetch()

    utils.write_to_file(target, json.dumps(transcript))

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

    click.echo(f"Source file: {s}\nTarget file: {target}")
    utils.check_existing_file(target, force)
    utils.ensure_folder(target)
    utils.write_to_file(target, utils.format_subs(utils.load_subtitiles(s), fmt))
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
        t1 = utils.parse_time_input(t1)
    if isinstance(t2, str):
        t2 = utils.parse_time_input(t2)
    if any(lambda _: not isinstance(_, float), [t1, t2]) or t1 >= t2:
        raise Exception("Incorrect time brackets provided")

    s = Path(source).absolute()
    target = s.parent / f"{name or s.stem}_chunk_{int(t1)}_{int(t2)}.{fmt}"
    subs = utils.load_subtitiles(s)

    utils.check_existing_file(target, force)
    utils.ensure_folder(target)

    filtered = []
    padding = None

    for record in subs:
        end = record["start"] + record["duration"]
        if record["start"] >= t1 and end < (t2 + record["duration"]):
            if shift:
                if padding is None:
                    padding = record["start"]
                record["start"] -= padding
            filtered.append(record)

    formatter = utils.format_txt if fmt == FMT_TXT else utils.format_srt
    utils.write_to_file(target, formatter(filtered))

    click.echo(f"Wrote to: {target}\nDone.")


# Command group registration:
@click.group
def grp():
    pass


grp.add_command(pull)
grp.add_command(convert)
grp.add_command(chunk)
