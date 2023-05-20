# TODO: define temp folders, cleanup
import pytest


ALLOW_PAID_MODEL_USAGE = False
"""Flag which decides whether to skip tests that make requests to paid models or not."""


@pytest.fixture()
def monetized():
    """Fixture that skips all cases if associated flag is disabled."""

    if not ALLOW_PAID_MODEL_USAGE:
        pytest.skip()
