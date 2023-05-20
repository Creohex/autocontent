
import pytest
# TODO: define temp folders, cleanup

ALLOW_PAID_MODEL_USAGE = False
"""Flag which decides whether to skip tests that make requests to paid models or not."""


@pytest.fixture(autouse=True)
def disable_monetized_requests():
    """Autofixture to skip all cases if flag is not enabled."""

    if not ALLOW_PAID_MODEL_USAGE:
        pytest.skip()
