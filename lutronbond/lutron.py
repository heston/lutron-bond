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
    ANY = 1
    BTN_1 = 2
    BTN_2 = 3
    BTN_3 = 4
    BTN_RAISE = 5
    BTN_LOWER = 6
    BTN_SCENE_1 = 8
    BTN_SCENE_2 = 9
    BTN_SCENE_3 = 10
    BTN_SCENE_4 = 11
    UNKNOWN = -1


class Action(enum.Enum):
    pass


class DeviceAction(Action):
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


class OutputAction(Action):
    SET_LEVEL = 1
    START_RAISING = 2
    START_LOWERING = 3
    STOP_RAISING_OR_LOWERING = 4
    UNKNOWN = -1
    # Additional actions available, but omitted


class LutronEvent:
    PREFIX = '~'

    def __init__(
            self,
            operation: Operation,
            device: int,
            component: Component,
            action: Action,
            parameters: str,
            bridge: str):
        self.operation = operation
        self.device = device
        self.component = component
        self.action = action
        self.parameters = parameters
        self.bridge = bridge

    @classmethod
    def parse(cls, raw: bytes, bridge: str) -> LutronEvent:  # noqa: C901
        logger.debug('Parsing: %s', raw)

        # Just good practice
        raw = raw.strip()

        # The first message after a command was sent will include the
        # ready prompt. We can safely remove it.
        if raw.startswith(READY_PROMPT):
            raw = raw[len(READY_PROMPT):]

        # ~OUTPUT,16,2,3
        if not raw.startswith(cls.PREFIX.encode('ascii')):
            # This is not an event we recognize
            raise ValueError('Unrecognized event: {!r}'.format(raw))

        # Consume leading ~
        raw = raw[1:]
        parts = raw.split(b',')

        try:
            operation = parts[0].decode()
            device = int(parts[1])
            component = int(parts[2])
            action = parts[3]
        except IndexError:
            raise ValueError('Invalid event format: {!r}'.format(raw))

        try:
            operation_enum = Operation(operation)
        except ValueError:
            operation_enum = Operation.UNKNOWN

        if operation_enum is Operation.OUTPUT:
            component_enum = Component.ANY

            try:
                action_enum: Action = OutputAction(component)
            except ValueError:
                action_enum = OutputAction.UNKNOWN

            parameters = action.decode()
        else:
            try:
                component_enum = Component(component)
            except ValueError:
                component_enum = Component.UNKNOWN

            try:
                action_enum = DeviceAction(float(action))
            except ValueError:
                action_enum = DeviceAction.UNKNOWN

            try:
                parameters = parts[4].decode()
            except IndexError:
                parameters = ""

        return cls(operation_enum, device, component_enum, action_enum, parameters, bridge)

    def __repr__(self) -> str:
        return (
            '{}('
            'operation={}, device={}, component={}, action={}, parameters={}, bridge={}'
            ')'.format(
                self.__class__.__name__,
                self.operation,
                self.device,
                self.component,
                self.action,
                self.parameters or None,
                self.bridge
            )
        )

    def __str__(self) -> str:
        return (
            '{}(BRIDGE:{} {}:{} {}:{}:{})'.format(
                self.__class__.__name__,
                self.bridge,
                self.operation.name,
                self.device,
                self.component.name,
                self.action.name,
                self.parameters or None
            )
        )


class LutronCommand(LutronEvent):
    PREFIX = '#'

    def __str__(self) -> str:
        """Formatted like #OUTPUT,1,1,75,01:30<CR><LF>"""

        if self.action.__class__ is OutputAction:
            return "{}{},{},{},{}\r\n".format(
                self.PREFIX,
                Operation.OUTPUT.value,
                self.device,
                self.action.value,
                self.parameters
            )
        elif self.action.__class__ is DeviceAction:
            return "{}{},{},{},{}\r\n".format(
                self.PREFIX,
                Operation.DEVICE.value,
                self.device,
                self.component.value,
                self.action.value
            )
        else:
            raise ValueError("Unknown Action subclass: {}".format(self.action.__class__))


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

    async def send(self, command: LutronCommand) -> None:
        if not self.is_connected:
            raise RuntimeError('Socket not connected')

        if not self.is_logged_in:
            raise RuntimeError('Not logged in')

        if self.host != command.bridge:
            raise ValueError("Intended bridge does not match this connection")

        self._writer.write(str(command).encode('ascii'))
        await self._writer.drain()


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


