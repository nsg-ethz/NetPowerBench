import argparse
import subprocess
import json
import yaml
import os
import time
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
    parser.add_argument('-u', '--user_confirm', type=bool, default=True, help='Manual user confirmation enabled/disabled')
    
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
                'user_confirm': yaml_config.get('user_confirm', True)
            }
    raise RuntimeError("Missing experiment parameters. Provide CLI args or a valid exp.yml file.")


def get_log_name(metadata):
    """
    Returns the file name for logging the experiment
    """

    exp_type = metadata['experiment_type']
    port_type = metadata['port_type']
    speed_label = metadata['port_speed']
    

    match exp_type:
        case 'base':
            log_name = exp_type
        case 'idle':
            log_name = f'{exp_type}_{port_type}'
        case 'switch':
            number_ports = len(metadata['port_list'])
            log_name = f'{exp_type}_{port_type}_{speed_label}_{number_ports}p'
        case 'trx':
            number_ports = len(metadata['port_list'])
            log_name = f'{exp_type}_{port_type}_{speed_label}_{number_ports}p'
        case 'snake-test':
            packet_size = metadata['packet_size_bytes']
            bandwidth = metadata['bandwidth_gbps']
            log_name = f'{exp_type}_{port_type}_{speed_label}_{packet_size}B_{bandwidth}Gbps'
        case _:
            raise ValueError(f"Unknown experiment type: {exp_type}")
    
    return log_name


def get_log_path(metadata, measurement_data):
    """
    Returns the log path for logging the experiment
    """
    workspace = get_parent_directory()
    log_name = get_log_name(metadata)
    dut_type = metadata['dut_type']
    device = metadata['device']
    time = str(measurement_data['time']).replace(' ','_').split('.')[0]

    log_path = Path(workspace, 'data', dut_type, device, 'static', log_name, time)
    return log_path


def start_traffic(metadata, measurement_data):
    """
    Starts traffic generation
    """
    workspace = get_parent_directory()
    location = os.path.join(workspace, "traffic_gen", "traffic_gen.py")
    total_time = str(metadata['measurement_time_s'] + metadata['configuration_time_s'])
    bandwidth = str(measurement_data['bandwidth_gbps'])
    packet_size = str(measurement_data['packet_size_bytes'])
    
    traffic_gen = subprocess.Popen(['python', location, total_time, bandwidth, packet_size])
    return traffic_gen

def stop_traffic(traffic_process):
    """
    Waits for the traffic to end
    """
    traffic_process.wait()
    time.sleep(1)
    print("Traffic stopped")

def load_json(json_file):
    """
    Simple helper to load json data
    """
    with open(json_file, 'r') as file:
        return json.load(file)

def load_yml(yaml_file):
    """
    Simple helper to load yaml data
    """

    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)

def save_as_json(dict, destination, name):
    """
    Saves a dictionary at destination as JSON with respecitve name
    """
    data = json.dumps(dict, indent=4)
    Path(destination).mkdir(parents=True, exist_ok=True)
    f = Path(destination, name)
    with open(f, "w") as file:
        file.write(data)
    


def save_as_yml(metadata, measurement_data, destination, name, sort_keys = False):
    """
    Saves metadata and measurement data as YAML in the given destination with the specified file name.
    """
    Path(destination).mkdir(parents=True, exist_ok=True)

    data = {
        'Metadata': metadata,
        'Measurement_Data': measurement_data
    }

    f = Path(destination, name)
    with open(f, "w") as file:
        yaml.dump(data, file, sort_keys=sort_keys)

def check_cwd():
    """ 
    Checks whether we call the scripts in the correct directory (automation).
    """
    cwd_name = os.path.basename(os.getcwd())
    if cwd_name != 'automation':
        raise Exception("Check working directory. Please run from the automation directory")

def get_parent_directory():
    """
    Returns the parent of the directory the script is run from.
    """
    check_cwd()         # Assumes we are in automation directory
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    return Path(workspace)

def check_existing_directory(target_directory):
    """
    Checks whether a directory with name target_directory exists and gives a warning to the user if it does.
    """
    if (os.path.exists(target_directory) is True):
        i = input("WARNING: Directory {} exists... potentially override stored data in this directory? (y/n)".format(target_directory))
        if (i == 'y'):
            return
        else:
            raise Exception("User input")