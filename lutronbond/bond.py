import asyncio
import functools
import logging
import pprint
import typing

import bond_async  # type: ignore

from . import config
from . import lutron


logger = logging.getLogger(__name__)


@functools.cache
def get_bond_connection(host: str, api_token: str) -> bond_async.Bond:
    return bond_async.Bond(host, api_token)


def get_default_bond_connection() -> bond_async.Bond:
    return get_bond_connection(
        config.BOND_BRIDGE_ADDR,
        config.BOND_BRIDGE_API_TOKEN
    )


def get_handler(
        config: dict
) -> typing.Callable[[lutron.LutronEvent], typing.Awaitable[bool]]:
    async def handler(event: lutron.LutronEvent) -> bool:
        actions = config['actions']

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

        await get_default_bond_connection().action(
            config['bondID'],
            bond_action
        )

        logger.info(
            '%s request sent to Bond Bridge %s',
            action,
            config['bondID']
        )
        return True

    return handler


async def verify_connection() -> None:
    logger.debug('Verifying Bond Bridge connection...')
    result = await get_default_bond_connection().version()
    logger.info(
        'Connected to Bond Bridge. Model {model}. Version {fw_ver}'.format(
            **result
        )
    )


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
