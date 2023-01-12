import os
from typing import Dict


def get_env(name: str, default: str = '') -> str:
    try:
        result = os.environ[name]
    except KeyError:
        if not len(default):
            raise ValueError(
                f'Required configuration not found in environment: {name}. '
                'Please set an environment variable with this name and try '
                'again.'
            )
        else:
            return default
    return result


LUTRON_BRIDGE_ADDR = get_env('LB_LUTRON_BRIDGE_ADDR')

try:
    LUTRON_BRIDGE2_ADDR = get_env('LB_LUTRON_BRIDGE2_ADDR')
except ValueError:
    pass

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

SMART_SWITCH_ACTIONS = {
    'BTN_1': {
        'PRESS': 'TurnOn',
        'RELEASE': None,
    },
    'BTN_3': {
        'PRESS': 'TurnOff',
        'RELEASE': None
    },
}

LUTRON_MAPPING: Dict[int, Dict] = {
    # Lutron Integration ID->Bond/Tuya Device
    21: {
        'name': 'Master Bedroom Fan Light Pico',
        'bond': {
            'name': 'Master Bedroom Fan Light',
            'id': BOND_IDS['Master Bedroom'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    71: {
        'name': 'Master Bedroom Fan Pico',
        'bond': {
            'name': 'Master Bedroom Fan',
            'id': BOND_IDS['Master Bedroom'],
            'actions': FAN_CONFIG,
        }
    },
    72: {
        'name': 'Living Room Fan Light Pico',
        'bond': {
            'name': 'Living Room Fan Light',
            'id': BOND_IDS['Living Room'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    8: {
        'name': 'Living Room Pico',
        'bond': {
            'name': 'Living Room Fan Light',
            'id': BOND_IDS['Living Room'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    63: {
        'name': 'Fireplace Pico',
        'bond': {
            'name': 'Living Room Fan Light',
            'id': BOND_IDS['Living Room'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    73: {
        'name': 'Living Room Fan Pico',
        'bond': {
            'name': 'Living Room Fan',
            'id': BOND_IDS['Living Room'],
            'actions': FAN_CONFIG,
        }
    },
    29: {
        'name': 'Guest Room Fan Pico',
        'bond': {
            'name': 'Guest Room Fan',
            'id': BOND_IDS['Guest Room'],
            'actions': FAN_CONFIG,
        }
    },
    75: {
        'name': 'Guest Room Fan Light Pico',
        'bond': {
            'name': 'Guest Room Fan Light',
            'id': BOND_IDS['Guest Room'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    00: {
        'name': 'Office Video Light Pico',
        'tuya': [
            {
                'name': 'Office Video Light Left',
                'id': '06200623b4e62d1a231b',
                'key': '58acbde7876e5a99',
                'addr': '192.168.1.207',
                'version': 3.1,
                'actions': SMART_SWITCH_ACTIONS,
            },
            {
                'name': 'Office Video Light Right',
                'id': '06200623b4e62d1a1a6b',
                'key': '318c0b25b8afd00b',
                'addr': '192.168.1.26',
                'version': 3.1,
                'actions': SMART_SWITCH_ACTIONS,
            },
        ],
    },
}

LUTRON2_MAPPING: Dict[int, Dict] = {
    58: {
        'name': 'Heated Outdoor Chair Pico',
        'tuya': {
            'name': 'Heated Outdoor Chairs',
            'id': 'ebfe2b76f486db7b067lvm',
            'key': 'b073d73bea4f94f5',
            'addr': '192.168.1.195',
            'version': 3.3,
            'actions': SMART_SWITCH_ACTIONS,
        },
    },
}
