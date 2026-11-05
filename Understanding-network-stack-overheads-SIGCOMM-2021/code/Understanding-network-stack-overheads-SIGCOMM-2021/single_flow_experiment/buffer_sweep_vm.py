#!/usr/bin/env python3
"""Optional buffer-size sensitivity study on VM loopback (not NIC buffer / cache experiment)."""
import argparse
import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sizes',nargs='+',default=['64K','128K','256K'])
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--seconds',type=int,default=20)
    p.add_argument('--server',default='127.0.0.1')
    a=p.parse_args()
    out=Path('results')/'buffer_sweep'/datetime.now().strftime('%Y%m%d_%H%M%S')
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for size in a.sizes:
        for run in range(1,a.repeats+1):
            cmd=['iperf3','-c',a.server,'-P','1','-t',str(a.seconds),'-w',size,'-J']
            cp=subprocess.run(cmd,text=True,capture_output=True)
            if cp.returncode:
                print('FAILED',size,run,cp.stderr.strip() or cp.stdout.strip())
                continue
            try:
                data=json.loads(cp.stdout)
                if 'error' in data:raise ValueError(data['error'])
                gbps=data['end']['sum_received']['bits_per_second']/1e9
            except (KeyError,ValueError) as exc:
                print('Invalid result',size,run,exc);continue
            (out/f'{size}_run_{run}.json').write_text(json.dumps(data,indent=2)+'\n')
            rows.append({'Requested_socket_buffer':size,'Run':run,'Goodput_Gbps':round(gbps,5)})
            print(size,run,round(gbps,3),'Gbps')
            time.sleep(1)
    if not rows:raise SystemExit('No measurements; check iperf3 and OS socket buffer limits')
    with (out/'buffer_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        sizes=list(dict.fromkeys(x['Requested_socket_buffer'] for x in rows))
        data=[[x['Goodput_Gbps'] for x in rows if x['Requested_socket_buffer']==s] for s in sizes]
        plt.figure(figsize=(8,5))
        plt.boxplot(data,labels=sizes)
        plt.ylabel('Goodput (Gbps)');plt.xlabel('Requested socket buffer (-w)')
        plt.title('Socket buffer sensitivity on Linux loopback (not Fig. 3(e) cache data)')
        plt.grid(axis='y',alpha=.25);plt.tight_layout();plt.savefig(out/'buffer_goodput.png',dpi=180);plt.close()
    except ImportError:
        print('matplotlib unavailable; CSV and JSON saved')
    print('Output:',out)

if __name__=='__main__':main()
