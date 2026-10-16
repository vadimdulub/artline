"""Independent fresh database, attribution, backup and public checks for batch168."""
import importlib.util,json,gzip,io
from pathlib import Path
import requests
from PIL import Image
sp=importlib.util.spec_from_file_location('batch168',Path(__file__).with_name('continuous-exhibitions-000168.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;R=m.R;B=m.B
p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];e=p['event']
assert pin==c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())
pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json')
assert pre==c.load(E/'transaction-preimage.json') and pre['plan_sha256']==post['plan_sha256']==pin and not any(pre['rows'].values())
with c.connect()as db:
 target=m.target(db);rows=m.snapshot(db);old=m.preserved(db)
assert old==p['preserved_entities']==pre['preserved_entities'] and rows==post['rows']
evt=rows['exhibitions'];sources=rows['exhibition_source_records'];venues=rows['exhibition_occurrences'];entries=rows['exhibition_entries'];artists=rows['exhibition_participants'];audits=rows['audits']
assert len(evt)==len(venues)==1 and len(entries)==len(artists)==2 and len(sources)==3 and len(audits)==9 and not rows['exhibition_publications']
assert evt[0]['import_batch']==m.OP and evt[0]['status']=='review' and evt[0]['checklist_state']=='partial' and evt[0]['event_state']=='held'
assert evt[0]['title']==e['title'] and evt[0]['start_date']==e['start'] and evt[0]['end_date']==e['end'] and evt[0]['start_year']==evt[0]['end_year']==1980
assert {s['source_record_id']for s in sources}=={'NG32/127','NG24/1980/10','NG60/48'}
for s in sources:
 expected=next(x for x in e['sources']if x['id']==s['id']);assert s['interpretation']['operation']==m.OP and s['interpretation']['plan_sha256']==pin and s['capture_sha256']==expected['receipt']['sha256'];assert c.sha(gzip.decompress(Path(s['capture_url']).read_bytes()))==s['capture_sha256']
assert venues[0]['id']==e['occurrence_id'] and venues[0]['institution_id']==m.MID and venues[0]['start_date']==e['start'] and venues[0]['end_date']==e['end'] and venues[0]['evidence']['plan_sha256']==pin
assert {a['artist_id']for a in artists}==set(m.AIDS)
for a in artists:assert a['evidence']['plan_sha256']==pin and a['evidence']['posthumous'] and not a['evidence']['personal_attendance']
for x in entries:
 expected=next(y for y in e['entries']if y['id']==x['id']);assert x['artwork_id']==expected['artwork_id'] and x['source_artwork_id']==expected['inventory'] and x['exhibition_id']==m.EID and x['occurrence_id']==e['occurrence_id'] and x['evidence']['plan_sha256']==pin and x['participation']=='exhibited'
 assert x['title_label']==expected['title'] and x['creator_label']==expected['creator'] and x['date_label']==expected['date_label'] and x['medium_label']==expected['medium_label'] and x['dimensions_label']==expected['dimensions_label']
expected_audits={(table,r['id'])for table in m.TABLES for r in rows[table]}
assert {(a['entity_type'],a['entity_id'])for a in audits}==expected_audits
for a in audits:
 assert a['before_json']is None and a['action']=='continuous_exhibition_insert' and a['request_id']==m.OP and a['after_json']['plan_sha256']==pin
 assert a['after_json']['record']==next(r for r in rows[a['entity_type']]if r['id']==a['entity_id'])
counts=dict(new_exhibitions=1,new_venue_stops=1,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=2,new_exact_artwork_links=2,new_images=0,existing_records_enriched=0)
c.save(E/'independent-database-verification.json',dict(at=c.now(),operation=m.OP,target=target,plan_sha256=pin,rows=rows,verified_counts=counts,absent_locked_preimage_and_persisted_plan_checksums=True,nine_null_before_insert_audits_verified=True,existing_entities_unchanged=True,unrelated_and_prior_campaign_changes_excluded=True,passed=True))
c.save(E/'backup-verification.json',dict(at=c.now(),files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
url=m.API+'exhibitions/'+m.EID;res=requests.get(url,timeout=(15,45));res.raise_for_status();d=res.json();c.save(R/'NG32-127-public.json',d)
u2=url+'/entries?limit=20';r2=requests.get(u2,timeout=(15,45));r2.raise_for_status();items=r2.json();c.save(R/'NG32-127-entries.json',items)
assert d['id']==m.EID and d['title']==e['title'] and d['startDate']==e['start'] and d['endDate']==e['end'] and d['state']=='held' and d['checklistState']=='partial' and d['entryCount']==2 and d['venueCount']==1 and d['participantCount']==2
assert {x['artist_id']for x in d['participants']}==set(m.AIDS)
assert d['venues'][0]['id']==e['occurrence_id'] and d['venues'][0]['institution_id']==m.MID and d['venues'][0]['start_date']==e['start'] and d['venues'][0]['end_date']==e['end']
assert {s['source_record_id']for s in d['sources']}=={'NG32/127','NG24/1980/10','NG60/48'} and all(s['interpretation']['plan_sha256']==pin for s in d['sources'])
assert items['total']==2 and not items['hasMore'] and len(items['items'])==2
for x in items['items']:
 expected=next(y for y in e['entries']if y['id']==x['id']);assert x['artworkId']==expected['artwork_id'] and x['creator']==expected['creator'] and x['title']==expected['title'] and x['evidence']['plan_sha256']==pin
 art=next(w for w in old['artworks']if w['id']==x['artworkId']);media=next(mm for mm in old['media']if mm['id']==art['primary_media_id']);assert x['image']==media['storage_path']
c.save(E/'independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=[dict(url=url,status=res.status_code,body_sha256=c.sha(res.content),entries_url=u2,entries_status=r2.status_code,entries_sha256=c.sha(r2.content))],exhibition_venue_artists_and_entries_verified=True,exact_entries=2,unresolved_documentary_entries=0,partial_checklist_verified=True,passed=True))
receipts=[]
for art in old['artworks']:
 media=next(mm for mm in old['media']if mm['id']==art['primary_media_id']);imurl='https://artlines.org'+media['storage_path'];im=requests.get(imurl,timeout=(15,45));im.raise_for_status()
 assert len(im.content)==media['byte_size']<=100000 and c.sha(im.content)==media['checksum_sha256'];img=Image.open(io.BytesIO(im.content));img.verify();img=Image.open(io.BytesIO(im.content));assert img.size==(media['width'],media['height'])
 path=R/('existing-'+art['accession_number']+'.jpg');path.write_bytes(im.content)
 receipts.append(dict(artwork_id=art['id'],accession=art['accession_number'],media_id=media['id'],url=imurl,status=im.status_code,sha256=c.sha(im.content),bytes=len(im.content),dimensions=img.size,path=str(path),rights_status=media['rights_status'],license_label=media['license_label']))
c.save(E/'existing-image-delivery-verification.json',dict(at=c.now(),receipts=receipts,new_images=0,existing_images_unchanged=True,technical_validation_only=True,visual_review_claimed=False,rights_not_changed=True,passed=True))
print(json.dumps(counts));print('Fresh production, audit, backup, public relationship and existing image checks passed.')
