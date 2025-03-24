def print_experiment_duration(time_per_run_s, number_of_runs):
    """
    Prints the expected duration of the experiment
    """

def get_log_path(metadata):
    """
    Returns the path including file name for logging the experiment
    """

    # Code currently in measure_and_store

def start_traffic(metadata):
    """
    Starts traffic generation
    """

def load_json(json_file):
    """
    Simple helper to load json data
    """

def load_yml(yaml_file):
    """
    Simple helper to load yaml data
    """

def save_as_json(data, destination, name):
    """
    Saves data at destination as JSON with respecitve name
    """

def save_as_yml(data, destionation, name, sort_keys = False):
    """
    Saves data at destination as YAML with respecitve name
    """

def check_cwd():
    """ 
    Checks whether we call the scripts in the correct directory (automation).
    """

def get_parent_directory():
    """
    Returns the parent of the directory the script is run from.
    """

def check_existing_directory(target_directory):
    """
    Checks whether a directory with name target_directory exists and gives a warning to the user if it does.
    """