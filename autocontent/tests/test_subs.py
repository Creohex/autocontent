import pytest

from ..subs import Subs


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
