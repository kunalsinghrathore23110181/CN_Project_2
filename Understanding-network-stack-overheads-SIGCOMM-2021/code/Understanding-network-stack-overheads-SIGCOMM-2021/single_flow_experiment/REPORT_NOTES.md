# Single-flow experiment: methods, results and limitations

## Motivation and research question

Cai et al. investigate CPU overheads in the Linux network stack at high link speeds. Their Section 3.1 evaluates a single long-lived TCP flow between two servers connected by a 100-Gbps Mellanox NIC link. The original investigation compares TSO/GRO, jumbo frames and accelerated receive flow steering; measures receiver/sender CPU utilization and function-level CPU overhead; and studies receive-buffer and NIC-descriptor effects on cache misses and processing latency. We reproduce the sustained one-flow traffic pattern and basic resource measurements, not all of those hardware-dependent investigations.

## Why we used one computer

The available test environment was an ASUS VivoBook running a college-provided Ubuntu VM in VirtualBox, with four virtual CPUs and roughly 3.8 GiB of allocated RAM. A dedicated pair of Linux servers and a 100-Gbps physical connection were unavailable. Instead of pretending that a lower-speed physical interface matched the researchers' NIC, we ran both TCP endpoints inside Ubuntu and used the Linux loopback address `127.0.0.1`. This removes external network bandwidth as a limit and makes the local TCP processing path the focus, but it is *not* the physical sender/NIC/receiver path from the paper.

## What actually happens on one VM

The iPerf3 client writes data into a TCP socket. The Linux kernel handles the TCP socket and delivers it through the loopback path to the local iPerf3 server's TCP socket. The receiver reads the data and discards it after benchmarking. Both applications use the same guest kernel, share the four virtual CPUs and guest memory, and ultimately share the laptop's physical resources through VirtualBox. There is no physical Ethernet framing on a cable, NIC DMA into last-level cache, hardware receive-side queue assignment, or Intel DDIO operation on this traffic path. VM CPU time is also affected by hypervisor scheduling.

## Test procedure

We started an iPerf3 server with `iperf3 -s -B 127.0.0.1`. A Python driver ran `iperf3 -c 127.0.0.1 -P 1 -t 20 -J` for each repetition, parsed the receiver-reported goodput and endpoint CPU percentages from the JSON, and saved each result. We first tested a small number of runs, then collected 50 repeated 20-second runs under one default TCP configuration, with approximately two seconds between tests. We also performed a separate active-transfer process CPU spot-check using `pidstat`. Raw JSON files and the original CSV are preserved in `results/`.

## Recorded observations (existing 50-run dataset)

- 50 successful iPerf3 invocations, each with one TCP data stream and a 20-second requested duration.
- Mean receiver-reported goodput: **55.1892 Gbps** (about **55.19 Gbps**).
- Minimum recorded goodput: **39.4378 Gbps** (Run 1).
- Maximum recorded goodput: **60.0741 Gbps** (Run 41).
- Sender process CPU was commonly around **98–99% of one logical CPU**.
- Receiver process CPU was generally around **60–66% of one logical CPU**, with an unusually low **2.58% in Run 1**. It is flagged rather than erased or silently excluded.
- Sender system-mode CPU was much larger than sender user-mode CPU. The percentages do not identify specific kernel functions.

These are **loopback goodput** values: they do not demonstrate a 55-Gbps physical NIC. Sequential measurements vary, so a trend across runs cannot be attributed to a particular hardware or scheduling cause from these data alone.

## Comparison with the research paper

