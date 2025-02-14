#!/bin/bash

# arg: DURATION     the number of seconds the workload should take
# arg: PATH         path the to pinpoint binary
# arg: WORKLOAD     path to the workload file

DURATION=$1
PATH=$2
SAMPLING_INTERVAL=$3
START_UP_DELAY=$4
logname="../data/log/pinpoint.log"

# Clear existing log
/bin/rm $logname

# Run pinpoint
# $PATH -c -e MCP1,MCP2 -i $SAMPLING_INTERVAL -b -$START_UP_DELAY -o  ../data/log/pinpoint.log --header -- /bin/sleep  $DURATION
# -> currently there is a bug where the header does not get written to the output, so just leave it out.
$PATH -c -e MCP1,MCP2 -i $SAMPLING_INTERVAL -b -$START_UP_DELAY -o  ../data/log/pinpoint.log -- /bin/sleep  $DURATION
# $PATH -c -e mcp:dev1ch1,mcp:dev1ch2 -i $SAMPLING_INTERVAL -b -$START_UP_DELAY -o  ../data/log/pinpoint.log -- /bin/sleep  $DURATION