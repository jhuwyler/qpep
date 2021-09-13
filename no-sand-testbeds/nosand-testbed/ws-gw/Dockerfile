FROM pavja2/qpep:ws-gw
# Force routing via the gateway box from the terminal ('internet')
ENTRYPOINT ip route del default && ip route add default via 172.22.0.4 && bash && go run /root/go/src/qpep/main.go