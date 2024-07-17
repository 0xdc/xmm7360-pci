#!/bin/bash

systemd_mm() {
	if which systemctl >/dev/null 2>&1 && test "$(systemctl is-enabled ModemManager.service)" = enabled; then
		if test "$(systemctl is-system-running)" = running; then
			case "$1" in
			start)	systemctl start ModemManager.service;;
			stop)	systemctl stop  ModemManager.service;;
			esac
		fi
	fi
}

write1() {
	test -f "$1" && echo 1 > "$1"
	sleep 1
}

systemd_mm stop
ip link set dev wwan0 down
ip addr flush dev wwan0
rmmod iosm wwan

write1 "/sys/bus/pci/devices/0000:01:00.0/reset"
write1 "/sys/bus/pci/devices/0000:01:00.0/remove"
write1 "/sys/bus/pci/rescan"

until ip link list dev wwan0; do
	sleep 2
done

ip link set dev wwan0 up
systemd_mm start
