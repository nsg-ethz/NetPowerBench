import sys
import random
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../power_measure')))
from main import *

def check_location():
    """ 
    Checks whether we call the scripts in the correct directory (test_config).
    """
    cwd_name = os.path.basename(os.getcwd())
    if cwd_name != 'test_config':
        raise Exception("Check working directory. Please run from /test_config ")

def get_test_params():
    if os.path.exists('test.yml'): # TODO: Path
        yaml_config = load_yml('test.yml')
        if yaml_config and all(k in yaml_config for k in ['device_id', 'test', 'speed', 'port_type']):
            return {
                'device_id': yaml_config['device_id'],
                'test': yaml_config['test'],
                'speed': yaml_config['speed'],
                'port_type': yaml_config['port_type'],
                'disable_reset': yaml_config.get('disable_reset', False),
                'not_reconfigure': yaml_config.get('not_reconfigure', False)
            }
    raise RuntimeError("Missing experiment parameters. Provide CLI args or a valid exp.yml file.")

def load_metadata(params):
    device_id = params['device_id']
    config_path = Path('..','devices',device_id)
    try: meta_config = load_yml(config_path / 'config.yml')
    except EncodingWarning:
        print("\n" + "*" * 80)
        print("WARNING: Device config not found.")
        print(f"Could not run test for {device_id}")
        print("*" * 80 + "\n")
        return
    
    metadata = dict(
        device               = meta_config['DUT']['id'],
        port_file            = meta_config['DUT']['port_file'],
        port_type            = params['port_type'],
        dut_type             = meta_config['DUT']['type'],
        needs_commit         = meta_config['DUT']['needs_commit'],
        seed                 = meta_config['random_seed'],
        wait_factor_short_s  = meta_config['wait_factor_per_port_others_s'],
        wait_factor_long_s   = meta_config['wait_factor_per_port_snake-test_s'],          # in seconds
        baudrate             = meta_config['baudrate'],
        serial_port          = meta_config['serial_port'],
        counter_1            = meta_config['counter_1'],
        counter_2            = meta_config['counter_2'],
        disable_reset        = params['disable_reset'],
        port_speed           = params['speed'] 

    )
    return metadata

if __name__ == '__main__':
    check_location()
    params = get_test_params()
    tests = params['test']
    metadata = load_metadata(params)
    port_file = metadata['port_file']
    port_type = metadata['port_type']
    device = metadata['device']
    config_path = Path('..','devices',device) 
    port_data = load_yml(config_path / port_file)
    metadata['all_ports'] = port_data['ports'][port_type]['ids']


    reset_cmd = get_port_config(metadata, 'disable')

    if 'system' in tests:
        cmd = get_port_config(metadata, 'system')
        configure_ports(metadata, cmd, ports_impacted=0) 
        print("The system should have been configured")
        usr1 = input("Continue? (y/n)\n")
        if usr1.lower() == 'n':
            sys.exit(0)

    if 'disable_all' in tests:
        # Disabling all ports
        cmd = get_port_config(metadata, 'disable_all')
        configure_ports(metadata, cmd)
        print("All ports should have been disabled with default label.")
        usr2 = input("Continue? (y/n)\n")
        if usr2.lower() == 'n':
            sys.exit(0)

    if 'enable' in tests:
        # Activating a random subset of the ports
        all_ports = metadata['all_ports']
        if 'seed' in metadata:
            random.seed(metadata['seed'])

        num_active_ports = random.randint(1, len(all_ports))
        active_ports = random.sample(all_ports, num_active_ports)

        activate_cmd = get_port_config(metadata, 'enable', active_ports)
        configure_ports(metadata, activate_cmd, ports_impacted=num_active_ports)

        print("The following ports should have been enabled:")
        print(sorted(active_ports))
        usr3 = input("Continue? (y/n)\n")
        if usr3.lower() == 'n':
            sys.exit(0)

        if not params['disable_reset']:
            configure_ports(metadata, reset_cmd, num_active_ports)
            print("All ports have been disabled")
        else:
            print("Port will not be reset")

    if 'snake-test' in tests:
        # Configure for snake-test
        snake_cmd = get_port_config(metadata, 'snake-test')
        configure_ports(metadata, snake_cmd, longer_wait=True)
        print("All ports should have been configured for snake-test.")
        usr4 = input("Continue? (y/n)\n")
        if usr4.lower() == 'n':
            sys.exit(0)

        if not params['disable_reset']:
            configure_ports(metadata, reset_cmd)
            print("All ports have been disabled")
        else:
            print("Ports will not be reset")
