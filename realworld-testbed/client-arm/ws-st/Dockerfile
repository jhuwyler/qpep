FROM alpine-base
# Force routing via the terminal box to the emulation network
ENTRYPOINT ip route del default && ip route add default via 172.22.0.4 && bash && exec tail -f /dev/null