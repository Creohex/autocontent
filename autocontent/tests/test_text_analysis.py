#!pytest -s

import pytest

from ..text_analysis import (
    completion_from_template,
    completion,
    segment,
    suggest_best_title,
    suggest_titles,
    summarize,
)


TRANSCRIPTION_SAMPLE = """\
"[00:00:00 - 00:00:02] - So contempt is criticism on steroids."
"[00:00:02 - 00:00:07] This is what John Gottman calls sulfuric acid for love."
"[00:00:07 - 00:00:10] Nothing will erode a relationship quicker than contempt."
"[00:00:10 - 00:00:13] Contempt is when you are looking at your partner"
"[00:00:13 - 00:00:15] from a superior position."
"""
"""Short exaple of a video transcription (readable format)."""


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


def test_suggest_titles():
    titles = suggest_titles(TRANSCRIPTION_SAMPLE, title_count=3)

    assert len(titles) == 3
    assert all([isinstance(title, str) for title in titles])


def test_suggest_best_title():
    title = suggest_best_title(TRANSCRIPTION_SAMPLE)

    assert title
    assert isinstance(title, str)
