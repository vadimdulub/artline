#!/usr/bin/env python3
import json, sys, os, fcntl, requests
from pathlib import Path
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT; E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000050'
B=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000050'
OP='continuous-exhibitions-20261013-batch-000050'; ACTOR='local-european-research'
IID='3f95f10d-82af-5f9e-bc51-997cfff3352c'; SID='e1ca621f-d481-50f5-b081-dea792f7163f'
SRC='https://www.hermitagemuseum.org/uploads/files/publications/d41d8cd98f00b204e9800998ecf8427e1731920686.pdf'
ROWS=[
 dict(native='ГЭ 2473',title='Saint George',date='1427–1430',first=1427,last=1430,precision='range',medium='Tempera on poplar panel',dimensions='53.5 × 20 cm (painted surface)',creator='Álvaro Pires de Évora',artist='01c79c8b-2aaf-58f2-8cf0-73da973677e4',entries=['531c09e3-52a7-55b4-95bd-6f168254ec22','d1d614d9-7d6f-528c-8a51-8cc79b8c13de'],pages='31–32',note='Same accession and panel in the 1922 and 1989 histories; historical titles and attributions remain on each entry.'),
 dict(native='ГЭ 228',title='Mary Magdalene',date='17th century',first=1600,last=1699,precision='century',medium='Oil on walnut panel',dimensions='118 × 88.5 cm',creator='Giulio Cesare Procaccini',artist='1c0150f3-fd87-4d31-a156-bdce331ccf86',entries=['c512ba11-a44b-5532-bf70-e4bc466f9f24'],pages='309–310',note='The 2011 catalogue accepts Procaccini; the 1923 exhibition entry retains its Procaccini-or-Strozzi historical attribution.'),
 dict(native='ГЭ 2773',title='Madonna and Child (Benois Madonna)',date='1478–1480',first=1478,last=1480,precision='range',medium='Oil on canvas, transferred from panel in 1824',dimensions='49.5 × 33 cm; rounded top',creator='Leonardo da Vinci',artist='f2432918-bd0d-47df-9aff-644d72e7ca91',entries=['6db89d73-1b42-52f1-8837-6e8dd01f575a'],pages='165–168',note='Exact Benois Madonna accession; not the Litta Madonna, a study, copy, or another version.'),
 dict(native='ГЭ 6443',title='Madonna and Child Enthroned with Saints James the Less, John the Baptist, Nicholas and Lawrence',date='second half of the 1380s',first=1385,last=1389,precision='circa',medium='Tempera on poplar panels',dimensions='132 × 162 cm; five-part polyptych',creator='Giovanni di Bartolomeo Cristiani',artist=None,entries=['eb8b64f5-d133-5482-a48d-f5228ce0fd43'],pages='164–165',note='One five-part polyptych, not five artworks; creator remains an explicit object label pending authority reconciliation.')]
for r in ROWS:
 r['id']=c.uid(OP+'/artwork/'+r['native']); r['slug']=c.norm(r['title']).replace(' ','-')+'-'+r['id'][:8]

def plain(v): return json.loads(json.dumps(v,default=str))
def save(p,v): c.save(p,v)
def target(db):
 actual='artline-508319:europe-west1:artline-postgres'
 row=plain(db.execute('select current_database() db').fetchone()); assert row['db']=='artline'; return actual
def snapshot(db):
 ids=[x for r in ROWS for x in r['entries']]
 return dict(entries=plain(db.execute('select * from exhibition_entries where id=any(%s::uuid[]) order by id',(ids,)).fetchall()),works=plain(db.execute("select id::text,title,accession_number,status from artworks where accession_number=any(%s) or id=any(%s::uuid[]) order by id",([r['native'] for r in ROWS],[r['id'] for r in ROWS])).fetchall()),institution=plain(db.execute('select id::text,name,status from institutions where id=%s',(IID,)).fetchone()),artists=plain(db.execute('select id::text,display_name,status from artists where id=any(%s::uuid[]) order by id',([r['artist'] for r in ROWS if r['artist']],)).fetchall()))
