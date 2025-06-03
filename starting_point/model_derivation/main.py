from helper_functions import *
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px


def analyse_data(measurement_path, display_plot=False):
    # Load power data
    df = pd.read_csv(measurement_path / 'power.log', names=['MCP1', 'MCP2'], header=0)
    df['Power [W]'] = (df['MCP1'] + df['MCP2']) / 1000.0
    median_power = df['Power [W]'].median()

    # Add a column for plotting the median line
    df['Median [W]'] = median_power

    # Create plot and save it
    fig = px.line(df, x=df.index, y=['Power [W]', 'Median [W]'], title="Power Consumption Over Time")
    plot_path = measurement_path / "power_plot.png"
    fig.write_image(str(plot_path))

    if display_plot:
        fig.show()

    return median_power

def store_datapoint(measurement_path, value, group, power_data):
    tmp = power_data
    
    for key in group.values():
        tmp = tmp.setdefault(key, {})

    tmp.setdefault('ts', []).append(measurement_path.name)
    tmp.setdefault('power', []).append(value)


def prepare_data(params):
    device_id = params['device_id']
    power_data = {'device' : device_id}
    # Load the paths
    input_data_path = Path('..','data',device_id)
    output_data_path = Path('..','devices',device_id)
    # iterate over all experiment types
    for exp_type_path in input_data_path.glob('*'):
        # iterate over each experiment run
        for measurement_path in sorted(exp_type_path.glob('*')):
            power_log = pd.read_csv(measurement_path/'power.log')

            # Discard if only one PSU was plugged in, meaning the average power was less than 1W
            if (float(power_log.iloc[:,0].mean()) < 1000 or float(power_log.iloc[:,1].mean()) < 1000):
                print(f'WARING: Appears to have only one channel measuring.\nDiscarding {measurement_path}')
                return
            # TODO: Discard if data is too irregular

            metadata = load_yml(measurement_path/'metadata.yml')
            group = get_group(metadata)
            value = analyse_data()
            store_datapoint(measurement_path, value, group, power_data)    
    # Put into file
    save_as_yml(power_data, output_data_path, 'power_data.yml', sort_keys=True)


def derive_model():
    return

if __name__ == '__main__':
    # Load parameters either from cli or from exp.yml
    params = get_derivation_params()

    if params['derive_only'] == False:
        prepare_data()
    else:
        print("WARNING: Preprocessing disabled, will only derive from existing data")
    
    if params['preprocess_only'] == False:
        derive_model()
    else:
        print("WARNING: Derivation disabled, will only preprocess data")
    
    

