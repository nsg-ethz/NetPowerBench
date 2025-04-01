import argparse
import yaml
import os
from pathlib import Path


def parse_cli_args():
    """
    Parses command-line arguments for running device experiments.

    Recognized arguments:
        -d, --device_id     : Identifier for the device to test (str)
        -e, --exp           : List of experiment types to run (e.g., base, idle, switch) (list of str)
        -s, --speed         : List of port speeds to test (e.g., 100G, 400G) (list of str)
        -p, --port_type     : Type of port to use (e.g., QSFP28) (str)
        -r, --repeats       : Number of times to repeat each test (int, default: 1)

    Returns:
        dict: A dictionary containing all parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Run device experiment tests.')
    parser.add_argument('-d', '--device_id', type=str, help='Device identifier')
    parser.add_argument('-e', '--exp', nargs='+', help='Experiment types (e.g., base idle switch)')
    parser.add_argument('-s', '--speed', nargs='+', help='Speeds to test (e.g., 100G 400G)')
    parser.add_argument('-p', '--port_type', type=str, help='Port type (e.g., QSFP28)')
    parser.add_argument('-r', '--repeats', type=int, default=1, help='Number of repeats per test')
    
    args = parser.parse_args()
    return vars(args)

def get_experiment_params():
    """
    Gets experiment parameters either from the CLI or from exp.yml

    If parameters can not be loaded, an error is thrown.

    Args:
        None

    Returns:
        dict: Dictionary containing the experiment parameters
    """
    args = parse_cli_args()

    if all(args.get(k) for k in ['device_id', 'exp', 'speed', 'port_type']):
        return args

    if os.path.exists('exp.yml'): # TODO: Path
        yaml_config = load_yml('exp.yml')
        if yaml_config and all(k in yaml_config for k in ['device_id', 'exp', 'speed', 'port_type']):
            return {
                'device_id': yaml_config['device_id'],
                'exp': yaml_config['exp'],
                'speed': yaml_config['speed'],
                'port_type': yaml_config['port_type'],
                'repeats': yaml_config.get('repeats', 1),
            }
    raise RuntimeError("Missing experiment parameters. Provide CLI args or a valid exp.yml file.")


def get_log_name(metadata):
    """
    Returns the file name for logging the experiment
    """

    exp_type = metadata['experiment_type']
    port_type = metadata['port_type']
    speed_label = metadata['port_speed']
    number_ports = len(metadata['port_list'])

    match exp_type:
        case 'base':
            log_name = exp_type
        case 'idle':
            log_name = f'{exp_type}_{port_type}'
        case 'switch':
            log_name = f'{exp_type}_{port_type}_{speed_label}_{number_ports}p'
        case 'trx':
            log_name = f'{exp_type}_{port_type}_{speed_label}_{number_ports}p'
        case 'snake-test':
            packet_size = metadata['packet_size_bytes']
            bandwidth = metadata['bandwidth_gbps']
            log_name = f'{exp_type}_{port_type}_{speed_label}_{packet_size}B_{bandwidth}Gbps'
        case _:
            raise ValueError(f"Unknown experiment type: {exp_type}")
    
    return log_name


def get_log_path(metadata):
    """
    Returns the log path for logging the experiment
    """
    workspace = get_parent_directory()
    log_name = get_log_name(metadata)
    dut_type = metadata['dut_type']
    device = metadata['device']
    time = str(metadata['time']).replace(' ','_').split('.')[0]
    
    log_path = Path(workspace, 'data', dut_type, device, 'static', log_name, time)
    return log_path


def start_traffic(metadata, settings):
    """
    Starts traffic generation
    """

def load_json(json_file):
    """
    Simple helper to load json data
    """

def load_yml(yaml_file):
    """
    Simple helper to load yaml data
    """

    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)

def save_as_json(data, destination, name):
    """
    Saves data at destination as JSON with respecitve name
    """

def save_as_yml(data, destionation, name, sort_keys = False):
    """
    Saves data at destination as YAML with respecitve name
    """

def check_cwd():
    """ 
    Checks whether we call the scripts in the correct directory (automation).
    """

def get_parent_directory():
    """
    Returns the parent of the directory the script is run from.
    """

def check_existing_directory(target_directory):
    """
    Checks whether a directory with name target_directory exists and gives a warning to the user if it does.
    """