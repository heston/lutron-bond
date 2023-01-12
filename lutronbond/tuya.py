import asyncio
import logging
import typing

import tinytuya  # type: ignore

from . import config, lutron


logger = logging.getLogger(__name__)

ACTIONS = {
    'TurnOn': 'turn_on',
    'TurnOff': 'turn_off',
}


def get_handler(
        configmap: dict
) -> typing.Callable[[lutron.LutronEvent], typing.Awaitable[bool]]:

    try:
        device = tinytuya.OutletDevice(
            dev_id=configmap['id'],
            address=configmap['addr'],
            local_key=configmap['key'],
            version=configmap['version']
        )
    except KeyError:
        logger.error('Invalid Tuya device: %s', configmap)
        raise

    device.set_socketRetryLimit(config.TUYA_RETRY_COUNT)
    device.set_socketTimeout(config.TUYA_CONNECTION_TIMEOUT)

    actions = configmap['actions']

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

        try:
            method_name = ACTIONS[action]
        except KeyError:
            logger.warning('Unknown device method: %s', action)
            return False

        method = getattr(device, method_name)

        def do_action() -> bool:
            method()
            logger.info(
                '%s request sent to Tuya device %s (%s)',
                action,
                configmap['id'],
                configmap.get('name', 'Unnamed')
            )

            return True

        logger.debug(
            'Starting %s request to Tuya device %s',
            action,
            configmap['id']
        )
        return await asyncio.to_thread(do_action)

    return handler
