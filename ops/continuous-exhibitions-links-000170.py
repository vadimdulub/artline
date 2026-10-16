"""Bounded original-catalogue/object reconciliation; external supervisor unchanged."""
import fcntl,gzip,json,os,subprocess,sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000170'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000170'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000170'
OP='continuous-exhibitions-20261013-batch-000170'
ACTOR='local-european-research'
EVENT='5c64ef50-18f0-5cf3-8a19-e86adf45c299'
ENTRY='0efc3b5f-66ce-5d85-ac0d-1d6cd7e532de'
ARTIST='de003eac-51c4-4057-bec5-4870d243b1b2'
SOURCE='caeb1bff-6be6-5bbe-9e31-24aabe6dc12b'
WORK=c.uid('christies/artwork/1053966/recto')
ESOURCE=c.uid(OP+'/christies/1053966')
IDS={k:c.uid(OP+'/'+k) for k in ['identifier','citation']}
URL='https://www.christies.com/en/lot/lot-1053966'
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)

def target(db):
 expected='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'
 assert expected in [x.strip() for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
 assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
 row=db.execute('select current_database() database,current_user role,pg_is_in_recovery() recovery').fetchone()
 assert row==dict(database='artline',role='artline_app',recovery=False)
 return dict(at=c.now(),instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,**row)

def check_receipt(rc):
 p=Path(rc['body_path']);raw=p.read_bytes();raw=gzip.decompress(raw) if p.suffix=='.gz' else raw
 assert c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes']
 return raw

def snapshot(db):
 out={}
 for tab in ['exhibitions','exhibition_entries','exhibition_occurrences','exhibition_participants','exhibition_publications','exhibition_source_records']:
  col='id' if tab=='exhibitions' else 'exhibition_id'
  out[tab]=db.execute('select * from '+tab+' where '+col+'=%s order by id',(EVENT,)).fetchall()
 for tab,col,order in [('artworks','id','id'),('artwork_artists','artwork_id','artwork_id,artist_id'),('artwork_location_assertions','artwork_id','id')]:
  out[tab]=db.execute('select * from '+tab+' where '+col+'=%s order by '+order,(WORK,)).fetchall()
 for tab in ['citations','external_identifiers']:
  out[tab]=db.execute('select * from '+tab+" where entity_type='artwork' and entity_id=%s order by id",(WORK,)).fetchall()
 out['artists']=db.execute('select * from artists where id=%s',(ARTIST,)).fetchall()
 out['sources']=db.execute('select * from sources where id=%s',(SOURCE,)).fetchall()
 return serial(out)

def duplicates(db):
 exact=db.execute("select * from external_identifiers where entity_type='artwork' and (canonical_url like '%1053966%' or external_id='1053966') order by id").fetchall()
 titles=db.execute("select a.id,a.title,a.accession_number,a.dimensions_text,a.current_institution_id,a.unlinked_creator_label from artworks a where a.normalized_title like '%elders%israel%' or a.normalized_title like '%ten%commandment%' or a.normalized_title like '%woman%upraised%' order by a.id").fetchall()
 ids=[str(x['id'])for x in titles]
 creators=db.execute('select aa.*,a.display_name from artwork_artists aa join artists a on a.id=aa.artist_id where aa.artwork_id=any(%s::uuid[]) order by aa.artwork_id,aa.artist_id',(ids,)).fetchall()
 all_blake=db.execute('select a.* from artworks a join artwork_artists aa on a.id=aa.artwork_id where aa.artist_id=%s order by a.id',(ARTIST,)).fetchall()
 assert not exact and not any(str(x['artist_id'])==ARTIST for x in creators)
 assert len(all_blake)==476
 return serial(dict(exact_identifiers=exact,title_candidates=titles,candidate_creators=creators,all_blake=all_blake))

def prepare():
 B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
 path=R/'christies-web-extraction.json';raw=path.read_bytes();text=c.load(path)
 assert isinstance(text,str)
 for s in ['1939, no. 160','Mrs W. Murray Crane','final half of the 1780s','pencil, pen and black ink, grey wash','31.1 x 33 cm.','(recto); Seated Woman with upraised arm (verso)']:assert s in text,s
 rc=dict(url=URL,retrieved_at=c.now(),capture_kind='web_tool_extracted_primary_page',retrieval_success=True,origin_html_not_captured=True,sha256=c.sha(raw),bytes=len(raw),body_path=str(path),http_status_not_reported_by_tool=True)
 pdf=c.load(E.parent/'000070/plan.json')['pdf_receipt'];check_receipt(pdf);assert c.sha((R/'blake1939.pdf').read_bytes())==pdf['sha256']
 with c.connect() as db:
  t=target(db);pre=snapshot(db);dup=duplicates(db)
  entry=next(x for x in pre['exhibition_entries']if x['id']==ENTRY)
  assert entry['artwork_id']is None and entry['catalogue_number']=='160' and entry['lender_label']=='Mrs. W. Murray Crane' and entry['participation']=='catalogued'
  original=next(x for x in pre['exhibition_source_records']if x['id']==entry['source_record_id'])
  _,ocr=c.capture(original['source_url']);assert ocr['sha256']==original['capture_sha256'];check_receipt(ocr)
  assert not pre['artworks'] and not pre['citations'] and not pre['external_identifiers']
  assert pre['artists'][0]['display_name']=='William Blake' and pre['exhibitions'][0]['checklist_state']=='partial'
  assert any(x['artist_id']==ARTIST for x in pre['exhibition_participants'])
 basis='Original Philadelphia1939 catalogue no160, printed p113/PDF139, identifies the wash-and-ink drawing, describes the central seated bearded figure and four standing figures, and names Mrs. W. Murray Crane as lender. Primary Christie\'s object/lot1053966 explicitly cites Philadelphia1939 no160 and documents the same Crane ownership in1939 and subsequent1971 bequest to Louise Crane. Creator, qualified subject, medium, exact exhibition number and lender provenance agree. The subject identification remains uncertain. The verso is described separately in the auction record and is not another exhibition entry or independently asserted as exhibited. No museum holding/current owner/current display inferred.'
 visual=dict(at=c.now(),method='Actual image-tool inspection of rendered original catalogue pages',pages=[dict(pdf_page=n,path=str(R/f'catalogue-{n}.png'),sha256=c.sha((R/f'catalogue-{n}.png').read_bytes()))for n in [139,143,144]],observations='PDF139/printed113 visibly lists no160, wash and india-ink, possible Moses, central seated figure and two standing figures on each side, with Mrs. W. Murray Crane lender. PDF144/printed118 visibly confirms no165 and Philip Hofer; no165 remains unmatched. PDF143 is an adjacent Michael Binding Satan plate and is not evidence for no160. No new artwork image prepared or reviewed; only these three pages viewed.',new_images_prepared=0,no_unsampled_review_claim=True,passed=True)
 obj=dict(native_id='1053966',native_id_type='Christies lot web identifier, not museum accession',accession=None,title='The Elders of Israel receiving the Ten Commandments (?) (recto)',verso_label='Seated Woman with upraised arm (verso)',date_display='late 1780s (approximately)',creation_year_start=1785,creation_year_end=1789,date_precision='circa_range',date_basis='Christies lot essay dates this example to the final half of the1780s; approximate range retained.',medium='pencil, pen and black ink, grey wash, on oatmeal paper',dimensions='12 x 13 in. (31.1 x 33 cm.)',creator='William Blake',work_type='drawing')
 uncertainty=dict(subject_identification='Question mark retained; original catalogue also says possibly Moses.',dimensions='Source imperial/metric values do not exactly convert. Verbatim label retained, no correction invented.',bibliography='Christies prints Butlin cat.no11; secondary search lead suggests113. No catalogue-raisonne identifier inserted without original verification.',provenance='Possible Tatham/Cunliffe steps remain possible. No current owner inferred from historical auction.',verso='Described in evidence only; not another main work or exhibited entry.')
 plan=dict(at=c.now(),operation=OP,target=t,event_id=EVENT,entry_id=ENTRY,artwork_id=WORK,source=rc,source_text=text,object=obj,original_catalogue_record=original,ocr_receipt=ocr,pdf_receipt=pdf,visual=visual,basis=basis,uncertainty=uncertainty,preimage=pre,duplicate_review=dup,scope=dict(exhibitions=[1600,1989],main_artworks_through=1970),image_policy=dict(selected_images=0,licence_not_inferred=True,current_holdings_not_inferred=True))
 c.save(E/'immutable-plan.json',plan);c.save(B/'immutable-plan.json',plan);pin=c.sha((E/'immutable-plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin))
 save('source-capture-verification.json',dict(at=c.now(),receipts=[rc,pdf,ocr],checksums_verified=True,extracted_primary_web_page_not_search_snippet=True,raw_origin_html_not_captured=True,source_bodies_outside_Documents=True,passed=True))
 save('visual-review-verification.json',visual)
 save('candidate-reconciliation-verification.json',dict(at=c.now(),selected_entries=['160','165'],prepared_exact_links=1,prepared_review_artworks=1,new_participants=0,full_creator_catalogue_rows=476,global_title_candidates=len(dup['title_candidates']),exact_native_duplicates=0,basis=basis,uncertainty=uncertainty,held=[dict(number='165',reason='Original catalogue verified; accessible searches did not establish a Harvard native object or secure later ownership. Harvard ownership is not inferred from Philip Hofer lender. Remains documentary.')],passed=True))
 print('Prepared one new review drawing and one exact existing-entry link.')

def apply():
 p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];assert c.sha((E/'immutable-plan.json').read_bytes())==c.sha((B/'immutable-plan.json').read_bytes())==pin
 for key in ['source','pdf_receipt','ocr_receipt']:check_receipt(p[key])
 with c.connect(write=True) as db:
  target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)');db.execute('select id from exhibition_entries where id=%s for update',(ENTRY,))
  cur=snapshot(db)
  if cur['artworks']:
   assert (B/'transaction-preimage.json').exists() and any(x['id']==ESOURCE and x['interpretation']['plan_sha256']==pin for x in cur['exhibition_source_records'])
   print('Own committed plan found; verify only.');return
  assert cur==p['preimage'] and duplicates(db)==p['duplicate_review'],'Concurrent state changed; do not overwrite'
  pre=dict(at=c.now(),operation=OP,plan_sha256=pin,target=target(db),rows=cur,locks=['artline-curated-ingestion',2026101201]);c.save(B/'transaction-preimage.json',pre);save('transaction-preimage.json',pre);save('production-target-before-write.json',pre['target']|dict(plan_sha256=pin,passed=True))
  o=p['object'];rc=p['source'];ev=dict(operation=OP,plan_sha256=pin,source_sha256=rc['sha256'],capture_kind=rc['capture_kind'],source_capture=rc['body_path'],original_catalogue_sha256=p['ocr_receipt']['sha256'],original_pdf_sha256=p['pdf_receipt']['sha256'],native_id=o['native_id'],native_id_type=o['native_id_type'],accession=None,catalogue_number='160',printed_page=113,pdf_page=139,basis=p['basis'],uncertainty=p['uncertainty'],object=o,participation_surface='recto',checklist_complete=False,current_display_claim=False,current_holding_claim=False)
  description='Drawing identified in the original Philadelphia1939 exhibition catalogue as no160. The subject identification remains uncertain. Christie\'s lot1053966 describes Seated Woman with upraised arm on the reverse; that surface is retained as evidence only and is not independently asserted as exhibited. The source dates the drawing approximately to the final half of the1780s. Current owner and holding institution are not established. Source dimensions are transcribed verbatim and retain an imperial/metric discrepancy.'
  db.execute("insert into artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,description_md,current_location_unknown_reason,status,research_candidate,created_by,updated_by)values(%s,%s,%s,%s,%s,1785,1789,'circa_range','drawing',%s,%s,%s,%s,'review',true,%s,%s)",(WORK,'blake-elders-israel-christies-1053966-recto',o['title'],c.norm(o['title']),o['date_display'],o['medium'],o['dimensions'],description,'Historical lender and auction record do not establish current holdings.',ACTOR,ACTOR))
  db.execute("insert into artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)values(%s,%s,'primary',%s)",(WORK,ARTIST,'Unqualified creator attribution in original1939 catalogue and primary Christie\'s lot1053966; subject identity remains qualified.'))
  db.execute("insert into external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)values(%s,'artwork',%s,'christies-lot','1053966',%s,%s,%s)",(IDS['identifier'],WORK,URL,SOURCE,rc['retrieved_at']))
  db.execute("insert into citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by)values(%s,'artwork',%s,'native_object_metadata_and_historical_exhibition_match',%s,'1053966',%s,%s,%s,%s,%s)",(IDS['citation'],WORK,SOURCE,URL,'Christies lot1053966, recto; Philadelphia1939 no160, p113',json.dumps(ev,ensure_ascii=False),rc['retrieved_at'],ACTOR))
  db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(ESOURCE,EVENT,OP,'christies/1053966/recto',URL,rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(object=o,source_text=p['source_text'],receipt=rc)),Jsonb(ev)))
  old=next(x for x in cur['exhibition_entries']if x['id']==ENTRY);evidence=old['evidence']|dict(canonicalObjectMatchPending=False,canonicalObjectMatch=ev,canonicalMatchSourceRecordID=ESOURCE)
  result=db.execute('update exhibition_entries set artwork_id=%s,match_basis=%s,evidence=%s where id=%s and artwork_id is null',(WORK,p['basis'],Jsonb(evidence),ENTRY));assert result.rowcount==1
  after=snapshot(db)
  audits=[('artwork',WORK,None,after['artworks'][0]),('exhibition_entry',ENTRY,old,next(x for x in after['exhibition_entries']if x['id']==ENTRY)),('exhibition_source_record',ESOURCE,None,next(x for x in after['exhibition_source_records']if x['id']==ESOURCE)),('citation',IDS['citation'],None,after['citations'][0]),('external_identifier',IDS['identifier'],None,after['external_identifiers'][0]),('artwork_artist',WORK,None,after['artwork_artists'][0])]
  for typ,ident,before,record in audits:db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_exact_object_reconciliation',typ,ident,OP,Jsonb(before),Jsonb(dict(record=record,plan_sha256=pin))))
  c.save(B/'transaction-postimage.json',dict(at=c.now(),operation=OP,plan_sha256=pin,rows=after))
 save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; verification pending.')