def get_handler(  # noqa: C901
        configmap: dict
) -> typing.Callable[[LutronEvent], typing.Awaitable[bool]]:

    actions = configmap['actions']

    if 'bridge' not in configmap:
        bridge_addr = config.LUTRON_BRIDGE_ADDR
    else:
        if configmap['bridge'] == 1:
            bridge_addr = config.LUTRON_BRIDGE_ADDR
        elif configmap['bridge'] == 2:
            bridge_addr = config.LUTRON_BRIDGE2_ADDR
        else:
            raise ValueError('Unknown Lutron bridge: {}'.format(configmap['bridge']))

    integration_id = configmap['id']

    async def handler(event: LutronEvent) -> bool:
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

        arg = None
        if isinstance(action, dict):
            action, arg = list(action.items())[0]
        else:
            raise ValueError('Invalid action declaration: {}'.format(action))

        # There are 4 cases that must be parsed slightly differently:
        #
        #    [Incoming Event]
        #    DEVICE     OUTPUT
        # +----------+----------+
        # |  Case 1  +  Case 2  | DEVICE
        # +----------+----------+        [Outgoing Action]
        # |  Case 3  |  Case 4  | OUTPUT
        # +----------+----------+
        #
        try:
            # Cases 1 and 3 handle DEVICE events
            #
            # [Case 3]
            # Check if this is a DEVICE event with an OUTPUT action
            lutron_action: Action = OutputAction[action]
            lutron_component = Component.ANY
            lutron_parameters = arg
            lutron_operation = Operation.OUTPUT
        except KeyError:
            # [Case 1]
            # That failed, so check if this is a DEVICE event with a DEVICE action
            try:
                lutron_component = Component[action]
                lutron_action = DeviceAction[arg]
                lutron_parameters = ""
                lutron_operation = Operation.DEVICE
            except KeyError:
                # Cases 1 and 3 failed, so maybe this is an OUTPUT event
                if not event.parameters:
                    # This isn't an OUTPUT event since all OUTPUT events have a parameter
                    raise RuntimeError('Unknown action encountered: {}'.format(action))

                # Cases 2 and 4 handle OUTPUT events
                #
                # [Case 4]
                # Check if this is an OUTPUT event with an OUTPUT action
                try:
                    try:
                        action_spec = component[event.action.name][event.parameters]
                    except KeyError:
                        logger.warning(
                            'Action not specified in config: %s:%s',
                            event.action,
                            event.parameters
                        )
                        return False

                    action, arg = list(action_spec.items())[0]

                    lutron_action = OutputAction[action]
                    lutron_component = Component.ANY
                    lutron_parameters = arg
                    lutron_operation = Operation.OUTPUT
                except KeyError:
                    # [Case 2]
                    # That failed, so check if this is an OUTPUT event with a DEVICE action
                    try:
                        lutron_component = Component[action]
                        lutron_action = DeviceAction[arg]
                        lutron_parameters = ""
                        lutron_operation = Operation.DEVICE
                    except KeyError as e:
                        # We shouldn't ever get here
                        raise RuntimeError('Unknown error encountered: {!r}'.format(e))

        lutron_command = LutronCommand(
            lutron_operation,
            integration_id,
            lutron_component,
            lutron_action,
            lutron_parameters,
            bridge_addr
        )

        logger.debug(
            'Translated event into Lutron command: %s', lutron_command
        )

        await get_lutron_connection(bridge_addr).send(lutron_command)
        return True

    return handler


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
