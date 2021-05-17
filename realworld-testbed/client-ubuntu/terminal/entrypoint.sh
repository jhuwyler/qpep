sysctl -w net.ipv4.ip_forward=1
/sbin/iptables -A PREROUTING -t mangle -p tcp -i eth0 -j TPROXY --on-port 8080 --tproxy-mark 1
/sbin/iptables -t nat -A POSTROUTING -d 0/0 -s 172.30.0.9/32 -j MASQUERADE
/sbin/ip rule add fwmark 1 lookup 100
/sbin/ip route add local 0.0.0.0/0 dev lo table 100
/usr/local/bin/qpep -client -gateway cloud.jhuwyler.dev