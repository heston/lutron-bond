import functools
import logging
import time

from . import config
from . import eventbus
from . import lutron

logger = logging.getLogger(__name__)


class EventSynthesizer:
    def __init__(self) -> None:
        self.last_press_times: dict[str, float] = {}

    def process(self, event: lutron.LutronEvent) -> None:
        if event.operation == lutron.Operation.DEVICE and event.action == lutron.DeviceAction.PRESS:
            key = f"{event.bridge}:{event.device}:{event.component.name}"
            now = time.time()
            last_press = self.last_press_times.get(key, 0.0)

            if now - last_press <= config.DOUBLE_TAP_WINDOW:
                logger.debug("Synthesizing DBLTAP for %s", key)
                self.last_press_times[key] = 0.0
                
                synthesized_event = lutron.LutronEvent(
                    operation=event.operation,
                    device=event.device,
                    component=event.component,
                    action=lutron.DeviceAction.DBLTAP,
                    parameters=event.parameters,
                    bridge=event.bridge
                )
                
                eventbus_key = f"{event.bridge}:{event.device}"
                eventbus.get_bus().pub(eventbus_key, synthesized_event)
            else:
                self.last_press_times[key] = now


@functools.cache
def get_synthesizer(name: str = 'default') -> EventSynthesizer:
    return EventSynthesizer()
