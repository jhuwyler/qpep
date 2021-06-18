FROM ubuntu:20.04
RUN apt -y update && apt -y upgrade &&\
    apt -y install wget tcpdump iptables netcat-openbsd \
    iputils-ping iputils-tracepath iproute2 iperf3\
    net-tools curl
COPY install-go.sh /tmp/install-go.sh
RUN chmod +x /tmp/install-go.sh && /bin/bash /tmp/install-go.sh