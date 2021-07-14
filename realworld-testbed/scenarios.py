from abc import ABC, abstractmethod
from loguru import logger
import docker
import time
import os
from dotenv import load_dotenv
load_dotenv()
load_dotenv(str(os.getenv("SERVER_ENV")))
load_dotenv(str(os.getenv("CLIENT_ENV")))

class Scenario(ABC):
    def __init__(self, name, testbed, benchmarks):
        self.name = name
        self.testbed = testbed
        self.benchmarks = benchmarks

    @abstractmethod
    def deploy_scenario(self):
        self.testbed.start_testbed()

    def run_benchmarks(self, deployed=False):
        for benchmark in self.benchmarks:
            if not deployed:
                self.deploy_scenario()
            benchmark.run()

    def print_results(self):
        print("*"*25)
        print("Benchmark Results for ", self.name)
        print("*"*25)
        for benchmark in self.benchmarks:
            print("****", benchmark.name, "****")
            benchmark.print_results()

class PlainScenario(Scenario):
    def deploy_scenario(self, testbed_up=False):
        if not testbed_up:
            super().deploy_scenario()
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        sitespeed_workstation = docker_client.containers.get(os.getenv("WS_SITESPEED_CONTAINER_NAME"))
        logger.debug("Configuring proxy on Terminal WS")
        terminal_workstation.exec_run("export http_proxy=http://"+os.getenv("PROXY_SRV_URL")+":5001")
        terminal_workstation.exec_run("export https_proxy=https://"+os.getenv("PROXY_SRV_URL")+":5001")
        logger.debug("Configuring proxy on Sitespeed")
        sitespeed_workstation.exec_run("export http_proxy=http://"+os.getenv("PROXY_SRV_URL")+":5001")
        sitespeed_workstation.exec_run("export https_proxy=https://"+os.getenv("PROXY_SRV_URL")+":5001")

class OpenVPNScenario(Scenario):
    def deploy_scenario(self, testbed_up=False):
        if not testbed_up:
            super().deploy_scenario()
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        # Satellite latency means that it takes OpenVPN a long time to establish the connection, waiting is easiest
        logger.debug("Launching OVPN and waiting...")
        terminal_workstation.exec_run("openvpn --config /root/client.ovpn --daemon")
        time.sleep(20)

class QPEPScenario(Scenario):

    def __init__(self, name, testbed, benchmarks, multi_stream=True):
        self.multi_stream = multi_stream
        super().__init__(name, testbed, benchmarks)

    def deploy_scenario(self, testbed_up=False):
        if not testbed_up:
            super().deploy_scenario()
        docker_client = docker.from_env()

        logger.debug("Configuring Client Side of QPEP Proxy")
        terminal_container = docker_client.containers.get(os.getenv("ST_CONTAINER_NAME"))
        terminal_container.exec_run("bash ./tmp/config/configure_qpep.sh")

        logger.debug("Configuring Gateway Side of QPEP Proxy")
        docker_client_cloud = docker.DockerClient(base_url="ssh://"+os.getenv("DOCKER_REMOTE_URL"))
        gateway_workstation = docker_client_cloud.containers.get(os.getenv('WS_GW_CONTAINER_NAME'))

        if testbed_up:
            # kill running QPEP services for fresh start
            gateway_workstation.exec_run("pkill -9 main")
            terminal_container.exec_run("pkill -9 main")

        logger.debug("Launching QPEP Client")
        terminal_container.exec_run("go run /root/go/src/qpep/main.go -client -gateway "+os.getenv("QPEP_SRV_URL")+" -port "+os.getenv("QPEP_SRV_PORT"), detach=True)
        logger.debug("Launching QPEP Gateway")
        gateway_workstation.exec_run("go run /root/go/src/qpep/main.go -port "+os.getenv("QPEP_SRV_PORT"), detach=True)
        logger.success("QPEP Running")

