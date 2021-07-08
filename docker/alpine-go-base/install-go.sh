# taken from https://stackoverflow.com/questions/52056387/how-to-install-go-in-alpine-linux
echo "installing go version 1.14.3..." 
apk add --no-cache --virtual .build-deps bash gcc musl-dev openssl go 
wget -O go.tgz https://golang.org/dl/go1.14.3.src.tar.gz
tar -C /usr/local -xzf go.tgz 
cd /usr/local/go/src/ 
./make.bash 
export PATH="/usr/local/go/bin:$PATH"
export GOPATH=/opt/go/ 
export PATH=$PATH:$GOPATH/bin 
apk del .build-deps 
go version