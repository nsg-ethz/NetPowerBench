import random
import datetime
import itertools
import time

import numpy as np
import serial

from helpers import *

"""
Script to determine static power model parameters.
"""

#TODO: this should be an argument, something like "measurement type"
# - base            Nothing in
# - idle            All ports connected but admin down
# - switch          Half the ports configured
# - transceiver     All the ports configured

#TODO
# argument: port speed -> or do we cycle through all directly?

#TODO
# argument: port type -> or do we cycle through all directly?

#TODO
# argument: number runs 


def print_experiment_duration(t_run_s, n_exp):
    exp_time = t_run_s * n_exp
    print('Expected experiment duration: {}'.format(str(datetime.timedelta(seconds=exp_time))))

def get_port_config(
        metadata,
        port_list=[],
        config_type="enable",
        ssh=False
):
    """
    Prepare the list of commands required to
    activate (or deactivate) a list of ports of 
    a given type at a given speed.
    """

    # TODO: Typecheck the inputs
    # TODO: rename/adapt the logic of the `enable` parameter (unclear right now)

    port_file = metadata['port_file']
    port_type = metadata['port_type']
    port_speed = metadata['port_speed']
    device = metadata['device']
    needs_commit = metadata['needs_commit']
    config_path = Path('..','devices',device)

    # Get available port ids
    port_data = load_yml(config_path / port_file)

    # If port_list is empty, use all
    if len(port_list) == 0:
        port_list = port_data['ports'][port_type]['ids']

    # Check that the port speed is defined
    if port_speed not in port_data['ports'][port_type]['speeds']:
        raise ValueError('Invalid `speed`: {}. \nAvailable options for this router model are: {}'.format(port_speed,port_data['ports'][port_type]['speeds'].keys()))

    # Define the type of operation to execute
    valid_config_types = ['enable','disable','snake-test','speed_config']
    if config_type in valid_config_types:
        OPS = config_type
    else:
        raise ValueError('Invalid `config_type`. Valid options are: %s'.format(','.join(valid_config_types)))

    # Skip if there is no `speed_config` commands 
    # for the port to configure
    if (OPS == 'speed_config' and 
        OPS not in port_data['ports'][port_type]['commands']):
        return '', port_list

    # initialize the config commands
    config = 'conf t\n'
    # counter used to assign VLAN numbers
    port_counter = 0

    for PORT in port_list:
        
        # .. sanity check
        # test that the port id is in the port file
        if PORT not in port_data['ports'][port_type]['ids']:
            raise ValueError('Port number {} not listed among the {} ports.'.format(PORT,port_type))
            
        # .. add all the commands specified in the port file
        speed = port_data['ports'][port_type]['speeds'][port_speed]['speed_label']
        interface = port_data['ports'][port_type]['speeds'][port_speed]['interface_label']
        for CMD in port_data['ports'][port_type]['commands'][OPS]:
            vlan_number = 100+int(port_counter/2)
            config += CMD.replace("INTERFACE_LABEL",interface).replace("PORT",str(PORT)).replace("SPEED_LABEL",str(speed)).replace("VLAN_NUMBER",str(vlan_number))
            config += '\n'

        # .. increment
        port_counter += 1

    # exiting conf mode
    if needs_commit:
        config += 'commit\n'
    config += 'exit\n'
    if ssh:
        # exiting ssh connection
        config += 'exit\n'

    return config, port_list

def push_cmd_over_serial(
        serial_port,
        cmd,
        baudrate=9600
):
    """
    Open a serial port and stream a set of cmd over it.

    Returns the number of bytes written.
    """

    if cmd == "":
        return

    #TODO: Add some way to know whether the config is completed
    print("Sending commands over serial...")

    # Open port at “9600,8,N,1”, no timeout:
    ser = serial.Serial(
        serial_port,
        baudrate,       # baud rate
        rtscts = False, # disable HW flow control
        dsrdtr = False  # disable HW flow control
    )  # open serial port

    # Write commands
    out_bytes = ser.write(cmd.encode('utf-8'))
    # Test for success
    if out_bytes == 0:
        raise RuntimeError('Writing cmd over serial failed.')
    
    print("Sending commands over serial... Done.")
    return


