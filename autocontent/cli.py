from pathlib import Path

import click

from . import utils
from .subs import FMT_JSON, FMT_SRT, FMT_TXT, FORMATS_SUB, Subs


# --- Subtitles ---
@click.command()
@click.option("-i", "--video_id", required=True, type=str, help="Youtube video ID")
@click.option(
    "-o", "--output", required=False, type=str, default="", help="output file name"
)
@click.option(
    "-f",
    "--force",
    default=False,
    is_flag=True,
    show_default=True,
    help="override target file if exists?",
)
def pull(video_id, output, force):
    """Downloads youtube video subtitles.

    video_id (str): youtube video ID
    name (str): override name for output file
    force (bool): overwrite output file if exists?
    """

    target_file = Path(__file__).parent.parent / "subs" / f"{output or video_id}.json"
    Subs(video_id=video_id).save(target_file, fmt=FMT_JSON, force=force)
    click.echo(f"Saved to: {target_file}")


@click.command()
@click.option("-s", "--source", required=True, help="path to subs in json format")
@click.option(
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS_SUB, case_sensitive=True),
    help=f"output format ({','.join(FORMATS_SUB)})",
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

    source = Path(source).absolute()
    target = source.parent / f"{source.stem}.{fmt}"

    click.echo(f"Source file: {source}\nTarget file: {target}")
    Subs(filepath=source).save(target, fmt=fmt, force=force)
    click.echo("Done.")


@click.command(help="Cuts subtitles into a chunk with possible time shift")
@click.option(
    "-s", "--source", required=True, type=str, help="path to subs in json format"
)
@click.option(
    "-a",
    "--t1",
    required=True,
    help="left time bracket in seconds or hh:mm:ss format",
)
@click.option(
    "-b",
    "--t2",
    required=True,
    help="right time bracket in seconds or hh:mm:ss format",
)
@click.option(
    "-o",
    "--output",
    required=False,
    type=str,
    default="",
    help="output file name",
)
@click.option(
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS_SUB, case_sensitive=True),
    help=f"output format ({','.join(FORMATS_SUB)})",
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
def chunk(source, t1, t2, output, fmt, force, shift):
    """Extracts subtitles in selected time range and outputs in desired file format

    source (str): youtube subtitle JSON file
    t1 (float): left time bracket
    t2 (float): right time bracket
    output (str): override output file name
    fmt (str): output subtitle format
    force (bool): overwrite output file?
    shift (bool): shifts subtitle timestamps to the left
    """

    source = Path(source).absolute()
    t1 = utils.parse_time_value(t1)
    t2 = utils.parse_time_value(t2)

    original = Subs(filepath=source)
    target_file = original.derive_chunk_filename(t1, t2, fmt, target_file=output)
    subs = original.cut(t1, t2)

    if shift:
        subs.shift_left()

    subs.save(target_file, fmt=fmt, force=force)
    click.echo(f"Wrote to: {target_file}")


# Command group registration:
@click.group
def grp():
    pass


grp.add_command(pull)
grp.add_command(convert)
grp.add_command(chunk)
