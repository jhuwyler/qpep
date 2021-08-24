FROM pavja2/qpep:ws-st
# Force routing via the terminal box to the emulation network
RUN apt update && apt install traceroute
RUN apt-get install -y tcpdump
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get update && apt-get install -y nodejs
RUN npm install -g browsertime
RUN apt-get install -y firefox
RUN apt-get install -y firefox-geckodriver
RUN apt-get install -y xvfb
COPY client.ovpn /root/client.ovpn
ENTRYPOINT ip route del default && ip route add default via 172.21.0.4 && bash && exec tail -f /dev/null