#!/usr/bin/env python3
"""Three exact historical connections for the existing Whistler painting."""
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
import requests
import exhibitions_common as c

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/cleveland-press-archive'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/whistler-mother'
OP='historical-exhibition-whistler-mother-20261012'
AID='0edd9c42-f15a-5f08-b46a-75e93b62e974'
ARTIST='cdb3d27d-8ee6-4c49-8942-ad330739a90d'
SOURCE=c.uid(OP+'/metadata-source')
ACTOR='local-european-research'
HISTORY='https://whistlerpaintings.gla.ac.uk/catalogue/display/?mid=y101&xml=his'
EVENTS=[
    dict(id='5e6b5b69-27bf-5a7a-b2f0-e2fe956065b7',year=1872,number='941',source='glasgow-whistler-y101',file='whistler-y101-history.html',page='History: Exhibitions; 1872 Royal Academy',
         title="Arrangement in grey and black: portrait of the painter's mother",basis='Catalogue raisonné explicitly lists the 104th Royal Academy exhibition, 1872, no. 941; narrative confirms actual hanging after initial selection controversy.'),
    dict(id='96ac9df0-a99f-55df-aa21-45926d7c172f',year=1883,number='2441',source='glasgow-whistler-y101',file='whistler-y101-history.html',page='History: Exhibitions; 1883 Salon, Paris',
         title='Portrait de ma mère',basis='Catalogue raisonné explicitly lists the Paris Salon at the Palais des Champs-Elysées, 1883, no. 2441. This is distinct from the same-titled January 1883 Nice Salon.'),
    dict(id='2aa3030b-20e4-5992-b070-d5a6c8ec076a',year=1933,number=None,source='cleveland-press-reviewed',file='cma-616391.json',page='Museum retrospective event 616391 and two original letters, page 1 each',
         title="Portrait of the Artist's Mother",basis='Museum retrospective explicitly identifies the painting and its December 7 departure; the two original museum letters identify the Louvre loan, after Chicago, alongside other Whistler paintings, etchings, lithographs and drawings.')]


def normal(v):
    return json.loads(json.dumps(v,default=str))


def receipts():
    out={}
    for name in ['whistler-y101-history.html','cma-616391.json','cmapr5497.pdf','cmapr5496.pdf','wikiart-mother.html']:
        path=OUT/name;rc=c.load(path.with_suffix(path.suffix+'.receipt.json'))
        assert rc['status']==200 and c.sha(path.read_bytes())==rc['sha256'];out[name]=rc
    return out


def plan():
    rc=receipts();pins=c.load(OUT/'whistler-mother-pins.json');events=[]
    text=BeautifulSoup((OUT/'whistler-y101-history.html').read_bytes(),'html.parser').get_text(' ',strip=True)
    assert all(x in text for x in ['YMSM 101','RF 699','1871','941','2441','Musée d’Orsay'.replace('’',"'")])
    wiki=BeautifulSoup((OUT/'wikiart-mother.html').read_bytes(),'html.parser').get_text(' ',strip=True)
    assert '1871' in wiki and 'Media: oil , canvas' in wiki and 'Public domain' in wiki
    with c.connect()as db:
        assert normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())==pins['artwork']
        assert pins['artwork']['work_type']=='unknown' and pins['artwork']['medium_text'] is None
        assert pins['artwork']['status']=='review' and pins['artwork']['creation_year_start']==1871
        assert any(x['artist_id']==ARTIST for x in pins['artists'])
        artist=db.execute('SELECT id,display_name,birth_year,death_year FROM artists WHERE id=%s',(ARTIST,)).fetchone()
        assert artist['birth_year']<=1871<=artist['death_year']
        for r in EVENTS:
            event=db.execute('SELECT * FROM exhibitions WHERE id=%s',(r['id'],)).fetchone();assert event['start_year']==r['year']
            entries=db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=%s',(r['id'],)).fetchall();assert not entries
            participants=db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s',(r['id'],)).fetchall()
            assert not any(str(x['artist_id'])==ARTIST for x in participants)
            occurrences=db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(r['id'],)).fetchall()
            if r['year']==1883:assert any(x['city_label']=='Paris' and x['venue_label']=='Palais des Champs-Elysées' for x in occurrences)
            events.append(dict(**r,before=event,participants=participants,occurrences=occurrences,entryID=c.uid(OP+'/entry/'+r['id']),sourceID=c.uid(OP+'/source/'+r['id'])))
    p=dict(at=c.now(),operation=OP,artworkPins=pins,artist=artist,events=events,receipts=rc,
        metadataUpdates=dict(work_type='painting',medium_text='Oil on canvas'),
        objectIdentity=dict(catalogueRaisonne='YMSM 101',museumInventory='RF 699',date=1871,
            basis='Same artist, uniquely identifying long title, date, Musée d’Orsay holding and visually inspected existing painted composition; separate Scottish drypoint record is excluded.',confidence=.99),
        imageReview=dict(existingImagePreserved=True,visuallyInspected=True,newImage=False,
            issue='Existing WikiArt reproduction is a cropped 4:3 view; source page itself supplies the same crop. It is authentic but not a full-frame reproduction. Replacement remains a separately recorded image gap; do not invent/crop/extend the missing image area.'),
        dateReview=dict(press5497='Original scan says 21 October 1933 and planned 3–30 November; OCR wrongly reads 1983.',
            press5496='Original scan says 3–29 November; OCR wrongly reads 8rd.',
            retrospective='CMA retrospective records 3 November–10 December 1933 for the whole exhibition and December 7 for the painting. Preserve these later institutional dates; do not overwrite with advance letters.'),
        excludedLinks=['1892 Goupil: explicitly a photograph of the painting, not the original.', '1887 Manchester: uncertain arrival and withdrawal; not an exhibited claim.'],
        newEvents=0,newArtworks=0,newImages=0,newEntries=3,newArtistConnections=3,realLocalDatabaseWrites=False)
    c.save(OUT/'whistler-delivery-plan.json',p);c.save(BACKUP/'preimage.json.gz',p)
    print('Prepared three exact illustrated connections and source-backed painting/medium enrichment; original image and dates preserved.',flush=True)


