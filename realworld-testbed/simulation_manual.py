import sys
import copy
from datetime import datetime
from statistics import mean
import json
from typing import Collection
from loguru import logger
from testbeds import RealWorldTestbed
from scenarios import QPEPScenario, OpenVPNScenario, PEPsalScenario, PlainScenario, QPEPAckScenario, QPEPCongestionScenario
from benchmarks import IperfBenchmark, SitespeedBenchmark, IperfUDPBenchmark
import numpy
import os
from dotenv import load_dotenv
load_dotenv()

def iperf_test_scenario():
    # Simulates IPERF transfers at different file sizes

    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    with open(str(os.getenv("TESTBED_FILE"))) as file:
        testbed_name = file.readlines()[0]
    benchmarks = [IperfBenchmark(file_sizes=iperf_file_sizes[1:2], iterations=1)]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNScenario(name="ovpn", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=copy.deepcopy(benchmarks), terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal", gateway=True, terminal=True, testbed=testbed,benchmarks=copy.deepcopy(benchmarks))
    qpep_scenario = QPEPScenario(name="qpep", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [plain_scenario, qpep_scenario, distributed_pepsal_scenario, vpn_scenario, pepsal_scenario]
    for scenario in scenarios:
        logger.debug("Running iperf test scenario " + str(scenario.name))
        iperf_scenario_results = {}
        scenario.run_benchmarks()
        for benchmark in scenario.benchmarks:
            logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
            iperf_scenario_results = benchmark.results
            print(iperf_scenario_results)
        scenario.print_results()
        benchmark.save_results_to_db(str(scenario.name),testbed_name)

def iperf_UDP_test_scenario():
    # Simulates IPERF transfers at different file sizes

    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    with open(str(os.getenv("TESTBED_FILE"))) as file:
        testbed_name = file.readlines()[0]
    benchmarks = [IperfUDPBenchmark(file_sizes=iperf_file_sizes[4:], iterations=2)]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNScenario(name="ovpn", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=copy.deepcopy(benchmarks), terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal", gateway=True, terminal=True, testbed=testbed,benchmarks=copy.deepcopy(benchmarks))
    qpep_scenario = QPEPScenario(name="qpep", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [plain_scenario]
    #scenarios = [qpep_scenario, distributed_pepsal_scenario, vpn_scenario, plain_scenario, pepsal_scenario]
    for scenario in scenarios:
        logger.debug("Running iperf test scenario " + str(scenario.name))
        iperf_scenario_results = {}
        scenario.run_benchmarks()
        for benchmark in scenario.benchmarks:
            logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
            iperf_scenario_results = benchmark.results
            print(iperf_scenario_results)
        scenario.print_results()
        benchmark.save_results_to_db(str(scenario.name),testbed_name)
def plt_test_scenario(testbed=None):
    if testbed is None:
        testbed = RealWorldTestbed()
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
    with open(str(os.getenv("TESTBED_FILE"))) as file:
        testbed_name = file.readlines()[0]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=[])
    vpn_scenario = OpenVPNScenario(name="ovpn", testbed=testbed, benchmarks=[])
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=[], terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal",terminal=True, gateway=True, testbed=testbed,benchmarks=[])
    qpep_scenario = QPEPScenario(name="qpep", testbed=testbed, benchmarks=[])
    scenarios = [plain_scenario, pepsal_scenario, distributed_pepsal_scenario, qpep_scenario, vpn_scenario]
    for scenario in scenarios:
        scenario.benchmarks = [SitespeedBenchmark(hosts=alexa_top_20[0:1], scenario=scenario, iterations=1, sub_iterations=1)]
        logger.debug("Running PLT test scenario " + str(scenario.name))
        scenario.deploy_scenario()
        scenario.run_benchmarks(deployed=True)
        for benchmark in scenario.benchmarks:
            print("Results for PLT " + str(scenario.name))
            print(benchmark.results)
            benchmark.save_results_to_db(str(scenario.name),testbed_name)
    for scenario in scenarios:
        if scenario.name == os.getenv("SCENARIO_NAME"):
            scenario.print_results()

if __name__ == '__main__':
    # These functions draw on parameters from the .env file to determine which scenarios to run and which portions of the scenario. See the QPEP README for some advice on using .env to run simulations in parallel
    logger.remove()
    #logger.add(sys.stderr, level="SUCCESS")
    logger.add(sys.stderr, level="DEBUG")

    # Run Iperf Goodput Tests
    #iperf_test_scenario()
    iperf_UDP_test_scenario()

    # Run PLT Alexa Top 20 Test
    #plt_test_scenario()

    #Next look at ACK decimation
    #ack_bundling_iperf_scenario()