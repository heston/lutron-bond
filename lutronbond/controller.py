import asyncio
import logging
import signal

from . import bond
from . import config
from . import eventbus
from . import lutron


EVENT_OPERATION: lutron.Operation = lutron.Operation.DEVICE

logger = logging.getLogger(__name__)


async def handler(lutron_event: lutron.LutronEvent) -> None:
    if lutron_event.operation != EVENT_OPERATION:
        logger.debug('Skipping Lutron event: %s', lutron_event)
        return

    logger.info('Handling Lutron event: %s', lutron_event)

    await eventbus.get_bus().pub(
        lutron_event.device,
        lutron_event
    )


def add_listeners() -> None:
    for lutron_id, subconfig in config.LUTRON_BOND_MAPPING.items():
        logger.debug('Subscribing to %s: %s', lutron_id, subconfig)
        eventbus.get_bus().sub(
            lutron_id,
            bond.get_handler(subconfig)
        )


shutting_down: bool = False


async def shutdown() -> None:
    global shutting_down
    shutting_down = True
    await lutron.get_default_lutron_connection().close()
    logger.info('Exiting...')


async def start() -> None:
    logger.info('Starting up...')
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: loop.create_task(shutdown())
    )

    await bond.verify_connection()
    cancel_bond_keepalive = bond.keepalive()

    add_listeners()

    c = lutron.get_default_lutron_connection()

    while not shutting_down:
        try:
            if await c.open():
                await c.stream(handler)
            else:
                return
        except asyncio.exceptions.IncompleteReadError:
            if not shutting_down:
                logger.warning('Connection closed unexpectedly. Retrying...')
        finally:
            cancel_bond_keepalive()
            await c.close()


if __name__ == '__main__':
    asyncio.run(start())
