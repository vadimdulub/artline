#!/usr/bin/env python3
"""Exact 1933 Chicago links from the pinned official object-history archive.

The 1934 edition, other World's Fair shows, and nonpictorial objects are distinct.
Original catalogue OCR remains an unreviewed research aid, not import authority.
"""
import collections
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/chicago-1933'
EID='2cd58f72-a7e7-5e46-8018-5b208f0c70e4'
MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3'
OP='historical-exhibition-chicago-aic-20261012'
ACTOR='local-european-research'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/chicago-1933'
TABLES=['exhibitions','exhibition_entries','exhibition_participants','exhibition_occurrences','exhibition_source_records','exhibition_publications']
HOLD={
    '217201':'Object creation is 1945, after this exhibition. Museum exhibition-history assignment conflicts with chronology; no link.',
    '13745':'Printed page 62, no. 459 is Herself. Himself is mentioned only as its companion in the collection. Printed page 63 starts no. 460, The Herring Net. No exhibited claim.'}
CORRECTIONS={
    '16362':('166e',26,'Museum history repeats 166-d; visually reviewed printed page 26 assigns Margato Shot to 166e.'),
    '16837':('907',93,'Museum history says 901; visually reviewed printed page 93 identifies Tynemouth Priory as 907. No. 901 is Prout’s Neck, Breakers.'),
    '31749':('1032',101,'Museum history says 1033; visually reviewed printed page 101 identifies Girl with Cat as 1032. No. 1033 is Woman Nursing Knee—A Foot.'),
    '25865':('460',63,'Museum history leaves catalogue number blank; visually reviewed printed page 63 supplies The Herring Net, no. 460.'),
    '65353':('467',63,'Museum history leaves catalogue number blank; visually reviewed printed page 63 supplies The Storm, no. 467.'),
    '65709':('488',66,'Museum history leaves catalogue number blank; visually reviewed printed page 66 supplies The Artist in the Studio, no. 488.')}
QUALIFIED=re.compile(r'\b(?:workshop|follower|circle|after|attributed|school)\b',re.I)


def evidence_pins():
    base=c.ROOT/'docs/research/million-catalogue-20261010'
    summary=c.load(base/'aic/dataset-summary.json');archive=c.load(base/'sources/aic/api-data.tar.bz2.receipt.json')
    candidates=c.load(OUT/'aic-century-history-candidates.json')
    assert candidates['sourceSHA256']==summary['files']['artworks']['sha256']
    assert c.sha(Path(candidates['source']).read_bytes())==candidates['sourceSHA256']
    assert summary['source_archive_sha256']==archive['sha256']and archive['status']==200
    scan=c.load(OUT/'catalogueofcentu00arti.pdf.receipt.json')
    assert scan['status']==200 and c.sha((OUT/'catalogueofcentu00arti.pdf').read_bytes())==scan['sha256']
    return dict(archive=archive,jsonlSHA256=candidates['sourceSHA256'],scan=scan)


