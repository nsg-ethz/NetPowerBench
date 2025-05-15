import sys
import random
from main import *

# This code uses the same functions to load data then the main code. 
# The list of experiment types wanted corresponds here to the type of configurations that are tested.
# The user confirmation is for the user to have enough time to check with an external tool (e.g. minicom) whether the device has been configured successfully.
# The mapping between the configuration that is tested and the experiment types is the following
#  - system configuration: reset_only
#  - disable everything (reset): base and idle
#  - enable a random selection of ports: port and trx
#  - configure ports for a snake-tese: snake-test
# If all pass successfully in the end all ports will be disabled
# disable_reset will lead to the configurations not being reset after configuring. 
# repeats, user_confirm and not_reconfigure will be ignored in this script.

if __name__ == '__main__':
    params = get_experiment_params()
    exp_list = params['exp']
    params['not_reconfigure'] = 'reset_only' not in exp_list # Using not reconfigure to disable system config independant of not reconfigure
    metadata = prepare_experiments(params)
    metadata['port_speed'] = params['speed'][0] # We just configure with the first speed listed
    reset_cmd = get_port_config(metadata, 'disable')

    if 'reset_only' in exp_list:
        print("The system should have been configured")
        usr1 = input("Continue? (y/n)\n")
        if usr1.lower() == 'n':
            sys.exit(0)

    if 'base' in exp_list or 'idle' in exp_list:
        # Disabling all ports
        configure_ports(metadata, reset_cmd)
        print("All ports should have been disabled.")
        usr2 = input("Continue? (y/n)\n")
        if usr2.lower() == 'n':
            sys.exit(0)

    if 'port' in exp_list or 'trx' in exp_list:
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

    if 'snake-test' in exp_list:
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
