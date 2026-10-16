#!/usr/bin/env python3
"""One selected, exact Royal Academy 1769 painting and its Commons reproduction."""
import base64
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb

import exhibitions_common as c

OUT = Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/royal-academy/1769/regulus'
RA = OUT.parent
ACTOR = 'local-european-research'
OP = 'historical-exhibition-regulus-20261012'
AID = c.uid('artwork/royal-collection/405416')
ARTIST = '8fbc0aea-3170-4fee-bc0f-916987bc3186'
IID = '058a7b14-2d56-5a87-977d-9756f661f65f'
SID = c.uid('metadata-source/royal-collection-history-20261012')
COMMONS = 'de4bd5ae-b280-4e0f-ba55-d462f47613d9'
EID = c.uid('royal-academy/summer/1769')
ENTRY = c.uid('entry/royal-academy/1769/120')
HISTORY = 'https://www.rct.uk/collection/stories/george-iii-joseph-farington-and-the-royal-academy/the-departure-of-regulus'
OBJECT = 'https://www.rct.uk/collection/405416/the-departure-of-regulus'


def conflicts(db):
    identifiers = db.execute("SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikidata' AND external_id='Q28038182') OR canonical_url=ANY(%s))",([OBJECT,OBJECT.replace('www.rct.uk','www.royalcollection.org.uk')],)).fetchall()
    scoped = db.execute("SELECT a.id,a.title,a.accession_number FROM artworks a WHERE (a.current_institution_id=%s AND a.accession_number IN ('405416','RCIN 405416')) OR (a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s) AND a.normalized_title LIKE '%%regulus%%')",(IID,ARTIST)).fetchall()
    return dict(identifiers=identifiers,scoped=scoped)


def plan():
    im = c.load(OUT/'image-prepared.json')
    rc = c.load(OUT/'commons.html.receipt.json')
    assert c.sha((OUT/'commons.html').read_bytes()) == rc['sha256']
    text = BeautifulSoup((OUT/'commons.html').read_bytes(),'html.parser').get_text(' ',strip=True)
    assert all(t in text for t in ['405416','1769','Benjamin West','225.4','307.2','public domain'])
    with c.connect() as db:
        prior = conflicts(db)
        assert not prior['identifiers'] and not prior['scoped'], prior
        artist = db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(ARTIST,)).fetchone()
        assert artist['display_name']=='Benjamin West' and artist['birth_year']<=1769<=artist['death_year']
        institution = db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone()
        assert institution['name']=='Royal Collection' and institution['status']!='archived'
        entry = db.execute('SELECT * FROM exhibition_entries WHERE id=%s',(ENTRY,)).fetchone()
        assert entry['catalogue_number']=='120' and entry['artwork_id'] is None and entry['creator_label']=='Benjamin West'
        event = db.execute('SELECT * FROM exhibitions WHERE id=%s',(EID,)).fetchone()
        assert event['start_year']==1769 and event['start_date'] is None and event['end_date'] is None
        occurrence = db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(EID,)).fetchall()
        assert len(occurrence)==1
    page = BeautifulSoup((RA/'page.html').read_bytes(),'html.parser').get_text(' ',strip=True)
    assert '26 April' in page and '27 May' in page and 'Pall Mall' in page
    review = dict(at=c.now(),artworkID=AID,title='The Departure of Regulus',artistID=ARTIST,
        institutionID=IID,accession='RCIN 405416',date=1769,medium='Oil on canvas',
        dimensions='225.4 × 307.2 cm',sourcePage=OBJECT,historyPage=HISTORY,
        museumHistoryEvidence=dict(retrieval='Web reader response received before the direct HTTP access hold.',
            observedFacts=['Royal Collection object RCIN 405416.','Benjamin West; signed and dated 1769.','The museum explicitly places this painting at the first Royal Academy exhibition in 1769.'],
            sourceURL=HISTORY,directRetrieval=c.load(OUT/'royal-history.html.receipt.json'),
            caution='Direct HTTP 403 retained as an access hold, not a successful source capture. No retry or bypass. The prior public web-reader response and primary 1769 catalogue independently support the event connection.'),
        commonsReceipt=rc,rights=dict(status='public_domain',label='Public domain; PD-Art (PD-old-auto-expired); Public Domain Mark 1.0',
            policyURL='https://creativecommons.org/publicdomain/mark/1.0/',
            basis='Commons identifies a faithful two-dimensional reproduction of the 1769 painting and labels this exact file PD-Art. Artist died in 1820. Metadata CC0 is not used as an image licence.',
            embeddedCredit='Royal Collection Trust/© Her Majesty Queen Elizabeth II 2019',
            distinction='The embedded Royal Collection copyright credit is preserved separately from the Commons PD-Art assessment; no independent Royal Collection licence is asserted.'),
        image=im,mediaID=c.uid('image/royal-collection/405416/'+im['sha256']),
        imagePath='/assets/artworks/historical-exhibitions-20261012/'+AID+'-'+im['sha256'][:16]+'.jpg',
        visualReview=dict(originalViewed=True,derivativeViewed=True,objectIdentity='Same full composition and RCIN 405416; central departing Regulus, distraught family, classical columns. Not a later print, study, detail or the unrelated Italian-school Regulus painting.',confidence=.99),
        sourceCatalogue=dict(number='120',page='14',entryPlanSHA256=c.sha((RA/'continuation-entry-plan.json').read_bytes())),
        eventDates=dict(start='1769-04-26',end='1769-05-27',basis='Explicit 26 April — 27 May in the 1769 Chronicle year summary, not IIIF navDate.',receipt=c.load(RA/'page.html.receipt.json')),
        pinnedArtist=artist,pinnedInstitution=institution,pinnedEntry=entry,pinnedExhibition=event,pinnedOccurrence=occurrence[0],duplicateCheck=prior,
        authorization='Selected historical paintings, exact exhibition artwork connections and missing authentic images authorized by the user; review status retained, production delivery authorized. Real local catalogue read-only.')
    c.save(OUT/'delivery-plan.json',review)
    print('Prepared one exact new painting, one selected image, catalogue no. 120 and explicit event dates.',flush=True)


