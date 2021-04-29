FROM ubuntu-base
# Force routing via the gateway box from the terminal ('internet')
COPY ./qpep /usr/local/bin/qpep
RUN chmod +x /usr/local/bin/qpep
ENTRYPOINT ip route del default && ip route add default via 172.25.0.4 && bash && /usr/local/bin/qpep