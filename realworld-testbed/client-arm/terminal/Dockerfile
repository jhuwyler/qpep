FROM alpine:3.13.5
RUN apk update && apk upgrade &&\
    apk add wget tcpdump iptables netcat-openbsd iputils iproute2 bash bash-completion
RUN wget https://golang.org/dl/go1.13.4.linux-armv6l.tar.gz && rm -rf /usr/local/go && tar -C /usr/local -xzf go1.13.4.linux-armv6l.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"
COPY entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
ENTRYPOINT /bin/bash /tmp/entrypoint.sh