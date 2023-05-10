from __future__ import annotations

import functools

import ai21
import jinja2
import openai
from ai21 import Segmentation, Summarize

from .utils import config
from .prompt_templates import SUMMARIZE_SINGLE


API_KEY_AI21 = "ai21_key"
API_KEY_OPENAI = "openai_key"
"""API key config names."""

API_KEYS = {
    API_KEY_AI21: ai21.api_key,
    API_KEY_OPENAI: openai.api_key,
}
"""API key <-> lib config field mapping."""

SOURCE_TYPE_URL = "URL"
SOURCE_TYPE_TEXT = "TEXT"
"""Requests source types."""

ENGINE_DAVINCI = "text-davinci-003"
ENGINE_3_TURBO = "gpt-3.5-turbo"
ENGINE_4 = "gpt-4"
ENGINES = [ENGINE_DAVINCI, ENGINE_3_TURBO, ENGINE_4]
"""Existing OpenAI engines."""

MAX_TOKENS_DEFAULT = 1000
TEMPERATURE_DEFAULT = 0.75
"""Default model parameters."""


jinja_env = jinja2.Environment()
"""..."""


def ensure_key(key_name: str) -> callable:
    """Verify that API key is set before executing a function."""

    print(">>>")
    def decorator(f):
        @functools.wraps(f)
        def wrapper():
            if not API_KEYS[key_name]:
                API_KEYS[key_name] = config(key_name)
            f()


    return decorator


# def ensure_key_ai21(func) -> callable:
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         if not ai21.api_key:
#             ai21.api_key = config(API_KEY_AI21)
#         func(*args, **kwargs)


# def ensure_key_openai(func) -> callable:
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         if not ai21.api_key:
#             ai21.api_key = config(API_KEY_AI21)
#         func(*args, **kwargs)


@ensure_key(API_KEY_AI21)
def _request_segmentation(
    source: str,
    source_type: str = SOURCE_TYPE_TEXT,
) -> list[str]:
    """Segmentation request helper."""

    results = Segmentation.execute(sourceType=source_type, source=source)
    return [_["segmentText"] for _ in results["segments"]]


def segment(text: str) -> list[str]:
    """Attempt to segment text into topics."""

    return _request_segmentation(text)


def segment_from_url(url: str) -> list[str]:
    """Attempt to segment data contained in provided URL into topics."""

    return _request_segmentation(url, source_type=SOURCE_TYPE_URL)


@ensure_key(API_KEY_AI21)
def sm(
    text: str,
    source_type: str = SOURCE_TYPE_TEXT,
) -> list[str]:
    """Summarize text."""

    return Summarize.execute(source=text, source_type=source_type).summary


@ensure_key(API_KEY_OPENAI)
def completion(
    text: str,
    engine: str = ENGINE_DAVINCI,
    max_tokens: str = MAX_TOKENS_DEFAULT,
    temperature: str = TEMPERATURE_DEFAULT,
) -> list[str]:
    """..."""

    compl = openai.Completion.create(
        prompt=text, engine=engine, max_tokens=max_tokens, temperature=temperature
    )

    return compl.choices[0]["text"].strip()


def completion_from_template(template, **template_params):
    """..."""

    return completion(jinja_env.from_string(template).render(**template_params))
