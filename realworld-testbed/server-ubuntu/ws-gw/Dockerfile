FROM ubuntu-go-base
COPY entrypoint.sh /tmp/entrypoint.sh
RUN chmod +x /tmp/entrypoint.sh
COPY pepsal /usr/bin/pepsal
COPY launch_pepsal.sh /tmp/launch_pepsal.sh
RUN chmod +x /usr/bin/pepsal
RUN chmod +x /tmp/launch_pepsal.sh
ENV PATH="$PATH:/usr/local/go/bin"
ENTRYPOINT /bin/bash /tmp/entrypoint.sh