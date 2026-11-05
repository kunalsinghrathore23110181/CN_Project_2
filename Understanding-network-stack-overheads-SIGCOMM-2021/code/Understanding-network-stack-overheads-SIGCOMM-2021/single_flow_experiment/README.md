# Single-flow TCP experiment — one Ubuntu VirtualBox VM

This directory contains our scaled-down single-flow benchmark based on Section 3.1 of Cai et al., *Understanding Host Network Stack Overheads* (SIGCOMM 2021). **It is not a reproduction of the authors' physical 100-Gbps NIC results.** Both endpoints run inside the same Ubuntu VM over the loopback interface (`127.0.0.1`). The original two-server scripts remain in `../scripts/` and require different hardware and kernel setup.

## What is already measured

The supplied `results/run_1.json` through `run_50.json` are **50 actual iPerf3 measurements**. The old `results/single_flow_results.csv` is retained for compatibility. We did not rerun or edit those observations when preparing the charts. The mean measured receiver goodput is about **55.19 Gbps**; this is an in-memory TCP/loopback result, **not physical NIC bandwidth**. The receiver CPU reading in Run 1 (about 2.58%) is conspicuously low compared with other runs. Keep it in the raw data and note it when interpreting CPU averages.

## Machine used

The captured environment was Ubuntu 20.04-based in VirtualBox, Linux `5.15.0-139-generic`, four guest vCPUs, about 3.8 GiB guest RAM, and iPerf3 3.7. The VM is running on an ASUS VivoBook. The physical host's precise CPU model and VirtualBox scheduling details were not recorded; do not assume them.

## Dependencies

Inside the Ubuntu VM:

```bash
sudo apt update
sudo apt install -y iperf3 sysstat python3 python3-matplotlib python3-numpy
cd ~/Understanding-network-stack-overheads-SIGCOMM-2021/single_flow_experiment
```

If the extracted folder is elsewhere, change `cd` accordingly. No patched kernel or second laptop is needed. Do **not** change VirtualBox's network configuration or a physical NIC to run this benchmark.

## Everyday commands (two terminals)

**Terminal 1 — start the receiver, leave it running:**

```bash
iperf3 -s -B 127.0.0.1
```

If you get `Address already in use`, the earlier server is likely still running. Do not run a second server on port 5201.

**Terminal 2 — run a quick manual test:**

```bash
iperf3 -c 127.0.0.1 -P 1 -t 20
```

**Terminal 2 — verify that CSV and original JSON agree:**

```bash
python3 validate_data.py
```

**Terminal 2 — generate charts from the *existing* 50-run data without new tests:**

```bash
python3 analyze_results.py --input results
```

Results appear in `results/paper_style_charts/`. See the chart map below.

**Terminal 2 — run 5 NEW tests with guest-wide CPU accounting:**

```bash
python3 run_vm.py --runs 5 --duration 20
```

**Terminal 2 — run 50 NEW tests, keeping previous results intact:**

```bash
python3 run_vm.py --runs 50 --duration 20 --pause 2
```

`single_flow.py` is now a compatibility entry point for the safe `run_vm.py` runner; the original script is retained as `single_flow_legacy.py` for reference. **Do not use the legacy script for new runs** because it overwrites `run_1.json` etc.

The new runner creates `results/sessions/YYYYMMDD_HHMMSS/` automatically. It will not overwrite the existing 50-run dataset. It saves each run's JSON, a `session_results.csv`, environment and command metadata, and a guest-CPU efficiency value. After a session completes, plot it with the printed folder path, for example:

```bash
python3 analyze_results.py --input results/sessions/YYYYMMDD_HHMMSS
```

Replace `YYYYMMDD_HHMMSS` with the **actual folder name** reported by the runner. To see folders:

```bash
ls -1 results/sessions/
```

**Optional process CPU monitoring** (run while the client is transmitting):

```bash
pidstat -u -C iperf3 1
```

**Optional system-wide CPU monitoring** (run at the same time as a 20-second test):

```bash
mpstat -P ALL 1 22
```

Note that a `pidstat` average over several minutes of idle time is not the active 20-second average.

## What the new CPU efficiency measurement means

The new runner reads `/proc/stat` before and after each trial. It estimates the fraction of all *guest* CPU time spent active (excluding idle, iowait, and stolen guest CPU time from active work). If the VM has four vCPUs and its guest-wide active fraction is 40%, this corresponds to `4 × 0.40 = 1.6` utilized vCPU equivalents. The script calculates `receiver_goodput_Gbps / utilized_vCPUs`.