def get_randomized_ports(
        metadata,
        one_per_pair=True,
        seed=None
):
    """
    Controlled randomization: In each iteration we randomize the ports to enable.
    """

    port_file = metadata['port_file']
    port_type = metadata['port_type']
    device = metadata['device']

    # Fixed the random generator if desired
    if seed is not None:
        print('Random seed is set to:\t {}'.format(seed))
        random.seed(seed)

    # Get available port ids
    config_path = Path('..','devices',device)
    port_data = load_yml(config_path / port_file)
    ports = port_data['ports'][port_type]['ids']

    # Initialize the output
    iterations = []

    ##
    #       We assume we list port numbers in the yaml file such that
    #       port i is connected to port i+1
    #       > We choose how to connect the ports, so this is okay
    #       > This is important when the same port types do not 
    #       have continuous port ids on a given device.
    ## 

    port_pairs = np.reshape(ports,(-1,2))
    n_pairs = np.shape(port_pairs)[0]

    # .. define the number of pairs used in a given iteration
    n_pairs_in_use = np.arange(1,n_pairs+1)
    # .. randomize the order
    random.shuffle(n_pairs_in_use)

    # .. select the ports to activate at each iteration
    for i in n_pairs_in_use:

        # .. define which pairs are considered
        pairs_in_use = port_pairs[np.random.choice(n_pairs, i, replace=False), :]
        # print(pairs_in_use)

        # Case 1: One port per pair
        if one_per_pair:
            port_list = []
            for j in np.arange(i):
                port_list.append(pairs_in_use[j,random.randint(0,1)])
            # print(port_list)
            iterations.append(port_list)

        # Case 2: Both ports in each pair
        else:
            iterations.append(np.reshape(pairs_in_use, -1).tolist())

    return iterations

def get_randomized_traffic_settings(
        metadata,
        seed=None
):
    """
    Controlled randomization: In each iteration we randomize 
    the bandwidth and packet sizes for the traffic.
    """

    # return traffic_settings
    # port_file = metadata['port_file']
    # port_type = metadata['port_type']
    # device = metadata['device']

    # Fixed the random generator if desired
    if seed is not None:
        print('Random seed is set to:\t {}'.format(seed))
        random.seed(seed)

    # Get available port ids
    # config_path = Path('..','devices',device)
    # port_data = load_yml(config_path / port_file)
    # ports = port_data['ports'][port_type]['ids']

    traffic_settings = load_yml('../traffic_gen/config.yml')

    # Initialize the output
    iterations = []

    # Loop through packet sizes and bandwidth to run
    for s in traffic_settings['packet_sizes']:
        s_bytes = s['bytes']
        for bw in traffic_settings['bandwidth_gbps']:
            if (not('max_bandwidth' in s) or (bw <= s['max_bandwidth'])):
                iterations.append([s_bytes, bw])

    # Randomize the order
    random.shuffle(iterations)
    return iterations

def save_traffic_output(output_file, metadata):
    """
    Extract the relevant outputs from the traffic generation
    """


    # RDMA traffic case
    if float(metadata['bandwidth_gbps']) >= 2.5:
        perftest_out = load_json(output_file)
        BW_average = perftest_out['results']['BW_average']

    # iperf3 traffic case
    else:
        with open(output_file) as inFile:
            perftest_out = load_json(output_file)
            BW_average = perftest_out['end']['sum']['bits_per_second']/1e9

    metadata['bandwidth_reached_gbps'] = BW_average
    
    # Clean up
    clean_process = subprocess.Popen(f'rm -f {output_file}', shell=True, stdout=subprocess.PIPE)
    clean_process.wait()
    
    return metadata

