#!/usr/bin/env python3
"""Derive ownership from application receipts, including later archived rows."""
import argparse,collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE
CAMPAIGNS=[('',c) for c in ('NL','GR','RU')]+[(n,c) for n,c in [('greek-historical','GR'),('france','FR'),('italy','IT'),('spain','ES'),('germany','DE'),('austria','AT'),('belgium','BE'),('finland','FI'),('portugal','PT')]]
def main(final=False,output=None):
 output=Path(output) if output else BASE/('session-application-index-final.json' if final else 'session-application-index.json')
 if output.exists():return
 targets={t:dict(new_artwork_ids=[],new_artist_ids=[],receipt_paths=[]) for t in ('local','production')};rounds=[]
 for campaign,code in CAMPAIGNS:
  root=BASE/campaign/code
  for n in range(1,21):
   folder=root/f'round-{n:02d}';scope=json.loads((folder/'scope.json').read_text());meta=json.loads((folder/'metadata-summary.json').read_text());delivery=folder/'delivery';vp=delivery/'verification.json';verification=json.loads(vp.read_text()) if vp.exists() else None
   selected=sum(len(json.loads(p.read_text())['selected']) for p in (folder/'selected').glob('*.json'))
   row=dict(campaign=campaign or 'initial',country=code,round=n,scope_artist_names=[a['name'] for a in scope['artists']],scope_artist_qids=[a['qid'] for a in scope['artists']],discovered_objects=meta.get('discovered_objects'),selected_metadata=selected,metadata_completed=meta.get('completed',False),both_databases_verified=bool(verification),verification_path=str(vp.relative_to(BASE)) if verification else None,counts=(verification or {}).get('databases',{}),scope_path=str((folder/'scope.json').relative_to(BASE)))
   rounds.append(row)
   for target in targets:
    for p in (delivery/'applied'/target).glob('*.json'):
     rec=json.loads(p.read_text());assert rec['target']==target
     if rec['action']=='new':targets[target]['new_artwork_ids'].append(rec['artwork_id'])
     if rec.get('new_artist'):targets[target]['new_artist_ids'].append(rec['artist_id'])
     targets[target]['receipt_paths'].append(str(p.relative_to(BASE)))
 for target in targets:
  for p in (BASE/'greek-primary-catalogues/applied'/target).glob('*.json'):
   rec=json.loads(p.read_text())
   if rec['action']=='new':targets[target]['new_artwork_ids'].append(rec['artwork_id'])
   targets[target]['receipt_paths'].append(str(p.relative_to(BASE)))
  p=BASE/'greek-historical/tzanes-met-primary'/(target+'-verified.json');assert p.exists();targets[target]['receipt_paths'].append(str(p.relative_to(BASE)))
  with m.m.r.base.connect(False) as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   # Tzanes creation uses deterministic identical UUIDs; confirm exact local
   # source membership and retain both completed target verification receipts.
   targets[target]['new_artwork_ids'] += [r['id'] for r in db.execute("SELECT w.id::text FROM artworks w WHERE EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=w.id AND s.slug='overnight-tzanes-met-primary-20260913') AND w.created_at>='2026-09-13T18:59:34Z'")]
   targets[target]['new_artist_ids'] += [r['id'] for r in db.execute("SELECT id::text FROM artists WHERE slug='wikimedia-painter-q9027667'")]
  triptych=BASE/'belgium/primary-triptych'/(target+'-metadata-verified.json')
  if triptych.exists():
   targets[target]['new_artwork_ids'].append(str(m.m.uid('artwork/Q21619670')));targets[target]['receipt_paths'].append(str(triptych.relative_to(BASE)))
  for k in ('new_artwork_ids','new_artist_ids'):targets[target][k]=sorted(set(targets[target][k]))
 result=dict(at=CORE.now(),targets=targets,country_rounds=rounds,scope='Own application receipts only; excludes concurrent Armenian/Georgian imports. Gross new rows include records later consolidated. Country round verification predates later primary corrections; final DB audit is separate.',gross_new_artworks=len(targets['local']['new_artwork_ids']),gross_new_artists=len(targets['local']['new_artist_ids']))
 CORE.save_new(output,result);print('Own receipt membership',result['gross_new_artworks'],result['gross_new_artists'],'country scopes',len(rounds),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();main(a.final,a.output)
