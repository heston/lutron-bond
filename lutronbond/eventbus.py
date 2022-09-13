from collections import defaultdict
import functools
import typing


class EventBus:
    def __init__(self) -> None:
        self._bus: defaultdict = defaultdict(list)

    async def pub(
            self,
            key: typing.Hashable,
            *args: typing.Any,
            **kwargs: typing.Any
    ) -> None:
        if key not in self._bus:
            return

        for action in self._bus[key]:
            await action(*args, **kwargs)

    def sub(
            self,
            key: typing.Hashable,
            action: typing.Callable[[typing.Any], typing.Awaitable[typing.Any]]
    ) -> None:
        self._bus[key].append(action)


@functools.cache
def get_bus(name: str = 'default') -> EventBus:
    return EventBus()
