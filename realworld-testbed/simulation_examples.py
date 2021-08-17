import sys
import copy
from loguru import logger
from testbeds import RealWorldTestbed
from scenarios import QPEPScenario, OpenVPNScenario, PEPsalScenario, PlainScenario, OpenVPNTCPScenario
from benchmarks import Benchmark, IperfBenchmark, SitespeedBenchmark, IperfUDPBenchmark, ChannelCharBenchmark
import os, time
from dotenv import load_dotenv
load_dotenv()
load_dotenv(str(os.getenv("SERVER_ENV")))
load_dotenv(str(os.getenv("CLIENT_ENV")))

def iperf_test_scenario():
    # Simulates IPERF transfers at different file sizes

    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    logger.info("+"*10+" Starting IPERF TCP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    benchmarks = [IperfBenchmark(file_sizes=iperf_file_sizes[int(os.getenv("IPERF_MIN_SIZE_INDEX")):int(os.getenv("IPERF_MAX_SIZE_INDEX"))], iterations=int(os.getenv("IPERF_ITERATIONS")))]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNScenario(name="ovpn-port"+str(os.getenv("WS_OVPN_PORT")), testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=copy.deepcopy(benchmarks), terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal", gateway=True, terminal=True, testbed=testbed,benchmarks=copy.deepcopy(benchmarks))
    qpep_scenario = QPEPScenario(name="qpep-port"+str(os.getenv("QPEP_SRV_PORT")), testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [qpep_scenario, distributed_pepsal_scenario, vpn_scenario, plain_scenario, pepsal_scenario]
    for scenario in scenarios:
        logger.debug("Running iperf test scenario " + str(scenario.name))
        iperf_scenario_results = {}
        scenario.run_benchmarks()
        for benchmark in scenario.benchmarks:
            logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
            iperf_scenario_results = benchmark.results
            logger.debug(iperf_scenario_results)
            benchmark.save_results_to_db(str(scenario.name),str(os.getenv("TESTBED_NAME")))
        logger.info("PROGRESS: "+str(int(scenarios.index(scenario))+1)+"/"+str(int(len(scenarios))))
    logger.info("-"*10+" Finished IPERF TCP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)

def iperf_UDP_test_scenario():
    # Simulates IPERF transfers at different file sizes

    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    logger.info("+"*10+" Starting IPERF UDP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    file_sizes= iperf_file_sizes[int(os.getenv("IPERF_MIN_SIZE_INDEX")):int(os.getenv("IPERF_MAX_SIZE_INDEX"))]
    iters = int(os.getenv("IPERF_ITERATIONS"))
    benchmarks = [
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="1M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="2.5M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="5M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="10M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="15M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="20M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="30M"),
        IperfUDPBenchmark(file_sizes=file_sizes, iterations=iters, bw_limit="50M")
    
    ]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNScenario(name="ovpn-port"+str(os.getenv("WS_OVPN_PORT")), testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=copy.deepcopy(benchmarks), terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal", gateway=True, terminal=True, testbed=testbed,benchmarks=copy.deepcopy(benchmarks))
    qpep_scenario = QPEPScenario(name="qpep-port"+str(os.getenv("QPEP_SRV_PORT")), testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [plain_scenario]
    for scenario in scenarios:
        logger.debug("Running iperf test scenario " + str(scenario.name))
        iperf_scenario_results = {}
        scenario.run_benchmarks()
        for benchmark in scenario.benchmarks:
            logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
            iperf_scenario_results = benchmark.results
            logger.info(iperf_scenario_results)
            benchmark.save_results_to_db(str(scenario.name),str(os.getenv("TESTBED_NAME")))
        logger.info("PROGRESS: "+str(int(scenarios.index(scenario))+1)+"/"+str(int(len(scenarios))))
    logger.info("-"*10+" Finished IPERF UDP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)

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
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=[])
    vpn_scenario = OpenVPNScenario(name="ovpn-port"+str(os.getenv("WS_OVPN_PORT")), testbed=testbed, benchmarks=[])
    pepsal_scenario = PEPsalScenario(name="pepsal", testbed=testbed, benchmarks=[], terminal=True, gateway=False)
    distributed_pepsal_scenario = PEPsalScenario(name="dist_pepsal",terminal=True, gateway=True, testbed=testbed,benchmarks=[])
    qpep_scenario = QPEPScenario(name="qpep-port"+str(os.getenv("QPEP_SRV_PORT")), testbed=testbed, benchmarks=[])
    scenarios = [plain_scenario, pepsal_scenario, distributed_pepsal_scenario, qpep_scenario, vpn_scenario]
    logger.info("+"*10+" Starting PLT on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    for scenario in scenarios:
        scenario.benchmarks = [SitespeedBenchmark(hosts=alexa_top_20[int(os.getenv("ALEXA_MIN")):int(os.getenv("ALEXA_MAX"))], scenario=scenario, iterations=int(os.getenv("PLT_ITERATIONS")), sub_iterations=int(os.getenv("PLT_SUB_ITERATIONS")))]
        logger.debug("Running PLT test scenario " + str(scenario.name))
        scenario.deploy_scenario()
        scenario.run_benchmarks(deployed=True)
        for benchmark in scenario.benchmarks:
            logger.info("Results for PLT " + str(scenario.name))
            logger.info(benchmark.results)
            benchmark.save_results_to_db(str(scenario.name),str(os.getenv("TESTBED_NAME")))
        logger.info("PROGRESS: "+str(int(scenarios.index(scenario))+1)+"/"+str(int(len(scenarios))))
    logger.info("-"*10+" Finished PLT on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)

def ovpn_tcp_iperf():
    testbed = RealWorldTestbed()
    # from 250k to 9.75 mb in 250kb steps
    # we add one modest "Warm up" sessions to start the connections for d_pepsal and qpep which have high first packet costs  but only
    # experience these costs once, when the customer starts the respective applications
    iperf_file_sizes = [25*1000, 50*1000, 100*1000, 150*1000]+[(i/4)*1000000 for i in range(1, 47)]
    iperf_file_sizes.sort()
    logger.info("+"*10+" Starting IPERF TCP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    benchmarks = [
        IperfBenchmark(file_sizes=iperf_file_sizes[int(os.getenv("IPERF_MIN_SIZE_INDEX")):int(os.getenv("IPERF_MAX_SIZE_INDEX"))], iterations=int(os.getenv("IPERF_ITERATIONS")))
    ]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    vpn_scenario = OpenVPNTCPScenario(name="ovpn-tcp"+str(os.getenv("WS_OVPN_PORT")), testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    scenarios = [plain_scenario, vpn_scenario, vpn_scenario, vpn_scenario]
    for scenario in scenarios:
        logger.debug("Running iperf test scenario " + str(scenario.name))
        iperf_scenario_results = {}
        scenario.run_benchmarks()
        for benchmark in scenario.benchmarks:
            logger.debug("Running Iperf Test Scenario (", str(scenario.name), ") with file sizes: " + str(benchmark.file_sizes))
            iperf_scenario_results = benchmark.results
            logger.debug(iperf_scenario_results)
            benchmark.save_results_to_db(str(scenario.name),str(os.getenv("TESTBED_NAME")))
        logger.info("PROGRESS: "+str(int(scenarios.index(scenario))+1)+"/"+str(int(len(scenarios))))
    logger.info("-"*10+" Finished IPERF TCP on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)

def ch_char_iperf():
    testbed = RealWorldTestbed()
    logger.info("+"*10+" Starting Channel Characterization on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    benchmarks = [ChannelCharBenchmark(60)]
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=copy.deepcopy(benchmarks))
    logger.debug("Running iperf test scenario " + str(plain_scenario.name))
    iperf_scenario_results = {}
    plain_scenario.run_benchmarks()
    for benchmark in plain_scenario.benchmarks:
        logger.debug("Running Iperf Test Scenario (", str(plain_scenario.name), ") for " + str(benchmark.send_time)+" seconds")
        iperf_scenario_results = benchmark.results
        logger.debug(iperf_scenario_results)
        benchmark.save_results_to_db(str(plain_scenario.name),str(os.getenv("TESTBED_NAME")))
    logger.info("-"*10+" Finished Channel Characterization on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)

def ovpn_tcp_plt(testbed=None):
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
    plain_scenario = PlainScenario(name="plain", testbed=testbed, benchmarks=[])
    vpn_scenario = OpenVPNTCPScenario(name="ovpn-tcp"+str(os.getenv("WS_OVPN_PORT")), testbed=testbed, benchmarks=[])

    scenarios = [plain_scenario, vpn_scenario, vpn_scenario, vpn_scenario]
    logger.info("+"*10+" Starting PLT on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"+"*10)
    for scenario in scenarios:
        scenario.benchmarks = [SitespeedBenchmark(hosts=alexa_top_20[int(os.getenv("ALEXA_MIN")):int(os.getenv("ALEXA_MAX"))], scenario=scenario, iterations=int(os.getenv("PLT_ITERATIONS")), sub_iterations=int(os.getenv("PLT_SUB_ITERATIONS")))]
        logger.debug("Running PLT test scenario " + str(scenario.name))
        scenario.deploy_scenario()
        scenario.run_benchmarks(deployed=True)
        for benchmark in scenario.benchmarks:
            logger.info("Results for PLT " + str(scenario.name))
            logger.info(benchmark.results)
            benchmark.save_results_to_db(str(scenario.name),str(os.getenv("TESTBED_NAME")))
        logger.info("PROGRESS: "+str(int(scenarios.index(scenario))+1)+"/"+str(int(len(scenarios))))
    logger.info("-"*10+" Finished PLT on Testbed "+str(os.getenv("TESTBED_NAME"))+" "+"-"*10)
if __name__ == '__main__':
    # These functions draw on parameters from the .env file to determine which scenarios to run and which portions of the scenario. See the QPEP README for some advice on using .env to run simulations in parallel
    logger.remove()

    logger.add(sys.stderr, level="DEBUG")
    # Channel charecterization Tests
    #for i in range(8):
    #    for i in range(10):
    #        ch_char_iperf()
    #    seconds = 20*60
    #    print("sleeping for "+str(seconds)+" seconds")
    #    time.sleep(seconds)

    # Run TCP version of OVPN (needs to be separately configured)
    #ovpn_tcp_iperf()
    #ovpn_tcp_plt()
    
    # Run Iperf Goodput Tests
    iperf_test_scenario()

    # Run PLT Alexa Top 20 Test
    plt_test_scenario()
