from statistics import mean

from loguru import logger
from abc import ABC, abstractmethod
import docker
import json
import time
import re
from pymongo import MongoClient
import pymongo
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
load_dotenv(str(os.getenv("SERVER_ENV")))
load_dotenv(str(os.getenv("CLIENT_ENV")))

alexa_top_20 = [
    "https://www.google.com",
    "https://www.youtube.com",
    "https://www.tmall.com",
    "https://www.facebook.com",
    "https://www.baidu.com",
    "https://www.qq.com",
    "https://www.sohu.com",
    "https://www.taobao.com",
    "https://www.360.cn",
    "https://www.jd.com",
    "https://www.yahoo.com",
    "https://www.amazon.com",
    "https://www.wikipedia.org",
    "https://www.weibo.com",
    "https://www.sina.com.cn",
    "https://www.reddit.com",
    "https://www.live.com",
    "https://www.netflix.com",
    "https://www.okezone.com",
    "https://www.vk.com"
]

class Benchmark(ABC):
    def __init__(self, name=""):
        self.results = {}
        self.name = name

    @abstractmethod
    def run(self):
        pass

    def print_results(self):
        print(self.results)
    
    def save_results_to_file(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.results, outfile)
    def push_to_db(self, collection_name, data):
        try:
            client = MongoClient(os.getenv("FIRST_DB_LOGIN_STR"), connectTimeoutMS=3000,serverSelectionTimeoutMS=5000)
            logger.debug(client.server_info())
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.warning('Could not connect to DB Server '+os.getenv("FIRST_DB_NAME"))
            try:
                client = MongoClient(os.getenv("SECOND_DB_LOGIN_STR"), connectTimeoutMS=3000,serverSelectionTimeoutMS=5000)
                logger.debug(client.server_info())
            except pymongo.errors.ServerSelectionTimeoutError:
                logger.warning('Could not connect to DB Server '+os.getenv("SECOND_DB_NAME"))
                logger.warning('Could not upload results to DB')
            else:
                db = client[os.getenv("DB_NAME")]
                db[collection_name].insert_one(data)
                logger.debug('uploaded to DB Server '+os.getenv("SECOND_DB_NAME"))
        else:
            db = client[os.getenv("DB_NAME")]
            db[collection_name].insert_one(data)
            logger.debug('uploaded to DB Server'+os.getenv("FIRST_DB_NAME"))
    
    @abstractmethod
    def save_results_to_db(self, scenario_name, testbed_name):
        pass

    def make_keys_mongoDB_compatible(self, data):
        # MongoDB does not accept '.' in keys so we need to replace them
        new_data = {}
        for key in data.keys():
            new_key = key.replace(".","-")
            new_data[new_key] = data[key]
        return new_data

