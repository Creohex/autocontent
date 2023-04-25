from pathlib import Path

import click
import moviepy.editor
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from . import utils


# TODO: clip video parts
#       apply subs (stylize?)
#       remove quiet parts


@click.command()
def test():
    video_file = Path(".").parent / "sources" / "v1.mp4"
    video = VideoFileClip(str(video_file)).subclip(15, 20)


@click.command()
@click.option("-s", "--source", required=True, type=str, help="Video file path")
@click.option(
    "-a", "--t1", required=True, help="left time bracket in seconds or hh:mm:ss"
)
@click.option(
    "-b", "--t2", required=True, help="right time bracket in seconds or hh:mm:ss"
)
@click.option(
    "-o", "output", required=False, type=str, default="", help="output clip file path"
)
@click.option(
    "--strip_sound",
    is_flag=True,
    required=False,
    show_default=True,
    default=False,
    help="strips audio from the resulting clip",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    show_default=True,
    default=False,
    help="override target file if exists?",
)
def clip(source, t1, t2, output, strip_sound, force):
    """Cuts a clip from provided video file."""

    utils.clip_video(
        source,
        t1,
        t2,
        target_file=output,
        strip_sound=strip_sound,
        force=force,
    )


# Command group registration:
@click.group
def grp():
    pass


grp.add_command(test)
grp.add_command(clip)
