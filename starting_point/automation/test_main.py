import random
import itertools
import datetime
import serial
import subprocess
import shutil
import numpy as np
from pathlib import Path

from helper_functions import *



def get_port_config(metadata, config_type, port_list = None):
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

    print(f"Generating port configuration for type {config_type} ...")

    # Load variables from metadata
    port_file = metadata['port_file']
    port_type = metadata['port_type']
    port_speed = metadata['port_speed']
    device = metadata['device']
    needs_commit = metadata['needs_commit']
    if port_list == None:
        port_list = metadata['all_ports']
        
    config_path = Path('..','devices',device)

    # Load port data
    port_data = load_yml(config_path / port_file) 


    # Check validity of arguments 
    valid_config_types = ['enable','disable','snake-test']
    if config_type in valid_config_types:
        OPS = config_type
    else:
        raise ValueError('Invalid `config_type`. Valid options are: %s'.format(','.join(valid_config_types)))

    if port_speed not in port_data['ports'][port_type]['speeds']:
        raise ValueError('Invalid `speed`: {}. \nAvailable options for this router model are: {}'.format(port_speed,port_data['ports'][port_type]['speeds'].keys()))

    config = 'conf t\n'
    port_counter = 0

    for PORT in port_list:
        if PORT not in port_data['ports'][port_type]['ids']:
            raise ValueError('Port number {} not listed among the {} ports.'.format(PORT,port_type))

        speed = port_data['ports'][port_type]['speeds'][port_speed]['speed_label']
        interface = port_data['ports'][port_type]['speeds'][port_speed]['interface_label']

        for CMD in port_data['ports'][port_type]['commands'][OPS]:
            vlan_number = 100+int(port_counter/2)
            config += CMD.replace("INTERFACE_LABEL",interface).replace("PORT",str(PORT)).replace("SPEED_LABEL",str(speed)).replace("VLAN_NUMBER",str(vlan_number))
            config += '\n'
        
        port_counter += 1

    if needs_commit:
        config += 'commit\n'
    config += 'exit\n'

    print("Port configuration command generated\n")

    return config

def configure_ports(metadata, conf_cmd): #Former push_cmd_over_serial
    """
    Opens a serial port and sends the configuration command for the ports so they get configured

    Args: 
        metadata (dict): Dictionary containing all the metadata of the experiment
        configuration_command (str): Command that configures the ports as desired
        
    Returns: 
        None
    """

    print(f"Configuring ports over serial...")
    if conf_cmd == "":
        return
    # Read out information needed from metadata
    baudrate = metadata['baudrate']
    serial_port = metadata['serial_port']

    # Open serial port
    ser_port = serial.Serial(serial_port, baudrate, rtscts=False, dsrdtr=False)

    # Send over command
    out_bytes = ser_port.write(conf_cmd.encode('utf-8'))

    # If not successful raise error
    if out_bytes == 0:
        raise RuntimeError('Writing cmd over serial failed.')

    # TODO: Verify whether configuration was completed
    print("Sending command was successful\n")
    return

def get_randomized_port_selection(metadata, user_confirm, one_per_pair = True): 
    """
    Gives a list that contains as element a randomized selection of ports to enable.

    Meant for switch and trx

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        one_per_pair (bool): Bool for whether only one port per pair should be activated

    Returns:
        list: List of lists of ports that should be activated in the respective iteration
    """

    print("Generating randomized port selection...")
    

    # Set seed to random value if not given
    seed = metadata['seed']
    if seed is not None:
        print('Random seed is set to:\t {}'.format(seed))
        random.seed(seed)

    ports = metadata['all_ports']
    iterations = []

    port_pairs = np.reshape(ports,(-1,2))

    # Sanity check for pairing
    print(f"The pairing of the ports is this: ")
    for i in port_pairs:
        print(i)

    if user_confirm:
        inp = input("Please verify that the ports are connected accordingly. (y/n)\n")
        if inp == 'n':
            raise ValueError("Invalid port pairing: Experiment stopped. Please list the ports in ports.yml according to the wiring.") 

    num_pairs = np.shape(port_pairs)[0]
    num_pairs_in_use = np.arange(1,num_pairs+1)
    random.shuffle(num_pairs_in_use)

    # Generate that port list
    for i in num_pairs_in_use:
        pairs_in_use = port_pairs[np.random.choice(num_pairs, i, replace=False), :]

        if one_per_pair:
            port_list = []
            for j in np.arange(i):
                port_list.append(pairs_in_use[j,random.randint(0,1)])
            iterations.append(port_list)
        else:
            iterations.append(np.reshape(pairs_in_use, -1).tolist())
    print("Porst per iterations are:")
    print(iterations)
    print()

    return iterations






