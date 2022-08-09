import numpy as np
from scipy import signal

controller = 'con1'

# Parameters:

# Pulse_durations
readout_pulse_len = 1000
MOT_pulse_len = 40
PGC_pulse_len = 40
Fountain_pulse_len = 40
FreeFall_pulse_len = 40
Probe_pulse_len = 4000
Depump_pulse_len = 40
OD_pulse_len = 40
Repump_pulse_len = 40
MOT_duration_len = 1e6
north_const_pulse_len = 500
south_const_pulse_len = 500
analyzer_const_pulse_len = 500
Detection_pulse_len = 1000
Flash_pulse_len = 10000

# Intermediate frequencies
IF_TOP1_MOT = 113e6
IF_TOP1_PGC = 103e6
IF_TOP1_Flash = 121.6625e6
IF_TOP2 = 89e6
IF_AOM_MOT = 110e6
IF_AOM_MOT_OFF = 80e6
IF_AOM_OD = 93e6
IF_AOM_Depump = 133.325e6
IF_AOM_Repump = 78.4735e6
# IF_AOM_N = 128e6
# IF_AOM_S = 91e6
IF_AOM_N = 110e6
IF_AOM_S = 110e6

IF_AOM_LO = 110e6
IF_Divert = 20e6
IF_AOM_Analyzer = np.abs(IF_AOM_N - IF_AOM_S) * 2

trig_samples = [0,0,0,0] + [0.3, 0.3, 0.3 ,0.3]*16 + [0,0,0,0]

Det_Gaussian_samples = ([0]*24 + (signal.gaussian(48, std=(12/2.355))*0.3).tolist()  + [0]*24)* 4
SWAP_Gaussian_samples = [0]*24 + (signal.gaussian(400, std=(100/2.355))*0.3).tolist() + [0]*24
DC_cal_samples = [0]*20 + ([0.3]*80) + [0]*20
EOM_pulse_seq_samples = Det_Gaussian_samples + SWAP_Gaussian_samples + DC_cal_samples + [0]*24

delay = 1
Det_square_samples = ([0]*16 + ([0.3]*64) + [0]*16)*4
SWAP_square_samples =([0]*20 + ([0.3]*408) + [0]*20)
square_cal_samples = ([0]*20 + ([0.3]*88) + [0]*20)
AOMs_pulse_seq_samples = [0]*delay + Det_square_samples + SWAP_square_samples + square_cal_samples + [0]*(24-delay)

## For Homodyne ##

LO_pulse_samples =([0.3]*2000 + [0]*2000)

