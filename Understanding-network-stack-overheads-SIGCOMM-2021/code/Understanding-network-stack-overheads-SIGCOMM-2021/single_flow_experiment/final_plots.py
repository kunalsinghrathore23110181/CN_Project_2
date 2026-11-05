
import csv
import statistics
import matplotlib.pyplot as plt

with open("results/single_flow_results.csv") as f:
    rows = list(csv.DictReader(f))

runs = [int(r["Run"]) for r in rows]
throughput = [float(r["Throughput_Gbps"]) for r in rows]
sender = [float(r["Sender_CPU_percent"]) for r in rows]
receiver = [float(r["Receiver_CPU_percent"]) for r in rows]

avg = statistics.mean(throughput)

# Figure 1: TCP throughput
plt.figure(figsize=(11, 5))
plt.plot(runs, throughput, marker="o", markersize=3)
plt.axhline(avg, linestyle="--",
            label=f"Mean = {avg:.2f} Gbps")
plt.xlabel("Experiment Run")
plt.ylabel("Throughput (Gbps)")
plt.title("Single Flow: Throughput Across 50 Runs")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("results/throughput_50_runs.png", dpi=200)
plt.close()

# Figure 2: CPU utilization
plt.figure(figsize=(11, 5))
plt.plot(runs, sender, label="Sender CPU")
plt.plot(runs, receiver, label="Receiver CPU")
plt.xlabel("Experiment Run")
plt.ylabel("CPU Utilization (%)")
plt.title("Single Flow: Process CPU Utilization")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("results/cpu_50_runs.png", dpi=200)
plt.close()

print("Total runs:", len(rows))
print("Mean:", round(avg, 4), "Gbps")
print("Median:", round(statistics.median(throughput), 4))
print("Standard deviation:",
      round(statistics.stdev(throughput), 4))
print("Both graphs saved successfully.")
