#!/usr/bin/env python3
"""Eight object-specific Blake exhibition histories from Getty catalogue 146."""
import sys,json,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-getty-blake-20261012'
OUT=c.DATA/'getty-blake-release';BACKUP=n.BACKUP.parent/'getty-blake'
AID='431a00dd-30dc-5554-8d1e-6112b045c8e8';ARTIST='de003eac-51c4-4057-bec5-4870d243b1b2'
SPECS=[
('1904','Works by William Blake',1904,None,'January 1904','month','Carfax and Co.','London',None),
('1906','Frescoes, Prints and Drawings by William Blake',1906,None,'June–July 1906','month','Carfax and Co.','London','34'),
('1914-nottingham','Works by William Blake',1914,None,'1914','year','Art Museum, Nottingham Castle','Nottingham','37'),
('1914-manchester','Works by William Blake',1914,None,'1914','year','Whitworth Institute','Manchester','57'),
('1927','Blake Centenary Exhibition',1927,None,'1927','year','Burlington Fine Arts Club','London','38'),
('1957','William Blake Bicentennial Exhibition',1957,None,'1957','year','Achenbach Foundation for Graphic Arts, Fine Arts Museums of San Francisco','San Francisco',None),
('1978','William Blake',1978,None,'March–May 1978','month','Tate Gallery','London','86'),
('1982','William Blake and His Followers',1982,1983,'December 1982–February 1983','month','Achenbach Foundation for Graphic Arts, Fine Arts Museums of San Francisco','San Francisco',None)]
def plan():
 rc=c.load(c.RUN/'london-gallery-project/getty-pdf-download.json')
 assert c.sha((c.DATA/'getty-european-drawings-1.pdf').read_bytes())==rc['sha256']
 with c.connect()as db:
  work=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())
  existing=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',('a2fcbbaa-b6fb-587b-9c70-2ff425f6a40f',)).fetchone())
  occurrence=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(existing['id'],)).fetchone())
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s AND artwork_id=%s',(existing['id'],AID)).fetchone()
  assert not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(existing['id'],ARTIST)).fetchone()
  assert db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(AID,ARTIST)).fetchone()
  before=db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 assert work['primary_media_id']=='551b7d1a-2276-53fa-be9f-bd070af9d1b6'
 events=[]
 for key,title,year,end,display,precision,venue,city,number in SPECS:
  events.append(dict(key=key,id=existing['id']if key=='1906'else c.uid(OP+'/'+key),oid=occurrence['id']if key=='1906'else c.uid(OP+'/venue/'+key),sid=c.uid(OP+'/source/'+key),entryID=c.uid(OP+'/entry/'+key),title=title,year=year,end=end,display=display,precision=precision,venue=venue,city=city,number=number,new=key!='1906'))
 evidence=dict(operation=OP,publication='European Drawings 1: Catalogue of the Collections (Getty, 1988)',catalogueEntry='146',printedPage=324,pdfPages=[335,336],accession='84.GC.49',source=rc,identityBasis='Visual comparison of original catalogue illustration PDF page336 and existing delivered WikiArt image: same far leg, wing veins, serpent, face and contours. Getty first pull, not Craxton second pull with missing far leg. Same title, signed1795. Imported dimensions differ; retained unchanged as metadata discrepancy.',imageMatchConfidence=.98,sourceCreationYear=1795,chronologyVerified=True,checklistComplete=False,currentDisplayClaim=False,metadataUnchanged=True)
 result=dict(at=c.now(),events=events,work=work,existing=existing,occurrence=occurrence,before=before,evidence=evidence,duplicateAudit=c.load(c.RUN/'london-gallery-project/getty-blake-event-duplicate-audit.json'),counts=dict(newExhibitions=7,newEntries=8,illustratedArtworkConnections=8,newArtistParticipants=8,newArtworks=0,newImages=0))
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())==p['work']
  assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(p['existing']['id'],)).fetchone())==p['existing']
  assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(p['occurrence']['id'],)).fetchone())==p['occurrence']
  for e in p['events']:
   if e['new']:
    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['year'],e['end'],e['display'],e['precision'],'Getty1988 catalogue146 explicit exhibition history for accession84.GC.49.',OP))
   rc=p['evidence']['source']
   db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],e['id'],OP,e['key'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e),Jsonb(p['evidence'])))
   if e['new']:
    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],e['venue'],e['city'],'United States'if e['city']=='San Francisco'else'United Kingdom','US'if e['city']=='San Francisco'else'GB',e['display'],Jsonb(p['evidence'])))
   else:
    db.execute('UPDATE exhibition_occurrences SET venue_label=%s,evidence=evidence||%s WHERE id=%s',(e['venue'],Jsonb(dict(gettyVenueEvidence=p['evidence'])),e['oid']))
   db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'William Blake','1795',%s,'exhibited',%s,%s)",(e['entryID'],e['id'],e['sid'],e['oid'],AID,'getty/84.GC.49',e['number'],'Satan Exulting over Eve','Graphite, pen and black ink, and watercolor over color print',Jsonb(p['evidence']),p['evidence']['identityBasis']))
   db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,'William Blake','artist',%s)",(c.uid(OP+'/artist/'+e['key']),e['id'],e['sid'],ARTIST,Jsonb(p['evidence'])))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');verified=[]
 for e in p['events']:
  url='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(url,timeout=40);r.raise_for_status();d=r.json();assert d['startYear']==e['year'];assert any(a['artist_id']==ARTIST for a in d['participants'])
  r=requests.get(url+'/entries',params=dict(limit=100),timeout=40);r.raise_for_status();entry=next(x for x in r.json()['items']if x['id']==e['entryID']);assert entry['artworkId']==AID and entry.get('image');verified.append(dict(id=e['id'],title=e['title'],illustrated=True))
 with c.connect()as db:
  assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone())==p['work']
  totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone())
 result=dict(at=c.now(),counts=p['counts'],events=verified,totals=totals,allAPIEntriesVerified=True,realLocalWrites=False,mainArtworkPreserved=True)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-blake-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
