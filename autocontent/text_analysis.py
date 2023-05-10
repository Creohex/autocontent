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
    ai21: API_KEY_AI21,
    openai: API_KEY_OPENAI,
}
"""Lib <-> API key config name mapping."""

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

JINJA_ENV = jinja2.Environment()
"""Initialized jinja environment obj."""


def ensure_key(lib) -> callable:
    """Verify that API key is set for specific service."""

    key_name = API_KEYS[lib]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not lib.api_key:
                lib.api_key = config(key_name)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@ensure_key(ai21)
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


@ensure_key(ai21)
def summarize(
    text: str,
    source_type: str = SOURCE_TYPE_TEXT,
) -> list[str]:
    """Summarize text."""

    return Summarize.execute(source=text, source_type=source_type).summary


@ensure_key(openai)
def completion(
    prompt: str,
    engine: str = ENGINE_DAVINCI,
    max_tokens: str = MAX_TOKENS_DEFAULT,
    temperature: str = TEMPERATURE_DEFAULT,
) -> str:
    """OpenAI's typical GPT prompt completion."""

    compl = openai.Completion.create(
        prompt=prompt, engine=engine, max_tokens=max_tokens, temperature=temperature
    )

    return compl.choices[0]["text"].strip()


def completion_from_template(template: str, **template_params) -> str:
    """GPT prompt completion using template."""

    return completion(JINJA_ENV.from_string(template).render(**template_params))
