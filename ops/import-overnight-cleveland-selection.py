#!/usr/bin/env python3
"""Import independently verified Cleveland works into existing review tables."""
import argparse,collections,importlib.util,json,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
museum=module('museum','overnight-cleveland-selected-images.py');guard=module('guard','import-overnight-met-selection.py');core=museum.core
print_review=module('print_review','overnight-distinct-print-review.py')
SOURCE='overnight-cleveland-selected-primary-20260915'
def snapshot(db,records):return print_review.augment(db,records,guard.snapshot(db,records,museum.SLUG,[museum.SCHEME,'cleveland-object']))
def conflicts(records,state):return guard.conflicts(records,state,title_collision_review=print_review.allow)
def candidate(lead):
 o=lead['object'];a=lead['artist'];oid=lead['source_object_id'];aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-cleveland/'+oid));c={'artwork_id':aid,'slug':'night-cleveland-'+oid,'external_id':oid,'scheme':museum.SCHEME,'provider':'night-cleveland','title':lead['title'],**{k:lead[k] for k in ('date_display','creation_year_start','creation_year_end','date_precision','work_type','accession_number')},'artist':a['display_name'],'aliases':a['aliases'],'artist_id':a['id'],'artist_slug':a['slug'],'artist_slugs':[a['slug']],'artist_qid':a['qid'],'artist_authority':lead['source_artist_id'],'roles':['primary'],'popular':a['popular'],'page':o['url'],'qid':None,'target_ids':{'local':aid}}
 url,facts=museum.source_match(c,o);checked=lead['metadata_capture']['retrieved_at'];credit=c['artist']+'; The Cleveland Museum of Art; '+(o.get('creditline') or '')
 if o.get('image_credit'):credit+='; '+o['image_credit']
 keys=('id','accession_number','title','alternate_titles','type','creation_date','creation_date_earliest','creation_date_latest','share_license_status','images','collection','department','url','creditline','image_credit','copyright','rights_and_reproductions','legal_status','record_type','on_loan','accession_date','technique','measurements','dimensions','cover_accession_number')
 raw={k:o[k] for k in keys if k in o};raw['creators']=[{k:v for k,v in m.items() if k not in ('biography',)} for m in o['creators']]
 c.update(source_image_url=url,scope_evidence=facts,policy_url=museum.CC0,rights_status='cc0',license_label='CC0 1.0',checked_at=checked,creator_credit=credit,attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. CC0 1.0 ('+museum.CC0+'). Full-frame proportional resize and JPEG compression.',source_name='The Cleveland Museum of Art',source_record_url=c['page'],image_url=url,image_license='CC0 1.0',image_license_url=museum.CC0,rights_statement='CC0',creator=c['artist'],creation_date=c['date_display'],source_object_id=oid,rights_verified_at=checked,metadata_license=museum.CC0,raw={'object':raw,'metadata_capture':lead['metadata_capture'],'metadata_license':museum.CC0},medium_text=o.get('technique'),dimensions_text=o.get('measurements'))
 if lead.get('physical_object_review'):c['physical_object_review']=lead['physical_object_review']
 return c
def plan(run):
 if (run/'plan.json').exists():return
 rows=[candidate(x) for x in json.loads((run/'source-leads.json').read_text())]
 with museum.ro('postgres://localhost/artline') as db:state=snapshot(db,rows);selected,held=conflicts(rows,state)
 selected=[c for c in selected if not c['already_present']]
 for c in selected:
  for k in ['target_artist_id','already_present']:c.pop(k,None)
  c['institution_ids']={'local':state['institution_id']}
 backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;core.save_new(backup/('local-selection-preimages-'+core.sha(core.encode(state))[:16]+'.json'),state);core.save_new(run/'plan.json',{'at':core.now(),'records':selected,'held':held,'policy':'Exact current Cleveland ownership and native object ID; independently matched existing artist with corroborating life date; source creation, classification and per-image CC0 verified. Review status preserved; no museum display claim.'});core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)});print('Cleveland selected',len(selected),'popular',sum(c['popular'] for c in selected),'types',dict(collections.Counter(c['work_type'] for c in selected)),'held',len(held),flush=True)
def apply(run,target):
 data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];records=data['records'];assert records;dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;out=[]
 with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
  state=snapshot(db,records);selected,held=conflicts(records,state);iid=state['institution_id'];p=backup/(target+'-import-preflight.json')
  if not p.exists():core.save_new(p,{'at':core.now(),'state':state,'held':held})
  if held:raise SystemExit('Target metadata conflicts require review: '+str(len(held)))
  with db.transaction():db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Cleveland Museum of Art: selected independently verified works','museum_api','https://openaccess-api.clevelandart.org/api/artworks/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,museum.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
  for start in range(0,len(selected),25):
   group=selected[start:start+25]
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260915)');active=[c for c in group if not c['already_present']]
    if active:assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=ANY(%s) AND external_id=ANY(%s)) OR canonical_url=ANY(%s))",([museum.SCHEME,'cleveland-object'],[c['external_id'] for c in active],[c['page'] for c in active])).fetchall(),'Source identity appeared during import'
    with db.pipeline():
     for c in group:
      museum.source_match(c,c['raw']['object'])
      if c['already_present']:out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
      aid=c['artwork_id'];page=c['page'];checked=c['checked_at']
      db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(aid,c['slug'],c['title'],guard.norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],c['medium_text'],c['dimensions_text'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
      db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact unqualified source artist name/alias and corroborating museum life year matched to existing painter authority.')",(aid,c['target_artist_id']))
      db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,museum.SCHEME,c['external_id'],page,sid,checked))
      db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,page,'Current museum legal_status accessioned, no long-term loan; accession '+c['accession_number']+'. Holding only, no current display claim.',checked))
      evidence={'primary_record':c['raw']['object'],'metadata_capture':c['raw']['metadata_capture'],'metadata_license':museum.CC0,'creator_identity':{'existing_wikidata':c['artist_qid'],'existing_slug':c['artist_slug'],'source_creator_id':c['artist_authority']},'date_review':'Original source artwork date text and normalized museum interval retained; artist lifespan/default activity dates excluded.'}
      if c.get('physical_object_review'):evidence['physical_object_review']=c['physical_object_review']
      db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],page,json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR));out.append({'artwork_id':aid,'outcome':'inserted'})
   print(core.now(),target,'Cleveland metadata',len(out),'of',len(selected),flush=True)
  verified=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert verified['n']==verified['ok']==len(records);p=run/(target+'-metadata-verified.json')
  if not p.exists():core.save_new(p,{'at':core.now(),'counts':verified,'records':out})
 if target=='local':
  for c in records:core.save_new(run/'selected/night-cleveland'/(c['artwork_id']+'.json'),c)
  core.save_new(run/'candidates.json',{'created_at':data['at'],'candidates':records,'production_metadata_pending':True})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();plan(a.run) if a.phase=='plan' else apply(a.run,a.target)