This includes **both** sender and receiver plus background guest work, and is **not** the paper's bottleneck-receiver throughput per core. Results in the existing 50-run data do **not** contain guest-wide `/proc/stat` measurements. It would be incorrect to invent them retrospectively.

## Chart map — adapted to the paper's Figure 3

| Local chart | Closest paper panel | What it really measures |
|---|---|---|
| `01_throughput_by_run.png` | Related to 3(a) | Receiver goodput across repeated runs, no optimization sweep |
| `02_throughput_distribution.png` | Additional reliability analysis | Distribution of observed goodput |
| `03_sender_receiver_cpu.png` | Related to 3(b) | iPerf3 *process* CPU per logical CPU, not paper whole-host utilization |
| `04_user_system_cpu.png` | Limited companion to 3(c,d) | User vs. system mode, not the paper's eight kernel-function categories |
| `05_retransmissions.png` | Additional diagnostic | TCP retransmits on loopback, not evidence of physical packet loss |
| `06_interval_throughput.png` | Additional analysis | Within-run goodput for selected real runs |
| `07_vm_cpu_efficiency.png` | Related to 3(a) | **Only generated for NEW sessions** with measured guest-wide CPU usage |

**The graphs for the paper's seven TSO/GRO/jumbo/aRFS configurations, NIC Rx descriptor/cache-miss curve in 3(e), and NAPI-to-copy latency in 3(f) cannot be derived from the present 50 runs.** This work does not fabricate substitute measurements.

## Optional: TCP socket buffer sensitivity (related to Section 3.1 / Figure 3(e))

This is a **separate additional test**, not part of the already completed 50 repetitions. It varies the requested TCP socket buffer using iPerf3 `-w` and records throughput, but it cannot reproduce the paper's NIC descriptor counts, DDIO behavior, or cache miss measurements:

```bash
python3 buffer_sweep_vm.py --sizes 64K 128K 256K --repeats 3 --seconds 20
```

It saves JSON, CSV, and a `buffer_goodput.png` box plot under `results/buffer_sweep/<timestamp>/`. Some buffer sizes can be rejected by Linux; failed runs are reported, not converted to zero measurements. No `sysctl` changes are needed. `-w` requests socket buffers at both endpoints; it does not independently tune only the receiver.

## Optional: kernel profiling, if this VM permits it

Start the iPerf3 server in Terminal 1. In Terminal 2:

```bash
perf --version
perf stat -e task-clock,context-switches,page-faults -- iperf3 -c 127.0.0.1 -P 1 -t 20
```

If `perf` works and permissions allow, collect a client-side software profile:

```bash
mkdir -p results/perf
perf record -e cpu-clock -g -o results/perf/client.data -- iperf3 -c 127.0.0.1 -P 1 -t 20
perf report -i results/perf/client.data --stdio > results/perf/client_report.txt
```

This only profiles the client and kernel work attributable to it. It is **not** a full sender+receiver, eight-category CPU-cycle breakdown. VirtualBox may restrict event profiling or stack traces; do not claim a missing profile was successfully measured. Do not disable protections or install the authors' patched kernel in a college-managed VM merely to enable it.

## Experiment notes / limitations

- Single-flow means **one TCP stream**, not a single CPU core assigned to the whole VM.
- Sender and receiver are processes on the **same kernel**, and their work competes for the same VM resources.
- Loopback bypasses real Ethernet transmission, NIC DMA, RSS/aRFS hardware steering, and NIC queue/descriptor behavior.
- VirtualBox adds a hypervisor scheduling layer; this can affect the numbers.
- iPerf3 CPU fields (`host_*` and `remote_*`) are endpoint process measurements, and their accounting differs from the paper's kernel-wide taxonomy.
- High `system` CPU usage indicates system-mode time, **not** proof that data copying dominates.
- Consecutive repeated measurements may vary with host load, CPU frequency and VM scheduling; observed trends alone do not identify a cause.

For a longer write-up suitable for the project report, see [`REPORT_NOTES.md`](REPORT_NOTES.md).

## Reference / provenance

Q. Cai et al., "Understanding Host Network Stack Overheads," ACM SIGCOMM 2021, Section 3.1 and Figure 3. Original scripts and license are preserved in the parent repository. This directory contains a **student adaptation** for one Ubuntu VM, not a replacement for the research artifact.
