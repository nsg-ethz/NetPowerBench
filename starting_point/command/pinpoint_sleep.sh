#!/bin/bash

# arg: DURATION           The number of seconds the workload (/bin/sleep) should run
# arg: PATH               Path to the pinpoint binary
# arg: SAMPLING_INTERVAL  Interval in milliseconds at which samples should be taken
# arg: START_UP_DELAY     Delay in milliseconds before sampling starts
# arg: COUNTER_1          First event/counter to monitor (e.g., MCP1, mcp:dev0ch1)
# arg: COUNTER_2          Second event/counter to monitor (e.g., MCP2, mcp:dev0ch2)


DURATION=$1
PATH=$2
SAMPLING_INTERVAL=$3
START_UP_DELAY=$4
COUNTER_1=$5
COUNTER_2=$6
logname="../data/log/pinpoint.log"

# Clear existing log
/bin/rm $logname

# Run pinpoint
$PATH -c -e $COUNTER_1,$COUNTER_2 -i $SAMPLING_INTERVAL -b -$START_UP_DELAY -o  ../data/log/pinpoint.log --header -- /bin/sleep  $DURATION