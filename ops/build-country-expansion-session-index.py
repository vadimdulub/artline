#!/usr/bin/env python3
"""Index this session's actual receipts; distinguish research rounds from delivery batches."""
import argparse,collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
C=m.m.core;B=m.x.SESSION_BASE
CAMPAIGNS=[('germany-expansion','DE'),('sweden-expansion','SE'),('czechia-historical','CZ'),('germany-second-pass','DE'),('poland-expansion','PL'),('norway-expansion','NO'),('hungary-expansion','HU'),('britain-expansion','GB'),('switzerland-expansion','CH'),('united-states-expansion','US'),('austria-expansion','AT')]
def main(output,require_complete=False):
 assert not output.exists();targets={t:dict(new_artwork_ids=[],new_artist_ids=[],receipt_paths=[],media_ids=[],touched_artwork_ids=[],touched_artist_ids=[]) for t in ('local','production')};rounds=[];incomplete=[]
 for campaign,code in CAMPAIGNS:
  root=B/campaign/code
  for n in range(1,21):
   run=root/f'round-{n:02}';meta=run/'metadata-summary.json';scope=run/'scope.json';vp=run/'delivery/verification.json'
   if not meta.exists() or not scope.exists():incomplete.append(str(run.relative_to(B)));continue
   md=json.loads(meta.read_text());sp=json.loads(scope.read_text());v=json.loads(vp.read_text()) if vp.exists() else None
   if not v:incomplete.append(str(vp.relative_to(B)))
   rounds.append(dict(campaign=campaign,country=code,round=n,scope_artist_names=[a['name'] for a in sp['artists']],scope_artist_qids=[a['qid'] for a in sp['artists']],discovered_objects=md['discovered_objects'],new_metadata_inspected=md['new_metadata_inspected'],selected_metadata=md['selected_records'],metadata_completed=md['completed'],both_databases_verified=bool(v),verification_path=str(vp.relative_to(B)) if v else None,counts=(v or {}).get('databases',{}),scope_path=str(scope.relative_to(B))))
  scopes=[set(r['scope_artist_qids']) for r in rounds if r['campaign']==campaign];assert sum(map(len,scopes))==len(set().union(*scopes)),'Round scopes must use distinct creator groups'
 for target,dest in targets.items():
  for p in B.glob('*/*/round-*/delivery/**/applied/'+target+'/*.json'):
   r=json.loads(p.read_text());assert r['target']==target
   if r.get('action')=='new':dest['new_artwork_ids'].append(r['artwork_id'])
   if r.get('new_artist'):dest['new_artist_ids'].append(r['artist_id'])
   if r.get('artwork_id'):dest['touched_artwork_ids'].append(r['artwork_id'])
   if r.get('artist_id'):dest['touched_artist_ids'].append(r['artist_id'])
   if r.get('media_id') and ('image_attached' not in r or r['image_attached']):dest['media_ids'].append(r['media_id'])
   dest['receipt_paths'].append(str(p.relative_to(B)))
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");rows=db.execute("SELECT DISTINCT c.entity_type,c.entity_id::text FROM citations c JOIN sources s ON s.id=c.source_id WHERE s.slug LIKE %s AND c.entity_type IN ('artist','artwork')",(m.x.SESSION_NAME+'%',)).fetchall()
   for r in rows:dest['touched_'+r['entity_type']+'_ids'].append(r['entity_id'])
   for kind,table in [('artwork','artworks'),('artist','artists')]:
    dest['touched_'+kind+'_ids'] += [r['id'] for r in db.execute("SELECT DISTINCT e.id::text FROM "+table+" e JOIN citations c ON c.source_record_id=e.slug JOIN sources s ON s.id=c.source_id WHERE c.field_name='duplicate_identity' AND c.entity_type=%s AND s.slug LIKE %s",(kind,m.x.SESSION_NAME+'%'))]
  for key in dest:dest[key]=sorted(set(dest[key]))
 if require_complete:
  assert len(rounds)==20*len(CAMPAIGNS) and not incomplete
  assert all((B/f).exists() for f in ('serial-recovered-german-images-completed.json','serial-selected-fields-completed.json','serial-inventory-aliases-completed.json','serial-identity-round-three-completed.json','serial-austria-completed.json'))
  assert len(targets['local']['new_artwork_ids'])==len(targets['production']['new_artwork_ids']) and len(targets['local']['new_artist_ids'])==len(targets['production']['new_artist_ids']) and set(targets['local']['media_ids'])==set(targets['production']['media_ids'])
 result=dict(at=C.now(),session=m.x.SESSION_NAME,targets=targets,country_rounds=rounds,focused_identity_recovery={'path':'primary-identity-recovery','separate_from_country_rounds':True},incomplete=incomplete,complete_required=require_complete,gross_new_artworks=len(targets['local']['new_artwork_ids']),gross_new_artists=len(targets['local']['new_artist_ids']),scope='Exact application receipts below this session; separate country-round manifests and focused identity recovery. Additional touched records identified by session-specific source citations and duplicate source slugs. Actor identity and unrelated concurrent jobs are never used as membership. Media only from actual attachment receipts; prepared/held files excluded.')
 C.save_new(output,result);print('Receipt index',result['gross_new_artworks'],result['gross_new_artists'],'images',len(targets['local']['media_ids']),'rounds',len(rounds),'verified',sum(r['both_databases_verified'] for r in rounds),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--require-complete',action='store_true');a=p.parse_args();main(a.output,a.require_complete)