def verify():
 p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
 assert c.sha((E/'immutable-plan.json').read_bytes())==pin==pre['plan_sha256']==post['plan_sha256'] and pre['rows']==p['preimage']
 with c.connect() as db:
  db.execute('set transaction isolation level repeatable read, read only');t=target(db);rows=snapshot(db);au=serial(db.execute('select * from audit_log where request_id=%s order by entity_type,entity_id',(OP,)).fetchall())
 assert rows==post['rows'] and len(au)==6 and all(a['after_json']['plan_sha256']==pin for a in au)
 before=next(x for x in pre['rows']['exhibition_entries']if x['id']==ENTRY);entry=next(x for x in rows['exhibition_entries']if x['id']==ENTRY)
 assert before['artwork_id']is None and entry['artwork_id']==WORK and entry['evidence']['canonicalObjectMatch']['plan_sha256']==pin
 for k in before:
  if k not in ['artwork_id','match_basis','evidence']:assert before[k]==entry[k],k
 for k in ['exhibitions','exhibition_occurrences','exhibition_participants','exhibition_publications','artists','sources','artwork_location_assertions']:assert pre['rows'][k]==rows[k],k
 assert [x for x in rows['exhibition_entries']if x['id']!=ENTRY]==[x for x in pre['rows']['exhibition_entries']if x['id']!=ENTRY]
 assert [x for x in rows['exhibition_source_records']if x['id']!=ESOURCE]==pre['rows']['exhibition_source_records']
 w=rows['artworks'][0];assert w['status']=='review' and w['primary_media_id']is None and w['current_institution_id']is None and w['accession_number']is None
 assert (w['creation_year_start'],w['creation_year_end'],w['date_precision'])==(1785,1789,'circa_range') and w['title']==p['object']['title']
 assert not pre['rows']['artworks'] and len(rows['artwork_artists'])==len(rows['citations'])==len(rows['external_identifiers'])==1
 assert rows['artwork_artists'][0]['artist_id']==ARTIST and rows['external_identifiers'][0]['external_id']=='1053966' and json.loads(rows['citations'][0]['evidence_note'])['plan_sha256']==pin
 sr=next(x for x in rows['exhibition_source_records']if x['id']==ESOURCE);assert sr['capture_sha256']==p['source']['sha256'] and sr['interpretation']['plan_sha256']==pin
 for a in au:assert a['before_json']==(before if a['entity_type']=='exhibition_entry' else None)
 counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=1,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=1,new_images=0,existing_records_enriched=1)
 if not (E/'independent-database-verification.json').exists():save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,audits=au,verified_counts=counts,attribution='Locked preimage has no work and null exact entry link; persisted citation/source record and six audits carry this batch and checksum. Previous/concurrent additions excluded.',passed=True))
 receipts=[]
 for key,url in [('entries',API+'exhibitions/'+EVENT+'/entries?limit=100'),('event',API+'exhibitions/'+EVENT),('work',API+'artists/'+rows['artists'][0]['slug']+'/works/'+WORK)]:
  res=requests.get(url,timeout=(15,45));res.raise_for_status();data=res.json();c.save(R/('public-'+key+'.json'),data)
  if key=='entries':
   assert len(data['items'])==28 and not data.get('nextCursor');x=next(x for x in data['items']if x['id']==ENTRY);assert x['artworkId']==WORK and not x.get('image');assert next(x for x in data['items']if x['catalogueNumber']=='165')['artworkId']is None
  elif key=='event':assert data['checklistState']=='partial'
  else:
   assert data['id']==WORK and data['title']==p['object']['title'] and data['status']=='review'
   assert data['creation_year_start']==1785 and data['creation_year_end']==1789 and data['date_precision']=='circa_range'
   assert data['holding']is None and data['display']is None and data['accession_number']is None
   assert data['medium_text']==p['object']['medium'] and data['dimensions_text']==p['object']['dimensions']
   assert any(x['source_url']==URL for x in data['citations'])
  receipts.append(dict(url=res.url,status=res.status_code,sha256=c.sha(res.content),capture=str(R/('public-'+key+'.json'))))
 save('independent-public-verification.json',dict(at=c.now(),receipts=receipts,entry_id=ENTRY,artwork_id=WORK,new_exact_links=1,new_review_artworks=1,checklist_entries=28,exact_links=16,remaining_documentary_entries=12,checklist_still_partial=True,no_image_selected=True,no165_preserved=True,passed=True))
 save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['immutable-plan.json','transaction-preimage.json','transaction-postimage.json']],postimage_matches_independent_read=True,passed=True))
 print(json.dumps(counts))

if __name__=='__main__':globals()[sys.argv[1]]()
