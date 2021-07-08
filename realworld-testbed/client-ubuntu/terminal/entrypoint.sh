sysctl -w net.ipv4.ip_forward=1
/sbin/iptables -t nat -A POSTROUTING -d 0/0 -s 172.30.0.9/32 -j MASQUERADE
tail -f /dev/null