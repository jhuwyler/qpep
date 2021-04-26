FROM alpine-base
COPY install-go.sh /tmp/install-go.sh
RUN chmod +x /tmp/install-go.sh && /bin/bash /tmp/install-go.sh
ENTRYPOINT /bin/ash