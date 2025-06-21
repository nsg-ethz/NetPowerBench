from helper_functions import *
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px


def analyse_data(measurement_path, display_plot=False):
    """
    Reads the power log from the specified measurement path, calculates the median power, 
    generates a plot of power over time with a median line, saves the plot as an image, 
    and optionally displays the plot.

    Args:
        measurement_path (Path): Path to the directory containing the 'power.log' file.
        display_plot (bool, optional): If True, displays the plot. Defaults to False.

    Returns:
        numpy.float64: The median power value in watts.
    """
    print(f"Analysing data for {measurement_path} ...")
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


def prepare_data(params):
    """
    Orchestrates data preparation: Iterates over all available measurements, loads power and metadata, process the data and stores the values in power_data.yml

    Args:
        params (dict): Arguments of the execution containing device_id etc. 

    Returns:
        None
    """
    print("Preparing data ...")
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
                continue
            # TODO: Discard if data is too irregular

            metadata = load_yml(measurement_path/'metadata.yml')
            group = get_group(metadata)
            value = analyse_data(measurement_path, params['plot_data'])
            store_datapoint(measurement_path, float(value), group, power_data)    
    # Put into file
    save_as_yml(power_data, output_data_path, 'power_data.yml', sort_keys=True)
    print("Preparation complete\n")


