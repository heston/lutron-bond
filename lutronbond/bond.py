import asyncio
import functools
import logging
import pprint
import typing

import aiohttp
import backoff
import bond_async  # type: ignore

from . import config
from . import lutron


logger = logging.getLogger(__name__)
logging.getLogger('backoff').addHandler(logging.StreamHandler())


@functools.cache
def get_bond_connection(host: str, api_token: str) -> bond_async.Bond:
    return bond_async.Bond(host, api_token)


def get_default_bond_connection() -> bond_async.Bond:
    return get_bond_connection(
        config.BOND_BRIDGE_ADDR,
        config.BOND_BRIDGE_API_TOKEN
    )


def get_handler(
        configmap: dict
) -> typing.Callable[[lutron.LutronEvent], typing.Awaitable[bool]]:

    bond_config = configmap['bond']
    actions = bond_config['actions']

    async def handler(event: lutron.LutronEvent) -> bool:
        try:
            component = actions[event.component.name]
        except KeyError:
            logger.warning('Unknown component: %s', event.component)
            return False

        try:
            action = component[event.action.name]
        except KeyError:
            logger.warning('Unknown action: %s', event.action)
            return False

        if action is None:
            return False

        arg = None
        if isinstance(action, dict):
            action, arg = list(action.items())[0]

        bond_action = bond_async.action.Action(action, argument=arg)

        logger.debug(
            'Translated event into bond action: %s with argument: %s',
            bond_action,
            arg
        )

        @backoff.on_exception(
            backoff.expo,
            aiohttp.client_exceptions.ClientConnectorError,
            max_tries=config.BOND_RETRY_COUNT,
            jitter=backoff.full_jitter
        )
        async def do_action() -> bool:
            logger.debug(
                'Starting %s request to Bond Bridge %s',
                action,
                bond_config['id']
            )
            await get_default_bond_connection().action(
                bond_config['id'],
                bond_action
            )
            logger.info(
                '%s for %s request sent to Bond Bridge %s',
                action,
                configmap.get('name', 'Unnamed'),
                bond_config['id']
            )
            return True

        try:
            return await do_action()
        except aiohttp.client_exceptions.ClientConnectorError:
            return False

    return handler


async def verify_connection() -> None:
    logger.debug('Verifying Bond Bridge connection...')
    result = await get_default_bond_connection().version()
    logger.info(
        'Connected to Bond Bridge. Model {model}. Version {fw_ver}'.format(
            **result
        )
    )


def keepalive() -> typing.Callable:
    if config.BOND_KEEPALIVE_INTERVAL == 0:
        return lambda: True

    async def poll() -> None:
        while True:
            await asyncio.sleep(config.BOND_KEEPALIVE_INTERVAL)
            logger.debug('Starting Bond keepalive check')
            await get_default_bond_connection().version()
            logger.debug('Bond keepalive check successful')

    loop = asyncio.get_event_loop()
    task = loop.create_task(poll())

    return lambda: task.cancel()


async def main() -> None:
    """Example of library usage."""

    bond = get_default_bond_connection()

    print("\nVersion:")
    print(await bond.version())

    print("\nDevice IDs:")
    device_ids = await bond.devices()
    pprint.pprint(device_ids)

    print("\nDevices:")
    devices = await asyncio.gather(
        *[bond.device(device_id) for device_id in device_ids]
    )
    pprint.pprint(dict(zip(device_ids, devices)))
    device_names = [device['name'] for device in devices]

    print("\nDevices Properties:")
    properties = await asyncio.gather(
        *[bond.device_properties(device_id) for device_id in device_ids]
    )
    pprint.pprint(dict(zip(device_names, properties)))

    print("\nDevices State:")
    state = await asyncio.gather(
        *[bond.device_state(device_id) for device_id in device_ids]
    )
    pprint.pprint(dict(zip(device_names, state)))


if __name__ == '__main__':
    asyncio.run(main())
