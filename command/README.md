# command
In here is the script that gets called to run the measurements. The software used is in the submodule pinpoint. 
## Submodule structure
```
.
├── pinpoint_sleep.sh
└── README.md
```
## Usage specification
`pinpoint_sleep.sh` takes the following arguments.
- DURATION : The number of seconds the workload (/bin/sleep) should run
- PATH : Path to the pinpoint binary
- SAMPLING_INTERVAL : Interval in milliseconds at which samples should be taken
- START_UP_DELAY : Delay in milliseconds before sampling starts
- COUNTER_1 : First event/counter to monitor (e.g., MCP1, mcp:dev0ch1)
- COUNTER_2 : Second event/counter to monitor (e.g., MCP2, mcp:dev0ch2)

It executes the pinpoint binary with the following command and writes the output to `../data/log/pinpoint.log`:
```
$PATH -c -e $COUNTER_1,$COUNTER_2 -i $SAMPLING_INTERVAL -b -$START_UP_DELAY -o  ../data/log/pinpoint.log --header -- /bin/sleep  $DURATION
```

Note that in the way the pinpoint software is used here, there is no workload.

Normally there should be no need of running this script as it gets called by `main.py`. Should there be any issues with running pinpoint for measurements it can help executing the command above manually with directing the output to the terminal. If there is no output, common reasons for that were:
- Powermeter not being plugged in
- Using wrong counters (mentioned in known issues). It has occurred that there were phantom counters that do not correspond to the actual ones used by the powermeter. With: ```$PATH -l``` you can list the available counters to try different arguments. 