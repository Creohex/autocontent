#!pytest -s

import pytest

from ..text_analysis import (
    completion,
    completion_from_template,
    summarize,
    segment,
)


ALLOW_PAID_MODEL_USAGE = True


@pytest.fixture(autouse=True)
def paid_model_requests():
    if not ALLOW_PAID_MODEL_USAGE:
        pytest.skip()


def test_completion():
    result = completion("Say 123")
    assert "123" in result


def test_completion_from_template():
    template = "Say {{word}}"
    result = completion_from_template(template, word="123")

    assert "123" in result


def test_summarize():
    # res = summarize("As if this were not enough, the art form into which his creative energies went was not remote and bookish but involved the vivid stage impersonation of human beings, commanding sympathy and inviting vicarious participation.\n\nThus, Shakespeare’s merits can survive translation into other languages and into cultures remote from that of Elizabethan England")
    context = "x" * 30
    summarized = summarize(context)

    assert context == summarized


# FIXME: ...
def test_segment():
    context = (
        "Water is an inorganic compound with the chemical formula H2O. "
        "It is a transparent, tasteless, odorless, and nearly colorless chemical "
        "substance, and it is the main constituent of Earth's hydrosphere and the "
        "fluids of all known living organisms. "
        "An experiment is a procedure carried out to support or refute a hypothesis, "
        "or determine the efficacy or likelihood of something previously untried."
    )
    segments = segment(context)

    assert len(segments) == 2
    assert all([isinstance(_, str) for _ in segments])
