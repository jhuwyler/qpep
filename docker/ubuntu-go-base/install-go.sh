# taken from https://stackoverflow.com/questions/52056387/how-to-install-go-in-alpine-linux
echo "installing go version 1.13.4..." 
wget -O go.tgz https://golang.org/dl/go1.13.4.linux-amd64.tar.gz
rm -rf /usr/local/go && tar -C /usr/local -xzf go.tgz 
export PATH="$PATH:/usr/local/go/bin"
go version