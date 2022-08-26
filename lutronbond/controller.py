import asyncio
import functools
import logging

from . import bond
from . import config
from . import eventbus
from . import lutron

EVENT_OPERATION = lutron.Operation.DEVICE

logging.basicConfig(
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def handler(lutron_event):
    logger.debug('Got event: %s', lutron_event)

    if lutron_event.operation != EVENT_OPERATION:
        logger.debug('Skipping operation: %s', lutron_event.operation)
        return

    logger.debug('Publishing to %s: %s', lutron_event.device, lutron_event)
    await eventbus.get_bus().pub(
        lutron_event.device,
        lutron_event
    )


def add_listeners():
    for lutron_id, subconfig in config.LUTRON_BOND_MAPPING.items():
        logger.debug('Subscribing to %s: %s', lutron_id, subconfig)
        eventbus.get_bus().sub(
            lutron_id,
            bond.get_handler(subconfig)
        )


async def main():
    add_listeners()

    c = lutron.get_lutron_connection(config.LUTRON_BRIDGE_ADDR)
    await c.open()

    try:
        await c.stream(handler)
    except KeyboardInterrupt:
        await c.close()


if __name__ == '__main__':
    asyncio.run(main())
