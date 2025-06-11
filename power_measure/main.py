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
        config_type (str): The way the ports should get configured ('enable','disable','snake-test','system', 'disable_all')
        port_list (list): The ports that should get configured (if None, all ports will get configured)
        ssh (bool): Whether the ports will be configured over a ssh connection.

    Returns:
        str: Configuration command
    
    """

    print(f"Generating port configuration for type {config_type} ...")

    # Check validity of arguments 
    valid_config_types = ['enable','disable','snake-test','system', 'disable_all']
    if config_type in valid_config_types:
        OPS = config_type
    else:
        raise ValueError('Invalid `config_type`. Valid options are: %s'.format(','.join(valid_config_types)))

    # Load variables from metadata
    port_file = metadata['port_file']
    port_type = metadata['port_type']
    device = metadata['device']
    needs_commit = metadata['needs_commit']

    if port_list == None:
        port_list = metadata['all_ports']

    config_path = Path('..','devices',device)

    # Load port data
    port_data = load_yml(config_path / port_file) 

    config = 'conf t\n'

    if OPS == 'system':
        if port_data['ports'][port_type]['commands'][OPS] != None:
            for CMD in port_data['ports'][port_type]['commands'][OPS]:
                config += CMD
                config += '\n'

    elif OPS == 'disable_all':
        port_type_list = port_data['ports'].keys()
        count_ports = 0
        for PT in port_type_list:
            default = port_data['ports'][PT]['speeds']['default']
            if PT == port_type and 'port_speed' in metadata:
                port_speed = metadata['port_speed']
                speed = port_data['ports'][port_type]['speeds'][port_speed]['speed_label']
                interface = port_data['ports'][port_type]['speeds'][port_speed]['interface_label']
            else:
                speed = port_data['ports'][PT]['speeds'][default]['speed_label']
                interface = port_data['ports'][PT]['speeds'][default]['interface_label']
            
            port_list = port_data['ports'][PT]['ids']
            for PORT in port_list:
                for CMD in port_data['ports'][port_type]['commands']['disable']:
                    config += CMD.replace("INTERFACE_LABEL",interface).replace("PORT",str(PORT)).replace("SPEED_LABEL",str(speed))
                    config += '\n'
                count_ports += 1
        
        metadata['total_port_number'] = count_ports

    else:
        port_speed = metadata['port_speed']
        if port_speed not in port_data['ports'][port_type]['speeds']:
            raise ValueError('Invalid `speed`: {}. \nAvailable options for this router model are: {}'.format(port_speed,port_data['ports'][port_type]['speeds'].keys()))
        port_counter = 0
        
        speed = port_data['ports'][port_type]['speeds'][port_speed]['speed_label']
        interface = port_data['ports'][port_type]['speeds'][port_speed]['interface_label']

        for PORT in port_list:
            if PORT not in port_data['ports'][port_type]['ids']:
                raise ValueError('Port number {} not listed among the {} ports.'.format(PORT,port_type))

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

def configure_ports(metadata, conf_cmd, longer_wait = False, ports_impacted = None): #Former push_cmd_over_serial
    """
    Opens a serial port and sends the configuration command for the ports so they get configured

    Args: 
        metadata (dict): Dictionary containing all the metadata of the experiment
        configuration_command (str): Command that configures the ports as desired
        longer_wait (bool): If set, the waiting time after sending the commands is increased. This is recommended if the configuration time is longer like e.g for snake test
        port_impacted (int): this gives the option of giving a better estimate of how long the configuration will take
        
    Returns: 
        None
    """

    print(f"Configuring ports over serial...")
    if conf_cmd == "":
        return
    # Read out information needed from metadata
    baudrate = metadata['baudrate']
    serial_port = metadata['serial_port']
    short_factor = metadata['wait_factor_short_s']
    long_factor = metadata['wait_factor_long_s']

    # Open serial port
    ser_port = serial.Serial(serial_port, baudrate, rtscts=False, dsrdtr=False)

    # Send over command
    out_bytes = ser_port.write(conf_cmd.encode('utf-8'))
    
    factor = long_factor if longer_wait else short_factor
    port_num = len(metadata['all_ports']) if ports_impacted == None else ports_impacted

    sleeping_time = port_num*factor
    time.sleep(sleeping_time)

    # If not successful raise error
    if out_bytes == 0:
        raise RuntimeError('Writing cmd over serial failed.')

    # TODO: Verify whether configuration was completed
    print("Sending command was successful\n")
    return

def get_randomized_port_selection(metadata, one_per_pair = True): 
    """
    Gives a list that contains as element a randomized selection of ports to enable.

    Meant for port and trx

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

    user_confirm = metadata['user_confirm']
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
                port_list.append(int(pairs_in_use[j,random.randint(0,1)]))
            iterations.append(port_list)
        else:
            iterations.append(np.reshape(pairs_in_use, -1).tolist())
    print("Ports per iterations are:")
    print(iterations)
    print()

    return iterations



