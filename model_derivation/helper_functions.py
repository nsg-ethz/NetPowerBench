import os
import yaml
import argparse
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from datetime import datetime

def parse_cli_args():
    """
    Parses command-line arguments for configuring and executing the power model derivation workflow.

    Recognized arguments:
        -d, --device_id           (str) : Identifier for the device.
        -s, --port_speed          (str) : Port speed (e.g., '100G', '400G').
        -p, --port_type           (str) : Port type (e.g., 'QSFP28').
        -t, --transceivers        (str) : Transceiver type (e.g., 'LR').
        -g, --traffic_generator   (str) : Type of traffic generator ('RDMA' or 'iperf3').
        --measurements_from       (str) : Will only consider data with timestamp later than this for the model (e.g., '2025-06-01_00:00:00').
        --measurements_to         (str) : Will only consider data with timestamp earlier than this for the model (e.g., '2025-06-01_12:00:00').
        --preprocess_only                : If set, only run preprocessing step (bool).
        --derive_only                    : If set, only run model derivation step (bool).
        --plot_data                      : If set, plot intermediate data during processing (bool).

    Returns:
        dict: Dictionary of parsed arguments, with argument names as keys.
    """
    parser = argparse.ArgumentParser(description='Parse data derivation parameters.')
    parser.add_argument('-d', '--device_id', type=str, help='Device identifier')
    parser.add_argument('-s', '--port_speed', type=str, help='Speed of port used in the model (e.g., 100G 400G)')
    parser.add_argument('-p', '--port_type', type=str, help='Port type used in the model (e.g., QSFP28)')
    parser.add_argument('-t', '--transceivers', type=str, help='Transceiver type used in the model(e.g., LR)')
    parser.add_argument('-g', '--traffic_generator', type=str, choices=['RDMA', 'iperf3'], help="Type of traffic generator used. Must be either 'RDMA' or 'iperf3'.")
    parser.add_argument('--measurements_from', type=str, help='Start time for measurements, only data with timestamp later than this will be considered for model.')
    parser.add_argument('--measurements_to', type=str, help='End time for measurements, only data with timestamp earlier than this will be considered for model.')
    parser.add_argument('--preprocess_only', action='store_true', help='Run only preprocessing (default: False)')
    parser.add_argument('--derive_only', action='store_true', help='Run only derivation (default: False)')
    parser.add_argument('--plot_data', action='store_true', help='Plot intermediate data (default: False)')

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
    print("Fetching parameters ...")
    args = parse_cli_args()
    has_cli_input = any(v is not None and v is not False for k, v in args.items())

    if has_cli_input:
        if all(args.get(k) for k in ['device_id', 'port_speed', 'port_type', 'transceivers', 'traffic_generator']):
            return args
    
    elif os.path.exists('args.yml'): # TODO: Path
        yaml_config = load_yml('args.yml')
        if yaml_config and all(k in yaml_config for k in ['device_id', 'port_speed', 'port_type', 'transceivers', 'traffic_generator']):
            tg = yaml_config['traffic_generator']
            if tg not in ['RDMA', 'iperf3']:
                raise RuntimeError(f"Invalid traffic_generator '{tg}' in exp.yml. Must be 'RDMA' or 'iperf3'.")

            params = {
                'device_id': yaml_config['device_id'],
                'port_speed': yaml_config['port_speed'],
                'port_type': yaml_config['port_type'],
                'transceivers':yaml_config['transceivers'],
                'traffic_generator': yaml_config['traffic_generator'],
                'measurements_from': yaml_config.get('measurements_from', None),
                'measurements_to': yaml_config.get('measurements_to', None),
                'preprocess_only': yaml_config.get('preprocess_only', False),
                'derive_only': yaml_config.get('derive_only', False),
                'plot_data': yaml_config.get('plot_data', False)
                
            }
            
            return params
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
    """
    Returns the group needed to store a datapoint of a specific experient type.
    """
    exp_type = metadata['Metadata']['experiment_type']
    print(f"Fetching group for {exp_type}")
    if exp_type == 'base':
        group = {'exp_type': exp_type}
    elif exp_type == 'idle':
        group = {
            'port_type'     : metadata['Metadata']['port_type'],
            'trx'           : metadata['Metadata']['transceivers'],
            'exp_type'      : metadata['Metadata']['experiment_type'],
            'n_ports'       : len(metadata['Metadata']['all_ports']), 
        }
    elif exp_type == 'snake-test':
        
        exact_bw = metadata['Measurement_Data']['bandwidth_reached_gbps']
        target_bw = metadata['Measurement_Data']['bandwidth_gbps']

        precision_map = {1: 1, 0.5: 2, 0.1: 2, 0.05: 3, 0.01: 3,  0.005: 4, 0.001: 4}

        if target_bw in precision_map:
            rounded_bw = round(exact_bw, precision_map[target_bw])
        else:
            # For bandwidths > 2.5 Gbps, round to nearest 0.5
            rounded_bw = round(2 * exact_bw, 0) / 2

        group = {
            'port_type'     : metadata['Metadata']['port_type'],
            'trx'           : metadata['Metadata']['transceivers'],
            'exp_type'      : metadata['Metadata']['experiment_type'],
            'port_speed'    : metadata['Metadata']['port_speed'],
            'n_ports'       : len(metadata['Metadata']['all_ports']), 
            'packet_size_bytes' : metadata['Measurement_Data']['packet_size_bytes'],
            'bandwidth_gbps': rounded_bw
        }
    else:
        group = {
            'port_type'     : metadata['Metadata']['port_type'],
            'trx'           : metadata['Metadata']['transceivers'],
            'exp_type'      : metadata['Metadata']['experiment_type'],
            'port_speed'    : metadata['Metadata']['port_speed'],
            'n_ports'       : len(metadata['Measurement_Data']['port_list']), 
        }
    return group

