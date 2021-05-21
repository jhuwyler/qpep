#!/bin/bash
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
bash && exec tail -f /dev/null