| Aspect | SIGCOMM 2021 paper | This adaptation |
|---|---|---|
| Hosts | Two dedicated physical servers | One Ubuntu VM / one ASUS laptop |
| Connection | 100-Gbps physical NIC link | Linux loopback `127.0.0.1` |
| Processor | Multi-socket Intel Xeon with NUMA | Four guest vCPUs; physical topology not controlled |
| Kernel | Patched Linux 5.4.43 | Guest Linux 5.15.0-139-generic |
| Traffic | One long TCP flow | One long TCP flow per run |
| Optimization sweep | Baseline, TSO/GRO, jumbo, aRFS combinations | Default stack only; not swept |
| CPU metrics | Bottleneck-side whole-host core equivalents; kernel function attribution | iPerf3 sender/receiver process CPU and optional guest-wide `/proc/stat` |
| Caches / DDIO / NIC buffers | Hardware measurements and tuning | Not available on loopback |
| Latency instrumentation | NAPI-to-start-of-copy kernel timing | Not available without different path and instrumentation |
| Repetitions | Controlled hardware comparisons | 50 repeated trials of one VM configuration |

The paper reports around 42 Gbps per core in its optimized physical setup. Our 55.19 Gbps is **aggregate single-flow loopback goodput** and should **never** be represented as a higher per-core physical NIC result. Our higher sender process CPU than receiver process CPU does not disprove the paper's receiver-bottleneck finding: accounting methods and network paths differ. We did not verify the paper's data-copy-dominance claim.

## What has and has not been reproduced

Reproduced: a long-lived single TCP data flow, repeated benchmark execution, basic throughput and process CPU measurements, and assessment of run-to-run variation. Added for our own setup: 50-run reliability plots, distributions, interval throughput and retransmit diagnostics. Available for future fresh runs: guest-wide CPU efficiency based on `/proc/stat` and optional `perf` software profiling if VirtualBox permits it. Separately available: a socket-buffer throughput sweep; that alone is **not** a reproduction of Figure 3(e) hardware cache results.

Not reproduced: physical 100-Gbps NIC throughput; TSO hardware, hardware GRO/receive offload or aRFS, jumbo-frame performance on a NIC; DDIO/cache-DMA interactions; NIC Rx ring descriptor adjustments; NUMA-local/remote NIC placement; a complete kernel-level CPU-cycle taxonomy; and the original NAPI-to-copy timing results. These require different hardware, a controlled Linux kernel/networking environment, or both.

## Interpreting the charts in a presentation

- **01: Throughput across 50 runs** — repeatability and variability, not an optimization comparison.
- **02: Throughput distribution** — central tendency and spread from actual results.
- **03: Sender and receiver process CPU** — closest to the question in Figure 3(b), but different accounting.
- **04: User versus system mode** — a limited substitute for the high-level CPU breakdown question in 3(c,d); cannot separate data copying from TCP/IP or `skb` costs.
- **05: TCP retransmissions** — diagnostic on loopback, not evidence of physical link loss.
- **06: Interval goodput** — throughput fluctuations within selected actual runs.
- **07: Guest-wide throughput per utilized vCPU** — available only after performing new runs with the revised driver; do not backfill from process percentages.

## Questions likely to come up

**Why did you use loopback instead of a real NIC?** Because a single VM cannot implement the paper's 100-Gbps two-server NIC experiment. Loopback lets us measure a real TCP flow without external network bottlenecks, but tests a different packet path.

**Does single flow mean one CPU core?** No. It means one transport connection. The VM has four vCPUs and may schedule the sender, receiver, and kernel work on several of them.

**Why is our throughput above the paper's approximately 42 Gbps/core?** The numbers use different denominators and hardware paths. Ours is aggregate loopback goodput; the paper reports receiver-bottleneck per-core efficiency over a physical link. They are not directly comparable.

**Can we say the sender is the bottleneck?** Not solely from iPerf3 per-process CPU percentages. Both endpoints share CPU resources and kernel work can be accounted differently. A controlled profile would be needed.

**What conclusions can we defend?** A single TCP flow through this guest Linux loopback path achieved an average of about 55.19 Gbps across 50 trials, while causing high endpoint system-mode CPU usage and measurable run-to-run variation. The findings characterize the tested VM, not NIC-specific mechanisms.
