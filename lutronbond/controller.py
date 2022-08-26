import functools
import logging

from . import eventbus
from . import lutron

EVENT_CATEGORY = 'OUTPUT'

logging.basicConfig(
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


@functools.cache
def get_bus():
    return eventbus.EventBus()


def handler(lutron_event):
    logger.debug('Got event: %s', lutron_event)

    if lutron_event.category != EVENT_CATEGORY:
        return

    get_bus().pub(
        lutron_event.device,
        command=lutron_event.command,
        value=lutron_event.value
    )


async def main():
    c = lutron.LutronConnection('192.168.86.247', 23)
    await c.open()

    try:
        await c.stream(handler)
    except KeyboardInterrupt:
        await c.close()
