from __future__ import annotations

import json
import math
import time
from itertools import pairwise
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

from . import exceptions, utils
from .exceptions import ValidationError


DEFAULT_DIR = utils.ROOT_DIR / "subs/"
"""Default directory for subtitle file management."""

FMT_JSON = "json"
FMT_TXT = "txt"
FMT_SRT = "srt"
FMT_COMPRESSED = "compressed"
FORMATS_SUB = [FMT_JSON, FMT_TXT, FMT_SRT, FMT_COMPRESSED]
"""Supported subtitle formats."""


class Subs:
    """Video subtitle model."""

    locales = ["en"]

    def __init__(
        self,
        transcript: list[dict] = None,
        filepath: str = None,
        video_id: str = None,
        sanitize: bool | None = True,
    ) -> Subs:
        """Instatiate subtitle transcription (from different sources).

        - transcript (list[dict], optional (None)): list of dicts (records)
        - filepath (str, optional (None)): path to a .json file
        - video_id (str, optional (None)): youtube video ID to download transcription from
        - sanitize (bool | None, optional (True)): Sanitize transcription text on load
        """
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
        elif video_id:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            self.transcript = transcript_list.find_transcript(self.locales).fetch()

        if sanitize:
            self.sanitize()

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

        fmt = fmt or FMT_TXT
        utils.check_existing_file(output_file, force=False if force is None else force)
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
                target_file = DEFAULT_DIR / Path(f"{utils.unique_id}_{tail}")

        return target_file

    def sanitize(self) -> None:
        """(in-place) Remove various artifacts from transcript."""

        to_eliminate = ["-"]  # FIXME

        for record in self.transcript:
            for character in to_eliminate:
                record["text"] = record["text"].replace(character, "")

            record["text"] = record["text"].strip()

    def restructure(self, lines=3):
        """(in-place) Split subtitles into blocks of words separated by newline.

        - lines (int, optional (3)): Amount of lines '\n'-separated lines
        """

        if not 0 < lines < 10:
            raise ValidationError(msg="Incorrect amount of lines provided", value=lines)

        for record in self.transcript:
            words = record["text"].replace("\n", " ").split()
            words_per_line = len(words) // lines
            if words_per_line == 0:
                words_per_line = len(words)

            restructured = []
            left = 0
            rem = len(words) % lines
            for i in range(lines):
                right = left + words_per_line + (1 if i < rem else 0)
                restructured.append(" ".join(words[left:right]))
                left = right

            record["text"] = "\n".join(restructured)

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
    def format_compressed(cls, records: list[dict[str, int | str]]) -> str:
        """.compressed formatter."""

        return "\n".join(f"{i} - {record['text']}" for i, record in enumerate(records))

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
        elif fmt == FMT_COMPRESSED:
            return cls.format_compressed(records)
        else:
            raise Exception(f"Unsupported format selected ({fmt})")