def upload():
    p=c.load(OUT/'delivery-plan.json');im=p['image'];raw=(OUT/'delivery.jpg').read_bytes()
    assert c.sha(raw)==im['sha256'] and len(raw)<=100000
    spec=importlib.util.spec_from_file_location('historical_image_core',Path(__file__).with_name('enrich-artwork-images.py'))
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    credentials=core.GcloudCredentials();credentials.refresh(None)
    blob=storage.Client(project='artline-508319',credentials=credentials).bucket('artline-508319-images').blob(p['imagePath'].lstrip('/'))
    blob.metadata={'sha256':im['sha256'],'operation':OP,'artwork-id':AID,'provider':'Wikimedia Commons'}
    blob.cache_control='public,max-age=31536000,immutable'
    try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
    except PreconditionFailed:blob.reload(timeout=30)
    assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
    response=requests.get('https://artlines.org'+p['imagePath'],timeout=(15,45));response.raise_for_status()
    assert c.sha(response.content)==im['sha256']
    c.save(OUT/'image-uploaded.json',dict(at=c.now(),generation=blob.generation,bytes=len(raw),sha256=im['sha256'],publicBytesVerified=True,planSHA256=c.sha((OUT/'delivery-plan.json').read_bytes())))
    print('One authentic image uploaded; public bytes verified.',flush=True)


