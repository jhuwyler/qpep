FROM sitespeedio/browsertime:10.6.2
RUN apt-get update
RUN apt-get install -y wget
RUN apt-get install -y net-tools iputils-ping
RUN apt-get install -y openvpn
COPY client.ovpn /root/client.ovpn
ENTRYPOINT exec tail -f /dev/null
CMD exec tail -f /dev/null
