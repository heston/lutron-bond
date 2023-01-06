import logging
import typing

import tinytuya  # type: ignore

from . import lutron


logger = logging.getLogger(__name__)

ACTIONS = {
    'TurnOn': 'turn_on',
    'TurnOff': 'turn_off',
}


def get_handler(
        configmap: dict
) -> typing.Callable[[lutron.LutronEvent], typing.Awaitable[bool]]:

    async def handler(event: lutron.LutronEvent) -> bool:
        actions = configmap['actions']
        tuya_config = configmap['tuya']

        try:
            device = tinytuya.OutletDevice(
                dev_id=tuya_config['id'],
                address=tuya_config['addr'],
                local_key=tuya_config['localKey'],
                version=tuya_config['version']
            )
        except KeyError:
            logger.error('Invalid Tuya device: %s', tuya_config)
            return False

        try:
            component = actions[event.component.name]
        except KeyError:
            logger.warning('Unknown component: %s', event.component)
            return False

        try:
            action = component[event.action.name]
            method_name = ACTIONS[action]
            method = getattr(device, method_name)
        except KeyError:
            logger.warning('Unknown action: %s', event.action)
            return False

        logger.debug(
            'Starting %s request to Tuya device %s',
            action,
            tuya_config['id']
        )
        method()
        logger.info(
            '%s request sent to Tuya device %s',
            action,
            tuya_config['id']
        )
        return True

    return handler
