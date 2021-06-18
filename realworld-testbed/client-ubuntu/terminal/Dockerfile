FROM ubuntu-go-base
COPY entrypoint.sh /tmp/entrypoint.sh
COPY launch_qpep.sh /tmp/launch_qpep.sh
RUN chmod +x /tmp/entrypoint.sh
ENV PATH="$PATH:/usr/local/go/bin"
ENTRYPOINT /bin/bash /tmp/entrypoint.sh