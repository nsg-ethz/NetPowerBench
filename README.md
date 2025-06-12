# NetPowerBench
NetPowerBench is a tool for generating a power model of a routing device. It is intended to be used in a lab setup.

The motivation behind the creation of the tool as well as a detailed description of the powermodel it generates is described in [this paper](https://www.research-collection.ethz.ch/handle/20.500.11850/728960) (also listed under references). 
## Environment and Prerequisites
### Hardware
The tool needs the following componends:
- Device under testing (DUT): A L2 or L3 routing device with at least 4 ports, ideally more
- A powermeter. The one we used is linked [here](https://www.microchip.com/en-us/development-tool/ADM00706)
- A workstation that is running the experiment. It need have two ports to send and receive traffic to the DUT and need to be able to generate the traffic volume that the user wants to test. Furthermore it needs a Serial connection to the DUT and a connection to the powermeter. 

### Software
In order to run the experiments, we used the following software environment:
- Python: 3.10.12
- IDE: Visual Studio Code 
- OS: Ubuntu 22.04
## Repository structure
Use tree command
## Setup
### General setup
which hardware is used
### Base test
trx not plugged in
### Idle, port and trx test
trx plugged in according to listing
### Snake test
trx plugged in for snake test

## Directories
### Archives

> The P4 code and the configuration of the Cisco devices used in [Lim2024](#references) are available in `\archive\configs_PowerModellingFrameworkforNetworkSwitches`.

### command
Contains Pinpoint
### data
There the data will end up
### devices
There your config files should be
### legacy
Old code
### model_derivation
Code for model derivation
### power_model
Code for measurements and preparation and exp.yml
### traffic_gen
Trafic generations
## Usage specification
How the code works (vlans etc)
How to use the code
## Known issues


To be described


## References
- https://www.research-collection.ethz.ch/handle/20.500.11850/728960
- Lim2024: [Lim, Jackie. "Power Modelling Framework for Network Switches." Master's thesis, ETH Zurich, 2024.](https://doi.org/10.3929/ethz-b-000663342)

Refere to the paper 