class IperfBenchmark(Benchmark):
    def __init__(self, file_sizes, reset_on_run=True, iterations=1):
        self.file_sizes = file_sizes
        self.reset_on_run = reset_on_run
        self.iterations = iterations
        super().__init__(name="IPerf")

    def run(self):
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        terminal_workstation.exec_run("wget http://1.1.1.1") #use this to warm up vpns/peps
        for i in range(0, self.iterations):
            for file_size in self.file_sizes:
                try:
                    test_results = self.run_iperf_test(file_size, self.reset_on_run)
                except KeyboardInterrupt:
                    break
                except:
                    logger.info("Iperf measurement Failed - Probably Docker Connection issue")
                    test_results = {
                        "sent_bytes": 0,
                        "sent_bps": 0,
                        "received_bytes": 0,
                        "received_bps": 0
                    }
                result_name = "iperf_" + str(round(file_size/1000000, 3)) + "mb"
                if result_name not in self.results.keys():
                    self.results[result_name] = {}
                    for key in test_results.keys():
                        self.results[result_name][key] = [test_results[key]]
                else:
                    for key in test_results.keys():
                        self.results[result_name][key].append(test_results[key])
            print("Interim Results (Iter:", i+1, " of ", self.iterations, "):", self.results)

    def run_iperf_test(self, transfer_bytes, reset_on_run, with_timeout=True, timeout=600):
        logger.debug("Starting iperf server")
        docker_client_cloud = docker.DockerClient(base_url="ssh://"+os.getenv("DOCKER_REMOTE_URL"))
        gateway_workstation = docker_client_cloud.containers.get(os.getenv('WS_GW_CONTAINER_NAME'))
        if reset_on_run:
            gateway_workstation.exec_run("pkill -9 iperf3")
            time.sleep(1)
        gateway_workstation.exec_run("iperf3 -s", detach=True)
        logger.debug("Starting iperf client")
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        if reset_on_run:
            terminal_workstation.exec_run("pkill -9 iperf3")
            time.sleep(1)
        if with_timeout:
            exit_code, output = terminal_workstation.exec_run("/usr/bin/timeout --signal=SIGINT " + str(timeout) +" /usr/bin/iperf3 --no-delay -c "  + str(os.getenv("IPERF_SERVER_ADDRESS"))+ " -R --json -n " + str(transfer_bytes))
        else:
            exit_code, output = terminal_workstation.exec_run("iperf3 --no-delay -c "  + str(os.getenv("IPERF_SERVER_ADDRESS"))+ " -R --json -n " + str(transfer_bytes))
        json_string = output.decode('unicode_escape').rstrip('\n').replace('Linux\n', 'Linux') # there's an error in iperf3's json output here
        try:
            test_result = json.loads(json_string)
        except:
            json_string = "error - control socket has closed unexpectedly"
        if "error - control socket has closed unexpectedly" in json_string:
            logger.debug("IPerf connect socket lost, download failed")
            return {
                "sent_bytes": 0,
                "sent_bps": 0,
                "received_bytes": 0,
                "received_bps": 0
            }
        try:
            logger.debug("Iperf Result: " + str(test_result["end"]["sum_sent"]["bits_per_second"]/1000000) +
                           "/" + str(test_result["end"]["sum_received"]["bits_per_second"]/1000000))
        except:
            logger.error("Unable to parse iperf result")
            print(json_string)
            return {
                "sent_bytes": 0,
                "sent_bps": 0,
                "received_bytes": 0,
                "received_bps": 0
            }
        return {
            "sent_bytes": test_result["end"]["sum_sent"]["bytes"],
            "sent_bps": test_result["end"]["sum_sent"]["bits_per_second"],
            "received_bytes": test_result["end"]["sum_received"]["bytes"],
            "received_bps": test_result["end"]["sum_received"]["bits_per_second"],
        }
    
    def print_results(self):
        print("Full Results: ")
        print(self.results)
        print("~"*25)
        print("Average Speeds: ")
        for result_key in self.results.keys():
            print(result_key, "sent_bps:", mean(self.results[result_key]["sent_bps"]) / 1000000)
            print(result_key, "received_bps:", mean(self.results[result_key]["received_bps"])/ 1000000)
    
    def save_results_to_db(self, scenario_name, testbed_name):
        data ={}
        now = datetime.now()
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        try:
            exit_code, output = terminal_workstation.exec_run("ping -c 1 google.ch")
        except:
            logger.warning("Ping measurement failed")
        try:
            string = output.decode()
            ping = re.findall("time=([0-9]+)", string)[0]
        except:
            logger.warning("Could not parse ping output. Raw String: "+string)
            ping = "9999"
        logger.debug("Ping[ms]:"+ping)
        data.update({
            "date": now,
            "testbed": testbed_name,
            "scenario": scenario_name,
            "ping": int(ping),
            "measurements": self.make_keys_mongoDB_compatible(self.results)
        })
        logger.debug(data)
        if data["measurements"] != {}:
            logger.debug("Uploading to DB")
            self.push_to_db("iperf_TCP",data)


 