def derive_model(params):
    """
    Derives a power consumption model for a given device configuration based on 
    preprocessed measurement data within a specified time range.

    The model includes baseline power, idle power, port and transceiver power 
    contributions, and energy per bit and packet. It also estimates offsets and saves 
    the resulting model as a YAML file for later use or inspection.

    Args:
        params (dict): Dictionary containing experiment and device configuration, including:
            - 'device_id' (str): Identifier of the device.
            - 'port_type' (str): Type of network port used.
            - 'port_speed' (str): Speed of the port.
            - 'transceivers' (str): Type of transceivers used.
            - 'traffic_generator' (str): Traffic generator used ('RDMA' or 'iperf3').
            - 'plot_data' (bool): Whether to plot intermediate results.
            - 'measurements_from' (str or None): Optional start timestamp for filtering.
            - 'measurements_to' (str or None): Optional end timestamp for filtering.

    Returns:
        None
    """
    # Load parameters into variables
    device_id = params['device_id']
    port_type = params['port_type']
    port_speed = params['port_speed']
    tranceivers = params['transceivers']
    traffic_generator = params['traffic_generator']
    plotting = params['plot_data']
    print(f"Deriving model for {device_id}, port type {port_type}, port speed {port_speed}, transceivers {tranceivers}. \n Data will be plotted: {plotting}")

    io_data_path  = Path('..','devices',device_id)
    power_data = load_yml(io_data_path/'power_data.yml')
    # Prepare variables
    P_BASE = np.nan
    P_IDLE   = np.nan
    P_TRX_IN = np.nan
    P_PORT   = np.nan
    P_TRX_UP = np.nan
    E_b = np.nan
    E_p = np.nan
    P_OFFSET = np.nan

    # Base => P_Base}
    data_base = get_datapoints(params, power_data, exp_type='base')
    if not data_base:
        print("WARNING: There seems to be no base data present.")
    else: 
        print("Processing base data\n")
        if plotting: plot_intermediate_data(data_base)
        P_BASE = np.median(data_base['power'])

    # Idle => P_IDLE, P_TRX_IN 
    data_idle = get_datapoints(params, power_data, exp_type='idle')
    if not data_idle:
        print("WARNING: There seems to be no idle data present.")
    else:
        print("Processing idle data\n")
        if plotting: plot_intermediate_data(data_idle)
        P_IDLE   = np.median(data_idle['power'])
        P_TRX_IN = np.median((data_idle['power'] - P_BASE)/data_idle['n_ports'])

    # Port => P_PORT
    data_port = get_datapoints(params, power_data, exp_type='port')
    if not data_port:
        print("WARNING: There seems to be no port data present. ")
    else:
        print("Processing port data\n")
        if plotting: plot_intermediate_data(data_port)

        df = pd.DataFrame(data_port)
        df["power_without_idle"] = df["power"] - P_IDLE
        fig = px.scatter(df, x="n_ports", y="power_without_idle", trendline="ols", trendline_options={"add_constant": False})
        
        if plotting: fig.show()

        results = px.get_trendline_results(fig)
        P_PORT = results.px_fit_results.iloc[0].params[0]

    # Trx => P_TRX_UP
    data_trx = get_datapoints(params, power_data, exp_type='trx')
    if not data_trx:
        print("WARNING: There seems to be no idle data present. ")
    else:
        print("Processing trx data\n")
        if plotting: plot_intermediate_data(data_trx)

        df = pd.DataFrame(data_trx)
        df["power_without_idle"] = df["power"] - P_IDLE
        fig = px.scatter(df, x="n_ports", y="power_without_idle", trendline="ols", trendline_options={"add_constant": False})
        
        if plotting: fig.show()
        
        results = px.get_trendline_results(fig)
        slope = results.px_fit_results.iloc[0].params[0]
        P_TRX_UP = slope - P_PORT


    # Snake-test => E_b, E_p, P_OFFSET
    data_snake = get_datapoints(params, power_data, exp_type='snake-test')
    if not data_snake:
        print("WARNING: There seems to be no snake-test data present. ")
    else:
        print("Processing snake data\n")
        if plotting: plot_intermediate_data(data_snake)

        if traffic_generator == 'RDMA':
            packet_header_length = 58
        else:
            packet_header_length = 42 
            
        packet_sizes = sorted(set(data_snake['packet_sizes']))

        df = pd.DataFrame(data_snake)
        df = df.astype({'packet_sizes' : str})
        df['bw'] = df['bw']*1e9 
        fig = px.scatter(df, x="bw", y="power", color="packet_sizes", trendline="ols", hover_data=['ts'])
        results = px.get_trendline_results(fig)
        intercepts_per_L    = [results.px_fit_results.iloc[i].params[0] for i in [mtu for mtu in range(len(packet_sizes))]]
        slopes_per_L        = [results.px_fit_results.iloc[i].params[1] for i in [mtu for mtu in range(len(packet_sizes))]]

        if plotting: fig.show()

        tmp = power_data[port_type][tranceivers]['snake-test'][port_speed]
        number_of_ports = next(iter(tmp))   

        rhs = np.multiply([8*(L + packet_header_length)/number_of_ports for L in packet_sizes], slopes_per_L)
        df = pd.DataFrame(data = {'packet_sizes' : packet_sizes, 'rhs': rhs})

        fig = px.scatter(df, x='packet_sizes', y="rhs", trendline="ols",)   

        if plotting: fig.show()

        results = px.get_trendline_results(fig)
        intercept = results.px_fit_results.iloc[0].params[0]
        slope = results.px_fit_results.iloc[0].params[1]

        if plotting: print(results.px_fit_results.iloc[0].summary())

        E_b = slope / 8
        E_p = intercept - (8*packet_header_length*E_b)

        try: 
            tmp = power_data[port_type][tranceivers]['trx'][port_speed][number_of_ports]
            power_no_traffic = np.median(tmp['power'])
        except KeyError:
            print('Warning: we miss the power value for {} ports without traffic.'.format(number_of_ports))
            print('-> Reconstructing based on other model parameters')
            power_no_traffic = P_BASE + (number_of_ports) * (P_PORT + P_TRX_IN + P_TRX_UP)
        
        P_OFFSET = np.median([intercepts_per_L - power_no_traffic])/number_of_ports

    # Save model in yml
    model_data = {
        'Arguments' : {
            'Device': device_id,
            'Port_type' : port_type,
            'Port_speed' : port_speed,
            'Transceivers' : tranceivers,
            'Traffic_generator' : traffic_generator,
            },
        'Power_model' : {
            'P_BASE': float(P_BASE),
            'P_PORT': float(P_PORT),
            'P_TRX' : float(P_TRX_IN+P_TRX_UP),
            'P_TRX_IN' : float(P_TRX_IN),
            'P_TRX_UP' : float(P_TRX_UP),
            'E_BIT' : float(E_b),
            'E_PKT' : float(E_p),
            'P_OFFSET' : float(P_OFFSET)
            }
    }
    file_name = f"power_model_{port_type}_{port_speed}_{tranceivers}_{traffic_generator}.yml"
    save_as_yml(model_data, io_data_path, file_name, sort_keys=False)

    print(yaml.dump(model_data, default_flow_style=False,sort_keys=False))
    print("Model derivation done\n")
    return

if __name__ == '__main__':
    # Load parameters either from cli or from exp.yml
    params = get_derivation_params()

    if params['derive_only'] == False:
        prepare_data(params)
    else:
        print("WARNING: Preprocessing disabled, will only derive from existing data")
    
    if params['preprocess_only'] == False:
        derive_model(params)
    else:
        print("WARNING: Derivation disabled, will only preprocess data")
    
    

