#!/usr/bin/env python3
"""Reviewed AIC historical exhibition metadata and exact existing-object links.

Discovery is deliberately broader than delivery. No new main-catalogue objects,
images, local database writes, inferred checklists or unverified document types.
"""
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

from psycopg.types.json import Jsonb
import requests
import historical_exhibitions_aic_archive_20261012 as a
import exhibitions_common as c

OUT=a.OUT
OP='historical-exhibitions-aic-reviewed-20261012'
PLAN=OUT/'delivery-plan.json'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/aic-exhibitions'
SEURAT='08df474b-17da-548e-9cf5-5079333375d1'
TABLES=['exhibitions','exhibition_occurrences','exhibition_entries','exhibition_participants','exhibition_source_records','exhibition_publications']
EXISTING={4017:SEURAT}
RELEASE={
    3747:'Cezanne retrospective travels Chicago to Metropolitan Museum in February–May 1952. Existing Minneapolis Watercolors by the Masters: Durer to Cezanne is a different multi-artist exhibition; source titles, venues and object histories reviewed.',
    3781:'1952 Chicago Contemporary Drawings from 12 Countries is distinct from Cleveland Contemporary Drawings of January–February 1950; periods, venues and scope reviewed.',
    3989:'Chicago April 1957 Monet display is separately listed before the St. Louis/Minneapolis loan exhibition in native object 81537 history. No catalogue versus numbered loan catalogue; separate event identities retained.',
    8557:'Chicago Gallery 13 Homer-only display, October–December 1944, is distinct from Walker-organized American Watercolor and Winslow Homer, 1945, documented in the CMA record with Detroit/Brooklyn/Walker stops and a Hopper loan. No touring equivalence established; native Homer histories identify the Chicago display separately.'}
MANUAL_HOLD={
    4696:'Possible existing 1966 Miss Mary Cassatt exhibition; reconcile title variants before counting another event.',
    4109:'Possible existing 1960 Work of Camille Corot; title variants require reconciliation.',
    6176:'Existing 1970–1971 Painting in Italy in the Eighteenth Century, Rococo to Romanticism may be the full tour.',
}
DATE_REVIEW={
    4456:'Museum index ends 1 August 1910; object histories range from August to November. Keep 10 May opening and 1910 ending year; exact closing day withheld.',
    5255:'Museum index ends 1 June 1924; native object 4749 history ends 1 July. Keep 14 April opening and 1924 ending year; exact closing day withheld.',
    4731:'Museum index says 6 April–3 May 1915; object 71583 history says 8–28 April. Preserve 1915 only in date fields until original catalogue review.',
    7218:'Museum index ends 4 March 1941; object 16367 history ends 2 March. Keep 30 January opening and 1941 ending year; exact closing day withheld.',
    3989:'Museum index ends 30 April 1957; 25 native object histories end 15 June. Keep 1 April opening and 1957 ending year; exact closing day withheld.',
    3747:'Index and eight object histories support Chicago 7 February–16 March 1952; object 14561 alone says 16 April, overlapping the New York stop. Retain the explicit event-index closing date with the isolated conflict in evidence. Tour continues to Metropolitan Museum 4 April–18 May, as explicitly recorded in several object histories.',
}
QUALIFIED=re.compile(r'\b(workshop|follower|circle|after|attributed|school|anonymous|unknown)\b',re.I)


def normal(v):return json.loads(json.dumps(v,default=str))


def pins():
    names=['exhibitions.json.gz','scope-discovery-v2.json','rare-token-duplicate-candidates.json','exact-history-candidates.json.gz','history-artwork-audit.json','target-duplicate-review.json']
    result={name:c.sha((OUT/name).read_bytes())for name in names}
    summary=c.load(c.ROOT/'docs/research/million-catalogue-20261010/aic/dataset-summary.json')
    result['objectJSONLSHA256']=c.sha(a.OBJECTS.read_bytes())
    assert result['objectJSONLSHA256']==summary['files']['artworks']['sha256']
    assert c.load(a.RECEIPT)['sha256']==summary['source_archive_sha256']
    return result


