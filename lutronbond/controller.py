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
        '{}:{}'.format(lutron_event.bridge, lutron_event.device),
        lutron_event
    )


def add_listeners() -> None:
    for lutron_id, subconfig in config.LUTRON_BOND_MAPPING.items():
        logger.debug(
            'Subscribing to %s:%s -> %s',
            config.LUTRON_BRIDGE_ADDR, lutron_id, subconfig
        )
        eventbus.get_bus().sub(
            '{}:{}'.format(config.LUTRON_BRIDGE_ADDR, lutron_id),
            bond.get_handler(subconfig)
        )

    if getattr(config, 'LUTRON_BRIDGE2_ADDR', None) and getattr(config, 'LUTRON2_BOND_MAPPING', None):
        for lutron_id, subconfig in config.LUTRON2_BOND_MAPPING.items():
            logger.debug(
                'Subscribing to %s:%s -> %s',
                config.LUTRON_BRIDGE2_ADDR, lutron_id, subconfig
            )
            eventbus.get_bus().sub(
                '{}:{}'.format(config.LUTRON_BRIDGE2_ADDR, lutron_id),
                bond.get_handler(subconfig)
            )


shutting_down: bool = False


async def shutdown() -> None:
    global shutting_down
    shutting_down = True
    for c in lutron.connections:
        await c.close()
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

    lutron.get_default_lutron_connection()

    if (config.LUTRON_BRIDGE2_ADDR):
        lutron.get_lutron_connection(config.LUTRON_BRIDGE2_ADDR)

    while not shutting_down:
        try:
            if all(await asyncio.gather(*[c.open() for c in lutron.connections])):
                await asyncio.gather(*[c.stream(handler) for c in lutron.connections])
            else:
                return
        except asyncio.exceptions.IncompleteReadError:
            if not shutting_down:
                logger.warning('Connection closed unexpectedly. Retrying...')
        finally:
            cancel_bond_keepalive()
            await asyncio.gather(*[c.close() for c in lutron.connections])

    lutron.reset_connection_cache()


if __name__ == '__main__':
    asyncio.run(start())
