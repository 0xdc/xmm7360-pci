#!/bin/bash

write1() {
	test -f "$1" && echo 1 > "$1"
	sleep 1
}

ip link set dev wwan0 down
ip addr flush dev wwan0
rmmod iosm wwan

write1 "/sys/bus/pci/devices/0000:01:00.0/reset"
write1 "/sys/bus/pci/devices/0000:01:00.0/remove"
write1 "/sys/bus/pci/rescan"

until ip link list dev wwan0; do
	sleep 2
done
