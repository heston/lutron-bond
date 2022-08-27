import asyncio
import enum
import functools
import logging

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

    def __init__(self, operation, device, component, action):
        self.operation = operation
        self.device = device
        self.component = component
        self.action = action

    @classmethod
    def parse(cls, raw):
        logger.debug('Parsing: %s', raw)

        # ~OUTPUT,16,1,0.00
        if not raw.startswith(b'~'):
            raise ValueError('Unrecognized event: {}'.format(raw))

        # Consume leading ~
        raw = raw.strip()[1:]
        parts = raw.split(b',')
        try:
            operation = parts[0].decode()
            device = int(parts[1])
            component = int(parts[2])
            action = float(parts[3])
        except IndexError:
            raise ValueError('Invalid event format: {}'.format(raw))

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

        return cls(operation_enum, device, component_enum, action_enum)

    def __repr__(self):
        return (
            'LutronEvent('
            'operation={}, device={}, component={}, action={}'
            ')'.format(
                self.operation, self.device, self.component, self.action
            )
        )

    def __str__(self):
        return (
            'LutronEvent({}:{} {}:{})'.format(
                self.operation.name,
                self.device,
                self.component.name,
                self.action.name
            )
        )


class LutronConnection:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.is_connected = False
        self.is_logged_in = False
        self._reader = None
        self._writer = None

    async def connect(self):
        logger.info(
            'Establishing connection to Lutron bridge at %s:%s',
            self.host,
            self.port
        )

        self._reader, self._writer = await asyncio.open_connection(
            self.host,
            self.port
        )
        self.is_connected = True
        logger.info('Connected!')
        return True

    async def close(self):
        if not self.is_connected:
            return

        logger.info('Closing connection...')
        self._writer.close()
        await self._writer.wait_closed()
        logger.info('Connection closed')
        self.is_connected = False
        self.is_logged_in = False

    async def login(self):
        if not self.is_connected:
            raise RuntimeError('Socket not connected')

        if self.is_logged_in:
            logger.debug('Already logged in!')
            return True

        tries = 5
        logger.debug('Starting login...')

        while not self.is_logged_in and tries:
            tries = tries - 1
            data = await self._reader.read(32)

            if data.startswith(LOGIN_PROMPT):
                logger.debug('Sending username')
                self._writer.write(USERNAME)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(PASSWORD_PROMPT):
                logger.debug('Sending password')
                self._writer.write(PASSWORD)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(READY_PROMPT):
                logger.info('Login successful!')
                self.is_logged_in = True

            return True

        logger.error('Unable to log in')
        return False

    async def open(self):
        await self.connect()
        return await self.login()

    async def stream(self, callback):
        logger.info('Listening for events...')

        while self.is_logged_in and self.is_connected:
            data = await self._reader.readuntil(LINE_TERM)
            logger.debug('Got data: %s', data)

            try:
                evt = LutronEvent.parse(data)
            except ValueError as e:
                logger.error('Error parsing event: %s', e)
                continue
            else:
                await callback(evt)


@functools.cache
def get_lutron_connection(host):
    return LutronConnection(host, 23)


def get_default_lutron_connection():
    return get_lutron_connection(config.LUTRON_BRIDGE_ADDR)


async def main():
    conn = get_lutron_connection(config.LUTRON_BRIDGE_ADDR)
    await conn.open()
    await conn.stream(lambda e: print(e))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
