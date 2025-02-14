from pathlib import Path
import yaml

import pandas as pd

from helpers import *

def plot_intermediate_data(dict):
    """
    Simple helper to display intermediate power data
    """
    tmp = dict.copy()
    tmp.pop('n_ports')
    tmp = pd.DataFrame.from_dict(tmp)
    tmp.sort_values(by='ts',inplace=True)
    fig = px.scatter(tmp, x='ts',y='power')
    fig.show()
    return 

# Computing the model parameters from the power data
def derive_model(param, plotting=True):

    device_id = param['metadata']['device_id']
    port_type = param['configuration']['port_type']
    port_speed_label = param['configuration']['port_speed']
    tranceiver_module = param['configuration']['tranceiver_module']


    # TODO: I'm not sure how to deal with this 
    # when I used both RDMA and iperf for the same config...
    # -> Use whichever of the two values. 
    #    The error induced by doing that is minuscule.
    packet_header_length = 58 # RDMA
    # packet_header_length = 42 # iperf3

    # ===========
    # Device-specific cases/weirdness
    #
    extra_ports_on = 0
    P_TRX_IN_april_only = False
    P_IDLE_april_only   = False
    P_IDLE_oct_only     = False
    night_filter        = False
    infer_idle_power    = False
    infer_trx_in_power  = False
    force_zero_Epkt     = False
    if device_id == 'aristaDCS-7280CR3K-32D4':
        # infer_idle_power = True
        print()
    elif device_id == 'cisco8201-32FH':
        print()
        # infer_idle_power = True
    elif device_id == 'ciscoNexus9336-FX2':
        print()
        # infer_idle_power = True
    elif device_id == 'ciscoNCS55A1-24H':
        P_TRX_IN_april_only = True
        if port_speed_label == '100G':
            extra_ports_on = 8
            P_IDLE_april_only = True
        elif port_speed_label in ['50G', '25G']:
            night_filter = True
            P_IDLE_oct_only = True
            # It looks like p_idle gets smaller when we set the interfaces
            # at 25G (does not happen at 50G though)
            # -> To avoid biasing the regressions on P_switch and P_trx
            #    we let the regression choose its constant.
            #    This leads to results that make sense regarding the interface power 
            #    but appling this model will most likely overestimate the "idle/base" power
            infer_idle_power = True
    elif device_id == 'N540X-8Z16G-SYS-A':
        if ((port_type == 'SFP') and 
            (tranceiver_module in ['LR','T']) and 
            (port_speed_label in ['1G','100M','10M'])):
            infer_idle_power = True
            infer_trx_in_power = True            
            packet_header_length = 42 # iperf3
            # force_zero_Epkt = True



    # 
    # ===========


    # Set paths
    input_data_path  = Path('..','devices',device_id)
    output_data_path = Path('..','devices',device_id)

    # Load power data
    power_data = load_yml(input_data_path/'power_data.yml')

    # Initialize the output dictionary
    model_data = {'device' : device_id}

    # Step 1: P_BASE
    # .. Define the dictionary group of interest
    group = {'exp_type':'base'}
    data_base = get_datapoints(power_data,group)
    if plotting: plot_intermediate_data(data_base)
    # print(data_base)

    P_BASE = np.median(data_base['power'])

    # Step 2: P_TRX_IN

    P_IDLE   = np.nan
    P_TRX_IN = np.nan

    # .. Define the dictionary group of interest
    group = {
        'port_type' : port_type,
        'trx'       : tranceiver_module,
        'exp_type'  : 'idle'
    }
    print('data_idle')
    data_idle = get_datapoints(power_data,group)

    if not data_idle:
        print("No idle data present?")
    else:
        if plotting: plot_intermediate_data(data_idle)

        P_IDLE   = np.median(data_idle['power'])
        P_TRX_IN = np.median((data_idle['power'] - P_BASE)/data_idle['n_ports'])

        # P_TRX_IN and P_IDLE corection
        if P_TRX_IN_april_only:
            print('Warning: Computing P_TRX_IN with April 2024 data only.')
            filter = [('2024-04' in ts) for ts in data_idle['ts']]
            filtered_power = np.array(data_idle['power'])[filter]
            filtered_n_ports = np.array(data_idle['n_ports'])[filter]
            P_TRX_IN = np.median((filtered_power - P_BASE)/filtered_n_ports)
        if P_IDLE_april_only:
            print('Warning: Computing P_IDLE with April 2024 data only.')
            filter = [('2024-04' in ts) for ts in data_idle['ts']]
            filtered_power = np.array(data_idle['power'])[filter]
            P_IDLE   = np.median(filtered_power)
        if P_IDLE_oct_only:
            print('Warning: Computing P_IDLE with October 2024 data only.')
            filter = [('2024-10' in ts) for ts in data_idle['ts']]
            filtered_power = np.array(data_idle['power'])[filter]
            P_IDLE   = np.median(filtered_power)

        print(P_IDLE)
        print(P_TRX_IN)

    # Step 3: P_PORT
    # .. Define the dictionary group of interest
    group = {
        'port_type' : port_type,
        'trx'       : tranceiver_module,
        'exp_type'  : 'switch',
        'port_speed': port_speed_label,
    }

    P_PORT   = np.nan
    P_TRX_UP = np.nan
    
    data_switch = get_datapoints(power_data,group)
    
    if not data_switch:
        print("No switch data present?")
    
    else:

        print('data_switch')
        if plotting: plot_intermediate_data(data_switch)
        # print(data_switch)
        df = pd.DataFrame(data_switch)

        if night_filter:
            print('Warning: using the night time data only')
            filter = [(('2024-10-27_00' in ts) or
                    ('2024-10-27_01' in ts) or
                    ('2024-10-27_02' in ts) or
                    ('2024-10-26_23' in ts))
                    for ts in data_switch['ts']]
            df = df.loc[filter]



        if infer_idle_power:
        # .. If the `idle` power data we have does not match with the `switch`
        #    measurement data, infer P_IDLE from the linear regression
            
            print('Infering P_IDLE from the linear regression...')
            # TODO That's rather pointless since we don't used P_IDLE
            # directly in the model. That's just a mean to derive P_TRX_IN
            # -> We MUST have a match between P_BASE and P_IDLE for that, 
            #    there is no way around that I can think of...
            fig = px.scatter(df, 
                            x="n_ports", 
                            y="power", 
                            trendline="ols",
                            )
            if plotting: fig.show()
            results = px.get_trendline_results(fig)
            P_IDLE = results.px_fit_results.iloc[0].params[0]
            slope  = results.px_fit_results.iloc[0].params[1]
            print(results.px_fit_results.iloc[0].summary())

            if infer_trx_in_power:
                print('Infering P_TRX_IN based on the linear regression for P_IDLE...')
                P_TRX_IN = (P_IDLE - P_BASE)/df['n_ports'].max()



        else:
        # .. Force the regression to intersect at P_IDLE in order to match 
        #    the expectation from the model
            df["power_without_idle"] = df["power"] - P_IDLE
            fig = px.scatter(df, 
                            x="n_ports", 
                            y="power_without_idle", 
                            trendline="ols",
                            trendline_options={"add_constant": False}
                            )
            if plotting: fig.show()
            results = px.get_trendline_results(fig)
            slope = results.px_fit_results.iloc[0].params[0]
            print(results.px_fit_results.iloc[0].summary())

        P_PORT = slope
        print(P_IDLE)
        print(P_PORT)


        # Step 4: P_TRX_UP
        # .. Define the dictionary group of interest
        group = {
            'port_type' : port_type,
            'trx'       : tranceiver_module,
            'exp_type'  : 'trx',
            'port_speed': port_speed_label,
        }

        data_trx = get_datapoints(power_data,group)
        if not data_trx:
            print("No trx data present?")
        else: 
            print('data_trx')
            if plotting: plot_intermediate_data(data_trx)

            df = pd.DataFrame(data_trx)
            if night_filter:
                print('Warning: using the night time data only')
                filter = [(('2024-10-27_00' in ts) or
                        ('2024-10-27_01' in ts) or
                        ('2024-10-27_02' in ts) or
                        ('2024-10-26_23' in ts))
                        for ts in data_trx['ts']]
                df = df.loc[filter]
            # display(df)

            if infer_idle_power:
                print('Infering P_IDLE from the linear regression...')
                # TODO That's rather pointless since we don't used P_IDLE
                # directly in the model. That's just a mean to derive P_TRX_IN
                # -> We MUST have a match between P_BASE and P_IDLE for that, 
                #    there is no way around that I can think of...
                fig = px.scatter(df, 
                                x="n_ports", 
                                y="power", 
                                trendline="ols",
                                )
                if plotting: fig.show()
                results = px.get_trendline_results(fig)
                P_IDLE = results.px_fit_results.iloc[0].params[0]
                slope  = results.px_fit_results.iloc[0].params[1]
                print(results.px_fit_results.iloc[0].summary())

            else:
                df["power_without_idle"] = df["power"] - P_IDLE
                # display(df)
                fig = px.scatter(df, 
                                x="n_ports", 
                                y="power_without_idle", 
                                trendline="ols",
                                trendline_options={"add_constant": False}
                                )
                if plotting: fig.show()
                results = px.get_trendline_results(fig)
                slope = results.px_fit_results.iloc[0].params[0]
                print(results.px_fit_results.iloc[0].summary())

            P_TRX_UP = slope - P_PORT
            print(P_IDLE)


    # Step 5: E_b, E_p
    # .. Define the dictionary group of interest
    group = {
        'port_type' : port_type,
        'trx'       : tranceiver_module,
        'exp_type'  : 'snake-test',
        'port_speed': port_speed_label,
    }
    packet_sizes = [256, 512, 1024, 2048, 4096]
    # packet_sizes = [256, 512, 1024, 2048]
    # packet_sizes = [1024, 2048, 4096]
    E_b = np.nan
    E_p = np.nan
    P_offset = np.nan

    data_snake = get_datapoints(power_data,group)
    
    if not data_snake:
        print("No snake-test data present?")
    
    else:
        df = pd.DataFrame(data_snake)
        # .. adjust the data type for plotting
        df = df.astype({'mtu' : str})
        # .. convert bw into bps
        df['bw'] = df['bw']*1e9 
        # display(df)    
        fig = px.scatter(df, 
                        x="bw", 
                        y="power", 
                        color="mtu",
                        trendline="ols",
                        hover_data=['ts']
                        )
        
        results = px.get_trendline_results(fig)
        # print(results.px_fit_results.iloc[4].params[1])
        intercepts_per_L    = [results.px_fit_results.iloc[i].params[0] for i in [mtu for mtu in range(len(packet_sizes))]]
        slopes_per_L        = [results.px_fit_results.iloc[i].params[1] for i in [mtu for mtu in range(len(packet_sizes))]]
        if plotting: fig.show()


        # .. Get the number of ports used during snake-testing
        tmp = power_data[port_type][tranceiver_module]['snake-test'][port_speed_label]
        number_of_ports = next(iter(tmp))

        rhs = np.multiply(
            [8*(L + packet_header_length)/number_of_ports for L in packet_sizes],
            slopes_per_L)
        df = pd.DataFrame(data = {'packet_sizes' : packet_sizes, 'rhs': rhs})
        if force_zero_Epkt:
            fig = px.scatter(df, 
                            x='packet_sizes', 
                            y="rhs", 
                            trendline="ols",
                            trendline_options={"add_constant": False}
                            )    
            if plotting: fig.show()
            results = px.get_trendline_results(fig)
            slope = results.px_fit_results.iloc[0].params[0]
            intercept = 0

            E_b = slope / 8
            E_p = intercept - (8*packet_header_length*E_b)

        else:
            fig = px.scatter(df, 
                            x='packet_sizes', 
                            y="rhs", 
                            trendline="ols",
                            )    
            if plotting: fig.show()
            results = px.get_trendline_results(fig)
            intercept = results.px_fit_results.iloc[0].params[0]
            slope = results.px_fit_results.iloc[0].params[1]


        if plotting: print(results.px_fit_results.iloc[0].summary())
        E_b = slope / 8
        E_p = intercept - (8*packet_header_length*E_b)
        # print("E_b={}\nE_p={}".format(E_b,E_p))
        
        # Step 6: P_offset
        # TODO: We are missing the "low-traffic" data point 
        # that would allow us to compute the P_offset as described in the report
        # -> Using the regression intercept for now.

        # .. Correct the intercepts
        corrected_intercepts = [i - extra_ports_on*(P_PORT+P_TRX_IN) for i in intercepts_per_L]
        # .. Get the corresponding power with no traffic but all ports up
        # -> Sometimes we got extra ports that were left on but not used for the snake test
        try: 
            tmp = power_data[port_type][tranceiver_module]['trx'][port_speed_label][number_of_ports+extra_ports_on]
            power_no_traffic = np.median(tmp['power'])
        except KeyError:
            print('Warning: we miss the power value for {} ports without traffic.'.format(number_of_ports+extra_ports_on))
            print('-> Reconstructing based on other model parameters')
            power_no_traffic = P_BASE + (number_of_ports+extra_ports_on) * (P_PORT + P_TRX_IN + P_TRX_UP)
        # .. Compute the offset 
        P_offset = np.median([corrected_intercepts - power_no_traffic])/number_of_ports


    # Summary
    # print('Device model:\t',device_id)
    # print('Port type:\t',port_type)
    # print('Port speed:\t',port_speed_label)

    model_data = {
            'P_BASE': float(P_BASE),
            'P_PORT': float(P_PORT),
            'P_TRX' : float(P_TRX_IN+P_TRX_UP),
            'P_TRX_IN' : float(P_TRX_IN),
            'P_TRX_UP' : float(P_TRX_UP),
            'E_BIT' : float(E_b),
            'E_PKT' : float(E_p),
            'P_OFFSET' : float(P_offset)
    }

    print(yaml.dump(model_data, default_flow_style=False,sort_keys=False))

    latex_string = '& {} & {} & {} &'.format(
        port_type,
        tranceiver_module,
        port_speed_label,    
    )
    sep = ' & '
    latex_string+=str(int(P_BASE))
    latex_string+=sep
    latex_string+=str(round(P_PORT,2))
    latex_string+=sep
    latex_string+=str(round(P_TRX_IN,2))
    latex_string+=sep
    latex_string+=str(round(P_TRX_UP,2))
    latex_string+=sep
    latex_string+=str(int(E_b*1e12))
    latex_string+=sep
    latex_string+=str(int(E_p*1e9))
    latex_string+=sep
    latex_string+=str(round(P_offset,2))
    latex_string+='\\\\'
    
    print(latex_string)


    return model_data