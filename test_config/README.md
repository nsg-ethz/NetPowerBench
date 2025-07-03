# Testing port configuration

This code is intended to help with finding the right commands for the DUT configuration. It is not needed for running actual measurements.

## Subdirectory structure

```
.
├── README.md
├── test_config.py
├── test_example.yml
├── test_template.yml
└── test.yml
```

## Code description

The code will configure the ports accoding to the types listed in `test.yml`.

The configurations will be, if listed, applied in the following order:

- `system`: Apply the  commands listed in `ports.yml` under `system` 
- `disable_all`: Disable all ports of the device with the commands listed under `disable`
- `enable`: Enables a random selection of ports with the command listed under `enable`
- `snake-test`: Applies the commands listed under `snake-test`

After each configuration, it will ask the user to verify the configuration and whether they want to continue. If not disabled, ports will be reset/disabled in between the configuration types.

## Usage specification

The script can be run with `python test_config.py`.

In order to run the test, there needs to be `test.yml` that contains the arguments. There is a template provided.

It is best used in combination with a console that can display the output of the DUT. We have been using minicom for this usecase to verify the successful applcation of the configration. 

When testing the configuration, it can be useful to adjust the parameters `wait_factor_per_port_snake-test_s:` and `wait_factor_per_port_others_s` to ensure that the code will wait long enough to ensure the correct configuraiton of the device before continuing with the measurements.

### Preconfiguration

An additional use case of the script can be the preconfigruation of the device, especially for `snake-test`. In this case:
1. Run `test_config.py` with `snake-test` listed under `test` and `disable_reset` set to `True`
2. Run snake-test as described `power_measure/` with `not_reconfigure` and `disable_reset` both set to `True`. 

This can significally speed up the time needed for a snake-test. 