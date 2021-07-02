FROM sitespeedio/browsertime:10.6.2
RUN apt-get update
RUN apt-get install -y wget curl
RUN apt-get install -y net-tools iputils-ping traceroute
ENTRYPOINT ip route del default && ip route add default via 172.21.0.4 && bash && exec tail -f /dev/null