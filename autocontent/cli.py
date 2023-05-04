from pathlib import Path

import click

from . import utils
from .subs import FMT_JSON, FMT_SRT, FMT_TXT, FORMATS_SUB, Subs
from .video import Video, FMT_MP4, VideoImporter, AUDIO_BITRATE_DEFAULT


# --- Templates ---
def opts_video_id_url(method):
    """Click options template for video_id/url args."""

    for dec in reversed(
        [
            click.option(
                "-i",
                "--video_id",
                required=False,
                default=None,
                type=str,
                help="Youtube video ID",
            ),
            click.option(
                "-u",
                "--url",
                required=False,
                default=None,
                type=str,
                help="Youtube video URL",
            ),
        ]
    ):
        method = dec(method)
    return method


def opts_output_force(method):
    """Click options template for output/force args."""

    for dec in reversed(
        [
            click.option(
                "-o",
                "--output",
                required=False,
                type=str,
                default="",
                help="output file name",
            ),
            click.option(
                "-f",
                "--force",
                default=False,
                is_flag=True,
                show_default=True,
                help="override target file if exists?",
            ),
        ]
    ):
        method = dec(method)
    return method


# --- Subtitles ---
@click.command(help="Download youtube video transcription")
@opts_video_id_url
@opts_output_force
def pull_subtitles(video_id, output, force):
    """Downloads youtube video subtitles.

    video_id (str): youtube video ID
    name (str): override name for output file
    force (bool): overwrite output file if exists?
    """

    target_file = Path(__file__).parent.parent / "subs" / f"{output or video_id}.json"
    Subs(video_id=video_id).save(target_file, fmt=FMT_JSON, force=force)
    click.echo(f"Saved to: {target_file}")


@click.command(help="Convert subtitles to specific format")
@click.option("-s", "--source", required=True, help="path to subs in json format")
@click.option(
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS_SUB, case_sensitive=True),
    help=f"output format ({','.join(FORMATS_SUB)})",
)
@opts_output_force
def convert(source, fmt, output, force):
    """Converts youtube video JSON transcription into readable text with timestamps.

    source (str): path to .json file
    fmt (str): output file format (txt, srt)
    output (str) output file location
    force (bool): override output file if exists
    """

    # TODO: handle 'output'

    source = Path(source).absolute()
    target = source.parent / f"{source.stem}.{fmt}"

    Subs(filepath=source).save(target, fmt=fmt, force=force)
    click.echo(f"Saved to: {target}")


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
    "-t",
    "--fmt",
    default=FMT_TXT,
    type=click.Choice(FORMATS_SUB, case_sensitive=True),
    help=f"output format ({','.join(FORMATS_SUB)})",
)
@click.option(
    "--shift",
    is_flag=True,
    show_default=True,
    default=False,
    help="shifts timestamps to 0",
)
@opts_output_force
def chunk(source, t1, t2, fmt, shift, output, force):
    """Extracts subtitles in selected time range and outputs in desired file format

    source (str): youtube subtitle JSON file
    t1 (float): left time bracket
    t2 (float): right time bracket
    fmt (str): output subtitle format
    shift (bool): shifts subtitle timestamps to the left
    output (str): override output file name
    force (bool): overwrite output file?
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


# --- Videos ---
@click.command(help="Download youtube video file")
@opts_video_id_url
@click.option(
    "-r",
    "--resolution",
    required=False,
    default=360,
    type=int,
    help="Preferred video vertical resolution",
)
@click.option(
    "-t",
    "--format",
    required=False,
    type=str,
    default=FMT_MP4,
    help="preferred video format",
)
@opts_output_force
# TODO: resolution, exact_resolution, mime_type
def pull_video(video_id, url, resolution, format, output, force):
    """Download youtube video file."""

    download_kwargs = {
        "output_file": output,
        "force": force,
        "max_resolution": resolution,
        "mime_type": VideoImporter.format_to_mime_type(format),
    }
    video = Video(video_id=video_id, url=url, download_kwargs=download_kwargs)
    click.echo(f"Saved to: {video.filepath}")


@click.command()
@click.option("-s", "--source", required=True, type=str, help="Video file path")
@click.option(
    "-a", "--t1", required=True, help="left time bracket in seconds or hh:mm:ss"
)
@click.option(
    "-b", "--t2", required=True, help="right time bracket in seconds or hh:mm:ss"
)
@click.option(
    "--strip_sound",
    is_flag=True,
    required=False,
    show_default=True,
    default=False,
    help="strips audio from the resulting clip",
)
@opts_output_force
def clip(source, t1, t2, strip_sound, output, force):
    """Cuts a clip from provided video file."""

    video = Video(filepath=source)
    vid = video.clip(t1, t2, output_file=output, strip_sound=strip_sound, force=force)
    click.echo(f"Saved to {vid.filepath}")


# --- Misc ---
@click.command()
def test():
    ...


# Command group registration:
@click.group
def grp():
    pass


grp.add_command(pull_subtitles)
grp.add_command(convert)
grp.add_command(chunk)

grp.add_command(pull_video)
grp.add_command(clip)

grp.add_command(test)
