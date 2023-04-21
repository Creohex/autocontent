#!/Users/creohex/github/autocontent/.venv/bin/python

import click
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


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
    """Converts youtube video JSON transcription into readable text with timestamps."""

    s = Path(source).absolute()
    if not s.exists():
        raise Exception("File not found")
    if not s.suffix == ".json":
        raise Exception("Incorrect file format")

    target = s.parent / f"{s.stem}_formatted.{fmt}"
    click.echo(f"Source file: {s}\nTarget file: {target}")

    with open(s) as file:
        subs = json.load(file)[0]

    if target.exists():
        if force:
            target.unlink(missing_ok=True)
        else:
            raise Exception("output file already exists")

    with open(target, "w") as target_file:
        formatter = format_txt if fmt == FMT_TXT else format_srt
        target_file.write(formatter(subs))

        # [target_file.write(formatter(record)) for record in subs]
        # for record in subs:

        #             start = time.strftime(TIME_FMT, time.gmtime(record["start"]))
        #             end = time.strftime(
        #                 TIME_FMT, time.gmtime(record["start"] + record["duration"])
        #             )
        #             line = f"[{start} - {end}] {record['text']}\n"
        #         case "srt":
        #             start
        #         case _:
        #             raise Exception("Incorrect format provided")

        #     target_file.write(formatter(record))

    click.echo("Done.")


# @click.command()
# def split()

if __name__ == "__main__":

    @click.group
    def cli():
        pass

    cli.add_command(convert)

    cli()
