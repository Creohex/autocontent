#!pytest -s

import pytest
import random
from string import ascii_lowercase

from ..subs import Subs
from ..utils import print


SAMPLE_TRANSCRIPT = [
    {
        "text": " ".join([random.choice(ascii_lowercase)] * random.randint(3, 15)),
        "start": _,
        "duration": 1,
    }
    for _ in range(10)
]


def test_init():
    sssss = Subs(transcript=[{"text": 123, "start": 123, "duration": 123}])
    print(sssss.transcript)


@pytest.mark.parametrize(("lines"), list(range(1, 10)))
def test_restructure(lines):
    subs = Subs(
        transcript=[
            {
                "text": "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
                "start": 123,
                "duration": 123,
            }
        ]
    )
    subs.restructure(lines=lines)

    assert len(subs.transcript[0]["text"].split("\n")) == lines


def test_format_compressed():
    text = Subs.format_compressed([{"text": "abc"}, {"text": "def"}, {"text": "ghi"}])

    assert text == "0: abc\n1: def\n2: ghi"
