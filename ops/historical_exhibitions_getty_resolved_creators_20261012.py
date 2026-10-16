#!/usr/bin/env python3
"""Resolve five exact Getty-object creator labels to existing artist identities."""
import sys,json
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST
OP='historical-exhibitions-getty-resolved-creators-20261012';OUT=DEST/'resolved-creators-release';BACKUP=n.BACKUP.parent/'getty-resolved-creators';SID=c.uid(OP+'/source')
M={'Nicolaes Eliasz. Pickenoy':('241dc389-0c27-4349-ab50-ec348774a56e','Nicolaes Eliasz. Pickenoy'),'Hans Holbein the Younger':('032ba90e-62a8-482d-b5a1-6d527e9082fb','Hans Holbein the Younger'),'Raphael (Raffaello Sanzio)':('737d46fd-968a-479c-aea5-46931604f574','Raphael'),"Nicolò dell'Abate":('d31daf8f-d851-4e2d-a153-8c491b881d32',"Niccolò dell'Abbate")}
def plan():
 p=c.load(DEST/'thirtyone-connections-release/plan.json.gz');entries=[e for e in p['entries']if e['object']['creator']and e['object']['creator'][0]in M];rows={e['workID']:e for e in entries};records=[]
 with c.connect()as db:
  for aid,e in rows.items():
   label=e['object']['creator'][0];artistID,name=M[label];artist=n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(artistID,)).fetchone());assert c.norm(artist['display_name'])==c.norm(name)
   w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(aid,)).fetchone());assert w['accession_number']==e['object']['accession'];assert not db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND attribution_role='primary'",(aid,)).fetchone()
   personID=e['source']['data']['produced_by']['carried_out_by'][0]['id'];person=c.load(DEST/'creators'/(personID.rsplit('/',1)[-1]+'.json'))
   records.append(dict(sourceCreator=person,work=w,artist=artist,source=e['source'],label=label,entries=[x for x in entries if x['workID']==aid]))
 result=dict(at=c.now(),records=records,review='Exact native Getty object and person records resolve creator names and historical lifetimes. Chosen existing artist profiles carry museum identifiers: Pickenoy FNG/SMK, Holbein NGA/WikiArt/Wikidata, Raphael NGA/Wikidata, Abate NGA/Wikidata. Abate spelling variant and source 1509/1512 birth range preserved; Pickenoy death range 1650/1656 preserved in evidence. Duplicate French-name profiles are not merged or changed. No artist dates, object metadata, image or status changes.')
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print('Planned',len(records),'artist links')
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');count=0
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Getty historical exhibition creator reconciliation','collection_page','https://www.getty.edu')",(SID,OP))
  for r in p['records']:
   w=r['work'];a=r['artist'];assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w;assert n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(a['id'],)).fetchone())==a
   assert not db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND attribution_role='primary'",(w['id'],)).fetchone()
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)VALUES(%s,%s,'primary',%s)",(w['id'],a['id'],'Getty object creator: '+r['label']))
   rc=r['source']['receipt'];ev=dict(operation=OP,basis=p['review'],sourceReceipt=rc,creatorLabel=r['label'],sourceObject=r['source']['data'],sourceCreator=r['sourceCreator']);db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES('artwork',%s,'getty_creator_reconciliation',%s,%s,%s,%s,%s,'local-european-research')",(w['id'],SID,w['accession_number'],rc['url'],json.dumps(ev,ensure_ascii=False),rc['retrieved_at']))
   for e in r['entries']:
    if db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(e['eid'],a['id'])).fetchone():continue
    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/'+e['eid']+'/'+a['id']),e['eid'],e['sid'],a['id'],a['display_name'],Jsonb(ev)));count+=1
 c.save(OUT/'delivered.json',dict(at=c.now(),newArtistLinks=len(p['records']),newParticipants=count));print('Committed',len(p['records']),'artist links',count,'participants')
def verify():
 p=c.load(OUT/'plan.json.gz')
 with c.connect()as db:
  for r in p['records']:
   assert db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(r['work']['id'],r['artist']['id'])).fetchone()
   for e in r['entries']:assert db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(e['eid'],r['artist']['id'])).fetchone()
   current=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(r['work']['id'],)).fetchone());assert current==r['work']
 result=c.load(OUT/'delivered.json')|dict(verifiedAt=c.now(),originalArtworksPreserved=True,realLocalWrites=False);c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-resolved-creators-delivery.json',result);print(result)
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
