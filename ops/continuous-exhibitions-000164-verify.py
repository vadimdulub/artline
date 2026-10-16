"""Independent read-only production and public-delivery checks for batch164."""
import importlib.util, json
from pathlib import Path
import requests
sp=importlib.util.spec_from_file_location('b161',Path(__file__).with_name('continuous-exhibitions-000164.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=m.c;E=m.E;B=m.B;R=m.R
p=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
assert pin==c.sha((E/'plan.json').read_bytes())==c.sha((B/'plan.json').read_bytes())==pre['plan_sha256']
assert pre['operation']==m.OP and not any(pre['rows'].values())
with c.connect() as db:
    db.execute('set transaction isolation level repeatable read, read only')
    target=m.target(db);rows=m.snapshot(db)
    assert m.preserved(db)==p['preserved_entities'] and m.collisions(db)==p['duplicate_matches']
    for table,n in dict(exhibitions=1,exhibition_source_records=2,exhibition_occurrences=1,exhibition_participants=2,exhibition_entries=2,exhibition_publications=0,audits=8).items():assert len(rows[table])==n,(table,len(rows[table]))
    for a in rows['audits']:
        assert a['request_id']==m.OP and a['before_json'] is None and a['after_json']['plan_sha256']==pin
        assert a['after_json']['record'] in rows[a['entity_type']]
    for event in p['events']:
        ex=next(x for x in rows['exhibitions'] if x['id']==event['id'])
        assert (ex['title'],ex['alternate_titles'],ex['start_date'],ex['end_date'],ex['start_year'],ex['end_year'],ex['date_display'],ex['date_precision'],ex['status'],ex['event_state'],ex['checklist_state'],ex['import_batch'])==(event['title'],event['alternate_titles'],event['start'],event['end'],event['year'],event['year'],event['date_display'],event['date_precision'],'review','held','partial',m.OP)
        for s in event['sources']:
            sr=next(x for x in rows['exhibition_source_records'] if x['id']==s['id']);rc=s['receipt']
            assert (sr['exhibition_id'],sr['source_record_id'],sr['source_url'],sr['capture_sha256'])==(event['id'],s['native_id'],rc['url'],rc['sha256'])
            assert sr['source_payload']['source_text']==s['text'] and sr['interpretation']['plan_sha256']==pin and sr['interpretation']['operation']==m.OP
            assert sr['interpretation']['date_qualified']==event['date_qualified']
        o=next(x for x in rows['exhibition_occurrences'] if x['exhibition_id']==event['id'])
        assert (o['id'],o['source_record_id'],o['institution_id'],o['venue_label'],o['city_label'],o['country_label'],o['country_code'],o['start_date'],o['end_date'],o['date_display'])==(event['occurrence_id'],event['sources'][0]['id'],m.MID,'National Gallery — '+event['room'],'London','United Kingdom','GB',event['start'],event['end'],event['date_display'])
        assert o['evidence']['plan_sha256']==pin
        for intended in event['entries']:
            en=next(x for x in rows['exhibition_entries'] if x['id']==intended['id'])
            assert (en['exhibition_id'],en['source_record_id'],en['occurrence_id'],en['artwork_id'],en['source_artwork_id'],en['title_label'],en['creator_label'],en['participation'])==(event['id'],intended['source_id'],event['occurrence_id'],intended['artwork_id'],intended['inventory'],intended['title'],intended['creator'],'exhibited')
            assert en['catalogue_number'] is None and en['lender_label'] is None and en['evidence']['plan_sha256']==pin
            assert en['evidence']['object_identity_receipt']==intended['object_source']['receipt']
        for intended in event['participants']:
            ar=next(x for x in rows['exhibition_participants'] if x['id']==intended['id'])
            assert (ar['exhibition_id'],ar['artist_id'],ar['source_record_id'],ar['name_label'],ar['role'])==(event['id'],intended['artist_id'],intended['source_id'],intended['name'],'artist')
            assert ar['evidence']['plan_sha256']==pin and ar['evidence']['posthumous'] and not ar['evidence']['personal_attendance']
counts=dict(new_exhibitions=1,new_venue_stops=1,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=2,new_exact_artwork_links=2,new_images=0,existing_records_enriched=0)
if not (E/'independent-database-verification.json').exists():
    c.save(E/'independent-database-verification.json',dict(at=c.now(),operation=m.OP,target=target,plan_sha256=pin,rows=rows,verified_counts=counts,attribution='Every counted row absent in locked transaction preimage. Persisted source/relationship plan hashes and8 null-before insert audits match this programme. Fresh read-only transaction confirms all relationships and unchanged existing artworks, creators, authorities, aliases and institution. No concurrent campaign additions counted.',passed=True))
else:assert c.load(E/'independent-database-verification.json')['rows']==rows
assert c.load(B/'transaction-postimage.json')['rows']==rows
assert c.sha((E/'transaction-preimage.json').read_bytes())==c.sha((B/'transaction-preimage.json').read_bytes())
if not (E/'backup-verification.json').exists():
    c.save(E/'backup-verification.json',dict(at=c.now(),files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_absent=True,postimage_matches_fresh_read=True,passed=True))
receipts=[];images={}
for event in p['events']:
    u=m.API+'exhibitions/'+event['id'];r=requests.get(u,timeout=(15,45));r.raise_for_status();j=r.json();c.save(R/(event['native_id'].replace('/','-')+'-public.json'),j)
    assert (j['id'],j['title'],j['startYear'],j['endYear'],j['entryCount'],j['checklistState'],j['state'],j['datePrecision'],j['dates'])==(event['id'],event['title'],event['year'],event['year'],2,'partial','held',event['date_precision'],event['date_display'])
    assert len(j['venues'])==1 and len(j['participants'])==2
    v=j['venues'][0]
    assert (v['id'],v['institution_id'],v['name'],v['city'],v['country'],v['start_date'],v['end_date'])==(event['occurrence_id'],m.MID,'National Gallery — '+event['room'],'London','United Kingdom',event['start'],event['end'])
    assert {x['artist_id'] for x in j['participants']}=={x['artist_id'] for x in event['participants']}
    eu=u+'/entries?limit=20';er=requests.get(eu,timeout=(15,45));er.raise_for_status();ej=er.json();c.save(R/(event['native_id'].replace('/','-')+'-entries.json'),ej)

    items=ej['items']
    assert len(items)==2
    for x in event['entries']:
        item=next(i for i in items if i['id']==x['id'])
        assert item['artworkId']==x['artwork_id'] and item['participation']=='exhibited'
        assert item['evidence']['inventory']==x['inventory'] and item['evidence']['plan_sha256']==pin
        assert item['title']==x['title'] and item['creator']==x['creator'] and item['catalogueNumber'] is None
        image_path=item.get('image')
        if image_path:images[image_path]=x['artwork_id']
    receipts.append(dict(url=u,status=r.status_code,body_sha256=c.sha(r.content),entries_url=eu,entries_status=er.status_code,entries_sha256=c.sha(er.content),event_id=event['id'],exact_entries=2,venue_and_artist_relationships_verified=True))
if not (E/'independent-public-verification.json').exists():
    c.save(E/'independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=receipts,source_date_qualifications_preserved=True,partial_checklists_verified=True,exact_existing_work_links_verified=True,passed=True))
print(json.dumps(dict(verified_counts=counts,image_paths=images),ensure_ascii=False))
