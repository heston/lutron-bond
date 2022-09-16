import os
from unittest.mock import Mock

import pytest


class AsyncMock(Mock):
    """https://stackoverflow.com/a/34828288/1864926"""

    def __call__(self, *args, **kwargs):
        sup = super(AsyncMock, self)

        async def coro():
            return sup.__call__(*args, **kwargs)  # type: ignore

        return coro()

    def __await__(self):
        return self().__await__()


@pytest.fixture
def amock():
    return AsyncMock


@pytest.fixture
def env():
    kv = {}

    def setenv(key, value):
        kv[key] = os.environ.get(key)

        if value is None:
            try:
                del os.environ[key]
            except KeyError:
                pass
        else:
            os.environ[key] = value

    yield setenv

    for key, value in kv.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value


# Set some default environment variables for testing purposes. These can be
# overridden with the `env` fixture on a per-test basis.
os.environ['LUTRON_BRIDGE_ADDR'] = '10.0.0.10'
os.environ['BOND_BRIDGE_ADDR'] = '10.0.0.11'
os.environ['BOND_BRIDGE_API_TOKEN'] = 'asdfasdf'
