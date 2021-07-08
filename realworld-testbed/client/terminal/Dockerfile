FROM pavja2/qpep:terminal
COPY config/ /tmp/config
COPY pepsal /usr/bin/pepsal
RUN chmod +x /usr/bin/pepsal
RUN chmod +x /tmp/config/entrypoint.sh
RUN chmod +x /tmp/config/launch_pepsal.sh
RUN chmod +x /tmp/config/configure_qpep.sh
ENTRYPOINT /bin/bash /tmp/config/entrypoint.sh