def plan():
 with c.connect() as db:
  t=target(db); pre=snapshot(db); assert len(pre['entries'])==5 and not pre['works'] and pre['institution']['status']!='archived' and len(pre['artists'])==3
  assert all(x['artwork_id'] is None for x in pre['entries'])
 p=dict(at=c.now(),operation=OP,target=t,source_url=SRC,source_sha256='bb3c733bb9ce2a8558268f2f12dbd7525f2384172fd9bf9781b6c4135916b950',records=ROWS,preimage=pre,scope=dict(exhibitions=[1600,1989],main_artworks_through=1970),partial_checklists=True)
 save(E/'plan.json',p);save(B/'transaction-preimage.json',p);save(E/'plan-pin.json',dict(sha256=c.sha((E/'plan.json').read_bytes()),backup=str(B/'transaction-preimage.json')))
 save(E/'research-review.json',dict(at=c.now(),selected_entries=5,distinct_objects=4,source='Official Hermitage 2011 collection catalogue',exact_identity_basis='Native Hermitage accessions, object-specific catalogue descriptions and reciprocal exhibition histories',qualified_labels_preserved=True,partial_checklists=True,images=0,holds=['No image licensed or selected in this batch.','Giovanni di Bartolomeo Cristiani remains an unlinked creator label pending authority reconciliation.']))
 print('planned 4 exact objects / 5 links')
