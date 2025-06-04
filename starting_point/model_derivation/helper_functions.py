import os
import yaml
import argparse
from pathlib import Path

def parse_cli_args():
    """
    Parses command-line arguments for running a data derivation task.

    Recognized arguments:
        -d, --device_id          : Identifier for the device (str) [required if not in exp.yml]
        --measurements_from      : Start time for measurements (str, e.g., '2025-06-01_00:00:00')
        --measurements_to        : End time for measurements (str, e.g., '2025-06-01_12:00:00')
        --preprocess_only        : Run only preprocessing step (bool, default: False)
        --derive_only            : Run only derivation step (bool, default: False)

    Returns:
        dict: A dictionary containing all parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Parse data derivation parameters.')
    parser.add_argument('-d', '--device_id', type=str, help='Device identifier')
    parser.add_argument('-s', '--port_speed', type=str, help='Speed of port used in the model (e.g., 100G 400G)')
    parser.add_argument('-p', '--port_type', type=str, help='Port type used in the model (e.g., QSFP28)')
    parser.add_argument('-t', '--transceivers', type=str, help='Transceiver type used in the model(e.g., LR)')
    parser.add_argument('--measurements_from', type=str, help='Start time for measurements, only data with timestamp later than this will be considered for model.')
    parser.add_argument('--measurements_to', type=str, help='End time for measurements, only data with timestamp earlier than this will be considered for model.')
    parser.add_argument('--preprocess_only', action='store_true', help='Run only preprocessing (default: False)')
    parser.add_argument('--derive_only', action='store_true', help='Run only derivation (default: False)')

    args = parser.parse_args()
    return vars(args)

def get_derivation_params():
    """
    Retrieves derivation parameters from CLI args or a fallback YAML config.

    Returns:
        dict: Dictionary with merged parameter values.

    Raises:
        RuntimeError: If 'device_id' is not provided by CLI or YAML.
    """
    args = parse_cli_args()
    has_cli_input = any(v is not None and v is not False for k, v in args.items())

    if has_cli_input:
        if all(args.get(k) for k in ['device_id', 'port_speed', 'port_type', 'transceivers']):
            return args
    
    elif os.path.exists('exp.yml'): # TODO: Path
        yaml_config = load_yml('exp.yml')
        if yaml_config and all(k in yaml_config for k in ['device_id', 'speed', 'port_type', 'transceivers']):
            return {
                'device_id': yaml_config['device_id'],
                'port_speed': yaml_config['port_speed'],
                'port_type': yaml_config['port_type'],
                'transceivers':yaml_config['transceivers'],
                'measurements_from': yaml_config.get('measurements_from'),
                'measurements_to': yaml_config.get('measurements_to'),
                'preprocess_only': yaml_config.get('preprocess_only', False),
                'derive_only': yaml_config.get('derive_only', False)
                
            }
    raise RuntimeError("Missing experiment parameters. Provide CLI args or a valid exp.yml file.")


def load_yml(yaml_file): # Doublicate of helper in power_measure
    """
    Simple helper to load yaml data
    """

    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)
    
def save_as_yml(data,dest,name,sort_keys=False):
    """
    Save dictionary as YAML
    """
    Path(dest).mkdir(parents=True, exist_ok=True)

    f = Path(dest,name)
    with open(f, "w") as file:
        yaml.dump(data,file,sort_keys=sort_keys)


def get_group(metadata):
    exp_type = metadata['experiment_type']
    
    if exp_type == 'base':
        group = {'exp_type': exp_type}
    elif exp_type == 'idle':
        group = {
            'port_type'     : metadata['port_type'],
            'trx'           : metadata['transceivers'],
            'exp_type'      : metadata['experiment_type'],
            'n_ports'       : metadata['port_number'],
        }
    elif exp_type == 'snake-test':
        
        exact_bw = metadata['bandwidth_reached_gbps']
        target_bw = metadata['bandwidth_gbps']

        precision_map = {1: 1, 0.5: 2, 0.1: 2, 0.05: 3, 0.01: 3,  0.005: 4, 0.001: 4}

        if target_bw in precision_map:
            rounded_bw = round(exact_bw, precision_map[target_bw])
        else:
            # For bandwidths > 2.5 Gbps, round to nearest 0.5
            rounded_bw = round(2 * exact_bw, 0) / 2

        group = {
            'port_type'     : metadata['port_type'],
            'trx'           : metadata['transceivers'],
            'exp_type'      : metadata['experiment_type'],
            'port_speed'    : metadata['port_speed'],
            'n_ports'       : metadata['port_number'],
            'packet_size_bytes' : metadata['packet_size_bytes'],
            'bandwidth_gbps': rounded_bw
        }
    else:
        group = {
            'port_type'     : metadata['port_type'],
            'trx'           : metadata['transceivers'],
            'exp_type'      : metadata['experiment_type'],
            'port_speed'    : metadata['port_speed'],
            'n_ports'       : metadata['port_number'],
        }
    return group
