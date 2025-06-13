# NetPowerBench
NetPowerBench is a tool for generating a power model of a routing device. It is intended to be used in a lab setup.

The motivation behind the creation of the tool as well as a detailed description of the powermodel it generates is described in [this paper](https://www.research-collection.ethz.ch/handle/20.500.11850/728960) (also listed under references). 

The workflow is separated into:
- Configuring the device and running the measurements 
- Processing the data and deriving the model
  
These two steps are separated programs and are descirbed more in detail in the respective directories.

## Environment and Prerequisites
### Hardware
The tool needs the following componends:
- Device under testing (DUT): A L2 or L3 routing device with at least 4 ports, ideally more
- A powermeter. It needs to support the pinpoint submodule. The one we used is linked [here](https://www.microchip.com/en-us/development-tool/ADM00706)
- A workstation that is running the experiment. It need have two ports to send and receive traffic to the DUT and need to be able to generate the traffic volume that the user wants to test. Furthermore it needs a Serial connection to the DUT and a connection to the powermeter. 

### Software
In order to run the experiments, we used the following software environment:
- Python: 3.10.12
- IDE: Visual Studio Code 
- OS: Ubuntu 22.04

## Repository structure
``` 
.
├── archive
│   └── configs_PowerModellingFrameworkforNetworkSwitches
│       ├── cisco_catalyst
│       │   └── running-config.txt
│       ├── cisco_nexus
│       │   └── sw1-run-config.bak
│       └── p4
│           ├── port_based_forwarder.p4
│           └── snake.py
├── command
│   ├── pinpoint_sleep.sh
│   └── README.md
├── data
├── devices
│   ├── <device identifier>
│   │   ├── config.yml
│   │   ├── ports.yml
│   │   ├── power_data.yml
│   │   └── power_model.yml
│   ├── config_template.yml
│   ├── ports_template.yml
│   └── README.md
├── legacy
│   ├── derive_model.py
│   ├── helpers.py
│   ├── power-model_derivation.ipynb
│   ├── README.md
│   └── static_test.py
├── model_derivation
│   ├── args_template.yml
│   ├── args.yml
│   ├── helper_functions.py
│   ├── main.py
│   ├── __pycache__
│   │   └── helper_functions.cpython-310.pyc
│   └── README.md
├── power_measure
│   ├── exp_template.yml
│   ├── exp.yml
│   ├── helper_functions.py
│   ├── main.py
│   ├── __pycache__
│   │   ├── helper_functions.cpython-310.pyc
│   │   ├── helpers.cpython-310.pyc
│   │   ├── main.cpython-310.pyc
│   │   └── test_main.cpython-310.pyc
│   ├── README.md
│   ├── test_config.py
│   ├── test_template.yml
│   └── test.yml
├── README.md
├── requirements.txt
└── traffic_gen
    ├── README.md
    ├── requirements.txt
    ├── setup.sh
    ├── traffic_gen.py
    ├── traffic_template.yml
    └── traffic.yml
```

## Directories
### Archives

> The P4 code and the configuration of the Cisco devices used in [Lim2024](#references) are available in `\archive\configs_PowerModellingFrameworkforNetworkSwitches`.

### command
This directory contains the script that will execute pinpoint, the software used to conduct the measurements with the powermeter. Pinpoint is a submodule of this repository. 
### data
This directory will contain the raw data and metadata from the measurements. 

`/log` contains `pinpoint.log`, which is the log of the last measurements and is there for debugging reasons. 

For each device tested there will be a subdirectory with the device identifier as name. In there there will be directories with names following one of these formats:
- `/base` 
- `/idle`
- `/port_<port_type>_<transceiver_type>_<port_speed>_<number_of_active_ports>p`
- `/trx_<port_type>_<transceiver_type>_<port_speed>_<number_of_active_ports>p`
- `/snake-test_<port_type>_<transceiver_type>_<port_speed>_<packet_size>_<bandwidth>`

Note that each of these directories refers to a test type and the relevant parameters for this test. As base and idle are indepentend of port_type or similar, they don't contain that information in the directory name. 

Inside the respective subdirectory there will be a subdirectory for each measurements run with this configuration with the timestamp of the measurement as directory name. This directory contains:
-  `metadata.yml`: The metadata of the measurement
-  `power.log`: The acutal measurement data

A possible layout of `data` could look like this:
```
├── data
│   ├── log
│   │   └── pinpoint.log
│   └── ciscoNexus9336-FX2
│           └── snake-test_QSFP28_LR_100G_256B_2.5Gbps
│               ├── 2025-05-15_16:20:45
│               │   ├── metadata.yml
│               │   └── power.log
```

For further details on the test types and measurement procedure, please refer to the documentation in `power_measure`.

### devices
For each DUI there needs to be a subdirectory in  `/devices` with the device identifier as directory. That folder needs to contain the configuration files of that device. There are templates available. The processed data from the measurements and the parameter values of the power model will be stored there as well. 

For further details please refer to the documentation in `/devices`. 

### legacy
This directory contains an older version of this code and is here for reference. It is not expected to be usable. 
### model_derivation
This directory contains the code to process the raw measurement data and derive the power modle values. 

### power_measure
This directory contains the code to run the measurements needed for the model derivation. 

Additionally there is another code that can help finding the right configuration commands for the tests (compare to the documentation in `/devices` and in `/power_measure`)`.
### traffic_gen
This directory contains all the files necessary for the traffic generation including the code, the configuration file and a setup script.
## Usage specification
In order to get a power model for a device, the following steps are advised:
- Prepare the following files with the device specific information (details are in `devices/`):
  - `devices/<device identifier>/config.yml`
  - `devices/<device identifier>/ports.yml`
- Follow the intructions in `/power_measure` in order to set up and run the measurements on the device
- Follow the instructions in `/model_derivation` in order to derive a power model 
## Known issues

- For us unknown reasons sometimes ghost counters appear. This means the pinpoint software recognizes counters that are not from the powermeter and will also be present when it is unplugged. Our way of solving this is making the counters used a parameter in `config.yml`. In case of the pinpoint script getting stuck, we advise the user to verify that the counters used are the ones the powermeter writes to and adapt `config.yml` accordingly. 
- The traffic generation needs sudo rights in order to be executed properly. As this is not really resolvable for us, our workaround was to disable the necessity of a password for executing sudo commands.
- Currently for many scrips there are dependencies on from where they are executed. This might be changed in the future but for now, in order to have everything properly executed, please run a script only from the directory it is in.  


## References
- https://www.research-collection.ethz.ch/handle/20.500.11850/728960
- Lim2024: [Lim, Jackie. "Power Modelling Framework for Network Switches." Master's thesis, ETH Zurich, 2024.](https://doi.org/10.3929/ethz-b-000663342)