def get_randomized_traffic_settings(metadata): # TODO Check whether we actually need metadata (e.g. for logging)
    """
    Gives a list that contains as an element randomized traffic settings

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment

    Returns:
        list: List of traffic settings for an iteration
    """
    print("Generating randomized traffic settings...")
    # Set seed to random value if not given
    seed = metadata['seed']
    if seed is not None:
        print('Random seed is set to:\t {}'.format(seed))
        random.seed(seed)

    # Load the traffic settings
    traffic_settings = load_yml('../traffic_gen/config.yml')

    # Generate that list
    iterations = []
    for packet_size in traffic_settings['packet_sizes']:
        bytes = packet_size['bytes']
        for bandwidth in traffic_settings['bandwidth_gbps']:
            if (not('max_bandwidth' in packet_size) or (bandwidth <= packet_size['max_bandwidth'])):
                iterations.append([bytes, bandwidth])

    # Randomize
    random.shuffle(iterations)
    print("Random traffic settings generated\n")
    return iterations


def save_traffic_output(metadata, output_file):
    """
    Extract the relevant outputs from the traffic generation and saves them

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        output_file (str): Name of the file where the traffic output was stored
    
    Returns:
        None
    """
    print(f"Traffic output from {output_file} is stored...")
    # Load output file
    perftest_out = load_json(output_file)

    # Based on method save respective output
    if float(metadata['bandwidth_gbps']) >= 2.5: # RDMA traffic case
        BW_average = perftest_out['results']['BW_average']
    else: # iperf3 traffic case
        BW_average = perftest_out['end']['sum']['bits_per_second']/1e9

    metadata['bandwidth_reached_gbps'] = BW_average

    os.remove(output_file)

    print(f"Bandwidth reached: {BW_average}\n")
    return

def run_pinpoint(metadata):
    """
    Runs the pinpoint_sleep.sh script to measure the energy usage

    Args:
        metadata (dict):Dictionary containing all the metadata of the experiment

    Returns:
        None
    """
    print("Running pinpoint...")
    # Extract the relevant data
    measure_time        = metadata['measurement_time_s']
    sampling_interval   = metadata['sampling_interval_ms']
    start_up_delay      = metadata['configuration_time_s']
    device              = metadata['device']

    config_path = Path('..','devices',device)
    config = load_yml(config_path / 'config.yml')
    workspace = get_parent_directory()
    Path(workspace / 'data' / 'log').mkdir(parents=True, exist_ok=True)

    # Start an extra process to run the script
    subprocess.run([os.path.join(workspace, "command", "pinpoint_sleep.sh"), 
            str(measure_time + start_up_delay),
            config['pinpoint']['binary'],
            str(sampling_interval),
            str(start_up_delay*1000)
        ])
    print("Pinpoint done\n")

def verify_pinpoint(): 
    """
    Verifies that pinpoint actually measured some values.

    Args:
        None

    Returns:
        bool: True if pinpoint was successful, False otherwise
    """

    # Check whether there are any output lines in the log
    workspace = get_parent_directory()
    num_lines = sum(1 for line in open(os.path.join(workspace, "data", "log", "pinpoint.log")))
    if num_lines <= 3:
        print("Pinpoint issue detected.")
        return False
    print("No pinpoint issue detected\n")
    return True

def save_pinpoint_log(log_path): 
    """
    Saves the pinpoint log at the respective destination.

    Args:
        log_path (str): Location where data is stored

    Returns:
        None
    """

    workspace = get_parent_directory()
    log_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        workspace / "data" / "log" / 'pinpoint.log',
        log_path/'power.log'
    )
    print("Pinpoint log has been copied to power.log\n")


def measure_and_store(metadata):
    """
    Runs the measurements on the device and stores them in the respecitve log

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
    
    Returns:
        None
    """
    print("Starting measurements...")
    # Set timestamps in metadata
    metadata['time'] = str(datetime.datetime.now()).split('.')[0]
    metadata['timestamp'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp()*1e6)

    # Get log path (with respective helper function)
    log_name = get_log_name(metadata)
    log_path = get_log_path(metadata)
    print(f"Log name: {log_name}")
    print(f"Stored at {log_path}")

    # Run the pinpoint script while not successful
    while True:
        run_pinpoint(metadata)
        if verify_pinpoint():
            break
    
    # Save output 
    save_pinpoint_log(log_path)
    print("Measure and store done\n")




