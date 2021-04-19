FROM alpine:3.13.5
RUN apk update && apk upgrade \
    apk add wget tcpdump iptables net-cat iputils iproute2 bash bash-completion
# Force routing via the terminal box to the emulation network
ENTRYPOINT ip route del default && ip route add default via 172.21.0.4 && bash && exec tail -f /dev/null