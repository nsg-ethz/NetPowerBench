import os
import yaml
import argparse

def parse_cli_args():
    """
    Parses command-line arguments for running a data derivation task.

    Recognized arguments:
        -d, --device_id          : Identifier for the device (str) [required if not in exp.yml]
        --measurements_from      : Start time for measurements (str, e.g., '2025-06-01_00:00:00')
        --measurements_to        : End time for measurements (str, e.g., '2025-06-01_12:00:00')
        --preprocess_only        : Run only preprocessing step (bool, default: False)
        --derive_only            : Run only derivation step (bool, default: False)

    Returns:
        dict: A dictionary containing all parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Parse data derivation parameters.')
    parser.add_argument('-d', '--device_id', type=str, help='Device identifier')
    parser.add_argument('--measurements_from', type=str, help='Start time for measurements, only data with timestamp later than this will be considered.')
    parser.add_argument('--measurements_to', type=str, help='End time for measurements, only data with timestamp earlier than this will be considered.')
    parser.add_argument('--preprocess_only', action='store_true', help='Run only preprocessing (default: False)')
    parser.add_argument('--derive_only', action='store_true', help='Run only derivation (default: False)')

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
    args = parse_cli_args()
    has_cli_input = any(v is not None and v is not False for k, v in args.items())

    if has_cli_input:
        if args.get('device_id'):
            return args
    
    elif os.path.exists('exp.yml'): # TODO: Path
        yaml_config = load_yml('exp.yml')
        if yaml_config and 'device_id' in yaml_config:
            return {
                'device_id': yaml_config['device_id'],
                'measurements_from': yaml_config.get('measurements_from'),
                'measurements_to': yaml_config.get('measurements_to'),
                'preprocess_only': yaml_config.get('preprocess_only', False),
                'derive_only': yaml_config.get('derive_only', False)
                
            }
    raise RuntimeError("Missing experiment parameters. Provide CLI args or a valid exp.yml file.")


def load_yml(yaml_file): # Doublicate of helper in power_measure
    """
    Simple helper to load yaml data
    """

    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)