def run_test(device_id, exp_type, port_speed, port_type, user_confirm): # Former main
    """
    Executes a test on the specified device with given experiment parameters.

    Args:
        device_id (str): Identifier or model name of the device under test.
        exp_type (str): Type of experiment to run ('base', 'idle', 'switch', 'trx', 'snake-test').
        port_speed (str): Speed of the ports
        port_type (str): Type of port hardware used 
        user_confirm (bool): Whether a user confirmation is wished

    Returns:
        None
    """
    print(f"Running {exp_type} for {device_id} with port type {port_type} and port speed {port_speed}...")

    # Load metadata
    check_cwd()
    config_path = Path('..','devices',device_id)
    meta_config = Path('devices', device_id) 
    try: meta_config = load_yml(config_path / 'config.yml')
    except EncodingWarning:
        print('Device config not found. Could not run test for {}'.format(device_id))
        return
    
    print("Loading metadata...")
    metadata = dict(
        device               = meta_config['DUT']['id'],
        port_file            = meta_config['DUT']['port_file'],
        transceivers         = meta_config['DUT']['transceivers'],
        dut_type             = meta_config['DUT']['type'],
        experiment_type      = exp_type,
        port_type            = port_type,
        port_speed           = port_speed, 
        seed                 = meta_config['random_seed'],
        needs_commit         = meta_config['DUT']['needs_commit'],
        manual_speed_setting = meta_config['DUT']['manual_speed_setting'],
        measurement_time_s   = meta_config['measurement_time_s'],        # in seconds
        configuration_time_s = meta_config['configuration_time_s'],      # in seconds
        sampling_interval_ms = meta_config['sampling_interval_ms'],      # in milliseconds 
        baudrate             = meta_config['baudrate'],
        serial_port          = meta_config['serial_port']           
    )
    
    # Get the list of all ports
    port_file = metadata['port_file']
    port_type = metadata['port_type']
    device = metadata['device']
    config_path = Path('..','devices',device) 
    port_data = load_yml(config_path / port_file)
    metadata['all_ports'] = port_data['ports'][port_type]['ids']

    # Check with user whether transceivers are correct (depends on the case)
    q = "No" if exp_type == 'base' else "All"
    print(f"{exp_type} test: {q} transceivers should be plugged in.")

    if(user_confirm):
        inp = input("Do you want to continue? (y/n)\n")
        if inp == 'n':
            return
    print()

    print(f"Starting {exp_type}...")
    if exp_type == 'base' or exp_type == 'idle':

        # Disable all ports
        disable_command = get_port_config(metadata, 'disable') 
        configure_ports(metadata, disable_command)
        print("Ports have been disabled")

        # Run measurements and store them
        measure_and_store(metadata)
        print("Experiment done\n")
        return
    elif exp_type == 'switch' or exp_type == 'trx':

        # Get the list with the ports for each iteration (one per pair based on case)
        one_per_pair = exp_type == 'switch'
        try: 
            ports_per_iteration = get_randomized_port_selection(metadata, user_confirm, one_per_pair)
        except ValueError as err:
            print(err)
            return

        reset_command = get_port_config(metadata, 'disable')

        number_tests = len(ports_per_iteration)
        i = 1
        for port_list in ports_per_iteration:
            enable_command = get_port_config(metadata, 'enable', port_list) 
            configure_ports(metadata, enable_command)

            metadata['port_list'] = port_list #TODO reviwe where port_list is needed

            print(f"Running {exp_type} {i} out of {number_tests} with {len(port_list)} ports")
            
            #   Run measurements
            measure_and_store(metadata)

            #   Reset ports
            configure_ports(metadata, reset_command)
            i += 1

        print("Experiment done\n")
        return
    elif exp_type == 'snake-test':
        
        # Get randomized traffic settings
        traffic_settings_list = get_randomized_traffic_settings(seed=metadata['seed'])

        # Configure ports for snake tests
        print("Configure ports...")
        config_command = get_port_config(metadata, 'snake-test')
        configure_ports(metadata, config_command)

        number_tests = len(traffic_settings_list)
        i = 1
        for traffic_settings in traffic_settings_list:
            #   Start traffic
            metadata['packet_size_bytes']   = traffic_settings[0]
            metadata['bandwidth_gbps']      = traffic_settings[1]
            print(f"Running snake test {i} out of {number_tests} with packetsize {metadata['packet_size_bytes']} and {metadata['bandwidth_gbps']}")
            traffic_process = start_traffic(metadata)

            #   Run measurements
            measure_and_store(metadata)

            stop_traffic(traffic_process)
            i += 1
        
        print("Reset ports...")
        reset_command = get_port_config(metadata, 'disable')
        configure_ports(metadata, reset_command)
        print("Experiment done\n")
        return
    else:
        raise ValueError(f"Unknown experiment type: {exp_type}")




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
    user_confirm = params['user_confirm']

    exp_list = [
        [e, s, t]
        for e, s, t in itertools.product(exp, speed, port_type)
        for _ in range(repeats_per_test)
    ]
    random.shuffle(exp_list)

    for exp_type, port_speed, port_type in exp_list:
        run_test(device_id, exp_type, port_speed, port_type, user_confirm)

