from helper_functions import *
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px


def analyse_data(measurement_path, display_plot=False):
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

def store_datapoint(measurement_path, value, group, power_data):
    tmp = power_data
    
    for key in group.values():
        tmp = tmp.setdefault(key, {})

    tmp.setdefault('ts', []).append(measurement_path.name)
    tmp.setdefault('power', []).append(value)


def prepare_data(params):
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

def get_datapoints(params, power_data, exp_type):
    print(f"Fetching dataponits for {exp_type} ...")
    port_type = params['port_type']
    port_speed = params['port_speed']
    tranceivers = params['transceivers']
    # Get group
    if exp_type == 'base':
        group = {'exp_type':'base'}
    elif exp_type == 'idle':
        group = {
            'port_type' : port_type,
            'trx'       : tranceivers,
            'exp_type'  : 'idle'
        }
    else:
        group = {
            'port_type' : port_type,
            'trx'       : tranceivers,
            'exp_type'  : exp_type,
            'port_speed': port_speed,
        }

    # Iterate to bottom
    tmp = power_data
    for level in group.values():
        tmp = tmp[level]

    # Read, process and return
    if exp_type == 'snake-test':
        number_ports = []
        timestamps = []
        power_values = []
        packet_sizes = []
        bandwidth = []

        for n_port in tmp.keys():
            tmp_n_port = tmp[n_port]
            for mtu in tmp_n_port.keys():
                tmp_mtu = tmp_n_port[mtu]
                for bw in tmp_mtu.keys():
                    number_ports = number_ports + (n_port * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    timestamps = timestamps + tmp_mtu[bw]['ts']
                    power_values = power_values + tmp_mtu[bw]['power']
                    packet_sizes = packet_sizes + (mtu * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
                    bandwidth = bandwidth + (bw * np.ones(len(tmp_mtu[bw]['ts']), dtype=int)).tolist()
        data =  {
            'n_ports'       : number_ports,
            'ts'            : timestamps,
            'power'         : power_values,
            'packet_sizes'  : packet_sizes, # Same as packet sizes
            'bw'            : bandwidth
        }

        # Filter out measurements based on bw: 
        filtered_indices = []
        for i, bw_val in enumerate(data['bw']):
            if params['traffic_generator'] == 'RDMA' and bw_val >= 2.5:
                filtered_indices.append(i)
            elif params['traffic_generator'] == 'iperf3' and bw_val < 2.5:
                filtered_indices.append(i)

        data = {
            key: [values[i] for i in filtered_indices]
            for key, values in data.items()
        }

    elif exp_type == 'base':
        data = {
            'n_ports':   [0 for _ in tmp['ts']],
            'ts'        : tmp['ts'],
            'power'     : tmp['power'],
        }
    else:
        number_ports = []
        timestamps   = []
        power_values = []
        for n_port in tmp.keys():
            number_ports = number_ports + (n_port * np.ones(len(tmp[n_port]['ts']), dtype=int)).tolist()
            timestamps = timestamps + tmp[n_port]['ts']
            power_values = power_values + tmp[n_port]['power']

        data = {
            'n_ports'   : number_ports,
            'ts'        : timestamps,
            'power'     : power_values
        }
    
    # Discard data with timestamps out of range 
    time_from = parse_timestamp(params['measurements_from']) if params['measurements_from'] != None else None
    time_to   = parse_timestamp(params['measurements_to']) if params['measurements_to'] != None else None

    parsed_ts = [parse_timestamp(ts)  for ts in data['ts']]

    valid_indices = [
        i for i, t in enumerate(parsed_ts)
        if (time_from is None or t >= time_from) and (time_to is None or t <= time_to)
    ]
    if not valid_indices:
        return None

    return {
        key: [values[i] for i in valid_indices]
        for key, values in data.items()
    }


def derive_model(params):
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
    
    

