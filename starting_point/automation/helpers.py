import os
import subprocess
from pathlib import Path
import json
import yaml
import shutil

import pandas as pd
import numpy as np
import plotly.express as px

"""
General functions for the implementation of the power benchmark.
"""

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

def clean_buggy_port_lists(file):
    """
    Some buggy writing makes reading back problematic. 
    This function just cuts the annoying part away in a crude way.
    """

    # Clean up
    with open(file) as inFile:
        text = inFile.read()
        tmp = text.split('port_list')
        out = tmp[0]+'time:'+tmp[1].split('time:')[1]

    # Write back
    file_path = Path(file)
    with open(file_path.parent/'metadata-fixed.yml', "w") as outFile:
        outFile.write(out)   
    


def check_cwd():
    """ 
    Helper function to check whether we call the scripts in the correct directory (automation).
    """
    cwd_name = os.path.basename(os.getcwd())
    if cwd_name != 'automation':
        raise Exception("Check working directory. Please run from the automation directory")
    

def get_workspace_directory():
    """
    Helper function to get the workspace directory. Easier to navigate from there.
    """
    check_cwd()         # Assumes we are in automation directory
    cwd = os.getcwd()
    workspace = os.path.dirname(cwd)
    return Path(workspace)

    
def check_existing_log_directory(target_directory=None):
    """ 
    A helper function to check to make sure we do not overwrite already existing logs  
    """
    if target_directory is None:
        raise Exception("Insufficient argument provided.")
    
    if (os.path.exists(target_directory) is True):
        i = input("WARNING: Directory {} exists... potentially override stored data in this directory? (y/n)".format(target_directory))
        if (i == 'y'):
            return
        else:
            raise Exception("User input")
        
def run_pinpoint(metadata):
    """
    Simply run command/pinpoint_*.sh depending on the input argument. 
    arg workload:           The workload to be run *ON BOILOVER"
    arg measure_time:       The time we should run pinpoint if no workload specified, in seconds. Default 30 seconds.
    arg sampling_interval:  The pinpoint sampling interval in ms. Default 50 milliseconds.
    arg start_up_delay:     The delay to apply before starting the measurement, in seconds. Default is 0s (no delay).
    """

    workload            = metadata['workload']
    measure_time        = metadata['measurement_time_s']
    sampling_interval   = metadata['sampling_interval_ms']
    start_up_delay      = metadata['configuration_time_s']
    device              = metadata['device']

    config_path = Path('..','devices',device)
    config = load_yml(config_path / 'config.yml')

    workspace = get_workspace_directory()
    # Make sure the output directory for pinpoint measurements exists
    Path(workspace / 'data' / 'log').mkdir(parents=True, exist_ok=True)
    if workload == None:
        subprocess.run([os.path.join(
            workspace, 
            "command", 
            "pinpoint_sleep.sh"), 
            str(measure_time + start_up_delay),
            config['pinpoint']['binary'],
            str(sampling_interval),
            str(start_up_delay*1000)
        ])
    else: 
        assert(type(workload) == str)
        subprocess.run([os.path.join(workspace, "command", "pinpoint_workload.sh"), str(workload)])


def safeguard_pinpoint():
    """
    Helper function. Pinpoint sometimes does not measure values due to ssh issues. 
    NOTE: This function is to be used if we expect the pinpoint.log data to be written with data.
    Returns 1 if the log has no data written due to the issue. Otherwise returns 0.
    """
    workspace = get_workspace_directory()
    num_lines = sum(1 for line in open(os.path.join(workspace, "data", "log", "pinpoint.log")))
    if num_lines <= 3:
        print("pinpoint issue detected.")
        return 1
    return 0

def save_as_json(data,dest,name):
    """
    Save dictionary as JSON
    """
    metadata = json.dumps(data,indent=4)
    Path(dest).mkdir(parents=True, exist_ok=True)

    f = Path(dest,name)
    with open(f, "w") as file:
        file.write(metadata)

def save_as_yml(data,dest,name,sort_keys=False):
    """
    Save dictionary as YAML
    """
    Path(dest).mkdir(parents=True, exist_ok=True)

    f = Path(dest,name)
    with open(f, "w") as file:
        yaml.dump(data,file,sort_keys=sort_keys)