config = {

    'version': 1,

    'controllers': {
        controller: {
            'type': 'opx1',
            'analog_outputs': {
                1: {'offset': +0.0},  # AOM Lock TOP 1
                2: {'offset': +0.0},  # AOM main TOP 2
                3: {'offset': +0.0},  # AOM 0
                4: {'offset': +0.0},  # AOM + / AOM 2-2'
                5: {'offset': +0.0},  # AOM - / AOM 2-3'
                6: {'offset': +0.0},  # AOM 1-2' - Repump
                7: {'offset': +0.0},  # Pulse_EOM
                8: {'offset': +0.0},  # AOM_N
                9: {'offset': +0.0},  # AOM_S
                10: {'offset': +0.0}, # AOM_Analyzer
            },
            'digital_outputs': {
                1: {},  # Switch AOM + / AOM 2-2'
                2: {},  # Switch AOM - / AOM 2-3'
                3: {},  # Switch ON/OFF anti-Helmholtz coils (for MOT)
                4: {},  # Switch ON/OFF Helmholtz coils (for Super-SPRINT)
                5: {},  # Camera Trigger
                6: {},  # Switch Homodyne detection
            },
            'analog_inputs': {
                1: {'offset': +0.0},  # DET10
                #2: {'offset': +0.1974044},  # Summing amp / Homodyne
                2: {'offset': +0.197359321899414038085},  # Summing amp / Homodyne

            }
        }
    },

    'elements': {

        "AOM_TOP_1": {
            "singleInput": {
                "port": (controller, 1)
            },
            'operations': {
                'MOT': "MOT_lock",
                'PGC': "PGC_lock",
            },
            'intermediate_frequency': IF_TOP1_MOT,
            'hold_offset': {'duration': 10},
        },

        "AOM_TOP_2": {
            "singleInput": {
                "port": (controller, 2)
            },
            'operations': {
                'Probe': "Probe_lock",
            },
            'intermediate_frequency': IF_TOP2,
            'hold_offset': {'duration': 10},
        },

        "MOT_AOM_0": {
            'singleInput': {
                "port": (controller, 3)
            },
            'operations': {
                'MOT': "MOT_lock",
                'PGC': "PGC_lock",
                'Fountain': "Fountain_conf",
            },
            'intermediate_frequency': IF_AOM_MOT,
            'hold_offset': {'duration': 10},
        },

        "MOT_AOM_+": {
            'singleInput': {
                "port": (controller, 4)
            },
            'operations': {
                'MOT': "MOT_lock",
                'PGC':"PGC_lock",
                'Fountain': "Fountain_conf",
            },
            'intermediate_frequency': IF_AOM_MOT,
            'hold_offset': {'duration': 10},
        },

        "AOM_2-2'": {
            "singleInput": {
                "port": (controller, 4)
            },
            'digitalInputs': {
                "switch1": {
                    "port": (controller, 1),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'Depump': "Depump_pulse",
            },
            'intermediate_frequency': IF_AOM_Depump,
        },

        "MOT_AOM_-": {
            'singleInput': {
                "port": (controller, 5)
            },
            'operations': {
                'MOT': "MOT_lock",
                'PGC': "PGC_lock",
                'Fountain': "Fountain_conf",
            },
            'intermediate_frequency': IF_AOM_MOT,
            'hold_offset': {'duration': 10},
        },

        "AOM_2-3'": {
            "singleInput": {
                "port": (controller, 4)
            },
            'digitalInputs': {
                "switch2": {
                    "port": (controller, 2),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'OD': "OD_pulse",
            },
            'intermediate_frequency': IF_AOM_OD,
        },

        "AOM_1-2'": {
            "singleInput": {
                "port": (controller, 6)
            },
            'operations': {
                'Repump': "Repump_pulse",
            },
            'intermediate_frequency': IF_AOM_Repump,
            'hold_offset': {'duration': 10},
        },

        "Pulse_EOM": {
            "singleInput": {
                "port": (controller, 7)
            },
            'digitalInputs': {
                "switch1": {
                    "port": (controller, 4),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'Detection_pulses': "Gaussian_detection_pulses",
                'SWAP_pulse': "Gaussian_SWAP_pulse",
                'DC_calibration': "DC_cal_pulse",
                'Pulse_sequence': "EOM_pulse_seq"
            },
            'intermediate_frequency': 0,
        },

        "AOM_N": {
            "singleInput": {
                "port": (controller, 8)
            },
            'operations': {
                'north': "north_const_pulse",
                'Detection_pulses': "square_detection_pulses",
                'SWAP_pulse': "square_SWAP_pulse",
                'DC_calibration': "square_cal_pulse",
                'Pulse_sequence': "AOMs_pulse_seq"
            },
            'intermediate_frequency': IF_AOM_N,
        },

        "AOM_S": {
            "singleInput": {
                "port": (controller, 9)
            },
            'operations': {
                'south': "south_const_pulse",
                'Detection_pulses': "square_detection_pulses",
                'SWAP_pulse': "square_SWAP_pulse",
                'DC_calibration': "square_cal_pulse",
                'Pulse_sequence': "AOMs_pulse_seq"
            },
            'intermediate_frequency': IF_AOM_S,
        },

        "AOM_Analyzer": {

            "singleInput": {
                "port": (controller, 10)
            },
            'operations': {
                'analyzer': "analyzer_const_pulse",
            },
            'intermediate_frequency': IF_AOM_Analyzer,
        },

        "Homodyne_detection": {
            "singleInput": {
                "port": (controller, 9)
            },
            'digitalInputs': {
                "switch1": {
                    "port": (controller, 6),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'Detection': "Homodyne_Det_pulse",
            },
            'intermediate_frequency': IF_AOM_LO,
            "outputs": {
                'Homodyne': (controller, 2)
            },
            'time_of_flight': 180 + 100,  # ns multiples of 4 28,32,..
            'smearing': 0
        },

        "AntiHelmholtz_Coils": {
            'digitalInputs': {
                "AntiHelmholtz": {
                    "port": (controller, 3),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'AntiHelmholtz_MOT': "AntiHelmholtz_on",
            },
        },

        "Zeeman_Coils": {
            'digitalInputs': {
                "Helmholtz": {
                    "port": (controller, 4),
                    "delay": 0,
                    "buffer": 0,
                },
            },
            'operations': {
                'ZeemanSplit': "Zeeman_on",
            },
        },

        "Camera": {
             "singleInput": {
                "port": (controller, 1)
             },
             'intermediate_frequency': IF_TOP1_MOT,
             'digitalInputs': {
                "Cam": {
                    "port": (controller, 5),
                    "delay": 30,
                    "buffer": 0,
                },
             },
             'operations': {
                'Snapshot': "Snapshot_Flash",
             },
        }
    },

    "pulses": {

        "MOT_lock": {
            'operation': 'control',
            'length': MOT_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            }
        },

        "PGC_lock": {
            'operation': 'control',
            'length': PGC_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            }
        },

        "Probe_lock": {
            'operation': 'control',
            'length': Probe_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            },
        },

        "Fountain_conf": {
            'operation': 'control',
            'length': Fountain_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            },
        },

        "Depump_pulse": {
            'operation': 'control',
            'length': Depump_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            },
            'digital_marker': 'ON'
        },

        "OD_pulse": {
            'operation': 'control',
            'length': OD_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            },
            'digital_marker': 'ON'
        },

        "Repump_pulse": {
            'operation': 'control',
            'length': Repump_pulse_len,
            'waveforms': {
                'single': 'const_wf'
            },
        },

        "Gaussian_detection_pulses": {
            'operation': 'control',
            'length': len(Det_Gaussian_samples),
            'waveforms': {
                'single': 'Detection_Gaussian_wf'
            }
        },

        "Gaussian_SWAP_pulse": {
            'operation': 'control',
            'length': len(SWAP_Gaussian_samples),
            'waveforms': {
                'single': 'SWAP_Gaussian_wf'
            }
        },

        "DC_cal_pulse": {
            'operation': 'control',
            'length': len(DC_cal_samples),
            'waveforms': {
                'single': 'DC_cal_wf'
            }
        },

        "EOM_pulse_seq": {
            'operation': 'control',
            'length': len(EOM_pulse_seq_samples),
            'waveforms': {
                'single': 'EOM_pulse_seq_wf'
            },
            'digital_marker': 'Trig'
        },

        "square_detection_pulses": {
            'operation': 'control',
            'length': len(Det_square_samples),
            'waveforms': {
                'single': 'Detection_square_wf'
            }
        },

        "square_SWAP_pulse": {
            'operation': 'control',
            'length': len(SWAP_square_samples),
            'waveforms': {
                'single': 'SWAP_square_wf'
            }
        },

        "square_cal_pulse": {
            'operation': 'control',
            'length': len(square_cal_samples),
            'waveforms': {
                'single': 'square_cal_wf'
            }
        },

        "AOMs_pulse_seq": {
            'operation': 'control',
            'length': len(AOMs_pulse_seq_samples),
            'waveforms': {
                'single': 'AOMs_pulse_seq_wf'
            }
        },

        "north_const_pulse": {
            'operation': 'control',
            'length': north_const_pulse_len,
            'waveforms': {
                'single': 'const_wf_n'
            }
        },

        "south_const_pulse": {
            'operation': 'control',
            'length': south_const_pulse_len,
            'waveforms': {
                'single': 'const_wf_s'
            }
        },

        "analyzer_const_pulse": {
            'operation': 'control',
            'length': analyzer_const_pulse_len,
            'waveforms': {
                'single': 'const_wf_a'
            }
        },

        "Homodyne_Det_pulse": {
            'operation': 'measurement',
            'length': len(LO_pulse_samples),
            'waveforms': {
                'single': 'LO_pulse_wf'
            },
            'integration_weights': {
                'Detection_opt': 'Homodyne_Det_opt'
            },
            'digital_marker': 'ON'
        },

        "AntiHelmholtz_on": {
            'operation': 'control',
            'length': MOT_duration_len,
            'digital_marker': 'ON'
        },

        "Zeeman_on": {
            'operation': 'control',
            'length': FreeFall_pulse_len,
            'digital_marker': 'ON'
        },

        "Snapshot_Flash": {
            'operation': 'control',
            'length': Flash_pulse_len,
            'waveforms': {
                'single': 'zero_wf'
            },
            'digital_marker': 'Trig'
        }
    },

    'integration_weights': {
        'integW': {
            'cosine': [1.0] * int(readout_pulse_len / 4),
            'sine': [0.0] * int(readout_pulse_len / 4)
        },
        'Homodyne_Det_opt': {
            'cosine': [1.0] * int(len(LO_pulse_samples) / 4),
            'sine': [0.0] * int(len(LO_pulse_samples) / 4)
        },
        'Det_opt': {
            'cosine': [1.0],
            'sine': [0.0]
        }
    },

    "waveforms": {
        'zero_wf': {
            'type': 'constant',
            'sample': 0.0
        },
        'MOT_wf': {
            'type': 'constant',
            'sample': 0.3
        },
        'PGC_wf': {
            'type': 'constant',
            'sample': 0.3
        },
        'Fountain_wf': {
            'type': 'constant',
            'sample': 0.3
        },
        'Detection_Gaussian_wf': {
            'type': 'arbitrary',
            'samples': Det_Gaussian_samples
        },
        'SWAP_Gaussian_wf': {
            'type': 'arbitrary',
            'samples': SWAP_Gaussian_samples
        },
        'DC_cal_wf': {
            'type': 'arbitrary',
            'samples': DC_cal_samples
        },
        'EOM_pulse_seq_wf': {
            'type': 'arbitrary',
            'samples': EOM_pulse_seq_samples
        },
        'Detection_square_wf': {
            'type': 'arbitrary',
            'samples': Det_square_samples
        },
        'SWAP_square_wf': {
            'type': 'arbitrary',
            'samples': SWAP_square_samples
        },
        'square_cal_wf': {
            'type': 'arbitrary',
            'samples': square_cal_samples
        },
        'AOMs_pulse_seq_wf': {
            'type': 'arbitrary',
            'samples': AOMs_pulse_seq_samples
        },
        'LO_pulse_wf': {
            'type': 'arbitrary',
            'samples': LO_pulse_samples
        },
        'const_wf_n': {
            'type': 'constant',
            'sample': 0.3
        },
        'const_wf_s': {
            'type': 'constant',
            'sample': 0.3
        },
        'const_wf_a': {
            'type': 'constant',
            'sample': 0.4
        },
        'const_wf': {
            'type': 'constant',
            'sample': 0.49
        }
    },

    "digital_waveforms": {
        "ON": {
            "samples": [(1, 0)]
        },
        "Trig": {
            "samples": [(1, 20000), (0, 0)]
        }
    },
}