def measure_and_store(metadata):
    """
    Run the measurement, and store data if complete. Store in subdirectory 'static'
    """

    # Save metadata
    ## Add current time
    ## .. in readable form
    metadata['time'] = str(datetime.datetime.now()).split('.')[0]
    ## .. UTC timestamp
    metadata['timestamp'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp()*1e6)


    # Construct the log path
    # .. directory name

    speed_label = metadata['port_speed']
    # if metadata['port_speed'] < 1000:
    #     speed_label = '{}M'.format(metadata['port_speed'])
    # else: 
    #     speed_label = '{}G'.format(int(metadata['port_speed']/1000))

    if metadata['experiment_type'] == 'base':
        log_name = metadata['experiment_type']
    elif metadata['experiment_type'] == 'idle':
        log_name = '{}_{}'.format(
            metadata['experiment_type'],
            metadata['port_type']
        )
    elif metadata['experiment_type'] == 'switch':
        log_name = '{}_{}_{}_{}p'.format(
            metadata['experiment_type'],
            metadata['port_type'],
            speed_label,
            len(metadata['port_list'])
        )
    elif metadata['experiment_type'] == 'trx':
        log_name = '{}_{}_{}_{}p'.format(
            metadata['experiment_type'],
            metadata['port_type'],
            speed_label,
            len(metadata['port_list'])
        )
    elif metadata['experiment_type'] == 'snake-test':
        log_name = '{}_{}_{}_{}B_{}Gbps'.format(
            metadata['experiment_type'],
            metadata['port_type'],
            speed_label,
            metadata['packet_size_bytes'],
            metadata['bandwidth_gbps']
        )
    # .. piece it together
    workspace = get_workspace_directory()
    log_path = Path(
        workspace, 
        'data',
        metadata['dut_type'],      # 'router' or 'switch'
        metadata['device'],
        'static', 
        log_name,
        str(metadata['time']).replace(' ','_').split('.')[0] # time in seconds without whitespaces
    )

    # .. display for tracking
    print('Current measurement:', log_name)

    # Start measurement
    if metadata['experiment_type'] == 'snake-test':
        # Generate traffic
        print('Generating traffic')
        # # .. make sure namespaces are set right
        # subprocess.run(['bash', os.path.join(
        #     workspace, 
        #     "traffic_gen", 
        #     "setup.sh")])
        # .. generate the traffic
        traffic_gen = subprocess.Popen(['python', os.path.join(
            workspace, 
            "traffic_gen", 
            "traffic_gen.py"), 
            str(metadata['measurement_time_s'] + metadata['configuration_time_s']),
            str(metadata['bandwidth_gbps']),
            str(metadata['packet_size_bytes'])
        ])

    run_pinpoint(metadata)
    if safeguard_pinpoint() == 1:
        measure_and_store(metadata)    # recursion
    else:

        if metadata['experiment_type'] == 'snake-test':
            # Make sure the traffic generation process returned
            traffic_gen.wait()
            time.sleep(1)
            metadata = save_traffic_output('perftest_out.json', metadata)

        save_pinpoint_log(metadata,log_path)
        save_as_yml(metadata,log_path,'metadata.yml')
        print('Measurement completed.')
    return 



