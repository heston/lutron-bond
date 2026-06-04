import asyncio
import functools
import logging
import typing

from aiohue import HueBridgeV2

from . import config, lutron

logger = logging.getLogger(__name__)


@functools.cache
def get_bridge() -> HueBridgeV2:
    if not config.HUE_BRIDGE_ADDR or not config.HUE_APP_KEY:
        raise ValueError("Hue bridge configuration is missing")
    return HueBridgeV2(config.HUE_BRIDGE_ADDR, config.HUE_APP_KEY)


async def setup() -> None:
    bridge = get_bridge()
    await bridge.initialize()
    logger.info("Connected to Hue Bridge %s at %s", bridge.bridge_id, config.HUE_BRIDGE_ADDR)


async def shutdown() -> None:
    try:
        bridge = get_bridge()
        logger.info("Closing connection to Hue Bridge %s at %s", bridge.bridge_id, config.HUE_BRIDGE_ADDR)
        await bridge.close()
    except ValueError:
        pass

    get_bridge.cache_clear()


def get_handler(  # noqa: C901
        configmap: dict
) -> typing.Callable[[lutron.LutronEvent], typing.Awaitable[bool]]:

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

        if event.is_output_event:
            try:
                action = action[event.parameters]
            except KeyError:
                logger.warning('Unknown action: %s:%s', event.component.name, event.parameters)
                return False

        bridge = get_bridge()

        if isinstance(action, dict):
            method_name, kwargs = list(action.items())[0]
            if not isinstance(kwargs, dict):
                # Fallback if someone configures action like {'TurnOn': None}
                kwargs = {}
        else:
            method_name = action
            kwargs = {}

        try:
            method = getattr(bridge.lights, method_name)
        except AttributeError:
            logger.warning('Unknown Hue device method: %s', method_name)
            return False

        logger.debug(
            'Starting %s request to Hue device %s with args %s',
            method_name,
            configmap['id'],
            kwargs
        )

        try:
            await method(configmap['id'], **kwargs)
            logger.info(
                '%s request sent to Hue device %s (%s)',
                method_name,
                configmap['id'],
                configmap.get('name', 'Unnamed')
            )
            return True
        except Exception as e:
            logger.error(
                '%s request to Hue device %s (%s) failed: %s',
                method_name,
                configmap['id'],
                configmap.get('name', 'Unnamed'),
                e
            )
            return False

    return handler


async def main() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL
    )

    if not config.HUE_BRIDGE_ADDR:
        logger.error("No bridge configured")
        return

    bridge = HueBridgeV2(config.HUE_BRIDGE_ADDR, config.HUE_APP_KEY)
    await bridge.initialize()

    logger.info("Connected to bridge: %s at address %s", bridge.bridge_id, config.HUE_BRIDGE_ADDR)
    logger.info("Found devices:")
    
    try:
        for item in bridge.devices:
            logger.info("Device: name=%s id=%s", item.metadata.name, item.id)
    
        for light in bridge.lights.items:
            logger.info("Light: id=%s metadata=%s", light.id, getattr(light, 'metadata', None))
    except Exception as e:
        logger.exception("Error: %s", e)

    await bridge.close()


if __name__ == '__main__':
    asyncio.run(main())
