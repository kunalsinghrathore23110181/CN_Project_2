#!/usr/bin/env python3
"""Verify that each row in the historical CSV matches its saved JSON."""
import csv
import json
from pathlib import Path

root=Path('results')
rows=list(csv.DictReader((root/'single_flow_results.csv').open(newline='')))
issues=[]
for row in rows:
    n=int(row['Run'])
    path=root/f'run_{n}.json'
    if not path.exists():
        issues.append(f'Missing {path}')
        continue
    data=json.loads(path.read_text())
    bps=data['end']['sum_received']['bits_per_second']/1e9
    if abs(bps-float(row['Throughput_Gbps']))>0.00006:
        issues.append(f'Run {n}: CSV throughput differs from JSON')
    cpu=data['end']['cpu_utilization_percent']
    for key,col in [('host_total','Sender_CPU_percent'),('remote_total','Receiver_CPU_percent')]:
        if abs(cpu[key]-float(row[col]))>0.001:
            issues.append(f'Run {n}: {col} differs from JSON')
print('CSV rows:',len(rows))
print('Available run JSON files:',len(list(root.glob('run_*.json'))))
print('Mismatches:',len(issues))
for issue in issues:print(issue)
if issues:raise SystemExit(1)
