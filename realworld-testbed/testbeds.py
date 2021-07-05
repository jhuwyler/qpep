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
        logger.debug("Shutting Down Previous Testbed: local")
        subprocess.call(["/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_CLIENT") ,"down"], stderr=subprocess.DEVNULL)
        logger.debug("Shutting Down Previous Testbeds: remote")
        subprocess.call(["ssh", os.getenv("DOCKER_REMOTE_URL"), "/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_SERVER") ,"down"], stderr=subprocess.DEVNULL)

        logger.debug("Starting local Testbed Containers")
        # Start the docker containers
        subprocess.call(["/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_CLIENT") , "up", "-d"])
        logger.debug("Starting remote Testbed Containers")
        subprocess.call(["ssh", os.getenv("DOCKER_REMOTE_URL"), "/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_SERVER") , "up", "-d"])

        logger.success("Real-world Testbed Running")

    def stop_testbed(self):
        logger.debug("Shutting Down Testbed: local")
        subprocess.call(["/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_CLIENT") ,"down"], stderr=subprocess.DEVNULL)
        logger.debug("Shutting Down Testbeds: remote")
        subprocess.call(["ssh", os.getenv("DOCKER_REMOTE_URL"), "/usr/local/bin/docker-compose", "-f", os.getenv("COMPOSE_SERVER") ,"down"], stderr=subprocess.DEVNULL)
    

if __name__ == '__main__':
    #subprocess.call(["docker-compose", "-f", os.getenv("COMPOSE_SERVER") ,"down"], stderr=subprocess.DEVNULL)
    #subprocess.call(["docker-compose", "-f", os.getenv("COMPOSE_SERVER"), "-c", "cloud" ,"up"], stderr=subprocess.DEVNULL)
    docker_client_cloud = docker.DockerClient(base_url="ssh://"+os.getenv("DOCKER_REMOTE_URL"))
    gateway = docker_client_cloud.containers.get(os.getenv('WS_GW_CONTAINER_NAME'))
    gateway.exec_run("iperf3 -s", detach=True)