def store_datapoint(measurement_path, value, group, power_data):
    """
    Stores value in the nested dictionary power_data with the values in group being the chain of keys to access.

    Args:
        measurement_path (Path): Path to the directory containing the 'power.log' file.
        value (float): Value to be stored
        group (dict): Dictionary with values that will be the keys in the nested dictionary
        power_data (dict): Nested Dictionary that value will be stored in. 

    Returns:
        None
    """
    tmp = power_data
    
    for key in group.values():
        tmp = tmp.setdefault(key, {})

    tmp.setdefault('ts', []).append(measurement_path.name)
    tmp.setdefault('power', []).append(value)


def parse_timestamp(ts_str):
    """
    Parses timestamp from string to datetime
    """
    return datetime.strptime(ts_str, "%Y-%m-%d_%H:%M:%S")

def get_datapoints(params, power_data, exp_type):
    """
    Fetches and filters power measurement data for a specified experiment type from the 
    provided preprocessed dataset. Handles different experiment types ('base', 'idle', 
    'snake-test', etc.) and filters entries based on traffic generator type and timestamp 
    constraints.

    Args:
        params (dict): Dictionary of test parameters 
        exp_type (str): Experiment type to extract data for (e.g., 'base', 'idle', 'snake-test').

    Returns:
        dict or None: Dictionary containing filtered lists of data points with keys like:
            - 'n_ports': Number of ports used.
            - 'ts': Timestamps.
            - 'power': Power values in watts.
            - 'packet_sizes': (Only for 'snake-test') Packet sizes.
            - 'bw': (Only for 'snake-test') Bandwidth values.
        Returns None if no valid data points remain after filtering.
    """

    print(f"Fetching dataponits for {exp_type} ...")
    port_type = params['port_type']
    port_speed = params['port_speed']
    tranceivers = params['transceivers']
    # Get group
    if exp_type == 'base':
        group = {'exp_type':'base'}
    elif exp_type == 'idle':
        group = {
            'port_type' : port_type,
            'trx'       : tranceivers,
            'exp_type'  : 'idle'
        }
    else:
        group = {
            'port_type' : port_type,
            'trx'       : tranceivers,
            'exp_type'  : exp_type,
            'port_speed': port_speed,
        }

    # Iterate to bottom
    tmp = power_data
    for level in group.values():
        tmp = tmp[level]

    # Read, process and return
    if exp_type == 'snake-test':
        number_ports = []
        timestamps = []
        power_values = []
        packet_sizes = []
        bandwidth = []

        for n_port in tmp.keys():
            tmp_n_port = tmp[n_port]
            for mtu in tmp_n_port.keys():
                tmp_mtu = tmp_n_port[mtu]
                for bw in tmp_mtu.keys():
                    number_ports = number_ports + (n_port * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    timestamps = timestamps + tmp_mtu[bw]['ts']
                    power_values = power_values + tmp_mtu[bw]['power']
                    packet_sizes = packet_sizes + (mtu * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    bandwidth = bandwidth + (bw * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
        data =  {
            'n_ports'       : number_ports,
            'ts'            : timestamps,
            'power'         : power_values,
            'packet_sizes'  : packet_sizes, # Same as packet sizes
            'bw'            : bandwidth
        }

        # Filter out measurements based on bw: 
        filtered_indices = []
        for i, bw_val in enumerate(data['bw']):
            if params['traffic_generator'] == 'RDMA' and bw_val >= 2.5:
                filtered_indices.append(i)
            elif params['traffic_generator'] == 'iperf3' and bw_val < 2.5:
                filtered_indices.append(i)

        data = {
            key: [values[i] for i in filtered_indices]
            for key, values in data.items()
        }

    elif exp_type == 'base':
        data = {
            'n_ports':   [0 for _ in tmp['ts']],
            'ts'        : tmp['ts'],
            'power'     : tmp['power'],
        }
    else:
        number_ports = []
        timestamps   = []
        power_values = []
        for n_port in tmp.keys():
            number_ports = number_ports + (n_port * np.ones(len(tmp[n_port]['ts']), dtype=int)).tolist()
            timestamps = timestamps + tmp[n_port]['ts']
            power_values = power_values + tmp[n_port]['power']

        data = {
            'n_ports'   : number_ports,
            'ts'        : timestamps,
            'power'     : power_values
        }
    
    # Discard data with timestamps out of range 
    time_from = parse_timestamp(params['measurements_from']) if params['measurements_from'] != None else None
    time_to   = parse_timestamp(params['measurements_to']) if params['measurements_to'] != None else None

    parsed_ts = [parse_timestamp(ts)  for ts in data['ts']]

    valid_indices = [
        i for i, t in enumerate(parsed_ts)
        if (time_from is None or t >= time_from) and (time_to is None or t <= time_to)
    ]
    if not valid_indices:
        return None

    return {
        key: [values[i] for i in valid_indices]
        for key, values in data.items()
    }


def plot_intermediate_data(dict):
    """
    Simple helper to display intermediate power data
    """
    tmp = dict.copy()
    tmp.pop('n_ports')
    tmp = pd.DataFrame.from_dict(tmp)
    tmp.sort_values(by='ts',inplace=True)
    fig = px.scatter(tmp, x='ts',y='power')
    fig.show()
    return 