def apply():
    p=c.load(OUT/'delivery-plan.json');im=p['image'];rights=p['rights'];pin=c.sha((OUT/'delivery-plan.json').read_bytes())
    assert c.load(OUT/'image-uploaded.json')['planSHA256']==pin
    with c.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert conflicts(db)==dict(identifiers=[],scoped=[])
        for query,arg,key in [
            ('SELECT * FROM exhibition_entries WHERE id=%s FOR UPDATE',ENTRY,'pinnedEntry'),
            ('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',EID,'pinnedExhibition'),
            ('SELECT * FROM exhibition_occurrences WHERE id=%s FOR UPDATE',p['pinnedOccurrence']['id'],'pinnedOccurrence'),
            ('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s FOR SHARE',ARTIST,'pinnedArtist'),
            ('SELECT id,name,status FROM institutions WHERE id=%s FOR SHARE',IID,'pinnedInstitution')]:
            assert json.loads(json.dumps(db.execute(query,(arg,)).fetchone(),default=str))==p[key],key
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,'royal-collection-exhibition-history-20261012','Royal Collection — historical exhibition object evidence','collection_page','https://www.rct.uk')",(SID,))
        db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,'1769',1769,1769,'exact','painting',%s,%s,%s,'review',true,%s,%s)",
            (AID,'the-departure-of-regulus-'+AID[:8],p['title'],c.norm(p['title']),p['medium'],p['dimensions'],p['accession'],ACTOR,ACTOR))
        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(AID,ARTIST,'Benjamin West: named by original catalogue no. 120, Royal Collection RCIN 405416 and exact Commons object record.'))
        for scheme,value,url in [('royal-collection','405416',OBJECT),('wikidata','Q28038182','https://www.wikidata.org/wiki/Q28038182')]:
            db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,%s,%s,%s,%s)",(c.uid('native/'+scheme+'/'+value),AID,scheme,value,url,SID))
        db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'historical_exhibition_object_identity','405416',%s,%s,%s,%s)",(c.uid(OP+'/citation'),AID,SID,HISTORY,json.dumps(p,ensure_ascii=False),p['at'],ACTOR))
        db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(c.uid(OP+'/holding'),AID,IID,SID,OBJECT,json.dumps(dict(confidence=.99,basis='Exact Royal Collection native RCIN 405416; museum web-reader history and Commons object record agree.',currentDisplayClaim=False)),p['at']))
        credit='Benjamin West; Royal Collection Trust/© Her Majesty Queen Elizabeth II 2019; reproduction via Wikimedia Commons.'
        db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'Wikimedia Commons','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)",
            (p['mediaID'],p['imagePath'],p['commonsReceipt']['url'],im['width'],im['height'],im['bytes'],im['sha256'],p['title']+' — Benjamin West, 1769',rights['status'],rights['label'],rights['policyURL'],credit,credit+' Proportionally resized and compressed; full frame preserved.',p['commonsReceipt']['retrievedAt'],ACTOR))
        db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,'RCIN 405416',%s,%s,%s,%s,%s,now(),%s)",(p['mediaID'],COMMONS,p['commonsReceipt']['sha256'],im['sourceImageReceipt']['url'],rights['policyURL'],rights['basis'],OP,Jsonb(dict(rights=rights,commonsReceipt=p['commonsReceipt'],image=im,visualReview=p['visualReview'],authorization=p['authorization'],planSHA256=pin))))
        db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full painting reproduction')",(AID,p['mediaID']))
        db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(p['mediaID'],AID))
        db.execute("UPDATE exhibition_entries SET artwork_id=%s,date_label='1769',medium_label='Oil on canvas',participation='exhibited',match_basis=%s,evidence=evidence||%s WHERE id=%s",(AID,'Original 1769 catalogue no. 120 plus explicit Royal Collection exhibition history, native RCIN and complete visual identity.',Jsonb(dict(canonicalObject=p,reviewPlanSHA256=pin)),ENTRY))
        db.execute("UPDATE exhibitions SET start_date=%s,end_date=%s,end_year=1769,date_display='26 April – 27 May 1769',date_precision='day',state_basis='The institution-supported Royal Academy Chronicle documents this annual exhibition, its original catalogue and explicit opening and closing dates.',updated_at=now() WHERE id=%s",(p['eventDates']['start'],p['eventDates']['end'],EID))
        db.execute("UPDATE exhibition_occurrences SET start_date=%s,end_date=%s,date_display='26 April – 27 May 1769',venue_label='Former auction rooms in Pall Mall',evidence=evidence||%s WHERE id=%s",(p['eventDates']['start'],p['eventDates']['end'],Jsonb(dict(dateReview=p['eventDates'],venueBasis='1769 Chronicle identifies an auctioneer’s premises in Pall Mall; the Royal Academy institution link remains an organizer link, not a claim for its current building.')),p['pinnedOccurrence']['id']))
        db.execute('UPDATE exhibition_source_records SET interpretation=interpretation||%s WHERE id=%s',(Jsonb(dict(dateReview=p['eventDates'],checklistReview=dict(numbersReviewed=136,eligibleEntries=119,excludedNonPictorial=11,mediumHeld=6,completeChecklist=False))),c.uid('source/royal-academy/1769')))
        result=db.execute('SELECT status,published_at,current_institution_id,primary_media_id,artline_has_selection_evidence(id) eligible_evidence FROM artworks WHERE id=%s',(AID,)).fetchone()
        assert result['status']=='review' and result['published_at'] is None and str(result['current_institution_id'])==IID and str(result['primary_media_id'])==p['mediaID'] and result['eligible_evidence']
    c.save(OUT/'delivered.json',dict(at=c.now(),newArtworks=1,newPrimaryImages=1,newExhibitionConnections=1,artworkID=AID,exhibitionID=EID,sourceCatalogueNumber='120',reviewStatusPreserved=True,localDatabaseWrites=False,exactExhibitionDates=p['eventDates'],planSHA256=pin))
    print('One illustrated review painting and its exact 1769 exhibition connection committed.',flush=True)