def plan():
    pins=evidence_pins();audit=c.load(OUT/'aic-existing-artwork-audit-v2.json')
    raw={str(r['data']['id']):r for r in c.load(OUT/'aic-century-history-candidates.json')['candidates']}
    artworks={r['id']:r for r in audit['artworks']};by=collections.defaultdict(set)
    for r in audit['external']:by[r['external_id']].add(r['entity_id'])
    chosen=[];held=[]
    for row in c.load(OUT/'aic-1933-history-draft.json'):
        native=str(row['id']);r=raw[native];o=r['data'];reason=HOLD.get(native)
        if o.get('artwork_type_title')not in ['Painting','Drawing and Watercolor','Print']:reason='Outside selected pictorial medium scope or a distinct Worlds Fair exhibition'
        elif len(row['hits'])!=1:reason='Ambiguous event-history segmentation'
        elif not re.search(r'Art Institute|Institute of Chicago',row['hits'][0],re.I):reason='Distinct venue or unresolved exhibition identity'
        elif len(by[native])!=1:reason='No unique existing internal native-ID match; further catalogue reconciliation required'
        if reason:held.append(dict(nativeID=native,title=row['title'],reason=reason,histories=row['hits']));continue
        aid=next(iter(by[native]));a=artworks[aid];history=row['hits'][0]
        assert a['accession_number']==o['main_reference_number'] and a['current_institution_id']==MID
        assert a['status']!='archived'and a['work_type']in ['painting','drawing','print']
        assert a['creation_year_start']is None or a['creation_year_start']<=1933
        numbers=re.findall(r'\b(?:cat\.?\s*(?:no\.?)?|no\.?)\s*(\d{1,4}(?:-?[a-z])?)\b',history,re.I)
        assert len(numbers)<=1,(native,numbers)
        number=numbers[0].replace('-','')if numbers else None
        page=re.search(r'\bp\.\s*(\d+)\b',history);page=int(page[1])if page else None
        correction=None
        if native in CORRECTIONS:number,page,correction=CORRECTIONS[native]
        if number:assert 1<=int(re.match(r'\d+',number)[0])<=1094
        links=[x for x in audit['artists']if x['artwork_id']==aid]
        note=None
        if native=='81537':note='Historical title Antibes, no. 290A, is preserved as evidence. Printed page 43 (visually reviewed) gives signed 1884, Potter Palmer collection and approximately 25.5 x 32 inches; official native object and publication history explicitly identify this third-edition entry as Bordighera. No modern title/date changes.'
        if native=='34698':note='Historical title Musical Instruments (cubist), 1916, is preserved. Printed page 102 (visually reviewed) gives a small watercolor; official publication history also cites Barr 1946 under Musical Instruments. Current museum title Woman in an Armchair is retained.'
        if number and number.startswith('166'):note=(note or '')+' The six native Goya panels remain separate works. Their source historical titles and oil-on-canvas description differ from modern titles and oil-on-panel metadata; modern object facts remain unchanged.'
        chosen.append(dict(nativeID=native,id=aid,before=a,artistLinks=links,object=o,archiveMember=r['archive_member'],recordSHA256=r['record_sha256'],
            history=history,catalogueNumber=number,printedPage=page,correction=correction,identityNote=note,
            sourceID=c.uid(OP+'/source/'+native),entryID=c.uid(OP+'/entry/'+native),
            matchBasis='Exact museum native object ID and accession number in the existing catalogue; official object exhibition history explicitly identifies the Art Institute 1933 event. Source conflicts and later attributions retained without changing artwork metadata.'))
    assert len({r['id']for r in chosen})==len(chosen)
    counts=collections.Counter(r['catalogueNumber']for r in chosen if r['catalogueNumber'])
    assert all(n==1 for n in counts.values()),counts
    participants={}
    existing={r['artist_id']for r in audit['event']['exhibition_participants']if r['artist_id']}
    for r in chosen:
        if QUALIFIED.search(r['object'].get('artist_title')or''):continue
        for link in r['artistLinks']:
            if link['attribution_role']!='primary'or link['artist_status']=='archived'or link['artist_id']in existing:continue
            if link['artist_id']not in participants:participants[link['artist_id']]=dict(artistID=link['artist_id'],name=link['display_name'],sourceID=r['sourceID'],artworkIDs=[])
            participants[link['artist_id']]['artworkIDs'].append(r['id'])
    p=dict(at=c.now(),operation=OP,exhibitionID=EID,sourcePins=pins,auditSHA256=c.sha((OUT/'aic-existing-artwork-audit-v2.json').read_bytes()),
        beforeEvent=audit['event'],records=chosen,held=held,participants=list(participants.values()),
        dateReview='Existing 1 June–1 November 1933 dates agree with the original title page and CMA record. Some current AIC object histories give 23 May–31 October or 23 May–1 November. Preserve all literal variants in evidence; do not overwrite event dates from conflicting object summaries.',
        labelPolicy='Entry titles, creators and creation dates use current official object metadata; historical titles and attributions remain in the verbatim exhibition history. No lifetime bounds inferred as creation dates.',
        checklistState='partial',newEvents=0,newArtworks=0,newEntries=len(chosen),alreadyIllustrated=sum(bool(r['before']['primary_media_id'])for r in chosen),
        qualifiedAttributionObjects=sum(bool(QUALIFIED.search(r['object'].get('artist_title')or''))for r in chosen),realLocalDatabaseWrites=False)
    c.save(OUT/'aic-delivery-plan.json',p);c.save(BACKUP/'aic-link-preimage.json.gz',p)
    print(json.dumps({k:p[k]for k in ['newEntries','alreadyIllustrated','qualifiedAttributionObjects']}|dict(newParticipants=len(participants),held=len(held))),flush=True)


