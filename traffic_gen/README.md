# Traffic Generation

The code in this directory handles the generation of the traffic needed for running snake test. 

It is called by the code in `power_measure/`. It will create two namespaces called `ns1` and `ns2` and send the traffic wanted from one namespace to the other.

## Subdirectory structure

```
.
├── README.md
├── setup.sh
├── traffic_example.yml
├── traffic_gen.py
├── traffic_template.yml
└── traffic.yml
```

## Code description

### traffic_gen.py

When run, this code will:
1. Take the three arguments duration, bandwidth and packet size
2. Check whether the namespaces needed, otherwise runs `setup.sh`
3. Decides based on the bandwidth wanted which traffic generator to use: For a bandwidth smaller than 2.5 gbps, iperf3 is used, otherwise RDMA
4. Sends the traffic with the metrics set by the arguments from one namespace to the other for the duration specified 
5. Outputs performance metrics and will write them into `power_measure/perftest.json`. This is only temporary, the file will be deleted after the output has been processed.

`setup.sh` and `traffic.yml` are expected to be in the same directory. 

Note that in order to run properly, this code needs sudo privileges. We have solved this by disabling the necessity of a password, but are aware that this might not be the ideal way to solve it (see also in Known issues).

### setup.sh

`setup.sh` is called by `traffic_gen.py` in case the namespaces `ns1` and `ns2` don't exist yet. 

It takes two arguments, the names of two interfaces, refert to as `if1` and `if2`. The names need to be specified in `traffic.yml`

It will: 
1. Create the two namespaces 
2. Move the interfaces `if1` and `if2` each into one of the namespaces. 
3. Assign them the IP adresses `192.168.1.1/24` and `192.168.1.2/24`
4. Bring the interfaces up
5. Set MTU to 6000


### traffic.yml

This file contains the interface names of the workstation that are connected to the DUT and the traffic configurations that will be tested in case of a snake-test. There will be a measurement for each packet size combined with each bandwidth, unless the bandwidth exceeds the maximum bandwidth listed. The reason for this is that for small packet sizes, the generator might not be able to reach the fastest bandwidth if the packets are too small. 

This file needs to be set by the user before a snake-test. There is a template provided. 

## Usage specification

In general there should be no need for the user to execute one of these scripts as they will be called by the code in `power_measure/` or call each other.

In case of a problem with the traffic generation it can be useful to run `traffic_gen.py` manually. The command for this has the following format:

```
python traffic_gen.py <duration> <bandwidth> <packet_size>
```

It is advised to pay attention to whether the bandwidth reached is the same or similar to the bandwidth desired. If not that could indicate a problem with the port configuration. 
