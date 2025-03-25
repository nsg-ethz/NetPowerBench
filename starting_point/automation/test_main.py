import random
import itertools
import os


from helper_functions import *



def get_port_config(metadata, config_type, port_list = None, ssh = False):
    """
    Prepares the string of commands needed in order to configure a port for the respective config type
    
    Args:
        metadata (dict): Dictionary containing all the metadata
        config_type (str): The way the ports should get configured
        port_list (list): The ports that should get configured (if None, all ports will get configured)
        ssh (bool): Whether the ports will be configured over a ssh connection.

    Returns:
        str: Configuration command
    
    """

    # Load variables from metadata

    # Load port data

    # Check validity of arguments 

    # Check whether there are commands for the speedconfig

    # Check whether ports are in the port list

    # Get commands from port data for each port and format them

    # If needed, add commit, and exit

    # Return generated command

def configure_ports(metadata, configuration_command): #Former push_cmd_over_serial
    """
    Opens a serial port and sends the configuration command for the ports so they get configured

    Args: 
        metadata (dict): Dictionary containing all the metadata of the experiment
        configuration_command (str): Command that configures the ports as desired
        
    Returns: 
        None
    """
    # Read out information needed from metadata

    # Open serial port

    # Send over command

    # If not successful raise error

    # Verify whether configuration was completed

def get_randomized_port_selection(metadata, one_per_pair = True, seed = None): 
    """
    Gives a list that contains as element a randomized selection of ports to enable.

    Meant for switch and trx

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        one_per_pair (bool): Bool for whether only one port per pair should be activated
        seed (int): Seed for randomization

    Returns:
        list: List of lists of ports that should be activated in the respective iteration
    """

    # Set seed to random value if not given

    # Sanity check for pairing

    # Generate that port list


def get_randomized_traffic_settings(metadata, seed = None):
    """
    Gives a list that contains as an element randomized traffic settings

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        seed (int): Seed for randomization

    Returns:
        list: List of traffic settings for an iteration
    """

    # Set seed to random value if not given

    # Load the traffic settings

    # Generate that list


def save_traffic_output(metadata, output_file):
    """
    Extract the relevant outputs from the traffic generation and saves them

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        output_file (str): Name of the file where the output should be saved
    
    Returns:
        None
    """

    # Load respective output file

    # Based on method save respective output

    # Return of metadata not necessary?


def run_pinpoint(metadata):
    """
    Runs the pinpoint_sleep.sh script to measure the energy usage

    Args:
        metadata (dict):Dictionary containing all the metadata of the experiment

    Returns:
        None
    """

    # Extract the relevant data

    # Start an extra process to run the script

def verify_pinpoint(metadata): 
    """
    Verifies that pinpoint actually measured some values.

    Args:
        metadata (dict):Dictionary containing all the metadata of the experiment

    Returns:
        None
    """

    # Check whether there are any output lines in the log

def save_pinpoint_log(log_path):
    """
    Saves the pinpoint log at the respective destination.

    Args:
        log_path (str): Location where data is stored

    Returns:
        None
    """

def measure_and_store(metadata):
    """
    Runs the measurements on the device and stores them in the respecitve log

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
    
    Returns:
        None
    """

    # Set timestamps in metadata

    # Get log path (with respective helper function)

    # Run the pinpoint script while not successful

    # Save output 




def run_test(device_id, exp_type, port_speed, port_type): # Former main
    """
    Executes a test on the specified device with given experiment parameters.

    Args:
        device_id (str): Identifier or model name of the device under test.
        exp_type (str): Type of experiment to run ('base', 'idle', 'switch', 'trx', 'snake-test').
        port_speed (str): Speed of the ports
        port_type (str): Type of port hardware used 

    Returns:
        None
    """

    # Load metadata, make sure all necessary information are set

    # Print some logging information
    # Print exspected duration here 

    if exp_type == 'base' or exp_type == 'idle':
        # Check with user whether transceivers are correct (depends on the case)

        # Disable all ports
        # Check successful configuration?

        # Run measurements and store them
        return
    elif exp_type == 'switch' or exp_type == 'trx':
        # Get the list with the ports for each iteration (one per pair based on case)

        # for each port selection:
            #   Enable the ports
            #   Run measurements
            #   Reset ports
        return
    elif exp_type == 'snake-test':
        
        # Get randomized traffic settings

        # Configure ports for snake tests

        # For each traffic configuration
        #   Start traffic
        #   Run measurements
        #   Verify traffic
        return
    else:
        raise ValueError(f"Unknown experiment type: {exp_type}")


    
def get_experiment_params():
    """
    
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
    



if __name__ == '__main__':

    # Here the experiment parameters are chosen. Namely we need:
    #  - device_id: Identifier for the device we want to test
    #  - exp: List of the experiment types we want to set
    #  - speed: List of speeds we want to set the port to 
    #  - port_type: Type of ports
    #  - repeats: How often a test should be repeated (former n_runs)
    # 
    # If there are arguments when the program was called, use those arguments
    # If there is a exp.yml use those
    # Otherwise give missing experiment parameters error
    # 
    # Then for all combinations of the test paramenters and repeats we should call run_test
    #

    params = get_experiment_params()
    
    device_id = params['device_id']
    exp = params['exp']
    speed = params['speed']
    port_type = [params['port_type']]
    repeats_per_test = params['repeats']

    exp_list = [
        [e, s, t]
        for e, s, t in itertools.product(exp, speed, port_type)
        for _ in range(repeats_per_test)
    ]
    random.shuffle(exp_list)

    for e, s, t in exp_list:
        run_test(device_id, e, s, t)

