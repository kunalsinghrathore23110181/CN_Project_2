
import subprocess
import json
import csv
import statistics
import time
from pathlib import Path

# Single-flow reproduction in Ubuntu VirtualBox
SERVER = "127.0.0.1"
DURATION = 20
REPETITIONS = 50

output = Path("results")
output.mkdir(exist_ok=True)

rows = []

for run in range(1, REPETITIONS + 1):
    print(f"\nStarting single-flow test {run}/{REPETITIONS}")

    command = [
        "iperf3",
        "-c", SERVER,
        "-P", "1",
        "-t", str(DURATION),
        "-J"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Experiment failed:", result.stderr)
        continue

    data = json.loads(result.stdout)

    if "error" in data:
        print("iPerf3 error:", data["error"])
        continue

    with open(output / f"run_{run}.json", "w") as f:
        json.dump(data, f, indent=2)

    summary = data["end"]

    throughput = (
        summary["sum_received"]["bits_per_second"] / 1e9
    )

    cpu = summary.get("cpu_utilization_percent", {})
    sender_cpu = cpu.get("host_total")
    receiver_cpu = cpu.get("remote_total")

    rows.append({
        "Run": run,
        "Throughput_Gbps": round(throughput, 4),
        "Sender_CPU_percent": sender_cpu,
        "Receiver_CPU_percent": receiver_cpu
    })

    print(f"Throughput: {throughput:.4f} Gbps")
    print(f"Sender CPU: {sender_cpu}%")
    print(f"Receiver CPU: {receiver_cpu}%")

    time.sleep(2)

if rows:
    with open(output / "single_flow_results.csv",
              "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    values = [r["Throughput_Gbps"] for r in rows]
    print("\nEXPERIMENT COMPLETE")
    print("Average throughput:",
          round(statistics.mean(values), 4), "Gbps")
    print("Results saved in results/")
else:
    print("No successful tests were completed.")
