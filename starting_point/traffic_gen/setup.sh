#!/bin/bash

ns1="ns1"
ns2="ns2"

if1="enp1s0f0np0"
if2="enp1s0f1np1"

ip1="192.168.1.1/24"
ip2="192.168.1.2/24"

# Create the namespaces
sudo ip netns add $ns1
sudo ip netns add $ns2

# Assign interfaces to namespaces
sudo ip link set $if1 netns $ns1
sudo ip link set $if2 netns $ns2

# Add IP addresses
sudo ip -n $ns1 addr add $ip1 dev $if1
sudo ip -n $ns2 addr add $ip2 dev $if2

# Set the links up
sudo ip netns exec $ns1 ip link set $if1 up
sudo ip netns exec $ns2 ip link set $if2 up

# Adjust the MTU 
sudo ip netns exec $ns1 ip link set dev $if1 mtu 6000
sudo ip netns exec $ns2 ip link set dev $if2 mtu 6000