def apply():
    p=c.load(OUT/'whistler-delivery-plan.json');pin=c.sha((OUT/'whistler-delivery-plan.json').read_bytes())
    assert receipts()==p['receipts'] and c.load(BACKUP/'preimage.json.gz')==p
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR UPDATE',(AID,)).fetchone())==p['artworkPins']['artwork']
        assert normal(db.execute('SELECT * FROM media_assets WHERE id=%s FOR SHARE',(p['artworkPins']['media']['id'],)).fetchone())==p['artworkPins']['media']
        for r in p['events']:
            assert normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',(r['id'],)).fetchone())==r['before']
            assert not db.execute('SELECT id FROM exhibition_entries WHERE exhibition_id=%s',(r['id'],)).fetchall()
            assert normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s',(r['id'],)).fetchall())==r['participants']
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://whistlerpaintings.gla.ac.uk')",(SOURCE,OP,'University of Glasgow — Whistler catalogue raisonné; selected historical exhibition review'))
        db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'work_type_and_medium','YMSM 101',%s,%s,%s,%s)",
            (c.uid(OP+'/citation'),AID,SOURCE,HISTORY,json.dumps(dict(previous={k:p['artworkPins']['artwork'][k]for k in p['metadataUpdates']},new=p['metadataUpdates'],identity=p['objectIdentity'],sources=p['receipts'],imageReview=p['imageReview'],planSHA256=pin),ensure_ascii=False),p['at'],ACTOR))
        db.execute("UPDATE artworks SET work_type='painting',medium_text='Oil on canvas',updated_by=%s WHERE id=%s",(ACTOR,AID))
        for r in p['events']:
            rc=p['receipts'][r['file']];evidence=dict(operation=OP,objectIdentity=p['objectIdentity'],basis=r['basis'],receipts=p['receipts'],dateReview=p['dateReview'] if r['year']==1933 else None,imageReview=p['imageReview'],planSHA256=pin)
            db.execute("INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (r['sourceID'],r['id'],r['source'],'YMSM101/'+str(r['year']),rc['url'],rc['retrievedAt'],rc['path'],rc['sha256'],Jsonb(dict(catalogueNumber=r['number'],title=r['title'],year=r['year'],objectIdentity=p['objectIdentity'])),Jsonb(evidence)))
            db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,lender_label,participation,source_page,evidence,match_basis) VALUES(%s,%s,%s,%s,'YMSM 101',%s,%s,'James McNeill Whistler','1871','Oil on canvas',%s,'exhibited',%s,%s,%s)",
                (r['entryID'],r['id'],r['sourceID'],AID,r['number'],r['title'],'Musée du Louvre, Paris' if r['year']==1933 else None,r['page'],Jsonb(evidence),r['basis']))
            db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,'James McNeill Whistler','artist',%s)",
                (c.uid(OP+'/artist/'+r['id']),r['id'],r['sourceID'],ARTIST,Jsonb(dict(basis='Named creator of the exact exhibited painting',artworkID=AID,planSHA256=pin))))
    c.save(OUT/'whistler-delivered.json',dict(at=c.now(),newEntries=3,newIllustratedConnections=3,newArtistConnections=3,existingArtworkMetadataEnriched=1,newEvents=0,newArtworks=0,newImages=0,existingImagePreserved=True,fullFrameImageGap=1,realLocalDatabaseWrites=False,planSHA256=pin))
    print('Committed three exhibition connections, three artist connections and one missing-medium correction.',flush=True)


def verify():
    p=c.load(OUT/'whistler-delivery-plan.json');api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions'
    checks=[]
    with c.connect()as db:
        a=normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone());before=p['artworkPins']['artwork']
        permitted={'work_type','medium_text','updated_by','updated_at','revision'}
        assert {k:v for k,v in a.items()if k not in permitted}=={k:v for k,v in before.items()if k not in permitted}
        assert a['work_type']=='painting'and a['medium_text']=='Oil on canvas'
        assert normal(db.execute('SELECT * FROM media_assets WHERE id=%s',(a['primary_media_id'],)).fetchone())==p['artworkPins']['media']
        for r in p['events']:
            assert normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(r['id'],)).fetchone())==r['before']
            response=requests.get(api+'/'+r['id']+'/entries',timeout=30);response.raise_for_status();items=response.json()['items']
            assert len(items)==1 and items[0]['artworkId']==AID and items[0]['catalogueNumber']==r['number'] and items[0]['image']==p['artworkPins']['media']['storage_path']
            checks.append(dict(exhibitionID=r['id'],entryID=r['entryID'],catalogueNumber=r['number'],internalImage=True))
    reverse=requests.get(api,params={'artwork':AID,'limit':50},timeout=30);reverse.raise_for_status()
    assert {r['id']for r in p['events']}.issubset({r['id']for r in reverse.json()['items']})
    c.save(OUT/'whistler-verified.json',dict(at=c.now(),checks=checks,unchangedEvents=3,existingImagePreserved=True,metadataOnlyFieldsChanged=['work_type','medium_text'],reverseConnectionsVerified=True,realLocalDatabaseWrites=False))
    print('Verified all three illustrated/reverse connections, original dates, image, review status and artwork identity.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply','verify']:raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
