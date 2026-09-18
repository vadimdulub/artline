#!/usr/bin/env python3
"""Resume nonpopular selected museum image work after popular attempts finish."""
import argparse,json,time,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();source=a.run/'smk-linked-followup';popular={c['artwork_id'] for c in json.loads((source/'candidates.json').read_text())['candidates'] if c.get('popular')};last=None
while time.time()<a.deadline:
 events={}
 for line in (source/'events.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('artwork_id'):events[x['artwork_id']]=x
 pending={aid for aid in popular if events.get(aid,{}).get('outcome') not in ('prepared','complete','failed','source_rate_limited','manual_review')}
 if len(pending)!=last:print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'Popular Danish image attempts remaining',len(pending),flush=True);last=len(pending)
 if not pending:break
 time.sleep(20)
if time.time()<a.deadline:
 children=[]
 for name,limit in [('smk-new',1643),('smk-native',3925),('smk-new-artist-works',2301)]:
  folder=a.run/name;log=(folder/'image-preparation.log').open('a');proc=subprocess.Popen([sys.executable,'ops/overnight-smk-selected-images.py','--run',str(folder),'--limit',str(limit),'--deadline',str(a.deadline)],stdout=log,stderr=subprocess.STDOUT);children.append((name,proc));print('Resumed',name,'PID',proc.pid,flush=True)
 for name,proc in children:print('Image preparation exited',name,proc.wait(),flush=True)