def save_pinpoint_log(metadata,log_path):
    """
    Save the pinpoint log in the correct destination
    """
    workspace = get_workspace_directory()

    print("Copying logs to {}".format(log_path))

    # Create the log directory
    log_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        workspace / "data" / "log" / 'pinpoint.log',
        log_path/'power.log'
    )
                
    # os.makedirs(os.path.join(workspace, target_directory, exist_ok=True)
    # shutil.copyfile(os.path.join(workspace, "data", "log", t_map[k][0]), os.path.join(target_directory, t_map[k][1], "{}.log".format(logname)))

def analyse_exp(data_path, display_plot=False):
    '''Parse the power log located at the input location,
    returns the median power of the log,
    plot the data, save it, and optionally display the plot.
    '''

    # load power data
    # .. make sure to have the appropriate headers
    df = pd.read_csv(data_path/'power.log', names=['MCP1','MCP2'], header=0)

    # compute the total power and median
    df['Power [W]'] = ((df['MCP1'] + df['MCP2'])/1000)
    df['Median'] = df['Power [W]'].median()

    # TODO: test that the data is stable... (monotonic)
    # I'd probably return a boolean like is_stationary and store that in a 
    # list like the timestamps (then when can easily filter with the list as a boolean index)

    # compute the median power for that experiment
    median_power = df['Median'].to_list()[0]

    # TODO: generate and save the px figure, with optional display
    fig = px.line(df, x=df.index, y=['Power [W]','Median'])
    if display_plot:
        fig.show()

    return median_power


def init_nested_dict(dict,group):
    '''`group` is a dictionary which values
    describe the nested keys we want to initialize
    in `dict`
    '''
    tmp = dict
    for level in group.values():
        tmp = tmp.setdefault(level, {})
    
    return dict


def store_datapoint(
        ts,
        power,
        model_dict,
        group
    ):

    # Get to the bottom of the group
    try:
        tmp = model_dict
        for level in group.values():
            tmp = tmp[level]

    except KeyError:
        # Set defaults for the entire group
        model_dict = init_nested_dict(model_dict,group)
        # Call again
        store_datapoint(ts,power,model_dict,group)
        return

    # Store the new data point
    try:
        tmp['ts'].append(ts)
        tmp['power'].append(power)
    except KeyError:
        # Set defaults the data points
        tmp.setdefault('ts',[])
        tmp.setdefault('power',[])
        # Call again
        store_datapoint(ts,power,model_dict,group)
        return



def get_datapoints(model_dict,group):

    # Get to the bottom of the group
    try:
        tmp = model_dict
        for level in group.values():
            tmp = tmp[level]

    except KeyError:
        print('problem with the dict group:',group)
        return {}

    concat_n = []
    concat_m = []
    concat_b = []
    concat_p = []
    concat_t = []

    # 'base' (no n_ports)
    if 'power' in tmp.keys():
        return {
            'n_ports'   : [0],
            'ts'        : tmp['ts'],
            'power'     : tmp['power'],
        }
    elif group['exp_type'] == 'snake-test':
        for n_port in tmp.keys():
            tmp_n_port = tmp[n_port]
            for mtu in tmp_n_port.keys():
                tmp_mtu = tmp_n_port[mtu]
                for bw in tmp_mtu.keys():
                    concat_n = concat_n + (n_port   * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    concat_m = concat_m + (mtu      * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    concat_b = concat_b + (bw       * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    concat_p = concat_p + tmp_mtu[bw]['power']
                    concat_t = concat_t + tmp_mtu[bw]['ts']
        return {
            'n_ports'   : concat_n,
            'ts'        : concat_t,
            'power'     : concat_p,
            'mtu'       : concat_m,
            'bw'        : concat_b
        }

    # 'idle' 'switch' and 'trx' cases
    for n_port in tmp.keys():
        concat_p = concat_p + tmp[n_port]['power']
        concat_t = concat_t + tmp[n_port]['ts']
        concat_n = concat_n + (n_port * np.ones(len(tmp[n_port]['ts']), dtype=int)).tolist()

    return {
        'n_ports'   : concat_n,
        'ts'        : concat_t,
        'power'     : concat_p
    }


def push_data_in_dict(dict,group,data):

    # Get to the bottom of the dict
    tmp = dict
    for level in group.values():
        if level not in tmp.keys():
            tmp[level] = {}
        tmp = tmp[level]

    # Save the data
    # print(tmp)
    tmp.update(data)

    # Return the dict
    return dict