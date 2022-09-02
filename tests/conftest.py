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
