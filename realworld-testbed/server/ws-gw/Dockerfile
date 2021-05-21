FROM pavja2/qpep:ws-gw
COPY config/gw.conf /etc/opensand/daemon.conf
COPY config/entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
COPY pepsal /usr/bin/pepsal
ENTRYPOINT /bin/bash /tmp/entrypoint.sh