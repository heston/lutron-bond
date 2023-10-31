import asyncio
import logging
import signal
import typing

from . import bond
from . import config
from . import eventbus
from . import lutron
from . import tuya


EVENT_OPERATION: list[lutron.Operation] = [
    lutron.Operation.DEVICE,
    lutron.Operation.OUTPUT,
]

logger = logging.getLogger(__name__)


def handler(lutron_event: lutron.LutronEvent) -> None:
    if lutron_event.operation not in EVENT_OPERATION:
        logger.debug('Skipping Lutron event: %s', lutron_event)
        return

    logger.info('Handling Lutron event: %s', lutron_event)

    eventbus.get_bus().pub(
        '{}:{}'.format(lutron_event.bridge, lutron_event.device),
        lutron_event
    )


def add_listeners_for_bridge(bridge_addr: str, config_map: typing.Dict) -> None:
    for lutron_id, subconfig in config_map.items():
        logger.debug(
            'Subscribing to %s:%s -> %s',
            bridge_addr, lutron_id, subconfig
        )

        key = '{}:{}'.format(bridge_addr, lutron_id)

        if 'bond' in subconfig:
            if type(subconfig['bond']) is list:
                for config_item in subconfig['bond']:
                    eventbus.get_bus().sub(key, bond.get_handler(config_item))
            else:
                eventbus.get_bus().sub(key, bond.get_handler(subconfig['bond']))

        if 'tuya' in subconfig:
            if type(subconfig['tuya']) is list:
                for config_item in subconfig['tuya']:
                    eventbus.get_bus().sub(key, tuya.get_handler(config_item))
            else:
                eventbus.get_bus().sub(key, tuya.get_handler(subconfig['tuya']))


def add_listeners() -> None:
    add_listeners_for_bridge(config.LUTRON_BRIDGE_ADDR, config.LUTRON_MAPPING)

    if (
            getattr(config, 'LUTRON_BRIDGE2_ADDR', None) and
            getattr(config, 'LUTRON2_MAPPING', None)
    ):
        add_listeners_for_bridge(config.LUTRON_BRIDGE2_ADDR, config.LUTRON2_MAPPING)


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

    if (getattr(config, 'LUTRON_BRIDGE2_ADDR', None)):
        lutron.get_lutron_connection(config.LUTRON_BRIDGE2_ADDR)

    while not shutting_down:
        try:
            if all(await asyncio.gather(*[c.open() for c in lutron.connections])):
                await asyncio.gather(*[c.stream(handler) for c in lutron.connections])
            else:
                break
        except asyncio.exceptions.IncompleteReadError:
            if not shutting_down:
                logger.warning('Connection closed unexpectedly. Retrying...')
        finally:
            await asyncio.gather(*[c.close() for c in lutron.connections])

    cancel_bond_keepalive()
    lutron.reset_connection_cache()


if __name__ == '__main__':
    asyncio.run(start())
