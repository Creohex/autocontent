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
    # start_time = 10  # in seconds
    # end_time = 30    # in seconds
    # ffmpeg_extract_subclip(str(video_file), start_time, end_time, targetname=str(video_file.parent/"clip.mp4"))


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

    t1 = utils.parse_time_input(t1)
    t2 = utils.parse_time_input(t2)
    if t1 >= t2:
        raise Exception(f"Incorrect time range provided ({t1} - {t2})")

    source_path = Path(source).absolute()
    video_path = utils.check_video_file(source)
    output = source_path.parent / Path(
        output or f"{source_path.stem}-clip-{str(t1)}-{str(t2)}.{utils.FMT_MP4}"
    )
    utils.check_existing_file(output, force=force)

    with VideoFileClip(video_path) as vid:
        subclip = vid.subclip(t1, t2)
        if strip_sound:
            subclip = subclip.without_audio()
        subclip.write_videofile(str(output))


# Command group registration:
@click.group
def grp():
    pass


grp.add_command(test)
grp.add_command(clip)
