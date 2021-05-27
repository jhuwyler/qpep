import sys
import copy
import time
from statistics import mean
import json
from loguru import logger
from testbeds import RealWorldTestbed
from scenarios import QPEPScenario, OpenVPNScenario, PEPsalScenario, PlainScenario, QPEPAckScenario, QPEPCongestionScenario
from benchmarks import IperfBenchmark, SitespeedBenchmark
import numpy
import os
from dotenv import load_dotenv
load_dotenv()

def ack_bundling_iperf_scenario():
    # Simulates ACK decimation ratios for different IPERF transfer sizes at different PLR rates
    # qpep-only scenario
    testbed = BasicTestbed(host_ip=HOST_IP)
    iperf_file_sizes=[1000000, 2000000, 5000000]
    plr_levels = [0, 1*pow(10,-7), 1*(pow(10, -4)), 1*(pow(10,-2))]
    benchmarks = [IperfBenchmark(file_sizes=iperf_file_sizes, reset_on_run=True, iterations=int(os.getenv("IPERF_ITERATIONS")))]
    ack_bundling_numbers = [ack for ack in range(1, 31, 1)]
    scenario = QPEPAckScenario(name='QPEP Ack Bundling Test', testbed=testbed, benchmarks=[])
    decimation_results = {}
    for ack_bundling_number in ack_bundling_numbers[int(os.getenv("ACK_BUNDLING_MIN")):int(os.getenv("ACK_BUNDLING_MAX"))]:
        scenario.deploy_scenario(ack_level=ack_bundling_number)
        if str(ack_bundling_number) not in decimation_results.keys():
            decimation_results[str(ack_bundling_number)] = {}
        for plr_level in plr_levels:
            plr_string = numpy.format_float_positional(plr_level, precision=7, trim='-')
            if plr_string not in decimation_results[str(ack_bundling_number)].keys():
                decimation_results[str(ack_bundling_number)][plr_string] = []
            
            scenario.testbed.set_plr_percentage(plr_string, st_out=False, gw_out=True)
            scenario.benchmarks = copy.deepcopy(benchmarks)
            scenario.run_benchmarks(deployed=True)
            
            for benchmark in scenario.benchmarks:
                decimation_results[str(ack_bundling_number)][plr_string].append(benchmark.results)
            
            logger.debug("Interim bundling results for PLR level " + str(plr_string) + " and ACK level " + str(ack_bundling_number) +":" + str(decimation_results))
    print("Final Ack Bundling Results for QPEP " + str(os.getenv("ACK_BUNDLING_MIN") + "-" + str(os.getenv("ACK_BUNDLING_MAX"))))
    print("*********************\n")
    print(decimation_results)
    print("\n*********************")

def iperf_test_scenario():
    # Simulates IPERF transfers at different file sizes

    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    benchmarks = [IperfBenchmark(file_sizes=iperf_file_sizes[int(os.getenv("IPERF_MIN_SIZE_INDEX")):int(os.getenv("IPERF_MAX_SIZE_INDEX"))], iterations=int(os.getenv("IPERF_ITERATIONS")))]
    plain_scenario = PlainScenario(name="Plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNScenario(name="OpenVPN", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    pepsal_scenario = PEPsalScenario(name="PEPSal", testbed=testbed, benchmarks=copy.deepcopy(benchmarks), terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="Distributed PEPsal", gateway=True, terminal=True, testbed=testbed,benchmarks=copy.deepcopy(benchmarks))
    qpep_scenario = QPEPScenario(name="QPEP", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [qpep_scenario, distributed_pepsal_scenario, vpn_scenario, plain_scenario, pepsal_scenario]
    for scenario in scenarios:
        if scenario.name == os.getenv("SCENARIO_NAME"):
            logger.debug("Running iperf test scenario " + str(scenario.name))
            iperf_scenario_results = {}
            scenario.run_benchmarks()
            for benchmark in scenario.benchmarks:
                logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
                iperf_scenario_results = benchmark.results
                print(iperf_scenario_results)
            scenario.print_results()

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
    plain_scenario = PlainScenario(name="Plain", testbed=testbed, benchmarks=[])
    vpn_scenario = OpenVPNScenario(name="OpenVPN", testbed=testbed, benchmarks=[])
    pepsal_scenario = PEPsalScenario(name="PEPSal", testbed=testbed, benchmarks=[], terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="Distributed PEPsal",terminal=True, gateway=True, testbed=testbed,benchmarks=[])
    qpep_scenario = QPEPScenario(name="QPEP", testbed=testbed, benchmarks=[])
    scenarios = [plain_scenario, pepsal_scenario, distributed_pepsal_scenario, qpep_scenario, vpn_scenario]
    for scenario in scenarios:
        if scenario.name == os.getenv("SCENARIO_NAME"):
            scenario.benchmarks = [SitespeedBenchmark(hosts=alexa_top_20[int(os.getenv("ALEXA_MIN")):int(os.getenv("ALEXA_MAX"))], scenario=scenario, iterations=int(os.getenv("PLT_ITERATIONS")), sub_iterations=int(os.getenv("PLT_SUB_ITERATIONS")))]
            logger.debug("Running PLT test scenario " + str(scenario.name))
            scenario.deploy_scenario()
            scenario.run_benchmarks(deployed=True)
            for benchmark in scenario.benchmarks:
                print("Results for PLT " + str(scenario.name))
                print(benchmark.results)
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

    # Run PLT Alexa Top 20 Test
    plt_test_scenario()

    #Next look at ACK decimation
    #ack_bundling_iperf_scenario()