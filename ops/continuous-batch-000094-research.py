#!/usr/bin/env python3
"""Bounded batch 94 preflight, reserve reconciliation and QAGOMA research."""
import importlib.util,json,csv,gzip,fcntl,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b94','ops/continuous-qagoma-images-000094.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
def run():
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  q=h.load(b.E.parents[1]/'source-queue.json');b.save('source-queue-before.json',q)
  paths=[b.ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),b.ROOT/'docs/ARTLINE_IMAGE_USE.md',b.ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',b.ROOT/'docs/LOCAL_DATA_LOCATIONS.md',b.E.parents[1]/'CHECKPOINT.json',b.E.parents[1]/'source-queue.json',b.E.parent/'000093/CHECKPOINT.json',b.E.parent/'000092/source-access-holds.json',b.ROOT/'ops/india-300-delivery-20261011.py']
  registry=list(csv.DictReader(paths[1].open()));assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in q['sources']}
  b.save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths],registry=registry,precedence='Current user and source-specific approvals. One bounded batch; real local catalogue read-only; external supervisor unchanged.'))
  b.save('production-target-reconciliation.json',b.target())
  previous=h.load(b.E.parent/'000093/independent-production-verification.json');receipt=h.load(b.E.parent/'000093/batch-verification-receipt.json')
  print('PRIOR_KEYS',list(previous),list(receipt),flush=True)
  with h.connect() as db:
   ids=receipt['production_ids'];live=h.snapshot(db,ids)
   assert live==previous['after']
   notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name='continuous_greek_object_evidence_b000093' AND entity_id=ANY(%s::uuid[])",(ids,))]
   assert len(notes)==len(ids) and all(x['pin']==receipt['metadata_plan_sha256'] for x in notes)
   own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(b.i.OP,))];assert not own
  b.save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=93,ids=ids,exact_snapshot_equal=True,persisted_plan_checksums_verified=True,current_batch_existing_writes=own,new_increments=0))
  reserve=b.mod('reserve94','continuous-reserve-warsaw-000052-research.py');reserve.E=b.E;reserve.reserve()
  pp=b.ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
  with h.connect() as db:
   live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
   assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
   for r in p['rows']:
    a=live[r['artwork_id']]['artwork'];im=p['images'][r['artwork_id']];assert a['accession_number']==r['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived';assert all(a[k]==v for k,v in r['date'].items())
  b.save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,physical_date_holds_preserved=['80082','80437','81054']))
  inherited=b.E.parent/'000092/source-access-holds.json';b.save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(inherited),inherited_sha256=h.sha(inherited.read_bytes()),native_qagoma_http403_preserved=True,native_qagoma_requests=0,wikiart_store_http403_preserved=True,wikiart_store_requests=0))
  old=h.load(b.E.parent/'000091/gap-input.json.gz');pending=next(x for x in q['sources'] if x['source_id']=='qagoma')['resume_cursor']['pending_artwork_ids'];rows=[x for x in old['rows'] if x['id'] in pending]
  with h.connect() as db:before=h.snapshot(db,pending)
  assert len(before)==9 and all(before[x]['artwork']['primary_media_id'] is None for x in pending)
  b.save('qagoma-before.json.gz',before)
  source=[]
  for row in rows:
   c=next(x for x in old['citations'] if x['entity_id']==row['id']);n=json.loads(c['evidence_note']);rc=n['source_receipt'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
   source.append(dict(artwork_id=row['id'],facts=n['raw_source_record']['facts'],receipt=rc,source_verified_now=True))
  b.save('qagoma-source-verification.json',dict(at=h.now(),records=source,native_requests=0,capture_reuse=True))
  slugs={'ALDER, Anthony':'anthony-alder','RIVERS, R. Godfrey':'richard-godfrey-rivers','FAIRWEATHER, Ian':'ian-fairweather','ELDERSHAW, John':'john-eldershaw','STARR, Louisa':'louisa-starr','FRISTRÖM, Oscar':'oscar-fristrom','WISHART, George':'george-wishart','DODS, Robin':'robin-dods'}
  captures={};outcomes=[]
  for row in rows:
   slug=slugs[row['unlinked_creator_label']];url='https://www.wikiart.org/en/'+slug+'/all-works/text-list'
   if url not in captures:
    try:
     raw,rc=b.capture(url);sp=BeautifulSoup(raw,'html.parser');links=[dict(title=a.get_text(' ',strip=True),url=a.get('href')) for a in sp.select('.painting-list-text-row a')];captures[url]=dict(receipt=rc,works=links)
    except AssertionError:
     rc=h.load(b.E/'source-captures'/(h.sha(url.encode())+'.json'));captures[url]=dict(receipt=rc,works=[])
    print(slug,captures[url]['receipt']['status'],len(captures[url]['works']),flush=True)
   outcomes.append(dict(**row,discovery=captures[url],selected=False,reason='Profile discovery pending editorial evaluation' if captures[url]['receipt']['status']==200 else 'Candidate profile route returned HTTP '+str(captures[url]['receipt']['status'])+'; exact source work not located. No unchanged retries. This does not prove no image exists.'))
  b.save('qagoma-discovery.json',dict(at=h.now(),rows=outcomes,selected=0,images_downloaded=0,discovery_slugs_are_hypotheses=True))
if __name__=='__main__':run()
