import subprocess
import os
from loguru import logger
import nclib
import docker
import time
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()

class BasicTestbed(object):
    def __init__(self, host_ip="192.168.1.199", display_number=0, linux=False):
        self.host_ip = host_ip
        self.display_number = display_number
        self.linux = linux

    def start_testbed(self):
        # First, shut down any old running testbeds
        logger.debug("Shutting Down Previous Testbeds")
        subprocess.call(["docker-compose", "down"], stderr=subprocess.DEVNULL)

        # The DISPLAY env variable points to an X server for showing OpenSAND UI
        my_env = {**os.environ, 'DISPLAY': str(self.host_ip) + ":" + str(self.display_number)}
        logger.debug("Starting Testbed Containers")

        # Start the docker containers
        subprocess.call(["docker-compose", "up", "-d"], env=my_env)

        # Wait for the opensand container to initialize then send a command to run the simulation
        logger.debug("Starting Opensand Platform")
        opensand_launched = False
        while not opensand_launched:
            try:
                nc = nclib.Netcat(('localhost', int(os.getenv('SAT_PORT_NUMBER'))), verbose=False)
                nc.recv_until(b'help')
                nc.recv()
                nc.send(b'status\n')
                response = nc.recv()
                opensand_launched = ('SAT' in str(response)) and ('GW0' in str(response)) and ('ST1' in str(response))
            except nclib.errors.NetcatError:
                continue

        time.sleep(1) # it often takes a little while for Opensand to identify all hosts
        logger.debug("Launching Opensand Simulation")
        nc.send(b'start\n')
        simulation_running = False
        while not simulation_running:
            nc.send(b'status\n')
            response = str(nc.recv())
            # wait for all three components (satellite, terminal and gateway) to start running
            simulation_running = response.count('RUNNING') > 3

        # now that the network is running, it is possible to add ip routes from user terminal through the network
        logger.debug("Connecting User Terminal to Satellite Spot Beam")
        docker_client = docker.from_env()
        terminal_container = docker_client.containers.get(os.getenv("ST_CONTAINER_NAME"))
        terminal_container.exec_run("/sbin/ip route delete default")
        terminal_container.exec_run("/sbin/ip route add default via " + str(os.getenv("GW_NETWORK_HEAD")) + ".0.3")
        logger.success("OpeSAND Testbed Running")

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

    def launch_wireshark(self):
        logger.debug("Starting Wireshark on Satellite Endpoint")
        docker_client = docker.from_env()
        satellite_container = docker_client.containers.get(os.getenv("SAT_CONTAINER_NAME"))
        satellite_container.exec_run("wireshark", detach=True)