def verify():
    base='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions'
    seen=set();after='';pages=0;ranks=[];linked=[]
    while True:
        response=requests.get(base+'/'+EID+'/entries',params={'limit':50,'after':after},timeout=30)
        response.raise_for_status();data=response.json();pages+=1
        assert data['total']==119
        for entry in data['items']:
            assert entry['id'] not in seen;seen.add(entry['id'])
            ranks.append((0 if entry.get('image') else 2)+(0 if entry['participation']=='exhibited' else 1))
            if entry.get('artworkId'):linked.append(entry['artworkId'])
        if not data['hasMore']:break
        after=data['nextCursor'];assert pages<10
    assert len(seen)==119 and ranks==sorted(ranks) and len(linked)==3 and AID in linked
    response=requests.get(base+'/'+EID,timeout=30);response.raise_for_status();detail=response.json()
    assert detail['startDate']=='1769-04-26' and detail['endDate']=='1769-05-27' and detail['participantCount']==46
    reverse=requests.get(base,params={'artwork':AID,'limit':10},timeout=30)
    reverse.raise_for_status();assert any(x['id']==EID for x in reverse.json()['items'])
    plan=c.load(OUT/'delivery-plan.json')
    image=requests.get('https://artlines.org'+plan['imagePath'],timeout=30)
    image.raise_for_status();assert c.sha(image.content)==plan['image']['sha256']
    with c.connect() as db:
        artwork=db.execute('SELECT id,title,date_precision,status,primary_media_id,current_institution_id,revision FROM artworks WHERE id=%s',(AID,)).fetchone()
        assert artwork['date_precision']=='exact' and artwork['status']=='review' and str(artwork['primary_media_id'])==plan['mediaID'] and str(artwork['current_institution_id'])==IID
        rights=db.execute('SELECT source_checksum,evidence_json FROM media_rights_evidence WHERE media_id=%s',(plan['mediaID'],)).fetchone()
        assert rights['source_checksum']==plan['commonsReceipt']['sha256'] and rights['evidence_json']['rights']['embeddedCredit']==plan['rights']['embeddedCredit']
    c.save(OUT/'verified.json',dict(at=c.now(),artwork=artwork,paginationPages=pages,
        distinctEntries=119,illustratedFirst=True,canonicalLinkedArtworks=linked,
        reverseExhibitionLink=True,publicImageBytesVerified=True,
        exactStartDate=detail['startDate'],exactEndDate=detail['endDate'],participants=46,
        realLocalDatabaseWrites=False))
    print('Verified 119 unique entries, three illustrated canonical links, exact dates, reverse connection and authentic public image.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['plan','upload','apply','verify']:
        raise SystemExit('Use plan, upload, apply, or verify')
    globals()[sys.argv[1]]()
