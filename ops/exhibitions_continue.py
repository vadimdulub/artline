#!/usr/bin/env python3
"""Resume reviewed Artsy batch delivery; never declare the audited goal complete."""
import argparse
import json
import os
import subprocess
import sys
import time
import exhibitions_common as c

p=argparse.ArgumentParser();p.add_argument('--wait-pid',type=int);p.add_argument('--target-buffer',type=int,default=105000);args=p.parse_args()
if args.wait_pid:
    while True:
        try:os.kill(args.wait_pid,0)
        except ProcessLookupError:break
        time.sleep(15)
for pass_no in range(1,30):
    for action in ['plan','apply']:
        subprocess.run([sys.executable,str(c.ROOT/'ops/exhibitions_deliver.py'),action,'--provider','artsy'],check=True)
    with c.connect() as db:
        counts=db.execute("SELECT event_state,count(*) n FROM exhibitions WHERE status<>'archived' GROUP BY 1").fetchall()
    checkpoint=dict(at=c.now(),pass_number=pass_no,counts=counts,requires_final_identity_audit=True)
    c.save(c.RUN/'continuation'/f'{pass_no:03d}.json',checkpoint);print(json.dumps(checkpoint),flush=True)
    if next((r['n'] for r in counts if r['event_state']=='held'),0)>=args.target_buffer:break
    time.sleep(30)
