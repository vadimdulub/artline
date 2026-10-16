#!/usr/bin/env python3
"""Independent captured-source, audit, production and public verification."""
import importlib.util,json,gzip,requests,sys
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-nationalmuseum-batch-000030.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E

def source():
 plan,pin=h.pinned(b.PHASE);records=[]
 assert 0<len(plan['records'])<=50 and not plan['new_institutions']
 assert plan['authorization']=='User authorized bounded source-backed production inserts; batch 30 Nationalmuseum icon supplement; new artworks stay review.'
 old=h.load(E/b.PHASE/'superseded-plan.json.gz');assert old['records']==plan['records']
 for r in plan['records']:
  oid=r['source_id'];raw=gzip.decompress((E/'source-captures'/('icon-'+oid+'.body.gz')).read_bytes());rc=h.load(E/'source-captures'/('icon-'+oid+'.receipt.json'));assert rc['status']==200 and h.sha(raw)==rc['sha256']
  o=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];assert o==h.load(E/'objects'/(oid+'.json'))
  assert h.sha((b.ROOT/r['evidence_file']).read_bytes())==r['evidence']['sha256'];assert r['evidence']['source_capture_sha256']==rc['sha256']
  assert r['raw']==dict(o,original_title=o['ObjTitleMainTxt_sv'])
  assert (r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['medium'],r['dimensions'])==(o['ObjTitleMainTxt'],o['ObjInventoryNumberTxt'],o['ObjDateMainTxt'],int(o['ObjFromYearTxt']),int(o['ObjToYearTxt']),o['ObjMaterialTechniqueTxt'],o['ObjDimensionGroupTxt'])
  assert r['first']<=r['last']<=1970 and r['creator_label']=='Unknown' and r['creator_link_hold'] and r['artist_id'] is None and r['before'] is None
  assert o['ObjCollectionSearchTxt']['LabelTxt']=='Icons' and o['Id']==oid
  assert r['source_url']==rc['url'] and r['holding_confidence']>=.8
  records.append(dict(artwork_id=r['artwork_id'],source_id=oid,accession=r['accession_number'],source_sha256=rc['sha256'],selected_sha256=r['evidence']['sha256'],native_bounds=[r['first'],r['last']],precision=r['precision'],unknown_creator_preserved=True,alternate_original_title=o['ObjTitleMainTxt_sv']))
 h.save(E/'independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,all_original_fields_verified=True,images_downloaded=0,direct_image_access_hold_preserved=True,no_creator_or_creation_date_inference=True))
 h.save(E/'actual-visual-review.json',dict(at=h.now(),prepared_images=0,actually_viewed_images=[],status='not_applicable_metadata_only',reason='Direct museum image route remains under recorded HTTP 403 hold. Newly documented separate media portal has no exact item/media identity established in this batch. No file or composition review claimed.'))
 print('independent source records verified',len(records))

def production():
 plan,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in plan['records']];locked=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
 with h.connect() as db:
  after=h.snapshot(db,ids);assert len(after)==len(ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256,evidence_note::jsonb->'evidence'->>'sha256' source_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(citations)==len(ids) and all(x['plan_sha256']==pin for x in citations)
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert {x['entity_id'] for x in events}==set(ids) and len(events)==len(ids) and all(x['before_json'] is None for x in events)
  for r in plan['records']:
   state=after[r['artwork_id']];a=state['artwork'];assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None
   assert (a['title'],a['alternate_title'],a['accession_number'],a['date_display'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['dimensions_text'],a['medium_text'],a['unlinked_creator_label'])==(r['title'],r['raw']['original_title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],r['creator_label'])
   assert a['current_institution_id']==r['institution_id'] and not state['creators'] and not state['attachments']
   hs=[x for x in state['holdings'] if x['claim_type']=='holding' and x['review_state']=='accepted' and x['institution_id']==r['institution_id']];assert len(hs)==1 and len(state['holdings'])==1 and not hs[0]['superseded_by']
   ev=json.loads(hs[0]['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
   native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='nationalmuseum-object' AND external_id=%s",(r['source_id'],)).fetchall();assert len(native)==1 and native[0]['entity_id']==r['artwork_id']
   cit=next(x for x in citations if x['entity_id']==r['artwork_id']);assert cit['source_record_id']==r['source_id'] and cit['source_sha256']==r['evidence']['sha256']
   audit=next(x for x in events if x['entity_id']==r['artwork_id']);assert audit['after_json']['slug']==a['slug']
  scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
 h.save(E/'independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),empty_locked_preimages_verified=True,rows=after,citations=citations,creation_scope=scope,new_review_artworks=len(ids),accepted_holdings=len(ids),local_database_connections=0))
 h.save(E/'independent-audit-history-verification.json',dict(at=h.now(),events=events,attribution='Empty locked transaction preimages; newly inserted UUIDs; exact source and programme plan checksums persisted in citations; insertion audit rows. Previous campaigns excluded.'))
 publics=[]
 for aid in ids:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;rr=requests.get(url,timeout=(15,45));rr.raise_for_status();obj=rr.json();assert obj['id']==aid and obj['title']==after[aid]['artwork']['title']
  publics.append(dict(artwork_id=aid,url=url,status=rr.status_code,response_sha256=h.sha(rr.content)))
 h.save(E/'independent-public-verification.json',dict(at=h.now(),rows=publics,unified_catalogue_visibility_verified=True))
 h.save(E/'independent-no-image-changes-verification.json',dict(at=h.now(),production_ids=ids,primary_media_all_null=True,attachments_all_empty=True,image_writes=0,images_viewed=0,access_hold_preserved=True))
 counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
 h.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,production_target=b.base.target(),attribution='Verified source fields, empty locked preimages, exact production rows, checksum-bound programme citations, insertion audit events, accepted holdings and public API responses.'))
 print(json.dumps(counts))
if __name__=='__main__':globals()[sys.argv[1]]()
