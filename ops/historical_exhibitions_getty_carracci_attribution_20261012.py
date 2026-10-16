#!/usr/bin/env python3
"""Preserve Getty's alternative Carracci attribution instead of a joint-creator label."""
import sys,json,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST
OP='historical-exhibitions-getty-carracci-attribution-20261012';OUT=DEST/'carracci-attribution-release';BACKUP=n.BACKUP.parent/'getty-carracci-attribution';LABEL='Annibale Carracci or Ludovico Carracci';SID=c.uid(OP+'/source')
def plan():
 p=c.load(DEST/'thirtyone-connections-release/plan.json.gz');entries=[e for e in p['entries']if e['object']['accession']=='85.GB.218'];src=entries[0]['source'];parts=src['data']['produced_by']['part'];assert any(x.get('_label')=='Artist/Maker (Producer) Name Prefix'and x.get('content')=='or'for part in parts for x in part.get('referred_to_by',[]))
 with c.connect()as db:
  w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(entries[0]['workID'],)).fetchone());old=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in entries],)).fetchall());assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(w['id'],)).fetchone()
 result=dict(at=c.now(),work=w,entries=entries,oldEntries=old,source=src,basis='Getty current production parts explicitly prefix Ludovico Carracci with or. This is an alternative attribution, not joint authorship. Preserve about1585 artwork date; nested 2010 dates describe attribution history. No confirmed primary artist selected.')
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print('Planned label correction for',len(entries),'entries')
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');count=0
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(p['work']['id'],)).fetchone())==p['work']
  for old in p['oldEntries']:assert n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s',(old['id'],)).fetchone())==old
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Getty Carracci alternative attribution','collection_page','https://www.getty.edu')",(SID,OP));rc=p['source']['receipt'];ev=dict(operation=OP,basis=p['basis'],source=p['source'],previousLabel=p['work']['unlinked_creator_label'])
  db.execute("UPDATE artworks SET unlinked_creator_label=%s,updated_by='local-european-research',updated_at=now()WHERE id=%s",(LABEL,p['work']['id']))
  db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES('artwork',%s,'getty_alternative_creator_attribution',%s,'85.GB.218',%s,%s,%s,'local-european-research')",(p['work']['id'],SID,rc['url'],json.dumps(ev,ensure_ascii=False),rc['retrieved_at']))
  for e in p['entries']:
   db.execute("UPDATE exhibition_entries SET creator_label=%s,evidence=evidence||%s::jsonb WHERE id=%s",(LABEL,Jsonb(dict(alternativeAttribution=ev)),e['id']))
   if db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND name_label=%s',(e['eid'],LABEL)).fetchone():continue
   db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/'+e['eid']),e['eid'],e['sid'],LABEL,Jsonb(ev)));count+=1
 c.save(OUT/'delivered.json',dict(at=c.now(),correctedArtworks=1,correctedEntryLabels=len(p['entries']),newQualifiedParticipants=count));print('Committed corrected labels and',count,'qualified participants')
def verify():
 p=c.load(OUT/'plan.json.gz')
 with c.connect()as db:
  w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(p['work']['id'],)).fetchone());assert w['unlinked_creator_label']==LABEL
  for k in ['primary_media_id','creation_year_start','creation_year_end','date_precision','status','current_institution_id']:assert w[k]==p['work'][k]
  assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(w['id'],)).fetchone()
  for e in p['entries']:assert db.execute('SELECT creator_label FROM exhibition_entries WHERE id=%s',(e['id'],)).fetchone()['creator_label']==LABEL
 for eid in {e['eid']for e in p['entries']}:
  r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid,timeout=40);r.raise_for_status();assert any(x.get('name')==LABEL and not x.get('artist_id')for x in r.json()['participants'])
 result=c.load(OUT/'delivered.json')|dict(verifiedAt=c.now(),qualifiedAttributionPreserved=True,noConfirmedArtistAssigned=True,realLocalWrites=False);c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-carracci-attribution-delivery.json',result);print(result)
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