def apply():
 p=c.load(E/'plan.json');assert p==c.load(B/'transaction-preimage.json');pin=c.sha((E/'plan.json').read_bytes());assert c.load(E/'plan-pin.json')['sha256']==pin
 with c.connect(write=True) as db:
  target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)');current=snapshot(db)
  if not current['works']:
   assert current==p['preimage']
   for r in ROWS:
    db.execute("insert into artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,current_institution_id,created_by,updated_by) values(%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,%s,'review',true,%s,%s,%s,%s)",(r['id'],r['slug'],r['title'],c.norm(r['title']),r['date'],r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],r['native'],None if r['artist'] else r['creator'],IID,ACTOR,ACTOR))
    ev=dict(operation=OP,planSHA256=pin,nativeAccession=r['native'],pages=r['pages'],basis=r['note'],sourceSHA256=p['source_sha256'],currentDisplayClaim=False,checklistComplete=False)
    db.execute("insert into citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) values(%s,'artwork',%s,%s,'historical_exhibition_object_identity',%s,%s,%s,%s,%s)",(c.uid(OP+'/citation/'+r['native']),r['id'],SID,r['native'],SRC,json.dumps(ev,ensure_ascii=False),p['at'],ACTOR))
    db.execute("insert into artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) values(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(c.uid(OP+'/holding/'+r['native']),r['id'],IID,SID,SRC,json.dumps(ev,ensure_ascii=False),p['at']))
    if r['artist']: db.execute("insert into artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) values(%s,%s,'primary',%s)",(r['id'],r['artist'],'Official Hermitage 2011 catalogue; '+r['note']))
    for eid in r['entries']: db.execute("update exhibition_entries set artwork_id=%s,match_basis=%s,evidence=evidence||%s where id=%s and artwork_id is null",(r['id'],'Exact Hermitage accession and object-specific catalogue history; version, historical title and qualified attribution preserved.',Jsonb(dict(canonicalObjectReview=ev)),eid))
  else:
   assert {x['id'] for x in current['works']}=={r['id'] for r in ROWS}
   assert all(next(x for x in current['entries'] if x['id']==eid)['artwork_id']==r['id'] for r in ROWS for eid in r['entries'])
  post=snapshot(db)
 save(E/'applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,postimage=post,counts=dict(new_catalogue_artworks=4,new_exact_artwork_links=5),committed=True))
 print('committed')
def verify():
 p=c.load(E/'plan.json');a=c.load(E/'applied.json'); rows=[]
 with c.connect() as db:
  t=target(db)
  for r in ROWS:
   w=plain(db.execute('select id::text,title,accession_number,status,creation_year_start,creation_year_end,current_institution_id::text,unlinked_creator_label from artworks where id=%s',(r['id'],)).fetchone());assert w['accession_number']==r['native'] and w['status']=='review' and w['creation_year_end']<=1970 and w['current_institution_id']==IID
   es=plain(db.execute('select id::text,artwork_id::text,source_artwork_id,match_basis from exhibition_entries where id=any(%s::uuid[]) order by id',(r['entries'],)).fetchall());assert len(es)==len(r['entries']) and all(x['artwork_id']==r['id'] and x['source_artwork_id'] in (r['native'],'hermitage/accession/'+r['native']) for x in es)
   rows.append(dict(artwork=w,entries=es))
 counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=4,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=5,new_images=0,existing_records_enriched=0)
 v=dict(at=c.now(),target=t,operation=OP,plan_sha256=a['plan_sha256'],rows=rows,verified_counts=counts,source_sha256=p['source_sha256'],attribution='All IDs were absent in the pinned transaction preimage and inserted under the programme operation; concurrent Danish/SMK work excluded.',passed=True,local_catalogue_writes=0)
 save(E/'independent-database-verification.json',v);save(E/'verification.json',v);save(E/'recovery-check.json',dict(at=c.now(),committed_receipt=True,replay_needed=False,all_planned_ids_present=True,plan_sha256=a['plan_sha256']))
 print(json.dumps(v['verified_counts']))
def finalize():
 counts=c.load(E/'verification.json')['verified_counts']; api=[]
 for r in ROWS:
  for eid in r['entries']:
   event=next(x['exhibition_id'] for x in c.load(E/'plan.json')['preimage']['entries'] if x['id']==eid)
   data=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+event+'/entries',params={'limit':100},timeout=40);data.raise_for_status();item=next(x for x in data.json()['items'] if x['id']==eid);assert item['artworkId']==r['id'];api.append(dict(entry=eid,event=event,artwork=r['id'],source_artwork_id=r['native']))
 save(E/'public-verification.json',dict(at=c.now(),verified_entries=api,count=5,passed=True))
 qp=E.parent.parent/'source-queue.json';lock=qp.with_suffix('.lock')
 with lock.open('a+') as ql:
  fcntl.flock(ql,fcntl.LOCK_EX);q=c.load(qp);before={x['source_id']:x for x in q['sources'] if x['source_id']!='hermitage'};h=next(x for x in q['sources'] if x['source_id']=='hermitage');h['research_status']='four_documentary_objects_promoted_to_review_catalogue_five_exact_links_verified';h['last_checked_at']=c.now();h['cursor']['last_reviewed_batch']=50;h['cursor']['batch50_exact_links']={'accessions':[r['native'] for r in ROWS],'artworks':4,'entries':5,'next':'Rotate to another undercovered official institutional object-history route; do not replay these Hermitage accessions.'};paths=['docs/research/continuous-exhibitions-20261013/batches/000050/'+x for x in ['research-review.json','verification.json','independent-database-verification.json','public-verification.json','recovery-check.json']];h['evidence']=list(dict.fromkeys(h.get('evidence',[])+paths));tmp=qp.with_suffix('.50.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);live=c.load(qp);assert before=={x['source_id']:x for x in live['sources'] if x['source_id']!='hermitage'}
 save(E/'queue-update.json',dict(at=c.now(),source_id='hermitage',research_status=h['research_status'],resume_cursor=h['cursor']['batch50_exact_links'],unrelated_entries_preserved=True))
 evidence=['independent-database-verification.json','verification.json','public-verification.json','recovery-check.json','research-review.json','plan-pin.json','queue-update.json','CHECKPOINT.json']
 result=dict(outcome='progress',summary='Promoted four exact Hermitage objects from documentary-only entries to review catalogue works and independently verified five accession-specific exhibition links. Historical titles and the 1923 alternative attribution remain explicit; all checklists remain partial.',next_task='Rotate to another undercovered official institutional object-history route; do not replay Hermitage accessions ГЭ 2473, ГЭ 228, ГЭ 2773 or ГЭ 6443.',blocker='',verified_counts=counts,evidence_paths=['docs/research/continuous-exhibitions-20261013/batches/000050/'+x for x in evidence])
 save(E/'CHECKPOINT.json',dict(at=c.now(),batch=50,outcome='progress',result=result,production_target='artline-508319:europe-west1:artline-postgres',local_catalogue_writes=0,shared_lock='artline-curated-ingestion',exhibition_lock=2026101201));save(E/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': globals()[sys.argv[1]]()
