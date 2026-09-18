#!/usr/bin/env python3
"""Bounded alternate photographer searches after the primary-file rights audit."""
import argparse,collections,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('austrian-collection-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);core=a.core

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=80);args=p.parse_args();source=args.run/'images-research';run=args.run/'alternate-images';run.mkdir(exist_ok=True);rows=json.loads((source/'candidates.json').read_text())['candidates'];prior=core.latest_events(source);done=core.latest_events(run)
 rows=[c for c in rows if c['provider']=='austria-commons' and prior.get(c['artwork_id'],{}).get('outcome') not in ('prepared','complete') and c['artwork_id'] not in done];rows.sort(key=lambda c:(not c['popular'],c['institution_qid'] not in ('Q303139','Q59435','Q371908','Q505873'),c['artist'],c['title']));fetch=core.Fetcher(run/'metadata')
 for c in rows[:args.limit]:
  try:
   e=json.loads((args.run/'wikimedia/entities'/(c['qid']+'.json')).read_text())['entity'];im=a.research_commons(c,e,fetch,run);a.verify(im);core.save_new(run/'selected'/c['provider']/(c['artwork_id']+'.json'),im);core.worker(c['provider'],[c],SimpleNamespace(run=run,prepare_only=True),None)
  except (AssertionError,ValueError,KeyError) as exc:core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'manual_review','reason':str(exc)})
  except Exception as exc:
   core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'temporary_error','reason':str(exc)[:200]});print(core.now(),'Alternate source paused',type(exc).__name__,flush=True);break
  print(core.now(),'Alternate Austrian photographs',dict(collections.Counter(x['outcome'] for x in core.latest_events(run).values())),flush=True)
if __name__=='__main__':main()