class IperfUDPBenchmark(Benchmark):
    def __init__(self, file_sizes, bw_limit="50M", iterations=1):
        self.file_sizes = file_sizes
        self.bw_limit = bw_limit
        self.iterations = iterations
        super().__init__(name="IPerfUDP")

    def run(self):
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        terminal_workstation.exec_run("wget http://1.1.1.1") #use this to warm up vpns/peps
        for i in range(0, self.iterations):
            for file_size in self.file_sizes:
                try:
                    test_results = self.run_iperf_test(file_size, self.bw_limit)
                except KeyboardInterrupt:
                    break
                except:
                    logger.info("Iperf measurement Failed - Probably Docker Connection issue")
                    test_results = {
                        "sent_bytes": 0,
                        "sent_bps": 0,
                        "received_bytes": 0,
                        "received_bps": 0
                    }
                result_name = "iperf_" + str(round(file_size/1000000, 3)) + "mb"
                if result_name not in self.results.keys():
                    self.results[result_name] = {}
                    for key in test_results.keys():
                        self.results[result_name][key] = [test_results[key]]
                else:
                    for key in test_results.keys():
                        self.results[result_name][key].append(test_results[key])
            print("Interim Results (Iter:", i+1, " of ", self.iterations, "):", self.results)

    def run_iperf_test(self, transfer_bytes, bw_limit, with_timeout=True, timeout=600):
        self.bw_limit = bw_limit
        logger.debug("Starting iperf server")
        docker_client_cloud = docker.DockerClient(base_url="ssh://"+os.getenv("DOCKER_REMOTE_URL"))
        gateway_workstation = docker_client_cloud.containers.get(os.getenv('WS_GW_CONTAINER_NAME'))
        
        gateway_workstation.exec_run("pkill -9 iperf3")
        time.sleep(1)
        gateway_workstation.exec_run("iperf3 -s", detach=True)
        logger.debug("Starting iperf client")
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        terminal_workstation.exec_run("pkill -9 iperf3")
        time.sleep(1)
        exit_code, output = terminal_workstation.exec_run("iperf3 -u -b "+bw_limit+" --no-delay -c "  + str(os.getenv("IPERF_SERVER_ADDRESS"))+ " -R --json -n " + str(transfer_bytes))
        json_string = output.decode('unicode_escape').rstrip('\n').replace('Linux\n', 'Linux') # there's an error in iperf3's json output here
        try:
            test_result = json.loads(json_string)
        except:
            json_string = "error - control socket has closed unexpectedly"
        if "error - control socket has closed unexpectedly" in json_string:
            logger.debug("IPerf connect socket lost, download failed")
            return {
                "seconds":      0,
                "bytes":        0,
                "bits_per_second":      0,
                "lost_packets": 0,
                "packets":      0,
                "lost_percent": 0
            }
        try:
            logger.debug("Iperf Result: " + str(test_result["end"]["sum"]["bits_per_second"]/1000000) +
                           "/" + str(test_result["end"]["sum"]["lost_percent"])+"%")
        except:
            logger.error("Unable to parse iperf result")
            print(json_string)
            return {
                "seconds":      0,
                "bytes":        0,
                "bits_per_second":      0,
                "lost_packets": 0,
                "packets":      0,
                "lost_percent": 0
            }
        return {
            "seconds":          test_result["end"]["sum"]["seconds"],
            "bytes":            test_result["end"]["sum"]["bytes"],
            "bits_per_second":  test_result["end"]["sum"]["bits_per_second"],
            "lost_packets":     test_result["end"]["sum"]["lost_packets"],
            "packets":          test_result["end"]["sum"]["packets"],
            "lost_percent":     test_result["end"]["sum"]["lost_percent"]
        }
    
    def print_results(self):
        print("Full Results: ")
        print(self.results)
        print("~"*25)
        print("Average Speeds: ")
        for result_key in self.results.keys():
            print(result_key, "bits_per_second:", mean(self.results[result_key]["bits_per_second"]) / 1000000)
            print(result_key, "lost_percent:", mean(self.results[result_key]["lost_percent"]))
            
    def save_results_to_db(self, scenario_name, testbed_name):
        data ={}
        now = datetime.now()
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        try:
            exit_code, output = terminal_workstation.exec_run("ping -c 1 google.ch")
        except:
            logger.warning("Ping measurement failed")
        try:
            string = output.decode()
            ping = re.findall("time=([0-9]+)", string)[0]
        except:
            logger.warning("Could not parse ping output. Raw String: "+string)
            ping = 9999
        logger.debug("Ping: "+ping)
        data.update({
            "date": now,
            "testbed": testbed_name,
            "scenario": scenario_name,
            "ping": int(ping),
            "bw_limit": self.bw_limit,
            "measurements": self.make_keys_mongoDB_compatible(self.results)
        })
        print(data)
        if data["measurements"] != {}:
            self.push_to_db("iperf_UDP",data)
