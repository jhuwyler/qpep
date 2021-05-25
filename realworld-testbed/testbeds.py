import subprocess
import os
from loguru import logger
import nclib
import docker
import time
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()

class RealWorldTestbed(object):
    def start_testbed(self):
        # First, shut down any old running testbeds
        logger.debug("Shutting Down Previous Testbeds")
        subprocess.call(["docker-compose", "-f", os.getenv("COMPOSE_LOCAL") ,"down"], stderr=subprocess.DEVNULL)

        logger.debug("Starting local Testbed Containers")

        # Start the docker containers
        subprocess.call(["docker-compose", "-f", "./client/docker-compose.yml" , "up", "-d"], env=my_env)

        # now that the network is running, it is possible to add ip routes from user terminal through the network
        logger.debug("Connecting User Terminal to Satellite Spot Beam")
        docker_client = docker.from_env()
        terminal_container = docker_client.containers.get(os.getenv("ST_CONTAINER_NAME"))
        terminal_container.exec_run("/sbin/ip route delete default")
        terminal_container.exec_run("/sbin/ip route add default via " + str(os.getenv("GW_NETWORK_HEAD")) + ".0.3")
        logger.success("Real-world Testbed Running")

    def stop_testbed(self):
        logger.debug("Shutting Down Previous Testbeds")
        subprocess.call(["docker-compose", "down"])

    def connect_terminal_workstation(self):
        logger.debug("Starting User Workstation")
        docker_client = docker.from_env()
        workstation_container = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        logger.debug("Adding External Route to Docker Host for GUI Services")
        workstation_container.exec_run("ip route add " + str(self.host_ip) + " via " + str(os.getenv("GUI_NETWORK_HEAD"))+".0.1 dev eth1")
        logger.debug("Connecting User Workstation to Satellite Router")
        workstation_container.exec_run("ip route del default")
        workstation_container.exec_run("ip route add default via " + str(os.getenv("ST_NETWORK_HEAD"))+".0.4")
        logger.success("Client Workstation Connected to Satellite Network")

    def connect_sitespeed_workstation(self):
        logger.debug("Starting Sitespeed Workstation")
        docker_client = docker.from_env()
        sitespeed_container = docker_client.containers.get(os.getenv("SITESPEED_CONTAINER_NAME"))
        sitespeed_container.exec_run("ip route del default")
        sitespeed_container.exec_run("ip route add default via " + str(os.getenv("ST_NETWORK_HEAD"))+".0.4")
        logger.success("Sitespeed Workstation Connected to Satellite Network")

if __name__ == '__main__':
    #subprocess.call(["docker-compose", "-f", os.getenv("COMPOSE_SERVER") ,"down"], stderr=subprocess.DEVNULL)
    #subprocess.call(["docker-compose", "-f", os.getenv("COMPOSE_SERVER") ,"up"], stderr=subprocess.DEVNULL)
    docker_client = docker.DockerClient(base_url="ssh://julian_huwyler@cloud.jhuwyler.dev")
    for container in docker_client.containers.list():
        print(container.id)

    