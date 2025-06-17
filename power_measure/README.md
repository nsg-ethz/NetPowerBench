# Power measure

This directory contains the code that configures the device and runs the actual measurements. There are five different types of experiments needed in order to have the data necessary to derive the power model and it is recommended to have multiple runs of an experient to improve the quality of the model.

## Submodule structure

```
.
├── exp_template.yml
├── exp.yml
├── helper_functions.py
├── main.py
└── README.md
```

## Code description

Tests are run for a specific port type, port speed and transceiver type. It is assumed that all transceivers used are of the same type. If a device has multiple port types available, the setup described below only correspond to the type to be tested. All other ports will be disabled and should not have anything plugged in. 

There are five different types of experiments. They are characterized by the state the device is in and whether there is traffic.  
- **base**: No transceivers are plugged in, all ports are disabled, no traffic. 
- **idle**: All transsceivers are plugged in, all ports are disabled, no traffic. 
- **port**: All transceivers are plugged in such that each port is connected to another port. Out of each port pair, one port is enabled and one is disabled. No traffic. Note that the way the ports are connected is implied by the order of the port numbers in `ports.yml` (mode details in `/devices`)
- **trx**: Same setup as for port, but this time, all ports will be enabled. 
- **snake-test**: A detailed description of snake-test is provided in [this blogpost](https://ostinato.org/blog/snake-test-guide). 

In order to get a better understanding of how the experiment types work and how they are used to infere the power model, please refer to [TODO: reference to paper]

The code has the following workflow:
1. Load the parameters needed from the different config file
2. If not disabled: Configures system and resets entire device
3. Takes the cross product of the different speeds and experiment types, repeat them as specified and then randomize the order. Each of them specify one test.
4. For each test: 
    1. Configure the device as needed and start traffic if needed
    2. Run the measurements using the pinpoint software
    3. Save the measurements in `/data`

Note that for port and trx instead of measuring the power of all ports at once, there are multiple runs with a randomized selection of ports. The effective value will be determined by a regression over those measurements. 

For snake-test, there will be a run for each combination of packet sizes and bandwidth specified in `traffic_gen/traffic.yml`.


## Physical Setup
### General setup

### Base test
trx not plugged in
### Idle, port and trx test
trx plugged in according to listing
### Snake test
trx plugged in for snake test



## Usage specification

In order to run one or multiple experiments, these are the recommended steps:
1. Fill in all config files needed:
    - `devices/<device_id>/config.yml`
    - `devices/<device_id>/ports.yml`
    - `traffic_gen/traffic.yml` (for snake-test)
2. Set the experiment parameters. These define what kind of experimet will be run and can be either set in `exp.yml` or given to the program via the CLI. For further details, please refer to the template provided or use `--help`.
3. Arrange the physical setup according to the experiment parameters as described above. 
4. Optionally: Preconfigure the device using `test_config.yml` and disable reconfiguration. This can save time for e.g. snake-test.
5. Run the code

## Output explanantion