class SitespeedBenchmark(Benchmark):
    def __init__(self, hosts=alexa_top_20, iterations=1, average_only=False, scenario=None, sub_iterations=1):
        self.hosts = hosts
        self.iterations = iterations
        self.average_only = average_only
        super().__init__(name="SiteSpeed")
        self.results = {}
        self.errors = 0
        self.scenario = scenario
        self.sub_iterations = sub_iterations

    def run(self):
        logger.debug("Launching SiteSpeed.io Tests")
        docker_client = docker.from_env()
        sitespeed_workstation = docker_client.containers.get(os.getenv("WS_SITESPEED_CONTAINER_NAME"))
        sitespeed_workstation.exec_run("wget http://1.1.1.1") #use this to warm up vpns/peps
        host_string = ''
        for i in range(0, self.iterations):
            for host in self.hosts:
                host_string = host + " "
                try:
                    host_result = sitespeed_workstation.exec_run('/usr/src/app/bin/browsertime.js -n ' + str(self.sub_iterations) +' --headless --browser firefox --cacheClearRaw --firefox.preference network.dns.disableIPv6:true --video=false --visualMetrics=false --visualElements=false ' + str(host_string))
                except KeyboardInterrupt:
                    break
                except:
                    logger.debug("Could not get result for "+str(host)+" due to errors")
                    continue
                matches = re.findall('Load: ([0-9.]+)([ms])', str(host_result))
                if self.sub_iterations > 0:
                    matches = matches[:-1] # the last match is the average load time, which we don't want mixing up our stats
                for match in matches:
                        # if the connection measures in milliseconds we take as is, otherwise convert
                    if match[1] == 'm':
                        host_val = float(match[0])
                    elif match[1] == 's':
                        host_val = float(match[0]) * 1000
                    if host not in self.results.keys():
                            self.results[host] = [host_val]
                    else:
                            self.results[host].append(host_val)
                    print(host_result)
                if len(matches) == 0:
                    logger.warning("No browsertime measurement for " + str(host_string))
                else:
                    logger.debug("Browsertime: " + str(host_string) + " " + str(match[0]) + str(match[1]))
                #count failed connections for host
                error_matches = re.findall('UrlLoadError', str(host_result))
                self.errors = self.errors + len(error_matches)
                logger.debug("Browsertime Error Count: " + str(len(error_matches)) + " " + host)
                print("Interim Results: ","(", self.name,")", self.results)
            if i != self.iterations - 1:  
                self.scenario.deploy_scenario()

    def print_results(self):
        print(self.results)

        #print("Mean page load time: ", mean(self.results))
        #print("Load time measurements: ", self.results)
        print("Failed load count: ", self.errors)

    def save_results_to_db(self, scenario_name, testbed_name):
        data ={}
        now = datetime.now()
        docker_client = docker.from_env()
        terminal_workstation = docker_client.containers.get(os.getenv("WS_ST_CONTAINER_NAME"))
        try:
            exit_code, output = terminal_workstation.exec_run("ping -c 1 google.ch")
        except:
            logger.warning("Ping measurement failed")
        try:
            string = output.decode()
            ping = re.findall("time=([0-9]+)", string)[0]
        except:
            logger.warning("Could not parse ping output. Raw String: "+string)
            ping = 9999
        logger.debug("Ping: "+ping)
        data.update({
            "date": now,
            "testbed": testbed_name,
            "scenario": scenario_name,
            "ping": int(ping),
            "measurements": self.make_keys_mongoDB_compatible(self.results)
        })
        logger.debug(data)
        if data["measurements"] != {}:
            self.push_to_db("sitespeed",data)

if __name__ == "__main__":
    benchmark = SitespeedBenchmark()
    benchmark.save_results_to_db("test","realworld")