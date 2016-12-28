#!/bin/bash
# This Nagios script checks Ubuntu machines for the condition that a reboot is required
# and which packages are requiring a reboot. 

if [ ! -f /var/run/reboot-required ]; then
        # no reboot required (0=OK)
        echo "OK: no reboot required"
        exit 0
else
        # reboot required (1=WARN)
        echo "WARNING: `cat /var/run/reboot-required.pkgs`"
        exit 1
fi