def main(device_id, exp_type, port_speed, port_type, single_test=False):
    
    # Sanity checks -> We call from '/automation'
    check_cwd()

    config_path = Path('..','devices',device_id)

    # Load the experiment meta data
    try: meta_config = load_yml(config_path / 'config.yml')
    except EncodingWarning:
        print('Device config not found. Typo in device ID?')
        return

    # Store all info in metadata
    metadata = dict(
        device          = meta_config['DUT']['id'],
        port_file       = meta_config['DUT']['port_file'],
        transceivers    = meta_config['DUT']['transceivers'],
        dut_type        = meta_config['DUT']['type'],
        experiment_type = exp_type,
        port_type       = port_type,
        port_speed      = port_speed, 
        seed            = meta_config['random_seed'],
        workload        = meta_config['pinpoint']['workload'],
        needs_commit         = meta_config['DUT']['needs_commit'],
        manual_speed_setting = meta_config['DUT']['manual_speed_setting'],
        measurement_time_s   = meta_config['measurement_time_s'],        # in seconds
        configuration_time_s = meta_config['configuration_time_s'],      # in seconds
        sampling_interval_ms = meta_config['sampling_interval_ms'],      # in milliseconds 
    )

    # Prepare the config to reset all ports 
    reset_config, port_list = get_port_config(
        metadata,
        config_type='disable')

    # Logging
    # TODO: make it nice
    print("ports: {}".format(metadata['port_file']))
    print("type: {}".format(metadata['experiment_type']))
    print("measurement of: {}".format(metadata['port_type']))
    # print("measurement at: {}Gbps".format(int(metadata['port_speed']/1000)))
    print("measurement time: {}s".format(metadata['measurement_time_s']))

    # Run 
    if exp_type == "base":
        # Verify that transceivers are NOT plugged
        print('No transceiver should be plugged.')
        # i = input("Continue? (y/n)\n")
        i = 'y'
        if i == 'n':
            return
        else: 
            # Verify that there is no active port
            push_cmd_over_serial(
                meta_config['serial_port'],
                reset_config,
                meta_config['baudrate'],
            )
            # Mesure
            metadata['port_number'] = 0
            metadata['port_list'] = None
            measure_and_store(metadata)

            return 

    elif exp_type == "idle":
        # Verify that transceivers ARE plugged
        print('All transceivers should be plugged.')
        # i = input("Continue? (y/n)\n") # disabling the input prompt
        i = 'y'
        if i == 'n':
            return
        else: 
            # Verify that there is no active port
            push_cmd_over_serial(meta_config['serial_port'],reset_config,
                meta_config['baudrate'])
            # Mesure
            port_data = load_yml(config_path / metadata['port_file'])
            port_list = port_data['ports'][metadata['port_type']]['ids']
            metadata['port_number'] = len(port_list)
            metadata['port_list'] = port_list
            measure_and_store(metadata)

            return

    elif exp_type == "switch":
        # Prepare the list of experiments
        exp_list = get_randomized_ports(
            metadata,
            one_per_pair=True,
            seed=metadata['seed']
        )
        print(exp_list)

    elif exp_type == "trx":
        if single_test: 
            exp_list = [[0]]
        else: 
            # Prepare the list of experiments
            exp_list = get_randomized_ports(
                metadata,
                one_per_pair=False,
                seed=metadata['seed']
            )
        print(exp_list)

    elif exp_type == "snake-test":
        # Prepare the list of traffic settings     
        exp_list = get_randomized_traffic_settings(
            metadata,
            seed=metadata['seed']
        )
        print(exp_list)

    # Log: expected completion time
    print_experiment_duration(metadata['measurement_time_s'], len(exp_list))

    # TODO: store the experiment list in some (tmp?) log

    # Set the interface at the correct speed
    if metadata['manual_speed_setting']:
        # Set the interface speed
        # .. define the config
        port_config, port_list = get_port_config(
            metadata,
            config_type='speed_config')
        # .. apply it
        push_cmd_over_serial(meta_config['serial_port'],port_config,
            meta_config['baudrate'])
        # Enable all interfaces 
        # .. define the config
        port_config, port_list = get_port_config(
            metadata,
            config_type='enable')
        # .. apply it
        push_cmd_over_serial(meta_config['serial_port'],port_config,
            meta_config['baudrate'])
        # .. wait a bit for the config to get applied
        time.sleep(10)

    # Loop through all the experiments
    if exp_type == "snake-test":
        # The port config is the same for all experiments
        # .. define the config
        port_config, port_list = get_port_config(
            metadata,
            config_type=exp_type)
        # .. apply it
        # print(port_config)
        push_cmd_over_serial(meta_config['serial_port'],port_config,
            meta_config['baudrate'])
        # .. save metadata
        metadata['port_number'] = len(port_list)
        metadata['port_list'] = port_list
        # .. wait a bit for the config to get applied
        # time.sleep(3)
        # .. loop through all experiments
        for exp in exp_list:
            metadata['packet_size_bytes']   = exp[0]
            metadata['bandwidth_gbps']      = exp[1]
            measure_and_store(metadata)
        # # .. clean the port config
        # push_cmd_over_serial(meta_config['serial_port'],reset_config,
        #         meta_config['baudrate'])
            
    # .. for other experiment type, the port config changes every time
    else:
        for port_list in exp_list:
            # .. generate the config
            port_config, port_list = get_port_config(
                metadata,
                port_list,
                config_type='enable')
            # .. apply it
            push_cmd_over_serial(meta_config['serial_port'],port_config,
                    meta_config['baudrate'])
            # .. save metadata
            metadata['port_number'] = len(port_list)
            metadata['port_list'] = port_list
            # i = input("reset? (y/n)\n")
            measure_and_store(metadata)
            # .. clean the port config
            push_cmd_over_serial(meta_config['serial_port'],reset_config,
                    meta_config['baudrate'])
            # i = input("next? (y/n)\n")

    return

if __name__ == '__main__':

    # Device to test
    device_id = 'ciscoNexus9336-FX2'
    # device_id = 'ciscoNCS55A1-24H'
    # device_id = 'N540X-8Z16G-SYS-A'
    # device_id = 'cisco8201-24H8FH'
    # device_id = 'cisco8201-32FH'
    # device_id = 'aristaDCS-7280CR3K-32D4'

    # Lists of parameters to iterate over
    # exp = ['idle','switch','trx']
    # exp = ['switch','trx']
    # exp = ['trx']
    # exp = ['switch']
    exp = ['base']
    # exp = ['idle']
    # exp = ['snake-test']
    speed = ['100G'] # 400G
    # speed = ['400G'] # 400G
    port_type = ['QSFP28']
    n_runs = 1

    # TODO: document usage
    # single_test = True
    single_test = False

    # Randomize the order 
    exp_list = []
    for e,s,t in itertools.product(exp,speed,port_type):
        for i in np.arange(n_runs): 
            exp_list.append([e,s,t])
    random.shuffle(exp_list)

    # Run all experiments
    for exp in exp_list:
        print(exp)
        main(device_id,exp[0],exp[1],exp[2],single_test)
        