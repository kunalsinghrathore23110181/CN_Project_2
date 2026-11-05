# CS 331 Project 2 — Understanding Host Network Stack Overheads

**Experiment:** Single Flow (Section 3.1)  
**Course:** CS 331 — Computer Networks  
**Team:** Gurudayal Meena and Kunal Singh Rathore  
**Paper:** *Understanding Host Network Stack Overheads* (ACM SIGCOMM 2021)

## About the project

In this project, we studied how the Linux operating system handles network traffic and why sending or receiving data can use a lot of CPU time. We used the paper *Understanding Host Network Stack Overheads* as our reference.

We focused on the **Single Flow** experiment from Section 3.1. The original researchers used two powerful servers connected by a 100 Gbps network link. We did not have that setup, so we tried a simpler version using one ASUS VivoBook laptop running Ubuntu in VirtualBox.

Our goal was to understand how a single TCP connection works, measure how much data it transfers, and observe how much CPU time the sender and receiver use.

## What we learned before starting

We first read the introduction and the sections explaining how the Linux network stack works. We studied:

- How an application sends data through sockets and the TCP/IP stack.
- How the receiver gets data and delivers it to the application.
- Why copying data and processing TCP packets use CPU time.
- What NAPI, TSO, GRO, and receive-side steering are used for in the original paper.
- Why the hardware and operating system can affect network performance.

This background helped us understand the purpose of the Single Flow experiment before running it ourselves.

## Work completed

During the project, we:

1. Read the paper and selected its Single Flow experiment.
2. Studied the sender-side and receiver-side TCP processing paths.
3. Used an Ubuntu VirtualBox VM on an ASUS VivoBook.
4. Configured iPerf3 for a local TCP test.
5. Started an iPerf3 server and connected a client to it using `127.0.0.1`.
6. Tested one TCP stream and checked that the connection worked.
7. Wrote a Python script to repeat the experiment and collect results.
8. Completed **50 recorded runs**, each lasting **20 seconds**, with a short pause between runs.
9. Saved the original iPerf3 output for every run as JSON and also created a combined CSV file.
10. Used `pidstat` to observe iPerf3 process CPU usage while the test was running.
11. Calculated the average, minimum, and maximum throughput.
12. Compared our setup and observations with the original paper and noted the limitations.
13. Prepared the project report and presentation from the work we completed.

## Our experiment setup

- **Computer:** ASUS VivoBook laptop
- **System used for testing:** Ubuntu in VirtualBox
- **Linux kernel:** 5.15.0-139-generic
- **Allocated CPU:** 4 virtual CPUs
- **Allocated memory:** About 3.8 GiB RAM
- **Traffic tool:** iPerf3 3.7
- **Automation:** Python 3
- **CPU observation:** iPerf3 CPU statistics and `pidstat`
- **TCP connection:** One stream, using `127.0.0.1` (loopback)

Both the sender and the receiver ran inside the **same Ubuntu VM**. They were separate iPerf3 processes, but the TCP traffic stayed inside Linux instead of travelling through an external network cable.

## Repository structure

```text
README.md
code/
    single_flow_experiment/
        single_flow.py
        single_flow_50_tests.log
        results/
            single_flow_results.csv
            run_1.json ... run_50.json
report/
    final_report.pdf
ppt/
    presentation.pptx
ai/
    complete AI prompts and conversation logs
```

The names under `report/` and `ppt/` should match the actual files uploaded to GitHub. The `ai/` folder should contain the **full raw conversations**, not summaries.

## How to run the experiment

These commands are for the original `single_flow.py` script used to collect our 50-run dataset.

### 1. Install the tools in Ubuntu

```bash
sudo apt update
sudo apt install -y iperf3 python3 sysstat
```

### 2. Open the code directory

From the root folder of this GitHub repository:

```bash
cd code/single_flow_experiment
```

### 3. Start the receiver (Terminal 1)

```bash
iperf3 -s -B 127.0.0.1
```

