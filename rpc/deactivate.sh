#!/bin/bash

ip link set dev wwan0 down
ip addr flush dev wwan0
rmmod iosm wwan

tee <<<1 "/sys/bus/pci/devices/0000:01:00.0/reset"
tee <<<1 "/sys/bus/pci/devices/0000:01:00.0/remove"

#tee <<<1 "/sys/bus/pci/rescan"
