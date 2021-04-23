FROM alpine-go-base
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH=/opt/go/ 
ENV PATH=$PATH:$GOPATH/bin
COPY network-config.sh /tmp/network-config.sh
RUN chmod +x /tmp/network-config.sh
ENTRYPOINT go run /root/go/src/qpep/main.go -client -gateway 34.65.137.121