Leave this terminal running. The server listens for a TCP connection from the client.

### 4. Try one manual transfer (Terminal 2)

```bash
iperf3 -c 127.0.0.1 -P 1 -t 20
```

- `-c 127.0.0.1` connects to the local server.
- `-P 1` uses a single TCP stream.
- `-t 20` sends data for 20 seconds.

We used this manual test to make sure the setup worked.

### 5. Run the automated experiment (Terminal 2)

**Warning:** The original script writes to `results/run_1.json` through `run_50.json` and `results/single_flow_results.csv`. Running it again can replace previously recorded measurements. Back up the results first:

```bash
cp -a results "results_backup_$(date +%Y%m%d_%H%M%S)"
python3 single_flow.py
```

The server from Terminal 1 must still be running. The script performs 50 tests and saves each successful test's iPerf3 output.

### 6. Optional: check process CPU usage

While a test is running, open another terminal and use:

```bash
pidstat -u -C iperf3 1
```

This shows the CPU usage of the iPerf3 processes. It is a separate observation from the CPU values stored by iPerf3 in the JSON files.

## Files saved during testing

- **`single_flow.py`** — automates the TCP tests and saves measurements.
- **`results/run_1.json` to `run_50.json`** — the original iPerf3 data from each run.
- **`results/single_flow_results.csv`** — the run number, receiver-reported throughput, sender CPU usage, and receiver CPU usage.
- **`single_flow_50_tests.log`** — saved terminal output from the experiment.

We kept the individual JSON files so the measurements could be checked again without running the tests a second time.

## What we observed

From the **50 recorded runs**:

- **Average TCP goodput:** 55.19 Gbps
- **Minimum:** 39.44 Gbps
- **Maximum:** 60.07 Gbps
- **Sender process CPU:** usually around 98–99% of one logical CPU
- **Receiver process CPU:** usually around 60–66% of one logical CPU

The first run reported an unusually low receiver CPU value (about 2.58%). We kept it in the saved data instead of deleting it.

The CPU values are for the iPerf3 processes. They do **not** mean that the entire four-vCPU machine was using those percentages.

## Why we got these results

Our client sent data to `127.0.0.1`, which is the Linux **loopback** address. This means that the data was exchanged inside the VM rather than through the laptop's Wi-Fi or Ethernet interface.

So, **55.19 Gbps is the measured rate of local TCP data transfer, not the speed of the laptop's physical network connection**. The CPU, memory, Linux TCP processing, and VM scheduling can all affect this kind of test.

We also noticed some variation between runs. Background activity and virtual CPU scheduling may have contributed, but we did not measure those causes separately, so we cannot say exactly why each run was different.

## How our experiment differs from the paper

The original paper used two physical servers connected by a 100 Gbps network interface. It also compared network optimizations and measured detailed CPU overhead inside Linux.

Our experiment used **one laptop, one Ubuntu VM, and the loopback interface**. We studied one TCP stream and measured its throughput and the CPU usage reported for the sender and receiver.

We did **not** reproduce the paper's physical NIC tests, hardware offload comparisons, cache experiments, NUMA measurements, or detailed kernel-function profiling. The paper's approximately 42 Gbps **per-core** result and our 55.19 Gbps **local TCP goodput** use different conditions and should not be treated as a direct performance comparison.

## What we learned

This project gave us practical experience with Linux TCP communication, running a sender and receiver, using iPerf3, automating tests in Python, saving measurements, and interpreting CPU usage. Most importantly, we learned that a throughput result only makes sense when we also explain **how the traffic was sent** and **what hardware was involved**.

Our work is an **adapted Single Flow experiment**, not a complete reproduction of the research paper.

## References

1. Q. Cai et al., *Understanding Host Network Stack Overheads*, ACM SIGCOMM 2021. https://doi.org/10.1145/3452296.3472888
2. Original paper's code: https://github.com/Terabit-Ethernet/Understanding-network-stack-overheads-SIGCOMM-2021