def normal(v):
    return json.loads(json.dumps(v,default=str))


def audit():
    rows=c.load(OUT/'aic-1933-history-draft.json');ids=[str(r['id'])for r in rows];out={}
    with c.connect()as db:
        out['columns']={t:db.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",(t,)).fetchall()for t in ['exhibition_entries','exhibition_publications','exhibition_participants','exhibition_source_records']}
        out['external']=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme=ANY(%s)",(ids,['aic-object','european-chicago-art-institute-of-chicago-object'])).fetchall()
        aids=list(set(r['entity_id']for r in out['external']))
        out['artworks']=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(aids,)).fetchall()
        out['artists']=db.execute('SELECT aa.*,a.display_name,a.slug,a.birth_year,a.death_year,a.status artist_status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(aids,)).fetchall()
        out['media']=db.execute('SELECT * FROM media_assets WHERE id=ANY(%s::uuid[])',([r['primary_media_id']for r in out['artworks']if r['primary_media_id']],)).fetchall()
        out['event']={t:db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s',(EID,)).fetchall()for t in TABLES}
    c.save(OUT/'aic-existing-artwork-audit-v2.json',out)
    print(json.dumps(dict(externalSchemes=collections.Counter(r['scheme']for r in out['external']),artworks=len(out['artworks']),illustrated=len(out['media']),types=collections.Counter(r['work_type']for r in out['artworks'])),default=str),flush=True)


def apply():
    p=c.load(OUT/'aic-delivery-plan.json');pin=c.sha((OUT/'aic-delivery-plan.json').read_bytes())
    assert evidence_pins()==p['sourcePins']and c.load(BACKUP/'aic-link-preimage.json.gz')==p
    assert c.sha((OUT/'aic-existing-artwork-audit-v2.json').read_bytes())==p['auditSHA256']
    ids=[r['id']for r in p['records']];wanted={r['id']:r['before']for r in p['records']}
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        for t in TABLES:
            current=normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=%s'+(' FOR UPDATE'if t=='exhibitions'else''),(EID,)).fetchall())
            assert sorted(current,key=lambda r:r['id'])==sorted(p['beforeEvent'][t],key=lambda r:r['id']),t
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=%s',(EID,)).fetchone(),'Separate projection requires atomic reconciliation'
        current=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR SHARE',(ids,)).fetchall())
        assert {r['id']:r for r in current}==wanted
        for r in p['records']:
            o=r['object'];url='https://www.artic.edu/artworks/'+r['nativeID']
            evidence=dict(operation=OP,planSHA256=pin,exactHistory=r['history'],catalogueNumberCorrection=r['correction'],identityNote=r['identityNote'],
                dateReview=p['dateReview'],labelPolicy=p['labelPolicy'],museumObjectID=r['nativeID'],accessionNumber=o['main_reference_number'],
                archiveMember=r['archiveMember'],recordSHA256=r['recordSHA256'],archiveReceipt=p['sourcePins']['archive'],jsonlSHA256=p['sourcePins']['jsonlSHA256'],
                scanReceipt=p['sourcePins']['scan'],metadataPreserved=True)
            payload={k:o.get(k)for k in ['id','title','artist_title','artist_display','main_reference_number','date_display','medium_display','dimensions','artwork_type_title','exhibition_history']}
            db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (r['sourceID'],EID,OP,r['nativeID']+'/1933',url,p['sourcePins']['archive']['retrieved_at'],str(OUT/'aic-century-history-candidates.json'),c.sha((OUT/'aic-century-history-candidates.json').read_bytes()),Jsonb(payload),Jsonb(evidence)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,source_page,evidence,match_basis)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s,%s)",
                (r['entryID'],EID,r['sourceID'],r['id'],r['nativeID'],r['catalogueNumber'],o['title'],o.get('artist_title')or o.get('artist_display'),o.get('date_display'),o.get('medium_display'),o.get('dimensions'),
                 'Official object exhibition history'+('; catalogue p. '+str(r['printedPage'])if r['printedPage']else''),Jsonb(evidence),r['matchBasis']))
        for r in p['participants']:
            db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                (c.uid(OP+'/participant/'+r['artistID']),EID,r['sourceID'],r['artistID'],r['name'],Jsonb(dict(operation=OP,planSHA256=pin,basis='Existing unqualified primary creator links for the exact historical objects; qualified source labels excluded from this canonical participant projection.',artworkIDs=r['artworkIDs']))))
        rc=p['sourcePins']['scan'];sid=c.uid(OP+'/source/catalogue')
        db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (sid,EID,OP,'catalogueofcentu00arti/1933','https://archive.org/details/catalogueofcentu00arti',rc['retrievedAt'],rc['path'],rc['sha256'],Jsonb(dict(edition='Third edition, fifth printing',year=1933,contributor='University of Illinois Urbana-Champaign',pdfPages=242)),
             Jsonb(dict(operation=OP,scanReceipt=rc,planSHA256=pin,checklistState='partial',ocrState='Unreviewed transcription candidates retained separately; not imported as verified catalogue entries',dateReview=p['dateReview']))))
        db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence)VALUES(%s,%s,%s,'catalogue',%s,%s,'1933',%s,'catalogueofcentu00arti','Paintings pp. 1–85; drawings, watercolours and pastels pp. 86–105',%s)",
            (c.uid(OP+'/publication'),EID,sid,'A Century of Progress: Exhibition of Paintings and Sculpture, Lent from American Collections — Third Edition (Fifth Printing)','Daniel Catton Rich (editor); Art Institute of Chicago','https://archive.org/details/catalogueofcentu00arti',Jsonb(dict(operation=OP,planSHA256=pin,scanReceipt=rc,excludedSection='Sculpture begins on printed page 106, catalogue no. 1095.'))))
    c.save(OUT/'aic-delivered.json',dict(at=c.now(),newEntries=len(ids),newArtistConnections=len(p['participants']),newSources=len(ids)+1,newPublications=1,newEvents=0,newArtworks=0,newImages=0,alreadyIllustrated=p['alreadyIllustrated'],planSHA256=pin,realLocalDatabaseWrites=False))
    print('Committed',len(ids),'exact native-object connections;',len(p['participants']),'canonical artist connections.',flush=True)


