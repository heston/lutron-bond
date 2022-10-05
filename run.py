import asyncio
import logging

from lutronbond import config, controller


logging.basicConfig(
    level=config.LOG_LEVEL
)


asyncio.run(controller.start())