class QPEPAckScenario(Scenario):
    def deploy_scenario(self, testbed_up=False, ack_level=4):
        if not testbed_up:
            super().deploy_scenario()

        docker_client = docker.from_env()
        terminal_container = docker_client.containers.get(os.getenv("ST_CONTAINER_NAME"))
        gateway_workstation = docker_client.containers.get(os.getenv("WS_GW_CONTAINER_NAME"))
        if testbed_up:
            logger.debug("Killing any prior QPEP")
            terminal_container.exec_run("pkill -9 main")
            gateway_workstation.exec_run("pkill -9 main")
            time.sleep(1)
        else:
            logger.debug("Configuring Client Side of QPEP Proxy")
            terminal_container.exec_run("bash /opensand_config/configure_qpep.sh")

            logger.debug("Configuring Gateway Side of QPEP Proxy")
            gateway_workstation.exec_run("bash /opensand_config/configure_qpep.sh")

        logger.debug("Launching QPEP Client")
        terminal_container.exec_run("go run /root/go/src/qpep/main.go -client -minBeforeDecimation 2 -ackDelay 8000 -varAckDelay 16.0 -gateway " + str(os.getenv("GW_NETWORK_HEAD")) + ".0.9 -acks " + str(ack_level), detach=True)
        logger.debug("Launching QPEP Gateway")
        gateway_workstation.exec_run("go run /root/go/src/qpep/main.go -minBeforeDecimation 2 -ackDelay 8000 -varAckDelay 16.0", detach=True)
        logger.success("QPEP Running")


class QPEPCongestionScenario(Scenario):
    def deploy_scenario(self, testbed_up=False, congestion_window=10):
        if not testbed_up:
            super().deploy_scenario()

        docker_client = docker.from_env()
        terminal_container = docker_client.containers.get(os.getenv("ST_CONTAINER_NAME"))
        gateway_workstation = docker_client.containers.get(os.getenv("WS_GW_CONTAINER_NAME"))
        if testbed_up:
            logger.debug("Killing any prior QPEP")
            terminal_container.exec_run("pkill -9 main")
            gateway_workstation.exec_run("pkill -9 main")
            time.sleep(1)
        else:
            logger.debug("Configuring Client Side of QPEP Proxy")
            terminal_container.exec_run("bash /opensand_config/configure_qpep.sh")

            logger.debug("Configuring Gateway Side of QPEP Proxy")
            gateway_workstation.exec_run("bash /opensand_config/configure_qpep.sh")

        logger.debug("Launching QPEP Client")
        terminal_container.exec_run("go run /root/go/src/qpep/main.go -client -gateway " + str(os.getenv("GW_NETWORK_HEAD")) +".0.9 -congestion " + str(congestion_window), detach=True)
        logger.debug("Launching QPEP Gateway")
        gateway_workstation.exec_run("go run /root/go/src/qpep/main.go -congestion " + str(congestion_window), detach=True)
        logger.success("QPEP Running")


class PEPsalScenario(Scenario):
    def __init__(self, name, testbed, benchmarks, terminal=True, gateway=False):
        self.terminal  = terminal
        self.gateway = gateway
        super().__init__(name=name, testbed=testbed, benchmarks=benchmarks)

    def deploy_scenario(self, testbed_up=False):
        if not testbed_up:
            super().deploy_scenario()
        logger.debug("Starting PEPsal Scenario")
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        sitespeed_workstation = docker_client.containers.get(os.getenv("WS_SITESPEED_CONTAINER_NAME"))
        logger.debug("Configuring proxy on Terminal WS")
        terminal_workstation.exec_run("export http_proxy=http://"+os.getenv("PROXY_SRV_URL")+":5001")
        terminal_workstation.exec_run("export https_proxy=https://"+os.getenv("PROXY_SRV_URL")+":5001")
        logger.debug("Configuring proxy on Sitespeed")
        sitespeed_workstation.exec_run("export http_proxy=http://"+os.getenv("PROXY_SRV_URL")+":5001")
        sitespeed_workstation.exec_run("export https_proxy=https://"+os.getenv("PROXY_SRV_URL")+":5001")
        if self.terminal and self.gateway:
            logger.debug("Deploying PEPsal in Distributed Mode")

        if self.terminal:
            logger.debug("Deploying PEPsal on Terminal Endpoint")
            terminal_workstation.exec_run("bash ./tmp/config/launch_pepsal.sh")
        if self.gateway:
            logger.debug("Deploying PEPsal on Gateway Endpoint")
            docker_client_cloud = docker.DockerClient(base_url="ssh://"+os.getenv("DOCKER_REMOTE_URL"))
            gateway_workstation = docker_client_cloud.containers.get(os.getenv('WS_GW_CONTAINER_NAME'))
            gateway_workstation.exec_run("bash ./tmp/launch_pepsal.sh")