def verify():
    p=c.load(OUT/'aic-delivery-plan.json');expected={r['entryID']:r for r in p['records']};ids=[r['id']for r in p['records']]
    with c.connect()as db:
        assert normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone())==p['beforeEvent']['exhibitions'][0]
        rows=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall())
        before={r['id']:r['before']for r in p['records']}
        # Images may be delivered by the separate evidence-pinned image phase.
        permitted={'primary_media_id','updated_at','revision'}
        assert all({k:v for k,v in r.items()if k not in permitted}=={k:v for k,v in before[r['id']].items()if k not in permitted}for r in rows)
        qplan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id LIMIT 101',(EID,)).fetchone()
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions';items=[];after=''
    for _ in range(10):
        response=requests.get(api+'/'+EID+'/entries',params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json();items+=data['items'];after=data.get('nextCursor')or''
        if not after:break
    assert not after and len(items)==len(expected)+len(p['beforeEvent']['exhibition_entries'])
    by={r['id']:r for r in items};assert set(expected).issubset(by)
    for eid,r in expected.items():
        item=by[eid];assert item['artworkId']==r['id']and item['catalogueNumber']==r['catalogueNumber']and item['participation']=='exhibited'
    for r in [p['records'][0],p['records'][-1]]:
        response=requests.get(api,params=dict(artwork=r['id'],limit=100),timeout=40);response.raise_for_status();assert EID in {x['id']for x in response.json()['items']}
    delivered_images=any((OUT/folder/'delivered.json').exists()for folder in ['images','wikiart-images'])
    dest=OUT/('aic-verified-with-images.json'if delivered_images else'aic-verified.json')
    c.save(dest,dict(at=c.now(),newConnections=len(expected),totalEventEntries=len(items),illustratedEntries=sum(bool(r.get('image'))for r in items),
        allEntryIDsNumbersAndParticipationVerified=True,reverseSamplesVerified=2,eventDatesAndCatalogueMetadataPreserved=True,queryPlan=qplan,realLocalDatabaseWrites=False))
    print('Verified',len(items),'event entries;',sum(bool(r.get('image'))for r in items),'illustrated.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['audit','plan','apply','verify']:raise SystemExit('Use audit, plan, apply or verify')
    globals()[sys.argv[1]]()
