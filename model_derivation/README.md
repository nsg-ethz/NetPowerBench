# Model derivation

This directory contains the files necessary for processing the data from the measurements and computing the power model. 

## Subdirectory structure

```
.
├── args_template.yml
├── args.yml
├── helper_functions.py
├── main.py
└── README.md
```

## Code description

The code's workflow is separated into two sections. One is the preprocessing of the measurement data, the other the derivation of the model based on the preprocessed data. There is the option to run only one of the two. 

### Preprocessing

The preprocessing, coordinated by the function `prepare_data(params)` iteraters over all available measurements from all test types. For each available measurement of the device in `/data/<device_id>` it will take the median of the sampled data and store it in a nested dictionary with the measurement parameters as keys. This nested dictionary is saved as `power_data.yml` in the device's directory in `devices/`. For more details on how to read `power_data.yml`, please refer to the [documentation in `devices/`](../devices/README.md). 

### Model derivation

The model derivation, coodinated by the function `derive_model(params)` and loads the preprocessed data from `power_data.yml`. When fetching the datapoints for a specific test type, the data with timestamps outside the specified time interval will be discarded if specified accordingly in the arguments. 

Additionally, in case of data from a snake-test, all data will be discarded that has not been generated with the traffic generator specified in the arguments. This distinction is based on the bandwith. Note that for the traffic generation a bandwidth over 2.5 gbps, RDMA is used, else iperf3 (see [here](../traffic_gen/README.md)). 

The mathematics behind calculating the values for the power model is descibed in detail in [[2]](../README.md#references) and [[3]](../README.md#references).

## Usage specification

The code can be run either with CLI arguments or with the arguments in `args.yml`. If there are no CLI arguments present, the code will look for `args.yml`. There is a template provided with detailed information about the arguments. Further information can also found when running the code with `python main.py --help`. 

Note that if both `preprocess_only` and `derive_only` are set to `True`, nothing will happen. 