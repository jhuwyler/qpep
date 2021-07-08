FROM pavja2/qpep:ws-st
# Force routing via the terminal box to the emulation network
RUN apt update && apt install traceroute
COPY client.ovpn /root/client.ovpn
ENTRYPOINT ip route del default && ip route add default via 172.21.0.4 && bash && exec tail -f /dev/null