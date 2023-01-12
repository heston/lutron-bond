import asyncio
from collections import defaultdict
import functools
import typing


class EventBus:
    def __init__(self) -> None:
        self._bus: defaultdict = defaultdict(list)
        self._running_handlers: typing.Set[typing.Awaitable[typing.Any]] = set()

    def pub(
            self,
            key: typing.Hashable,
            *args: typing.Any,
            **kwargs: typing.Any
    ) -> None:
        if key not in self._bus:
            return

        for action in self._bus[key]:
            task = asyncio.create_task(action(*args, **kwargs))
            self._running_handlers.add(task)
            task.add_done_callback(self._running_handlers.discard)

    def sub(
            self,
            key: typing.Hashable,
            action: typing.Callable[[typing.Any], typing.Awaitable[typing.Any]]
    ) -> None:
        self._bus[key].append(action)

    async def await_running_handlers(self) -> None:
        await asyncio.gather(*list(self._running_handlers))


@functools.cache
def get_bus(name: str = 'default') -> EventBus:
    return EventBus()