def plan():
    pin=pins();scope=c.load(OUT/'scope-discovery-v2.json');raw={r['data']['id']:r for r in c.load(OUT/'exhibitions.json.gz')['records']}
    duplicates={r['nativeID']:r for r in scope['duplicateCandidates']}
    rare={r['nativeID']:r for r in c.load(OUT/'rare-token-duplicate-candidates.json')}
    records=[];decisions=[]
    for r in scope['selected']:
        native=r['nativeID'];reason=MANUAL_HOLD.get(native)
        if native not in RELEASE and native not in EXISTING:
            if native in duplicates or native in rare:reason=reason or 'Possible source duplicate or touring relation held for individual reconciliation.'
        if (dt.date.fromisoformat(r['last'])-dt.date.fromisoformat(r['first'])).days>250:reason='Unusually long source period: possible year error or permanent-display record; date review required.'
        if reason:decisions.append(dict(nativeID=native,action='held',reason=reason));continue
        eid=EXISTING.get(native)or c.uid(OP+'/event/'+str(native))
        first=r['first'];last=r['last'];precision='day';display=first+' – '+last
        if native in DATE_REVIEW and native!=3747:
            last=None;precision='mixed';display=first+' – '+r['last'][:4]+' (closing date disputed)'
            if native==4731:first=None;precision='year';display='1915 (exact dates disputed)'
        records.append(dict(nativeID=native,id=eid,new=native not in EXISTING,title=r['title'],startDate=first,endDate=last,
            year=int(r['first'][:4]),endYear=int(r['last'][:4]),datePrecision=precision,dateDisplay=display,
            chicagoStartDate=first,chicagoEndDate=last,chicagoDateDisplay=display,
            sourceID=c.uid(OP+'/source/exhibition/'+str(native)),occurrenceID=c.uid(OP+'/occurrence/chicago/'+str(native)),
            archiveMember=raw[native]['archiveMember'],recordSHA256=raw[native]['recordSHA256'],source=raw[native]['data'],
            duplicateReview=RELEASE.get(native)or ('Explicit native object histories identify Chicago then MoMA as one tour. Add Chicago occurrence to the existing event.'if native in EXISTING else'No unresolved candidate from full same-period title, occurrence and rare-token comparisons.'),
            dateReview=DATE_REVIEW.get(native),extraOccurrences=[]))
        decisions.append(dict(nativeID=native,action='new_event'if native not in EXISTING else'enrich_existing',reason=records[-1]['duplicateReview']))
    byevent={r['nativeID']:r for r in records};audit=c.load(OUT/'history-artwork-audit.json')
    bynative=collections.defaultdict(set);works={r['id']:r for r in audit['artworks']}
    for r in audit['external']:bynative[r['external_id']].add(r['entity_id'])
    entries=[];held=[];seen=set()
    for row in c.load(OUT/'exact-history-candidates.json.gz')['candidates']:
        native=row['nativeID'];event=byevent.get(row['exhibitionNativeID']);o=row['object'];reason=None
        if not event:reason='Exhibition remains held; no participation claim imported.'
        elif re.search(r'\b(possibl[ey]|probably|may have|not exhibited|not shown|withdrawn|cancelled|discussed only)\b',row['history'],re.I):reason='Participation is qualified or negative; requires individual evidence review.'
        elif len(bynative[str(native)])!=1:reason='No unique existing native museum-object match; reconcile before adding main-catalogue records.'
        elif o.get('date_start') and o['date_start']>event['year']:reason='Object creation postdates the documented exhibition.'
        elif o.get('date_end') and o['date_end']>1970:reason='Source creation range exceeds catalogue cutoff; no automatic eligibility.'
        if reason:held.append(dict(exhibitionNativeID=row['exhibitionNativeID'],nativeID=native,title=o['title'],history=row['history'],reason=reason));continue
        aid=next(iter(bynative[str(native)]));w=works[aid]
        if w['accession_number']!=o['main_reference_number']or w['current_institution_id']!=a.MID:
            held.append(dict(exhibitionNativeID=row['exhibitionNativeID'],nativeID=native,reason='Accession or museum cross-check is missing or conflicts; retain for individual identity review.'));continue
        if w['status']=='archived'or w['work_type']not in ['painting','drawing','print','icon']:
            held.append(dict(exhibitionNativeID=row['exhibitionNativeID'],nativeID=native,reason='Existing work is archived or has a conflicting type.'));continue
        if w['creation_year_start'] and w['creation_year_start']>event['year']:
            held.append(dict(exhibitionNativeID=row['exhibitionNativeID'],nativeID=native,reason='Catalogue creation date conflicts with event.'));continue
        key=(event['id'],aid)
        if key in seen:continue
        seen.add(key)
        nums=re.findall(r'\b(?:cat\.?\s*(?:no\.?)?|no\.?)\s*(\d{1,4}(?:-?[a-z])?)\b',row['history'],re.I)
        # Ambiguous alternatives and multi-exhibition paragraphs keep no number.
        number=nums[0]if len(nums)==1 else None
        entries.append(dict(**row,id=c.uid(OP+'/entry/'+str(row['exhibitionNativeID'])+'/'+str(native)),artworkID=aid,
            exhibitionID=event['id'],occurrenceID=event['occurrenceID'],catalogueNumber=number,
            sourceID=c.uid(OP+'/source/object/'+str(row['exhibitionNativeID'])+'/'+str(native)),before=w,
            artistLinks=[r for r in audit['artists']if r['artwork_id']==aid],
            numberReview='Multiple catalogue references preserved without selecting a number.'if len(nums)>1 else None))
    with c.connect()as db:
        before={t:normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s ORDER BY id',(SEURAT,)).fetchall())for t in TABLES}
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(SEURAT,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone()
        before_count=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
        # Bound the institution lookup and preserve a label if none matches.
        met=normal(db.execute("SELECT id,name FROM institutions WHERE name IN ('The Metropolitan Museum of Art','Metropolitan Museum of Art')").fetchall())
    existing_pairs={(r['exhibition_id'],r['artwork_id'])for r in before['exhibition_entries']if r['artwork_id']}
    entries=[r for r in entries if (r['exhibitionID'],r['artworkID'])not in existing_pairs]
    existing_people={(r['exhibition_id'],r['artist_id'])for r in before['exhibition_participants']if r['artist_id']}
    participants={}
    for r in entries:
        if QUALIFIED.search(r['object'].get('artist_title')or''):continue
        for link in r['artistLinks']:
            key=(r['exhibitionID'],link['artist_id'])
            if key in existing_people or link['attribution_role']!='primary'or link['artist_status']=='archived':continue
            if key not in participants:participants[key]=dict(exhibitionID=r['exhibitionID'],artistID=link['artist_id'],name=link['display_name'],sourceID=r['sourceID'],artworkIDs=[])
            participants[key]['artworkIDs'].append(r['artworkID'])
    for r in records:
        if r['nativeID']==3747:
            proof=next(e for e in entries if e['exhibitionNativeID']==3747 and e['nativeID']in [101509,111436,16487,25838,62371])
            r['extraOccurrences']=[dict(id=c.uid(OP+'/occurrence/met/3747'),institutionID=met[0]['id']if len(met)==1 else None,
                venue='The Metropolitan Museum of Art',city='New York',first='1952-04-04',last='1952-05-18',sourceID=proof['sourceID'],history=proof['history'])]
            r['endDate']='1952-05-18';r['dateDisplay']=r['startDate']+' – 1952-05-18'
        if r['nativeID']==4017:
            old=before['exhibitions'][0];assert old['start_date']=='1958-03-24'and old['end_date']=='1958-05-11'
            r['endDate']=old['end_date'];r['dateDisplay']=r['startDate']+' – '+old['end_date']
        r['entries']=[e['id']for e in entries if e['exhibitionID']==r['id']]
    assert len({r['id']for r in records})==len(records)
    p=dict(at=c.now(),operation=OP,sourcePins=pin,archiveReceipt=c.load(a.RECEIPT),records=records,entries=entries,participants=list(participants.values()),
        decisions=decisions,heldEntries=held,beforeExisting=before,beforeActive=before_count,
        sourceScope='Museum Closed exhibition index; explicitly pictorial historical events. Through-1970 event subset reviewed here; remaining 1971–1989/mixed/unclear candidates remain pending, not rejected as universally out of scope.',
        mainCatalogueWrites=False,newImages=0,realLocalDatabaseWrites=False)
    p['counts']=dict(newEvents=sum(r['new']for r in records),enrichedEvents=sum(not r['new']for r in records),
        occurrences=sum(1+len(r['extraOccurrences'])for r in records),newEntries=len(entries),linkedWorks=len({r['artworkID']for r in entries}),
        illustratedConnections=sum(bool(r['before']['primary_media_id'])for r in entries),participants=len(participants),
        sources=len(records)+len(entries),eventsWithEntries=sum(bool(r['entries'])for r in records),heldEvents=len([r for r in decisions if r['action']=='held']))
    c.save(PLAN,p);c.save(BACKUP/'preimage.json.gz',p)
    print(json.dumps(p['counts']),flush=True)


def apply():
    p=c.load(PLAN);assert p['sourcePins']==pins()and c.load(BACKUP/'preimage.json.gz')==p
    plan_sha=c.sha(PLAN.read_bytes());receipt=p['archiveReceipt'];expected={r['artworkID']:r['before']for r in p['entries']}
    evidence_base=dict(operation=OP,planSHA256=plan_sha,archiveReceipt=receipt,scope=p['sourceScope'],checklistComplete=False,holdingClaim=False,currentDisplayClaim=False)
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not db.execute('SELECT 1 FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(SEURAT,)).fetchone()
        for t in TABLES:
            rows=normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s ORDER BY id'+(' FOR UPDATE'if t=='exhibitions'else''),(SEURAT,)).fetchall())
            assert rows==p['beforeExisting'][t],t
        rows=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall());assert {r['id']:r for r in rows}==expected
        # Check exact title/year identities again immediately before mutation.
        current={(r['start_year'],c.norm(r['title']))for r in db.execute('SELECT title,start_year FROM exhibitions WHERE start_year BETWEEN 1885 AND 1970').fetchall()}
        assert not [(r['nativeID'],r['title'])for r in p['records']if r['new']and(r['year'],c.norm(r['title']))in current]
        with db.pipeline():
            for r in p['records']:
                if r['new']:
                    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical',%s,'review',%s)",
                        (r['id'],r['title'],c.norm(r['title']),r['startDate'],r['endDate'],r['year'],r['endYear'],r['dateDisplay'],r['datePrecision'],
                         'Official museum archive records a Closed historical exhibition with dated occurrence; unresolved date conflicts retained in source evidence.','partial'if r['entries']else'unknown',OP))
                else:
                    db.execute("UPDATE exhibitions SET start_date=%s,start_year=%s,end_date=%s,end_year=%s,date_display=%s,checklist_state='partial',updated_at=now() WHERE id=%s",
                        (r['startDate'],r['year'],r['endDate'],r['endYear'],r['dateDisplay'],r['id']))
                ev=evidence_base|dict(nativeExhibitionID=r['nativeID'],archiveMember=r['archiveMember'],recordSHA256=r['recordSHA256'],duplicateReview=r['duplicateReview'],dateReview=r['dateReview'],documentIDsUnreviewed=r['source']['document_ids'])
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (r['sourceID'],r['id'],OP,'exhibition/'+str(r['nativeID']),r['source']['api_link'],receipt['retrieved_at'],str(OUT/'exhibitions.json.gz'),p['sourcePins']['exhibitions.json.gz'],Jsonb(r['source']),Jsonb(ev)))
                db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,source_venue_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (r['occurrenceID'],r['id'],r['sourceID'],a.MID,str(r['source']['gallery_id'])if r['source']['gallery_id']else None,'Art Institute of Chicago','Chicago','United States','US',r['chicagoStartDate'],r['chicagoEndDate'],r['chicagoDateDisplay'],Jsonb(ev)))
            for r in p['entries']:
                o=r['object'];ev=evidence_base|dict(exactHistory=r['history'],nativeObjectID=r['nativeID'],nativeExhibitionID=r['exhibitionNativeID'],archiveMember=r['archiveMember'],recordSHA256=r['recordSHA256'],numberReview=r['numberReview'],catalogueMetadataPreserved=True)
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (r['sourceID'],r['exhibitionID'],OP,'object/'+str(r['exhibitionNativeID'])+'/'+str(r['nativeID']),o['api_link'],receipt['retrieved_at'],str(a.OBJECTS),p['sourcePins']['objectJSONLSHA256'],Jsonb({k:o.get(k)for k in ['id','title','artist_title','artist_display','main_reference_number','date_display','date_start','date_end','medium_display','dimensions','artwork_type_title','exhibition_history']}),Jsonb(ev)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",
                    (r['id'],r['exhibitionID'],r['sourceID'],r['occurrenceID'],r['artworkID'],str(r['nativeID']),r['catalogueNumber'],o['title'],o.get('artist_display')or o.get('artist_title'),o.get('date_display'),o.get('medium_display'),o.get('dimensions'),Jsonb(ev),
                     'Exact museum native ID and accession in the existing catalogue. Official object exhibition history identifies the reviewed event; participation tied to the documented Chicago occurrence, not inferred for every tour stop.'))
            for r in p['records']:
                for o in r['extraOccurrences']:
                    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (o['id'],r['id'],o['sourceID'],o['institutionID'],o['venue'],o['city'],'United States','US',o['first'],o['last'],o['first']+' – '+o['last'],Jsonb(evidence_base|dict(exactTourHistory=o['history'],allObjectsAtThisStopNotInferred=True))))
            for r in p['participants']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                    (c.uid(OP+'/participant/'+r['exhibitionID']+'/'+r['artistID']),r['exhibitionID'],r['sourceID'],r['artistID'],r['name'],Jsonb(evidence_base|dict(basis='Existing unqualified primary creator links of exact exhibited objects',artworkIDs=r['artworkIDs']))))
            db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,1883,1989,'partial',%s)",
                (c.uid(OP+'/coverage'),a.MID,OP,'https://api.artic.edu/docs/',Jsonb(evidence_base|dict(sourceRecords=6259,historicalDateCandidates=4065,delivery=p['counts'],remaining='Mixed/non-pictorial ambiguity, post-1970 content review, duplicate/tour identities, date conflicts, full original checklists and image gaps.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),operation=OP,counts=p['counts'],planSHA256=plan_sha,newArtworks=0,newImages=0,realLocalDatabaseWrites=False))
    print('Committed',json.dumps(p['counts']),flush=True)


def verify():
    p=c.load(PLAN);events={r['id']:r for r in p['records']};expected={r['artworkID']:r['before']for r in p['entries']}
    reconciliation=c.load(OUT/'seurat-participant-reconciliation.json')if (OUT/'seurat-participant-reconciliation.json').exists()else None
    with c.connect()as db:
        current=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall());assert {r['id']:r for r in current}==expected
        rows=normal(db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[])',(list(events),)).fetchall());assert len(rows)==len(events)
        for r in rows:
            e=events[r['id']];assert r['start_date']==e['startDate']and r['end_date']==e['endDate']and r['start_year']==e['year']and r['end_year']==e['endYear']
            assert r['status']=='review'and r['event_state']=='held'
        entries=normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([r['id']for r in p['entries']],)).fetchall());assert len(entries)==len(p['entries'])
        assert {(r['id'],r['artwork_id'],r['occurrence_id'],r['participation'])for r in entries}=={(r['id'],r['artworkID'],r['occurrenceID'],'exhibited')for r in p['entries']}
        counts={t:db.execute('SELECT count(*) n FROM '+t+' WHERE '+('import_batch'if t=='exhibitions'else'source_key')+'=%s',(OP,)).fetchone()['n']for t in ['exhibitions','exhibition_source_records']}
        assert counts['exhibitions']==p['counts']['newEvents']and counts['exhibition_source_records']==p['counts']['sources']
        active=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n'];assert active==p['beforeActive']+p['counts']['newEvents']
        selected=next(r for r in p['records']if r['nativeID']==6157)
        query_plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id LIMIT 101',(selected['id'],)).fetchone()
        for table in TABLES[1:]:
            old=p['beforeExisting'][table]
            if old:
                cur=normal(db.execute('SELECT * FROM '+table+' WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in old],)).fetchall())
                if reconciliation and table=='exhibition_participants':
                    for now,then in zip(cur,old):
                        if now['id']==reconciliation['existingParticipantResolved']:
                            assert now['artist_id']==reconciliation['canonicalArtistID']
                            assert all(now[k]==v for k,v in then.items()if k not in ['artist_id','evidence'])
                            assert all(now['evidence'].get(k)==v for k,v in then['evidence'].items())
                        else:assert now==then
                else:assert cur==old,table
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions';checked=[]
    for e in p['records']:
        if not e['entries']:continue
        items=[];after=''
        for _ in range(20):
            response=requests.get(api+'/'+e['id']+'/entries',params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];after=data.get('nextCursor')or''
            if not after:break
        assert not after;by={r['id']:r for r in items}
        wanted=[r for r in p['entries']if r['exhibitionID']==e['id']]
        for r in wanted:assert by[r['id']]['artworkId']==r['artworkID']and by[r['id']]['participation']=='exhibited'
        illustrated=sum(bool(by[r['id']].get('image'))for r in wanted)
        assert illustrated==sum(bool(r['before']['primary_media_id'])for r in wanted)
        checked.append(dict(id=e['id'],nativeID=e['nativeID'],newEntries=len(wanted),illustrated=illustrated))
    for r in [p['entries'][0],p['entries'][-1]]:
        response=requests.get(api,params=dict(artwork=r['artworkID'],limit=100),timeout=40);response.raise_for_status();assert r['exhibitionID']in {e['id']for e in response.json()['items']}
    dest=OUT/('verified-after-participant-reconciliation.json'if reconciliation else'verified.json')
    c.save(dest,dict(at=c.now(),counts=p['counts'],activeEvents=active,mainArtworkRecordsPreserved=True,existingSeuratChildRecordsPreserved=not bool(reconciliation),seuratParticipantReconciliation=reconciliation,
        apiEntryChecks=checked,allNewEntryLinksAndImagesVerified=True,reverseSamplesVerified=2,queryPlan=query_plan,
        imageGapConnections=p['counts']['newEntries']-p['counts']['illustratedConnections'],newArtworks=0,newImages=0,realLocalDatabaseWrites=False))
    print('Verified',active,'active events;',sum(r['newEntries']for r in checked),'exact new links;',sum(r['illustrated']for r in checked),'illustrated connections.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply','verify']:raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
