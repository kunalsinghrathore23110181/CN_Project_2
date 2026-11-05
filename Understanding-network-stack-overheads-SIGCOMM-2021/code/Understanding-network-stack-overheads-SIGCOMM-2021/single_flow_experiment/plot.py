
import csv
import matplotlib.pyplot as plt

runs = []
throughputs = []

with open("results/single_flow_results.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        runs.append(int(row["Run"]))
        throughputs.append(float(row["Throughput_Gbps"]))

plt.figure(figsize=(8, 5))
plt.bar([str(r) for r in runs], throughputs)

plt.xlabel("Experiment Run")
plt.ylabel("Throughput (Gbps)")
plt.title("Single TCP Flow - Ubuntu VirtualBox")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig("results/single_flow_throughput.png", dpi=200)
plt.show()
