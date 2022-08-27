import os


def get_env(name, default=None):
    return os.environ.get(name, default)


LUTRON_BRIDGE_ADDR = get_env('LUTRON_BRIDGE_ADDR', '192.168.86.247')
BOND_BRIDGE_ADDR = get_env('BOND_BRIDGE_ADDR', '192.168.86.60')
BOND_BRIDGE_API_TOKEN = get_env('BOND_BRIDGE_API_TOKEN', '913ca00159de3da0')

FAN_LIGHT_CONFIG = {
    'BTN_1': {
        'PRESS': 'TurnLightOn',
        'RELEASE': None,
    },
    'BTN_2': {
        'PRESS': 'ToggleLight',
        'RELEASE': None,
    },
    'BTN_3': {
        'PRESS': 'TurnLightOff',
        'RELEASE': None,
    },
    'BTN_RAISE': {
        'PRESS': 'StartDimmer',
        'RELEASE': 'Stop',
    },
    'BTN_LOWER': {
        'PRESS': 'StartDimmer',
        'RELEASE': 'Stop',
    }
}

FAN_CONFIG = {
    'BTN_1': {
        'PRESS': {
            'SetSpeed': 2,
        },
        'RELEASE': None,
    },
    'BTN_2': {
        'PRESS': 'ToggleDirection',
        'RELEASE': None,
    },
    'BTN_3': {
        'PRESS': 'TurnOff',
        'RELEASE': None,
    },
    'BTN_RAISE': {
        'PRESS': {
            'SetSpeed': 3,
        },
        'RELEASE': None,
    },
    'BTN_LOWER': {
        'PRESS': {
            'SetSpeed': 1,
        },
        'RELEASE': None,
    }
}

LUTRON_BOND_MAPPING = {
    # Lutron Integration ID->Bond Device
    21: {
        'name': 'Master Bedroom Fan Light',
        'bondID': '6409d2a2',
        'actions': FAN_LIGHT_CONFIG,
    },
    -1: {
        'name': 'Master Bedroom Fan',
        'bondID': '6409d2a2',
        'actions': FAN_CONFIG,
    },
    -2: {
        'name': 'Living Room Fan Light',
        'bondID': '0b965995',
        'action': FAN_LIGHT_CONFIG,
    },
    -3: {
        'name': 'Living Room Fan',
        'bondID': '0b965995',
        'actions': FAN_CONFIG,
    }
}
