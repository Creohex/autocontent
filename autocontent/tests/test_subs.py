import pytest

from ..subs import Subs


def test_init():
    sssss = Subs(transcript=[{"text": 123, "start": 123, "duration": 123}])
    print(sssss.transcript)