def get_randomized_traffic_settings(metadata): 
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
    traffic_settings = load_yml('../traffic_gen/traffic.yml')

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


def save_traffic_output(measurement_data, output_file):
    """
    Extract the relevant outputs from the traffic generation and put them into metadata

    Args:
        measurement_data (dict): Dictionary containing metadata specific to this measurement run
        output_file (str): Name of the file where the traffic output was stored
    
    Returns:
        None
    """
    print(f"Traffic output from {output_file} is stored...")
    
    bw = float(measurement_data['bandwidth_gbps']) 
    # Load output file
    perftest_out = load_json(output_file)

    # Based on method save respective output
    if bw >= 2.5: # RDMA traffic case
        BW_average = perftest_out['results']['BW_average']
    else: # iperf3 traffic case
        BW_average = perftest_out['end']['sum']['bits_per_second']/1e9

    measurement_data['bandwidth_reached_gbps'] = BW_average

    deviation = abs(BW_average - bw) / bw

    if deviation > 0.10:
        print("\n" + "*" * 80)
        print(f"WARNING: Expected bandwidth was {bw} but only {BW_average} was reached.")
        print("This could indicate an error in the device configuration or traffic generation. ")
        print("*" * 80 + "\n")
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
    counter_1           = metadata['counter_1']
    counter_2           = metadata['counter_2']

    config_path = Path('..','devices',device)
    config = load_yml(config_path / 'config.yml')
    workspace = get_workspace_directory()
    Path(workspace / 'data' / 'log').mkdir(parents=True, exist_ok=True)

    # Start an extra process to run the script
    subprocess.run([os.path.join(workspace, "command", "pinpoint_sleep.sh"), 
            str(measure_time + start_up_delay),
            config['pinpoint']['binary'],
            str(sampling_interval),
            str(start_up_delay*1000),
            counter_1,
            counter_2
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
    workspace = get_workspace_directory()
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

    workspace = get_workspace_directory()
    log_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        workspace / "data" / "log" / 'pinpoint.log',
        log_path/'power.log'
    )
    print("Pinpoint log has been copied to power.log\n")


def measure(metadata, measurement_data):
    """
    Runs the measurements on the device 

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        measurement_data (dict): Dictionary containing metadata specific to this measurement run
    
    Returns:
        None
    """
    print("Starting measurements...")
    # Set timestamps in metadata
    measurement_data['time'] = str(datetime.datetime.now()).split('.')[0]
    measurement_data['timestamp'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp()*1e6)

    # Run the pinpoint script while not successful
    while True:
        run_pinpoint(metadata)
        if verify_pinpoint():
            break

    print("Measurements done")
    
    

def save_to_log(metadata, measurement_data):
    """
    Stores the measurements respecitve log

    Args:
        metadata (dict): Dictionary containing all the metadata of the experiment
        measurement_data (dict): Dictionary containing metadata specific to this measurement run
    
    Returns:
        None
    """
    # Get log path (with respective helper function)
    log_name = get_log_name(metadata, measurement_data)
    log_path = get_log_path(metadata, measurement_data)
    print(f"Log name: {log_name}")
    print(f"Stored at {log_path}")

    # Save output 
    save_pinpoint_log(log_path)
    save_as_yml(metadata, measurement_data, log_path, 'metadata.yml')
    print("Logging done\n")





def run_test(device_id, exp_type, port_speed, metadata): # Former main
    """
    Executes a test on the specified device with given experiment parameters.

    Args:
        device_id (str): Identifier or model name of the device under test.
        exp_type (str): Type of experiment to run ('base', 'idle', 'port', 'trx', 'snake-test', 'reset_only').
        port_speed (str): Speed of the ports
        metadata (dict):Dictionary containing all the metadata of the experiment

    Returns:
        None
    """

    # Put current parameters into metadata
    metadata['experiment_type'] = exp_type
    metadata['port_speed'] = port_speed 
    
    # Load variables
    port_type = metadata['port_type']
    user_confirm = metadata['user_confirm']

    print(f"Running {exp_type} for {device_id} with port type {port_type} and port speed {port_speed}...\n")

    if exp_type == 'reset_only':
        print("Resetting device: Disabeling all ports with default interface name...")
        disable_command = get_port_config(metadata, 'disable_all') 
        configure_ports(metadata, disable_command)
        print("Ports have been disabled")
        print("reset_only has been completed\n")
        return

    measurement_data = {}

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

        if metadata['not_reconfigure']:
            print("\n" + "*" * 80)
            print("WARNING: Reconfiguration is DISABLED.")
            print("It is assumed that all ports are disabled, otherwise this might lead to wrong results")
            print("*" * 80 + "\n")

        
        # Run measurements and store them
        measure(metadata, measurement_data)
        save_to_log(metadata, measurement_data)
        print("Experiment done\n")
        return
    elif exp_type == 'port' or exp_type == 'trx':

        if metadata['not_reconfigure']:
            print("\n" + "*" * 80)
            print("WARNING: Reconfiguration is DISABLED.")
            print("It is assumed that all ports are disabled, otherwise this might lead to wrong results")
            print("*" * 80 + "\n")

        # Get the list with the ports for each iteration (one per pair based on case)
        one_per_pair = exp_type == 'port'
        try: 
            ports_per_iteration = get_randomized_port_selection(metadata, one_per_pair)
        except ValueError as err:
            print(err)
            return


        number_tests = len(ports_per_iteration)
        i = 1
        for port_list in ports_per_iteration:
            print(f"Running {exp_type} {i} out of {number_tests} with {len(port_list)} ports")
            measurement_data['port_list'] = port_list 
            enable_command = get_port_config(metadata, 'enable', port_list) 
            configure_ports(metadata, enable_command, ports_impacted=len(port_list))

            #   Run measurements
            measure(metadata, measurement_data)
            save_to_log(metadata, measurement_data)

            #   Reset ports
            reset_command = get_port_config(metadata, 'disable', port_list)
            configure_ports(metadata, reset_command, ports_impacted=len(port_list))
            i += 1

        print("Experiment done\n")
        return
    elif exp_type == 'snake-test':
        
        # Get randomized traffic settings
        traffic_settings_list = get_randomized_traffic_settings(metadata)

        if metadata['not_reconfigure']:
            print("\n" + "*" * 80)
            print("WARNING: Reconfiguration is DISABLED.")
            print("It is assumed the device is already correctly configured, otherwise this might lead to wrong results.")
            print("*" * 80 + "\n")
        else:
            # Configure ports for snake tests
            print("Configure ports...")
            config_command = get_port_config(metadata, 'snake-test')
            configure_ports(metadata, config_command, longer_wait=True)

        number_tests = len(traffic_settings_list)
        i = 1
        for traffic_settings in traffic_settings_list:
            #   Start traffic
            measurement_data['packet_size_bytes']   = traffic_settings[0]
            measurement_data['bandwidth_gbps']      = traffic_settings[1]
            print(f"Running snake test {i} out of {number_tests} with packetsize {measurement_data['packet_size_bytes']} and {measurement_data['bandwidth_gbps']}")
            traffic_process = start_traffic(metadata, measurement_data)

            #   Run measurements
            measure(metadata, measurement_data)
            stop_traffic(traffic_process)
            save_traffic_output(measurement_data, 'perftest_out.json')
            save_to_log(metadata, measurement_data)
            i += 1
        if metadata['disable_reset']:
            print("\n" + "*" * 80)
            print("WARNING: Resetting ports after snake-test is  DISABLED.")
            print("This could possibly lead to wrong results if tests are repeated. ")
            print("*" * 80 + "\n")
        else:
            print("Reset ports...")
            reset_command = get_port_config(metadata, 'disable')

        # configure_ports(metadata, reset_command)
        print("Experiment done\n")
        return
    else:
        raise ValueError(f"Unknown experiment type: {exp_type}")


def prepare_experiments(params):
    print("Preparing experiment ...")
    
    device_id = params['device_id']
    
    # Load metadata
    check_cwd()
    config_path = Path('..','devices',device_id)
    try: meta_config = load_yml(config_path / 'config.yml')
    except EncodingWarning:
        print("\n" + "*" * 80)
        print("WARNING: Device config not found.")
        print(f"Could not run test for {device_id}")
        print("*" * 80 + "\n")
        return
    
    print("Loading metadata...")
    metadata = dict(
        device               = meta_config['DUT']['id'],
        port_file            = meta_config['DUT']['port_file'],
        port_type            = params['port_type'],
        transceivers         = params['transceivers'],
        needs_commit         = meta_config['DUT']['needs_commit'],
        seed                 = meta_config['random_seed'],
        measurement_time_s   = meta_config['measurement_time_s'],        # in seconds
        configuration_time_s = meta_config['configuration_time_s'],      # in seconds
        wait_factor_short_s  = meta_config['wait_factor_per_port_others_s'],
        wait_factor_long_s   = meta_config['wait_factor_per_port_snake-test_s'],        # in seconds
        sampling_interval_ms = meta_config['sampling_interval_ms'],      # in milliseconds 
        baudrate             = meta_config['baudrate'],
        serial_port          = meta_config['serial_port'],
        counter_1            = meta_config['counter_1'],
        counter_2            = meta_config['counter_2'],
        user_confirm         = params['user_confirm'],
        disable_reset        = params['disable_reset'],
        not_reconfigure      = params['not_reconfigure']

    )

    # Get the list of all ports
    port_file = metadata['port_file']
    port_type = metadata['port_type']
    device = metadata['device']
    config_path = Path('..','devices',device) 
    port_data = load_yml(config_path / port_file)
    metadata['all_ports'] = port_data['ports'][port_type]['ids']

    if metadata['not_reconfigure']:
        print("\n" + "*" * 80)
        print("WARNING: Reconfiguration is DISABLED.")
        print("It is assumed the device is already correctly configured, otherwise this might lead to wrong results.")
        print("*" * 80 + "\n")
    else:
        # Get command 
        cmd = get_port_config(metadata, 'system')
        # Set up device 
        configure_ports(metadata, cmd, ports_impacted=0) 

        # Get full reset command
        cmd = get_port_config(metadata, 'disable_all')
        # Reset all port types
        configure_ports(metadata, cmd, ports_impacted=metadata['total_port_number'])
    
    print("Preparation done\n")
    return metadata
    


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

    metadata = prepare_experiments(params)
    
    device_id = params['device_id']
    exp = params['exp']
    speeds = params['port_speed']
    repeats_per_test = params['repeats']


    exp_list = []
    for e, s in itertools.product(exp, speeds):
        if e =='reset_only':
            exp_list.append([e, s])  
        else:
            exp_list.extend([[e, s]] * repeats_per_test)  

    random.shuffle(exp_list)

    for exp_type, port_speed in exp_list:
        run_test(device_id, exp_type, port_speed,  metadata)

