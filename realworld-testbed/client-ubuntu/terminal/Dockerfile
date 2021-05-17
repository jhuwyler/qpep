FROM ubuntu-base
COPY entrypoint.sh /tmp/entrypoint.sh
COPY launch_qpep.sh /tmp/launch_qpep.sh
COPY ./qpep /usr/local/bin/qpep
RUN chmod +x /usr/local/bin/qpep
RUN chmod +x /tmp/entrypoint.sh
ENTRYPOINT /bin/bash /tmp/entrypoint.sh