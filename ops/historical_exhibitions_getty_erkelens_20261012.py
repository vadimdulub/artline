#!/usr/bin/env python3
"""Create source-backed Antonie Erkelens profile and link his existing drawing."""
import sys,json,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST
OP='historical-exhibitions-getty-erkelens-20261012';OUT=DEST/'erkelens-release';BACKUP=n.BACKUP.parent/'getty-erkelens';SID=c.uid(OP+'/source');PID='621f8f00-cce9-41f5-b635-218e9b87763d';AID=c.uid('artist/getty/'+PID)
def collision(db):
 return db.execute("SELECT id FROM artists WHERE normalized_name=%s OR id=%s OR id IN(SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND canonical_url=%s)",(c.norm('Antonie Erkelens'),AID,'https://data.getty.edu/museum/collection/person/'+PID)).fetchall()
def plan():
 src=c.load(DEST/'creators'/(PID+'.json'));assert src['data']['_label']=='Antonie Erkelens';assert any(x.get('content')=='1774 - 1804'for x in src['data']['referred_to_by']);p=c.load(DEST/'thirtyone-connections-release/plan.json.gz');entries=[e for e in p['entries']if e['object']['accession']=='2006.14'];assert entries
 with c.connect()as db:
  assert not collision(db);w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(entries[0]['workID'],)).fetchone());assert w['creation_year_start']>=1774 and w['creation_year_end']<=1804;assert not db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND attribution_role='primary'",(w['id'],)).fetchone()
 result=dict(at=c.now(),sourceCreator=src,work=w,entries=entries,artistID=AID,nameAudit=c.load(DEST/'erkelens-name-audit.json'),basis='Getty native person identity explicitly states Antonie Erkelens, Dutch, 1774–1804. Variant-name and lifetime audit found only unrelated artists. Source painting/drawing creation range about 1790–1800 is within the documented life. No inferred biography, active period or current display.')
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print('Planned one artist and',len(entries),'venue connections')
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');count=0
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not collision(db);w=p['work'];assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Getty Antonie Erkelens creator identity','collection_page','https://www.getty.edu')",(SID,OP))
  db.execute("INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,created_by,updated_by)VALUES(%s,'antonie-erkelens-getty','Antonie Erkelens','Erkelens, Antonie',%s,1774,1804,'1774','1804','exact','exact',1774,1804,'1774–1804','life','review','local-european-research','local-european-research')",(AID,c.norm('Antonie Erkelens')))
  rc=p['sourceCreator']['receipt'];ev=dict(operation=OP,basis=p['basis'],sourceCreator=p['sourceCreator']);note=json.dumps(ev,ensure_ascii=False)
  db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)VALUES('artist',%s,'getty-person',%s,%s,%s,%s)",(AID,PID,rc['url'],SID,rc['retrieved_at']))
  for kind,ident in [('artist',AID),('artwork',w['id'])]:db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,%s,'getty_creator_identity',%s,%s,%s,%s,%s,'local-european-research')",(kind,ident,SID,PID,rc['url'],note,rc['retrieved_at']))
  db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)VALUES(%s,%s,'primary','Getty creator: Antonie Erkelens')",(w['id'],AID))
  for e in p['entries']:
   if db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(e['eid'],AID)).fetchone():continue
   db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,'Antonie Erkelens','artist',%s)",(c.uid(OP+'/'+e['eid']),e['eid'],e['sid'],AID,Jsonb(ev)));count+=1
 c.save(OUT/'delivered.json',dict(at=c.now(),newArtists=1,newArtworkArtistLinks=1,newParticipants=count));print('Committed new artist and',count,'participants')
def verify():
 p=c.load(OUT/'plan.json.gz')
 with c.connect()as db:
  a=db.execute('SELECT * FROM artists WHERE id=%s',(AID,)).fetchone();assert a['birth_year']==1774 and a['death_year']==1804 and a['status']=='review';assert db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(p['work']['id'],AID)).fetchone();assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(p['work']['id'],)).fetchone())==p['work']
 for eid in {e['eid']for e in p['entries']}:
  r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid,timeout=40);r.raise_for_status();assert AID in {x['artist_id']for x in r.json()['participants']}
 result=c.load(OUT/'delivered.json')|dict(verifiedAt=c.now(),artistID=AID,liveParticipantsVerified=True,artworkPreserved=True,realLocalWrites=False);c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-erkelens-delivery.json',result);print(result)
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
