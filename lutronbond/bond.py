import asyncio
import functools
import logging
import pprint

import bond_async

from . import config


logger = logging.getLogger(__name__)


@functools.cache
def get_bond_connection(host, api_token):
    return bond_async.Bond(host, api_token)


def get_default_bond_connection():
    return get_bond_connection(
        config.BOND_BRIDGE_ADDR,
        config.BOND_BRIDGE_API_TOKEN
    )


def get_handler(config):
    async def handler(event):
        actions = config['actions']

        try:
            component = actions[event.component.name]
        except KeyError:
            logger.warning('Unknown component: %s', event.component)
            return

        try:
            action = component[event.action.name]
        except KeyError:
            logger.warning('Unknown action: %s', event.action)
            return

        if action is None:
            return

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

    return handler


async def main():
    """Example of library usage."""

    bond = get_bond_connection(
        config.BOND_BRIDGE_ADDR,
        config.BOND_BRIDGE_API_TOKEN
    )

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
