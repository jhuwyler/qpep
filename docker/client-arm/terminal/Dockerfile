FROM alpine-base
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH=/opt/go/ 
ENV PATH=$PATH:$GOPATH/bin
COPY network-config.sh /tmp/network-config.sh
COPY ./qpep /usr/local/bin/qpep
RUN chmod +x /tmp/network-config.sh
RUN chmod +x /usr/local/bin/qpep
ENTRYPOINT /usr/local/bin/qpep -client -gateway 34.65.137.121