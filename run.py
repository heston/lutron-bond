import asyncio
import logging

from lutronbond import controller


logging.basicConfig(
    level=logging.INFO
)


asyncio.run(controller.start())
