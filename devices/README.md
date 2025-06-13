# devices
For each device tested there should be a directory with the device identifier as name. That directory should contain the file `config.yml` and the config file with the port config information, usually called `ports.yml`. Provided are templates for these files as well as an example directory and directories of devices we worked with. In here will also be the output of the model derivation.

Note that the files in `/example` are only there to give an impression of how those files might look like and are not consistent with each other. Also note that the files for the devices we worked with might be outdated and not work with the current format that is expected by the code. It is safe to follow the format used in the templates and `example`.
## Submodule structure
```
.
├── config_template.yml
├── example
│   ├── config.yml
│   ├── ports.yml
│   ├── power_data.yml
│   └── power_model_<port_type>_<port_speed>_<transceiver_type>_<traffic_generator>.yml
├── ports_template.yml
└── README.md
```
## config.yml
This file contains the device specific information tat 
## port.yml
What should the config commands for the ports achieve?
### system
### enable
### disable
### snake-test

## power_data.yml


## power_model_\<params>.yml