



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

    # The list of ports should be loaded separately

    # Case distinction for different experiment types

    




if __name__ == '__main__':

    # Here the experiment parameters should be chosen. Namely we need:
    #  - device_id: Identifier for the device we want to test
    #  - exp: List of the experiment types we want to set
    #  - speed: List of speeds we want to set the port to 
    #  - port_type: List of types of ports
    #  - repeats_per_test: How often a test should be repeated (former n_runs)
    # 
    # Then for all combinations of the test paramenters and repeats we should call run_test
    #
    # Proposal: Instead of hardcoding the experiment parameters, have them in a separate yml 
    #   so that the code doesn't have to be changed for different experiments