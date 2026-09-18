#!/usr/bin/env python3
"""Continue bounded receipt-backed source batches until the campaign deadline."""
import argparse,collections,datetime,json,subprocess,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True)
    p.add_argument('--limit',type=int,default=250);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    terminal={'complete','no_explicit_open_image','metadata_needs_review','source_missing','failed'}|({'prepared'} if a.prepare_only else set())
    records=json.loads((a.run/'candidates.json').read_text())['candidates']
    round_number=0;stalled=0
    while time.time()<a.deadline:
        latest={}
        if (a.run/'events.jsonl').exists():
            for line in (a.run/'events.jsonl').read_text().splitlines():
                try:r=json.loads(line)
                except ValueError:continue
                if r.get('artwork_id'):latest[r['artwork_id']]=r
        pending=[r for r in records if r['artwork_id'] not in latest or latest[r['artwork_id']]['outcome'] not in
          terminal]
        if not pending:print('All direct-source candidates examined',flush=True);break
        before=sum(r['outcome'] in terminal for r in latest.values());round_number+=1
        print(datetime.datetime.now(datetime.timezone.utc).isoformat(),'Round',round_number,'pending',len(pending),dict(collections.Counter(r['provider'] for r in pending)),flush=True)
        command=[sys.executable,str(Path(__file__).with_name('overnight-image-campaign.py')),'run','--run',str(a.run),'--limit',str(a.limit),'--deadline',str(a.deadline)]
        if a.prepare_only:command.append('--prepare-only')
        result=subprocess.run(command,check=False)
        if result.returncode:print('Batch exited',result.returncode,flush=True);stalled+=1
        progress=json.loads((a.run/'direct-progress.json').read_text())
        if sum(n for k,n in progress['outcomes'].items() if k in terminal)<=before:stalled+=1
        else:stalled=0
        if stalled>=3:print('Repeated stalled batches; supervisor stops for inspection',flush=True);break
        time.sleep(2)
    print('Supervisor checkpoint',datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)

if __name__=='__main__':main()
