#!/usr/bin/env python3
"""Attach visually reviewed primary Finnish images after metadata reconciliation."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;a.RUN=m.x.BASE/'finland/primary-followup/images'
def plan(target=None):
 if (a.RUN/a.PLAN_NAME).exists():return
 selected_targets=(target,) if target else ('local','production')
 for t in selected_targets:assert (a.RUN.parent/(t+'-verified.json')).exists()
 prep=json.loads((a.RUN/'preparation.json').read_text());qa=json.loads((a.RUN/'quality-review.json').read_text());assert qa['approved'] and qa['contact_sheet_sha256']==prep['contact_sheet_sha256']==CORE.sha((a.RUN/'contact-sheet.jpg').read_bytes())
 images=[];targets={t:[] for t in selected_targets};holds=[]
 for name,sha in prep['prepared_hashes'].items():
  raw=(a.RUN/'prepared'/name).read_bytes();assert CORE.sha(raw)==sha;im=json.loads(raw);q=im['key']
  if q in qa.get('held_images',{}):continue
  e=im['identity']['primary'];round=e['round'];paths={t:m.x.BASE/'finland/FI'/f'round-{round:02d}'/'delivery/applied'/t/(q+'.json') for t in targets}
  if not all(p.exists() for p in paths.values()):holds.append(dict(qid=q,reason='original_country_import_identity_guard_held'));continue
  for target,path in paths.items():
   aid=json.loads(path.read_text())['artwork_id']
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(aid,)).fetchone()['row'];assert w['status']=='review' and w['published_at'] is None and not w['primary_media_id'] and w['creation_year_end']<=1970
    assert m.m.accession_key(w['accession_number'])==m.m.accession_key(e['evidence']['primary_object']['inventoryNumber']);targets[target].append(dict(key=q,work=w))
  images.append(im)
 for t,rows in targets.items():CORE.save_new(m.BACKUPS/('fng-primary-images-'+t+'-preimages.json'),rows)
 CORE.save_new(a.RUN/a.PLAN_NAME,dict(at=CORE.now(),images=images,targets=targets,qa=qa,holds=holds));CORE.save_new(a.RUN/a.MANIFEST_NAME,dict(plan_sha256=CORE.sha((a.RUN/a.PLAN_NAME).read_bytes()),images=len(images),targets=list(targets)));print('Primary FNG image plan',len(images),'held',len(holds),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.target:a.PLAN_NAME='application-plan-'+args.target+'.json';a.MANIFEST_NAME='application-manifest-'+args.target+'.json'
 plan(args.target) if args.command=='plan' else getattr(a,args.command)()
