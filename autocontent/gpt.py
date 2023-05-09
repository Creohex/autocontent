from __future__ import annotations

import openai
import jinja2

from .utils import config
from .prompt_templates import SUMMARIZE_SINGLE


ENGINE_DAVINCI = "text-davinci-003"
ENGINE_3_TURBO = "gpt-3.5-turbo"
ENGINE_4 = "gpt-4"
ENGINES = [ENGINE_DAVINCI, ENGINE_3_TURBO, ENGINE_4]
"""Existing OpenAI engines."""

MAX_TOKENS_DEFAULT = 1000
TEMPERATURE_DEFAULT = 0.75
"""Default model parameters."""


class Completion:
    ENGINE = ENGINE_DAVINCI
    MAX_TOKENS = MAX_TOKENS_DEFAULT
    TEMPERATURE = TEMPERATURE_DEFAULT
    """Completion configuration."""

    def __init__(
        self,
        engine=ENGINE,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    ):
        self.engine = engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.jinja_env = jinja2.Environment()
        openai.api_key = config("openai_key")

    def request(self, prompt: str, **kwargs) -> str:
        """Communicate with a model using prompt."""

        params = {
            "prompt": prompt,
            "engine": self.engine,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        params.update(kwargs)
        compl = openai.Completion.create(**params)

        return compl.choices[0]["text"].strip()

    def request_from_template(self, template: str, **params):
        """Communicate with a model using prompt template."""

        return self.request(self.jinja_env.from_string(template).render(**params))
