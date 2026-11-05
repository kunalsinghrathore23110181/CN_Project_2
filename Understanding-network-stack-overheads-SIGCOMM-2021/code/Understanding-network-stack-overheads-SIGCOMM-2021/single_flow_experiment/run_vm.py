#!/usr/bin/env python3
"""Run a new loopback single-flow session with non-overwriting outputs."""
import argparse
import csv
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


def cpu_times():
    with open('/proc/stat') as f:
        parts = list(map(int, f.readline().split()[1:]))
    # Exclude guest/guest_nice: already included in user/nice.
    total = sum(parts[:9])
    idle = parts[3] + parts[4]
    steal = parts[8]
    return total, idle, steal


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=int,default=5)
    p.add_argument('--duration',type=int,default=20)
    p.add_argument('--pause',type=float,default=2.0)
    p.add_argument('--server',default='127.0.0.1')
    p.add_argument('--port',type=int,default=5201)
    p.add_argument('--output',type=Path,default=None)
    a=p.parse_args()
    if a.runs<1 or a.duration<1 or a.pause<0:
        p.error('runs/duration must be positive, pause nonnegative')
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    output=a.output or Path('results')/'sessions'/stamp
    output.mkdir(parents=True,exist_ok=False)
    core_count=os.cpu_count() or 1
    results=[]
    for run in range(1,a.runs+1):
        command=['iperf3','-c',a.server,'-p',str(a.port),'-P','1','-t',str(a.duration),'-J']
        print(f'Run {run}/{a.runs} — {a.duration}s')
        start_total,start_idle,start_steal=cpu_times()
        cp=subprocess.run(command,text=True,capture_output=True)
        end_total,end_idle,end_steal=cpu_times()
        if cp.returncode:
            print('FAILED:',cp.stderr.strip() or cp.stdout.strip());continue
        try:
            data=json.loads(cp.stdout)
            if 'error' in data:
                raise ValueError(data['error'])
            bps=data['end']['sum_received']['bits_per_second']
        except (ValueError,KeyError,TypeError) as e:
            print('Invalid JSON:',e);continue
        (output/f'run_{run}.json').write_text(json.dumps(data,indent=2)+'\n')
        delta=end_total-start_total
        busy=delta-(end_idle-start_idle)-(end_steal-start_steal)
        fraction=max(0,min(1,busy/delta)) if delta>0 else 0
        utilized=core_count*fraction
        cpu=data['end'].get('cpu_utilization_percent',{})
        row={
            'Run':run,'Throughput_Gbps':round(bps/1e9,5),
            'Sender_CPU_percent':cpu.get('host_total'),
            'Receiver_CPU_percent':cpu.get('remote_total'),
            'VM_CPU_percent':round(100*fraction,4),
            'Utilized_vCPUs':round(utilized,4),
            'Gbps_per_utilized_vCPU':round(bps/1e9/utilized,4) if utilized else '',
            'Steal_fraction_percent':round(100*(end_steal-start_steal)/delta,4) if delta>0 else ''
        }
        results.append(row)
        print(f"  {row['Throughput_Gbps']} Gbps; utilized guest vCPUs: {row['Utilized_vCPUs']}; "
              f"efficiency: {row['Gbps_per_utilized_vCPU']} Gbps/vCPU")
        if run<a.runs:time.sleep(a.pause)
    if results:
        with (output/'session_results.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=results[0].keys())
            writer.writeheader();writer.writerows(results)
    (output/'session_metadata.json').write_text(json.dumps({
        'mode':'same-VM loopback; single TCP stream; one client and one server',
        'duration_seconds':a.duration,'requested_runs':a.runs,
        'completed_runs':len(results),'pause_seconds':a.pause,'server':a.server,
        'guest_vcpus':core_count,'measurement_note':'/proc/stat guest-wide activity including background work; no subtraction of baseline, not equivalent to paper per-core NIC measurement',
        'command':' '.join(command)
    },indent=2)+'\n')
    print(f'Completed {len(results)} of {a.runs} runs. Output: {output}')
    if len(results)!=a.runs:
        raise SystemExit(1)

if __name__=='__main__':main()
