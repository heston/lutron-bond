from collections import defaultdict
import functools


class EventBus:
    def __init__(self):
        self._bus = defaultdict(list)

    async def pub(self, key, *args, **kwargs):
        if key not in self._bus:
            return

        for action in self._bus[key]:
            await action(*args, **kwargs)

    def sub(self, key, action: callable):
        self._bus[key].append(action)


@functools.cache
def get_bus(name='default'):
    return EventBus()
