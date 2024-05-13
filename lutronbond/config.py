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

TUYA_RETRY_COUNT = int(get_env('LB_TUYA_RETRY_COUNT', '3'), 10)
TUYA_CONNECTION_TIMEOUT = int(get_env('LB_TUYA_CONNECTION_TIMEOUT', '3'), 10)

FAN_LIGHT_CONFIG = {
    'BTN_1': {
        'PRESS': None,
        'RELEASE': 'TurnLightOn',
    },
    'BTN_2': {
        'PRESS': None,
        'RELEASE': 'TurnLightOn',
    },
    'BTN_3': {
        'PRESS': None,
        'RELEASE': 'TurnLightOff',
    },
    'BTN_RAISE': {
        'PRESS': 'StartDimmer',
        'RELEASE': 'Stop',
    },
    'BTN_LOWER': {
        'PRESS': 'StartDimmer',
        'RELEASE': 'Stop',
    },
    'BTN_SCENE_1': {
        'PRESS': None,
        'RELEASE': 'TurnLightOn',
    },
    'BTN_SCENE_2': {
        'PRESS': None,
        'RELEASE': 'TurnLightOn',
    },
    'BTN_SCENE_3': {
        'PRESS': None,
        'RELEASE': 'TurnLightOff',
    },
    'BTN_SCENE_4': {
        'PRESS': None,
        'RELEASE': 'TurnLightOff',
    },
}

FAN_CONFIG = {
    'BTN_1': {
        'PRESS': None,
        'RELEASE': {
            'SetSpeed': 2,
        },
    },
    'BTN_2': {
        'PRESS': None,
        'RELEASE': 'ToggleDirection',
    },
    'BTN_3': {
        'PRESS': None,
        'RELEASE': 'TurnOff',
    },
    'BTN_RAISE': {
        'PRESS': None,
        'RELEASE': {
            'SetSpeed': 3,
        },
    },
    'BTN_LOWER': {
        'PRESS': None,
        'RELEASE': {
            'SetSpeed': 1,
        },
    }
}

BOND_IDS = {
    'Master Bedroom': '6409d2a2',
    'Living Room': '0b965995',
    'Guest Room': 'cb22812453dceb35',
}

SMART_SWITCH_ACTIONS = {
    'BTN_1': {
        'PRESS': None,
        'RELEASE': 'TurnOn',
    },
    'BTN_3': {
        'PRESS': None,
        'RELEASE': 'TurnOff'
    },
}

SMART_SWITCH_OUTPUT_ACTIONS = {
    'ANY': {
        'SET_LEVEL': {
            '100.00': 'TurnOn',
            '0.00': 'TurnOff',
        }
    }
}

HAYES_CLOUD_LIGHT = {
    'name': 'Hayes Bedroom Cloud Light',
    'id': 'eb0e8441252f2f6d2bppsu',
    'key': '$$/</w7Q+cQ}#Mt1',
    'addr': '192.168.1.21',
    'version': 3.3,
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
        'name': 'Living Room Keypad Pico',
        'bond': {
            'name': 'Living Room Fan Light',
            'id': BOND_IDS['Living Room'],
            'actions': FAN_LIGHT_CONFIG,
        }
    },
    13: {
        'name': 'Fireplace Keypad Pico',
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
    # 53: {
    #     'name': 'Ada Bedroom Main Lights',
    #     'tuya': {
    #         'name': 'Ada Bedroom Butterfly Light',
    #         'id': 'eb92905167786963c1nlkc',
    #         'key': 't(cD_7>a$5LA(8}m',
    #         'addr': '192.168.1.138',
    #         'version': 3.3,
    #         'actions': SMART_SWITCH_OUTPUT_ACTIONS,
    #     }
    # },
    50: {
        'name': 'Hayes Bedroom Light Switch',
        'tuya': dict(HAYES_CLOUD_LIGHT, actions=SMART_SWITCH_OUTPUT_ACTIONS)
    },
    60: {
        'name': 'Hayes Cloud Light Pico',
        'tuya': dict(HAYES_CLOUD_LIGHT, actions=SMART_SWITCH_ACTIONS),
        'lutron': {
            'name': 'Hayes Bedroom Main Lights',
            'bridge': 1,
            'id': 50,
            'actions': {
                'BTN_RAISE': {
                    'PRESS': None,
                    'RELEASE': {
                        'SET_LEVEL': '100,00.50',
                        # In English:
                        #   when integration ID 60's BTN_RAISE is released,
                        #   set the output level of integration ID 50 to
                        #   100 with a transition duration of half a second.
                    },
                },
                'BTN_LOWER': {
                    'PRESS': None,
                    'RELEASE': {
                        'SET_LEVEL': '0,01',
                    },
                },
                'BTN_2': {
                    'PRESS': None,
                    'RELEASE': {
                        'SET_LEVEL': '38,01',
                    }
                },
            }
        }
    },
}

LUTRON2_MAPPING: Dict[int, Dict] = {
    60: {
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
