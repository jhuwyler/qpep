# QPEP real-world testbed

To test QPEP over real satellite links, a real-world testbed was developed. It is very similar to the OpenSAND testbed. In the following we will explain how to deploy the testbed and make it work. The real-world instances use Ubnutu 20.04 as OS and were tested on them.

## Prerequisites

* [Docker & Docker-Compose](https://docs.docker.com/compose/install/) (_tested on Docker for Linux, Engine (v20.10.7), Compose (v1.29.2)_)
* Python 3.7+
* [Python pip](https://www.pypa.io/en/latest/)
* Satellite link as well as second out-of-band connection

## Installing
 
Installation is very similar to the simulated testbed with the exception, that we do not need Xservers, but also do not have the ability for live browsing.

### Client Side Setup

On the Client side first clone the repository into a folder:
```
> mkdir qpep
> cd qpep
> git clone https://github.com/jhuwyler/qpep --recursive
```

We then need to create a new python virtual environment and install the necessary dependencies:

```
> cd qpep
> python3 -m venv venv
> source venv/bin/activate
> cd qpep/realworld-testbed
> pip3 install -r requirements.txt 
```

Now we need to setup the client to route traffic from the Docker testbeds over the Satellite connection. First, enable IPv4 forwarding:

```
> sysctl -w net.ipv4.ip_forward=1
```

We then need to create a special routing table for Docker, to be able to reroute the traffic over the satellite link like in this guide [Routing Docker containers](https://serverfault.com/questions/696747/routing-from-docker-containers-using-a-different-physical-network-interface-and):
>:warning: ** Note: ** The specific IPs and interfaces need to match the ones in your specific setup.
```
# Create a new routing table just for docker
echo "1 docker" >> /etc/iproute2/rt_tables

# Add a rule stating any traffic from the docker0 bridge interface should use 
# the newly added docker routing table
# ATTENTION: ip address must be the same as specified in docker compose file
ip rule add from 172.21.0.0/16 table docker

# Add a route to the newly added docker routing table that dictates all traffic
# go out the different interface
ip route add default via [satellite-if-ip] dev [sat-interface] table docker

# Flush the route cache
ip route flush cache

# Restart the Docker daemon
/etc/init.d/docker restart
```
This will redirect all traffic from our docker interface to the satellite link as intended.

Next we need to fill out all '.env' files correctly to provide the server addresses to the Python and Docker files. Example files with the values needed are placed at each location to ease this step. Copy the file and remove the '.example' part, such that the files are named '.env'. Fill in all the names of your servers and containers in this folder, the '/client' folder and '/server' folder. Note that the names of the containers have to be the same on the server as well.

For the connections to work, we need to deploy our SSH keys from the client in the server, to be able to login automatically. If one wants to save results on a MongoDB, this database needs to be accessible via a key and the connection string, which is provided in the .env files. For redundancy, two database connections can be provided, this can also be used for two alternate ways to access the same database.

### Server Side Setup

Setup a folder on the server side as well and clone the repository:
```
> mkdir qpep
> cd qpep
> git clone https://github.com/jhuwyler/qpep --recursive
```

For the Docker containers to act as servers, enable IPv4 forwarding:

```
> sysctl -w net.ipv4.ip_forward=1
```

We then need to enable traffic from the client to the server on the following ports: 
- TCP/UDP 5201, 5001 (iperf3)
- TCP 80,443 (http/https)
- TCP/UDP 1194 (OpenVPN)
- UDP 4242 (QPEP)

Next we need to fill out the '.env' files on the server, similar to the client. Copy the file and remove the '.example' part, such that the files are named '.env'. Fill in all the names of your servers and containers in this folder and '/server' folder.

If not already done in the client setup, add the SSH keys from the client to the server, to be able to login via SSH from the client without a password.

After all these steps we can finally run the Python scripts on the client to perform measurements, the same way as in the simulated testbed:
```
> /qpep/realworld-testbed/simulation_examples.py
```