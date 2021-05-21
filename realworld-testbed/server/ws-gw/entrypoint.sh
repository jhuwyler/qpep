#!/bin/bash
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
go run /root/go/src/qpep/main.go