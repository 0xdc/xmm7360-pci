#!/bin/bash

ip link set dev wwan0 down
ip addr flush dev wwan0
rmmod iosm wwan

echo 1 > "/sys/bus/pci/devices/0000:01:00.0/reset"
echo 1 > "/sys/bus/pci/devices/0000:01:00.0/remove"
sleep 1

echo 1 > "/sys/bus/pci/rescan"

modprobe iosm

until ip link list dev wwan0; do
	sleep 1
done
