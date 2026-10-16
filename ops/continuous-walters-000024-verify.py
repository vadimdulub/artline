#!/usr/bin/env python3
"""Independent source and post-transaction verification for bounded Walters metadata."""
import importlib.util,json,gzip,csv,io,requests,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-walters-batch-000024.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E

original_save=h.save
def saved_receipt(path,value):
 if path.exists():
  def stable(v):
   if isinstance(v,dict):return {k:stable(x) for k,x in v.items() if k!='at'}
   if isinstance(v,list):return [stable(x) for x in v]
   return v
  assert stable(h.safe(value))==stable(h.load(path)),str(path)
  return h.load(path)
 return original_save(path,value)
h.save=saved_receipt

def source():
 checks=[];data={}
 for name in ['README.md','art.csv','creators.csv','media.csv','relationships.csv']:
  raw=gzip.decompress((E/'source-captures'/(name+'.body.gz')).read_bytes());rc=h.load(E/'source-captures'/(name+'.receipt.json'));assert rc['status']==200 and h.sha(raw)==rc['sha256'];data[name]=raw;checks.append(dict(file=name,sha256=rc['sha256'],bytes=len(raw),verified=True))
 allart={x['ObjectID']:x for x in csv.DictReader(io.StringIO(data['art.csv'].decode('utf-8-sig')))};creators={x['id']:x for x in csv.DictReader(io.StringIO(data['creators.csv'].decode()))}
 plan,pin=h.pinned(b.PHASE);records=[]
 assert 0<len(plan['records'])<=25 and not plan['new_institutions']
 for r in plan['records']:
  assert not r['before'] and r['first']<=r['last']<=1970
  x=allart[r['source_id']];src=h.load(Path(r['evidence_file']));assert src['object']==x and r['raw']==x
  assert h.sha(Path(r['evidence_file']).read_bytes())==r['evidence']['sha256']
  assert src['creators']==[creators[k] for k in x['Creators'].split('|') if k in creators]
  assert (r['title'],r['accession_number'],r['date_display'],r['first'],r['last'])==(x['Title'],x['AccessionNumber'],x['DateText'],int(x['DateBeginYear']),int(x['DateEndYear']))
  assert r['creator_link_hold'] and r['artist_id'] is None and not x['RelatedObjects'] and 'Walters Art Museum' in x['CreditLine']
  records.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],accession=r['accession_number'],selected_source_sha256=r['evidence']['sha256'],dates=[r['first'],r['last']],original_creator_labels_preserved=True,documented_collection_provenance=x['Provenance']))
 h.save(E/'independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,source_files=checks,records=records,images_downloaded=0,main_and_image_http_403_holds_preserved=True))
 print('independent source records verified',len(records))

def production():
 plan,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in plan['records']];locked=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
 with h.connect() as db:
  after=h.snapshot(db,ids);assert len(after)==len(ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(citations)==len(ids) and all(x['plan_sha256']==pin for x in citations)
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert {x['entity_id'] for x in events}==set(ids)
  for r in plan['records']:
   state=after[r['artwork_id']];a=state['artwork'];assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None
   assert (a['title'],a['accession_number'],a['date_display'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['dimensions_text'],a['medium_text'],a['unlinked_creator_label'])==(r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],r['creator_label'])
   assert a['current_institution_id']==r['institution_id'] and not state['creators'] and not state['attachments']
   holdings=[x for x in state['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and x['institution_id']==r['institution_id']];assert len(holdings)==1 and not any(x['claim_type']=='on_view' for x in state['holdings'])
   ev=json.loads(holdings[0]['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
   native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='walters-object' AND external_id=%s",(r['source_id'],)).fetchall();assert len(native)==1 and native[0]['entity_id']==r['artwork_id']
  scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
 h.save(E/'independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),empty_locked_preimages_verified=True,rows=after,citations=citations,creation_scope=scope,new_review_artworks=len(ids),accepted_holdings=len(ids),local_database_connections=0))
 h.save(E/'independent-audit-history-verification.json',dict(at=h.now(),events=events,attribution='Empty locked transaction preimages plus unique new IDs and programme checksum-bound citations; previous campaigns excluded.'))
 publics=[]
 for aid in ids:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;rr=requests.get(url,timeout=(15,45));rr.raise_for_status();obj=rr.json();assert obj['id']==aid and obj['title']==after[aid]['artwork']['title']
  publics.append(dict(artwork_id=aid,url=url,status=rr.status_code,response_sha256=h.sha(rr.content)))
 h.save(E/'independent-public-verification.json',dict(at=h.now(),rows=publics,unified_catalogue_visibility_verified=True))
 counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
 h.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,production_target=b.base.target(),attribution='Independent source, locked empty preimages, exact current rows, new programme citations, insertion audit events, holdings and public detail responses.'))
 print(json.dumps(counts))
if __name__=='__main__':globals()[sys.argv[1]]()
