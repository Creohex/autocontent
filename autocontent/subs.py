from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

# from typing import e

from youtube_transcript_api import YouTubeTranscriptApi

from . import utils


DEFAULT_DIR = utils.ROOT_DIR / "subs/"
"""Default directory for subtitle file management."""

FMT_JSON = "json"
FMT_TXT = "txt"
FMT_SRT = "srt"
FORMATS_SUB = [FMT_JSON, FMT_TXT, FMT_SRT]
"""Supported subtitle formats."""


class Subs:
    """Video subtitle model."""

    locales = ["en"]

    def __init__(
        self,
        transcript: str = None,
        filepath: str = None,
        video_id: str = None,
    ) -> Subs:
        if sum(map(bool, (transcript, filepath, video_id))) != 1:
            raise Exception("Either transcript, filepath or video_id must be provided")

        self.filepath = filepath
        self.video_id = video_id

        if transcript:
            expected_keys = set(["text", "start", "duration"])
            if (
                not isinstance(transcript, list)
                or not all((isinstance(t, dict) for t in transcript))
                or any(
                    bool(set(t.keys()).symmetric_difference(expected_keys))
                    for t in transcript
                )
            ):
                raise Exception("Invalid transcript structure")
            self.transcript = transcript
        elif filepath:
            self.transcript = self.load_subtitiles(filepath)
        else:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            self.transcript = transcript_list.find_transcript(self.locales).fetch()

    @classmethod
    def load_subtitiles(cls, file: Path | str) -> list[Subs]:
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

    def save(
        self,
        output_file: Path,
        fmt: str | None = FMT_TXT,
        force: bool | None = False,
    ) -> None:
        """Export subs to file in preferred format."""

        utils.check_existing_file(output_file, force=force)
        utils.ensure_folder(output_file)
        utils.write_to_file(output_file, self.format_subs(self.transcript, fmt))

    def cut(self, t1: int | float | str, t2: int | float | str) -> Subs:
        """Cuts subtitles in selected time range.

        t1 (float/int/str): left time bracket
        t2 (float/int/str): right time bracket
        """

        filtered = []
        t1 = utils.parse_time_value(t1)
        t2 = utils.parse_time_value(t2)

        if t1 >= t2:
            raise Exception("Incorrect time brackets provided")

        for record in self.transcript:
            end = record["start"] + record["duration"]
            if record["start"] >= t1 and end <= (t2 + record["duration"]):
                filtered.append(record)

        return Subs(transcript=filtered)

    def shift_left(self) -> None:
        """Shifts transcript timestamps to the left."""

        if not self.transcript:
            raise Exception("Empty transcript")

        offset = self.transcript[0]["start"]

        for record in self.transcript:
            record["start"] -= offset

    def derive_chunk_filename(
        self,
        t1: float,
        t2: float,
        fmt: str,
        target_file: Path | str = None,
    ) -> Path:
        """Generate filename for subtitle chunk.

        t1 (str): left time bracket
        t2 (str): right time bracket
        fmt (str): target format
        target_file (Path, optional): Override target file. Defaults to None.
        """

        if target_file:
            target_file = Path(target_file).absolute()

        if not target_file:
            tail = f"chunk_{float(t1)}_{float(t2)}.{fmt}"
            if self.filepath:
                target_file = self.filepath.parent / f"{self.filepath.stem}_{tail}"
            elif self.video_id:
                target_file = DEFAULT_DIR / Path(f"{self.video_id}_{tail}")
            else:
                target_file = DEFAULT_DIR / Path(f"{str(uuid.uuid4())[-4:]}_{tail}")

        return target_file

    @classmethod
    def format_txt(cls, records: list[dict[str, int | str]]) -> str:
        """.txt formatter."""

        text = ""
        for record in records:
            start = time.strftime(utils.TIME_FMT, time.gmtime(record["start"]))
            end = time.strftime(
                utils.TIME_FMT, time.gmtime(record["start"] + record["duration"])
            )
            text += f"[{start} - {end}] {record['text']}\n"
        return text

    @classmethod
    def format_srt(cls, records: list[dict[str, int | str]]) -> str:
        """.srt formatter."""

        text = ""
        for i, record in enumerate(records):
            start = utils.format_time_ms(record["start"])
            end = utils.format_time_ms(record["start"] + record["duration"])
            text += f"{i + 1}\n{start} --> {end}\n{record['text']}\n\n"
        return text

    @classmethod
    def format_subs(cls, records: list[dict[str, int | str]], fmt: str) -> str:
        """Formats subtitles from JSON to appropriate format.

        records (list): subtitles in JSON format
        fmt (str): prefered output format
        """

        if fmt == FMT_JSON:
            return json.dumps(records)
        elif fmt == FMT_TXT:
            return cls.format_txt(records)
        elif fmt == FMT_SRT:
            return cls.format_srt(records)
        else:
            raise Exception(f"Unsupported format selected ({fmt})")
