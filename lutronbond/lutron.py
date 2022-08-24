import asyncio

LOGIN_PROMPT = b'login: '
PASSWORD_PROMPT = b'password: '
READY_PROMPT = b'GNET> '
USERNAME = b'lutron'
PASSWORD = b'integration'
LINE_TERM = b'\r\n'


class LutronConnection:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.is_connected = False
        self._reader = None
        self._writer = None
        self.is_logged_in = False

    async def connect(self):
        self._reader, self._writer = await asyncio.open_connection(
            self.host,
            self.port
        )
        self.is_connected = True
        return True

    async def close(self):
        self._writer.close()
        await self._writer.wait_closed()
        self.is_connected = False
        self.is_logged_in = False

    async def login(self):
        if not self.is_connected:
            raise RuntimeError('Socket not connected.')

        if self.is_logged_in:
            return True

        tries = 5

        while not self.is_logged_in and tries:
            tries = tries - 1
            data = await self._reader.read(32)

            if data.startswith(LOGIN_PROMPT):
                self._writer.write(USERNAME)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(PASSWORD_PROMPT):
                self._writer.write(PASSWORD)
                self._writer.write(LINE_TERM)
                await self._writer.drain()
                continue

            if data.startswith(READY_PROMPT):
                self.is_logged_in = True

            return True
        return False

    async def open(self):
        await self.connect()
        await self.login()

    async def stream(self, callback):
        while True:
            data = await self._reader.readuntil(LINE_TERM)
            if callback(data) is False:
                break

def cb(data):
    print(data)
    return False


async def main():
    c = LutronConnection('192.168.86.247', 23)
    await c.open()
    await c.stream(cb)
    await c.close()

