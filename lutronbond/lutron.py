import asyncio
import logging

LOGIN_PROMPT = b'login: '
PASSWORD_PROMPT = b'password: '
READY_PROMPT = b'GNET> '
USERNAME = b'lutron'
PASSWORD = b'integration'
LINE_TERM = b'\r\n'

logger = logging.getLogger(__name__)


class LutronEvent:

    def __init__(self, category, device, command, value):
        self.category = category
        self.device = device
        self.command = command
        self.value = value

    @classmethod
    def parse(cls, raw):
        # ~OUTPUT,16,1,0.00
        if not raw.startswith(b'~'):
            raise ValueError('Unrecognized command: {}'.format(raw))

        # Consume leading ~
        raw = raw.strip()[1:]
        parts = raw.split(b',')
        try:
            category = parts[0]
            device = int(parts[1])
            command = int(parts[2])
            value = float(parts[3])
        except IndexError:
            raise ValueError('Invalid command format: {}'.format(raw))

        return cls(category, device, command, value)

    def __repr__(self):
        return (
            'LutronEvent('
            'category={}, device={}, command={}, value={}'
            ')'.format(
                self.category, self.device, self.command, self.value
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
        logger.debug(
            'Establishing connection to Lutron bridge at %s:%s',
            self.host,
            self.port
        )

        self._reader, self._writer = await asyncio.open_connection(
            self.host,
            self.port
        )
        self.is_connected = True
        logger.debug('Connected!')
        return True

    async def close(self):
        logger.debug('Closing connection...')
        self._writer.close()
        await self._writer.wait_closed()
        logger.debug('Connection closed')
        self.is_connected = False
        self.is_logged_in = False

    async def login(self):
        if not self.is_connected:
            raise RuntimeError('Socket not connected')

        if self.is_logged_in:
            logger.debug('Already logged in!')
            return True

        tries = 5

        while not self.is_logged_in and tries:
            tries = tries - 1
            logger.debug('Starting login. Tries remaining: %s', tries)
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
                logger.debug('Login successful!')
                self.is_logged_in = True

            return True
        return False

    async def open(self):
        await self.connect()
        await self.login()

    async def stream(self, callback):
        while True:
            logger.debug('Listening for events...')
            data = await self._reader.readuntil(LINE_TERM)
            logger.debug('Got data: %s', data)
            try:
                evt = LutronEvent.parse(data)
            except ValueError as e:
                logger.error('Error parsing event: %s', e)
                continue
            else:
                callback(evt)
