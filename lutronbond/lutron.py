from __future__ import annotations
import asyncio
import enum
import functools
import logging
import signal
import typing

from . import config


LOGIN_PROMPT = b'login: '
PASSWORD_PROMPT = b'password: '
READY_PROMPT = b'GNET> '
USERNAME = b'lutron'
PASSWORD = b'integration'
LINE_TERM = b'\r\n'

logger = logging.getLogger(__name__)


class Operation(enum.Enum):
    DEVICE = 'DEVICE'
    OUTPUT = 'OUTPUT'
    UNKNOWN = '?'


class Component(enum.Enum):
    BTN_1 = 2
    BTN_2 = 3
    BTN_3 = 4
    BTN_RAISE = 5
    BTN_LOWER = 6
    UNKNOWN = -1


class Action(enum.Enum):
    ENABLE = 1
    DISABLE = 2
    PRESS = 3
    RELEASE = 4
    HOLD = 5
    DBLTAP = 6
    SCENE = 7
    LED = 9
    LEVEL = 14
    UNKNOWN = -1


class LutronEvent:

    def __init__(
            self,
            operation: Operation,
            device: int,
            component: Component,
            action: Action,
            bridge: str):
        self.operation = operation
        self.device = device
        self.component = component
        self.action = action
        self.bridge = bridge

    @classmethod
    def parse(cls, raw: bytes, bridge: str) -> LutronEvent:
        logger.debug('Parsing: %s', raw)

        # ~OUTPUT,16,2,3
        if not raw.startswith(b'~'):
            raise ValueError('Unrecognized event: {!r}'.format(raw))

        # Consume leading ~
        raw = raw.strip()[1:]
        parts = raw.split(b',')
        try:
            operation = parts[0].decode()
            device = int(parts[1])
            component = int(parts[2])
            action = float(parts[3])
        except IndexError:
            raise ValueError('Invalid event format: {!r}'.format(raw))

        try:
            operation_enum = Operation(operation)
        except ValueError:
            operation_enum = Operation.UNKNOWN

        try:
            component_enum = Component(component)
        except ValueError:
            component_enum = Component.UNKNOWN

        try:
            action_enum = Action(action)
        except ValueError:
            action_enum = Action.UNKNOWN

        return cls(operation_enum, device, component_enum, action_enum, bridge)

    def __repr__(self) -> str:
        return (
            'LutronEvent('
            'operation={}, device={}, component={}, action={}, bridge={}'
            ')'.format(
                self.operation, self.device, self.component, self.action, self.bridge
            )
        )

    def __str__(self) -> str:
        return (
            'LutronEvent(BRIDGE:{} {}:{} {}:{})'.format(
                self.bridge,
                self.operation.name,
                self.device,
                self.component.name,
                self.action.name
            )
        )


class LutronConnection:

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.is_connected: bool = False
        self.is_logged_in: bool = False
        self._reader: asyncio.StreamReader
        self._writer: asyncio.StreamWriter
        self.logger = logger.getChild('LutronConnection<{}>'.format(self.host))

    async def connect(self) -> bool:
        self.logger.debug(
            'Establishing connection to Lutron bridge at %s:%s',
            self.host,
            self.port
        )

        self._reader, self._writer = await asyncio.open_connection(
            self.host,
            self.port
        )
        self.is_connected = True
        self.logger.info('Connected to Lutron Bridge')
        return True

    async def close(self) -> bool:
        if not self.is_connected:
            return False

        self.logger.info('Closing connection...')
        self._writer.close()
        await self._writer.wait_closed()
        self.logger.info('Connection closed')
        self.is_connected = False
        self.is_logged_in = False
        return True

    async def login(self) -> bool:
        if not self.is_connected:
            raise RuntimeError('Socket not connected')

        if self.is_logged_in:
            self.logger.debug('Already logged in!')
            return True

        tries = 5
        self.logger.debug('Starting login...')

        while not self.is_logged_in and tries:
            tries = tries - 1
            data = await self._reader.read(32)

            if data.startswith(LOGIN_PROMPT):
                self.logger.debug('Sending username')
                self._writer.write(USERNAME)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(PASSWORD_PROMPT):
                self.logger.debug('Sending password')
                self._writer.write(PASSWORD)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(READY_PROMPT):
                self.logger.debug('Login successful!')
                self.is_logged_in = True

            return True

        self.logger.error('Unable to log in')
        return False

    async def open(self) -> bool:
        await self.connect()
        return await self.login()

    async def stream(
            self,
            callback: typing.Callable[[LutronEvent], None]
    ) -> None:
        self.logger.info('Listening for events...')

        while self.is_logged_in and self.is_connected:
            data = await self._reader.readuntil(LINE_TERM)
            self.logger.debug('Got data: %s', data)

            try:
                evt = LutronEvent.parse(data, self.host)
            except ValueError as e:
                self.logger.error('Error parsing event: %s', e)
                continue
            else:
                callback(evt)


connections: typing.List[LutronConnection] = []


@functools.cache
def get_lutron_connection(host: str) -> LutronConnection:
    c = LutronConnection(host, 23)
    connections.append(c)
    return c


def get_default_lutron_connection() -> LutronConnection:
    return get_lutron_connection(config.LUTRON_BRIDGE_ADDR)


def reset_connection_cache() -> None:
    connections.clear()
    get_lutron_connection.cache_clear()


async def main() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL
    )

    async def shutdown() -> None:
        for c in connections:
            await c.close()
        logger.info('Exiting...')

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: loop.create_task(shutdown())
    )

    def print_event(evt: LutronEvent) -> None:
        print(evt)

    get_lutron_connection(config.LUTRON_BRIDGE_ADDR)

    if getattr(config, 'LUTRON_BRIDGE2_ADDR', None):
        get_lutron_connection(config.LUTRON_BRIDGE2_ADDR)

    if all(await asyncio.gather(*[c.open() for c in connections])):
        try:
            await asyncio.gather(*[c.stream(print_event) for c in connections])
        except asyncio.exceptions.IncompleteReadError:
            pass

    reset_connection_cache()


if __name__ == '__main__':
    asyncio.run(main())
