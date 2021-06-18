FROM sitespeedio/browsertime:10.6.2
RUN apt-get update
RUN apt-get install -y wget curl
RUN apt-get install -y net-tools iputils-ping traceroute
COPY configure_proxy.sh /tmp/configure_proxy.sh
RUN chmod +x /tmp/configure_proxy.sh
ENTRYPOINT ip route del default && ip route add default via 172.30.0.4 && bash && exec tail -f /dev/null