"""Fresh production and public API verification, separate from the apply process."""
import importlib.util,json,gzip
from pathlib import Path
import requests
sp=importlib.util.spec_from_file_location('batch169',Path(__file__).with_name('continuous-exhibitions-000169.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B
p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256']
assert pin==c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())
pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
assert pre==c.load(E/'transaction-preimage.json')and pre['plan_sha256']==post['plan_sha256']==pin and not any(pre['rows'].values())
with c.connect()as db:
 target=m.target(db);rows=m.snapshot(db);old=m.preserved(db)
assert rows==post['rows']and old==p['preserved']==pre['preserved']
assert {t:len(rows[t])for t in m.TABLES}==dict(exhibitions=2,exhibition_source_records=3,exhibition_occurrences=3,exhibition_participants=2,exhibition_entries=0,exhibition_publications=1)
assert len(rows['audits'])==11
for e in p['events']:
 event=next(x for x in rows['exhibitions']if x['id']==e['id'])
 assert event['title']==e['title']and event['alternate_titles']==e['alternate_titles']and event['start_date']==e['start']and event['end_date']==e['end']
 assert event['start_year']==event['end_year']==1981 and event['import_batch']==m.OP and event['status']=='review'and event['checklist_state']=='unknown'and event['event_state']=='held'
 for s in e['sources']:
  actual=next(x for x in rows['exhibition_source_records']if x['id']==s['id']);rc=s['receipt']
  assert actual['source_record_id']==s['native']and actual['source_url']==rc['url']and actual['capture_sha256']==rc['sha256']and actual['interpretation']['operation']==m.OP and actual['interpretation']['plan_sha256']==pin
  assert c.sha(gzip.decompress(Path(actual['capture_url']).read_bytes()))==actual['capture_sha256']
 for o in e['occurrences']:
  actual=next(x for x in rows['exhibition_occurrences']if x['id']==o['id'])
  for field,key in [('institution_id','institution_id'),('venue_label','venue'),('city_label','city'),('country_label','country'),('country_code','country_code'),('start_date','start'),('end_date','end')]:assert actual[field]==o[key]
  assert actual['source_record_id']==o['source_id']and actual['exhibition_id']==e['id']and actual['evidence']['plan_sha256']==pin
 a=next(x for x in rows['exhibition_participants']if x['id']==e['participant_id'])
 assert a['artist_id']==e['artist_id']and a['name_label']==e['name']and a['evidence']['plan_sha256']==pin and a['evidence']['posthumous']==e['posthumous']and not a['evidence']['personal_attendance_claimed']
b=rows['exhibition_publications'][0];expected=p['events'][1]['publication']
assert b['source_identifier']==expected['identifier']and b['title_label']==expected['title']and b['exhibition_id']==m.EIDS[1]and b['evidence']['plan_sha256']==pin and b['evidence']['bibliography_only']and not b['evidence']['full_catalogue_inspected']
assert {(x['entity_type'],x['entity_id'])for x in rows['audits']}=={(t,x['id'])for t in m.TABLES for x in rows[t]}
for a in rows['audits']:
 assert a['before_json']is None and a['request_id']==m.OP and a['action']=='continuous_exhibition_insert'and a['after_json']['plan_sha256']==pin
 assert a['after_json']['record']==next(x for x in rows[a['entity_type']]if x['id']==a['entity_id'])
counts=dict(new_exhibitions=2,new_venue_stops=3,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=2,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
if not(E/'independent-database-verification.json').exists():
 c.save(E/'independent-database-verification.json',dict(at=c.now(),operation=m.OP,target=target,plan_sha256=pin,rows=rows,verified_counts=counts,absent_locked_preimages=True,persisted_source_plan_checksums=True,eleven_null_before_insert_audits=True,existing_creators_and_institution_unchanged=True,other_jobs_excluded=True,passed=True))
else:
 earlier=c.load(E/'independent-database-verification.json');assert earlier['rows']==rows and earlier['plan_sha256']==pin and earlier['verified_counts']==counts and earlier['passed']
backup_files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']]
if not(E/'backup-verification.json').exists():
 c.save(E/'backup-verification.json',dict(at=c.now(),files=backup_files,preimage_absent=True,postimage_matches_fresh_production_read=True,passed=True))
else:assert c.load(E/'backup-verification.json')['files']==backup_files
receipts=[]
for e in p['events']:
 url=m.API+'exhibitions/'+e['id'];res=requests.get(url,timeout=(15,45));res.raise_for_status();d=res.json();c.save(R/(e['id']+'-public.json'),d)
 assert d['id']==e['id']and d['title']==e['title']and d['startDate']==e['start']and d['endDate']==e['end']and d['state']=='held'and d['checklistState']=='unknown'
 assert d['entryCount']==0 and d['venueCount']==len(e['occurrences'])and d['participantCount']==1
 assert len(d['participants'])==1 and d['participants'][0]['artist_id']==e['artist_id']
 assert {x['id']for x in d['venues']}=={x['id']for x in e['occurrences']}
 for o in e['occurrences']:
  v=next(x for x in d['venues']if x['id']==o['id']);assert v['institution_id']==o['institution_id']and v['start_date']==o['start']and v['end_date']==o['end']and v['name']==o['venue']and v['city']==o['city']and v['country']==o['country']
 assert {x['source_record_id']for x in d['sources']}=={x['native']for x in e['sources']}and all(x['interpretation']['plan_sha256']==pin for x in d['sources'])
 eu=url+'/entries?limit=20';er=requests.get(eu,timeout=(15,45));er.raise_for_status();entries=er.json();c.save(R/(e['id']+'-entries.json'),entries)
 assert entries['total']==0 and entries['items']==[]and not entries['hasMore']
 if e['publication']:assert any(x['source_identifier']==expected['identifier']for x in d['publications'])
 receipts.append(dict(url=url,status=res.status_code,body_sha256=c.sha(res.content),entries_url=eu,entries_status=er.status_code,entries_sha256=c.sha(er.content),exhibition_id=e['id'],venue_count=len(e['occurrences']),participant_count=1,entry_count=0))
c.save(E/'independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=receipts,distinct_exhibitions=2,venue_stops=3,artist_links=2,bibliographic_references=1,checklists_unknown=True,no_fabricated_artwork_entries=True,no_new_images_or_files_uploaded=True,passed=True))
print(json.dumps(counts));print('Fresh database attribution, backups and independent public verification passed.')
