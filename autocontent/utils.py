from __future__ import annotations

import itertools
import os
import progressbar
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path


DEBUG = False
"""Global debug flag."""

TIME_FMT = r"%H:%M:%S"
# TIME_FMT_MS = r"%H:%M:%S,%f"
"""Time format strings."""

ROOT_DIR = Path(__file__).absolute().parent.parent
"""Project root directory."""

HOME_DIR = Path(os.getenv("HOME")).absolute()
"""Home directory."""


def unique_id():
    """Generate unique ID."""

    return str(uuid.uuid4())[-4:]


def format_time_ms(seconds: float) -> str:
    """Formats seconds to HH:MM:SS:MS format."""

    formatted_td = str(timedelta(seconds=seconds)).split(".")[0]
    formatted_time = datetime.strptime(formatted_td, TIME_FMT)
    ms = int(seconds % 1 * 1000)
    formatted_time_str = formatted_time.strftime(TIME_FMT)
    formatted_str = f"{formatted_time_str},{ms:03d}"
    return formatted_str


def ensure_inside_home(file: Path | str) -> None:
    """Checks if provided path is inside home directory

    - file (Path | str): file path
    """

    if not Path(file).absolute().is_relative_to(HOME_DIR):
        raise exceptions.InvalidFilePath(
            msg=f"Invalid path provided (outside of home direcotry): {file}"
        )


def ensure_folder(file_path: Path | str) -> None:
    """Ensures that all folders leading to the provided file path exist."""

    if not isinstance(file_path, (str, Path)):
        raise Exception("Incorrect file_path: 'Path' or 'str' expected")
    file_path = Path(file_path)

    for directory in reversed(list(file_path.parents)):
        if not directory.exists():
            directory.mkdir()


def check_existing_file(file: Path, force: bool = False) -> None:
    """Check if file exist and deletes it when forced to.

    - file (Path): File location
    - force (bool | None, optional (False)): delete file if True
    """

    force = False if force is None else force

    if file.exists():
        if force:
            file.unlink()
        else:
            raise Exception(f"file already exists: {file}")


def write_to_file(file: Path | str, contents: str) -> None:
    """Writes contents to file.

    - file (Path | str): File location
    - contents (str): File contents
    """

    file = Path(file)

    if file.exists():
        raise Exception(f"Couldn't write to {file}: already exists.")

    try:
        with open(file, "w") as target_file:
            target_file.write(contents)
    except:
        file.unlink()
        raise


def parse_time_value(predicate: int | float | str) -> float:
    """Parses time input in various forms and return in float type.

    - predicate (int | float | str): input value
    """

    match predicate:
        case float():
            return predicate
        case int():
            return float(predicate)
        case str():
            h = m = s = 0
            if re.match(r"^\d+(\.(0?[0-9]|[0-9]{1,2}))?$", predicate):
                return float(predicate)
            elif re.match(r"^\d{1,2}:\d{1,2}$", predicate):
                m, s = predicate.split(":")
            elif re.match(r"^\d{1,2}:\d{1,2}:\d{1,2}$", predicate):
                h, m, s = predicate.split(":")
            else:
                raise Exception(f"Incorrect time format: {predicate}")

            return 1.0 * (int(h) * 3600 + int(m) * 60 + int(s))
        case _:
            raise Exception(
                f"Invalid time argument type ({predicate}, {type(predicate)})"
            )


def dialog_confirm(message: str | None = None) -> bool:
    """Command line confirmation dialogue."""

    message = message or "Confirm action?"
    reply = "-"
    positive_replies = ["y", "yes"]
    negative_replies = ["n", "no"]

    while True:
        print(f"{message} 'y/n': ", end="")
        reply = input().lower()
        if reply in positive_replies:
            return True
        elif reply in negative_replies:
            return False


class ProgressBar:
    def __init__(self, key_total, key_progress) -> ProgressBar:
        self.key_total = key_total
        self.key_progress = key_progress
        self.bar = progressbar.ProgressBar()

    def __call__(self, update):
        if not self.bar.max_value:
            self.bar.max_value = update[self.key_total]
        self.bar.update(update[self.key_progress])


class Spinner:
    def __init__(self, title_former: callable | None = None) -> Spinner:
        self.title_former = title_former
        self.spinner = itertools.cycle(["-", "\\", "|", "/"])

    def __call__(self, update) -> None:
        text = "... "
        if self.title_former:
            text = self.title_former(update) + text
        print(text + next(self.spinner), end="\r")
