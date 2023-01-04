import os
from typing import Dict


def get_env(name: str, default: str = '') -> str:
    try:
        result = os.environ[name]
    except KeyError:
        if not len(default):
            raise RuntimeError(
                f'Required configuration not found in environment: {name}. '
                'Please set an environment variable with this name and try '
                'again.'
            )
        else:
            return default
    return result


LUTRON_BRIDGE_ADDR = get_env('LB_LUTRON_BRIDGE_ADDR')
LUTRON_BRIDGE2_ADDR = get_env('LB_LUTRON_BRIDGE2_ADDR', None)
BOND_BRIDGE_ADDR = get_env('LB_BOND_BRIDGE_ADDR')
BOND_BRIDGE_API_TOKEN = get_env('LB_BOND_BRIDGE_API_TOKEN')

BOND_KEEPALIVE_INTERVAL = int(get_env('LB_BOND_KEEPALIVE_INTERVAL', '0'), 10)
BOND_RETRY_COUNT = int(get_env('LB_BOND_RETRY_COUNT', '5'), 10)
LOG_LEVEL = get_env('LB_LOG_LEVEL', 'INFO')

FAN_LIGHT_CONFIG = {
    'BTN_1': {
        'PRESS': 'TurnLightOn',
        'RELEASE': None,
    },
    'BTN_2': {
        'PRESS': 'TurnLightOn',
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

BOND_IDS = {
    'Master Bedroom': '6409d2a2',
    'Living Room': '0b965995',
    'Guest Room': 'cb22812453dceb35',
}

LUTRON_BOND_MAPPING: Dict[int, Dict] = {
    # Lutron Integration ID->Bond Device
    21: {
        'name': 'Master Bedroom Fan Light',
        'bondID': BOND_IDS['Master Bedroom'],
        'actions': FAN_LIGHT_CONFIG,
    },
    71: {
        'name': 'Master Bedroom Fan',
        'bondID': BOND_IDS['Master Bedroom'],
        'actions': FAN_CONFIG,
    },
    72: {
        'name': 'Living Room Fan Light',
        'bondID': BOND_IDS['Living Room'],
        'actions': FAN_LIGHT_CONFIG,
    },
    8: {
        'name': 'Living Room Pico',
        'bondID': BOND_IDS['Living Room'],
        'actions': FAN_LIGHT_CONFIG,
    },
    63: {
        'name': 'Fireplace Pico',
        'bondID': BOND_IDS['Living Room'],
        'actions': FAN_LIGHT_CONFIG
    },
    73: {
        'name': 'Living Room Fan',
        'bondID': BOND_IDS['Living Room'],
        'actions': FAN_CONFIG,
    },
    29: {
        'name': 'Guest Room Fan',
        'bondID': BOND_IDS['Guest Room'],
        'actions': FAN_CONFIG,
    },
    75: {
        'name': 'Guest Room Fan Light',
        'bondID': BOND_IDS['Guest Room'],
        'actions': FAN_LIGHT_CONFIG,
    },
}

LUTRON2_BOND_MAPPING: Dict[int, Dict] = {

}
