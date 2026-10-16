#!/usr/bin/env python3
"""One reciprocal historical exhibition connection for Getty Poussin 81.PA.43."""
import sys,json,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST,OUT as RESEARCH
OP='historical-exhibitions-getty-poussin-connection-20261012';OUT=DEST/'poussin-connection-release';BACKUP=n.BACKUP.parent/'getty-poussin-connection'
def plan():
 scope=c.load(DEST/'scope-review.json.gz');discovery=c.load(DEST/'discovery.json.gz');matches={x['accession']:x for x in c.load(DEST/'poussin-release/plan.json.gz')['records']};objects={o['id']:o for o in scope['eligibleObjects']if o['accession']in matches};occs={o['sourceID']:o for o in c.load(RESEARCH/'venue-release/plan.json.gz')['occurrences']};entries=[]
 for ref in discovery['connections']:
  if ref['objectID']not in objects:continue
  obj=objects[ref['objectID']];o=occs[ref['activityID']];assert ref['reciprocal'];entries.append(dict(id=c.uid(OP+'/'+ref['activityID']+'/'+ref['objectID']),eid=ref['eventID'],oid=ref['occurrenceID'],sid=c.uid(OP+'/source/'+ref['activityID']+'/'+ref['objectID']),workID=matches[obj['accession']]['id'],object=obj,occurrence=o,source=c.load(DEST/'objects'/(obj['id'].rsplit('/',1)[-1]+'.json'))))
 with c.connect()as db:
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  works=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([m['id']for m in matches.values()],)).fetchall());assert len(works)==1 and all(w['primary_media_id']for w in works)
  artistLinks=n.normal(db.execute("SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])AND aa.attribution_role='primary'",([w['id']for w in works],)).fetchall())
  events=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[])',([e['eid']for e in entries],)).fetchall());participants=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',([e['id']for e in events],)).fetchall())
  for e in entries:
   assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s AND occurrence_id=%s AND artwork_id=%s',(e['eid'],e['oid'],e['workID'])).fetchone()
   w=next(w for w in works if w['id']==e['workID']);assert w['accession_number']==e['object']['accession']and w['current_institution_id']=='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';assert w['creation_year_start']is None or w['creation_year_start']<=e['occurrence']['dates']['lastYear']
 p=dict(at=c.now(),entries=entries,works=works,artistLinks=artistLinks,events=events,participants=participants,counts=dict(newIllustratedEntries=len(entries),existingArtworks=1,affectedExhibitions=len(events),newArtworks=0,newImages=0))
 c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');participants=0
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  for w in p['works']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w
  for event in p['events']:assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(event['id'],)).fetchone())==event
  for e in p['entries']:
   o=e['object'];rc=e['source']['receipt'];ev=dict(operation=OP,basis='Exact Getty holding/accession and reciprocal native object/activity references.',objectID=o['id'],accession=o['accession'],activityReceipt=e['occurrence']['source']['receipt'],currentDisplayClaim=False,checklistComplete=False)
   assert not db.execute('SELECT 1 FROM exhibition_entries WHERE exhibition_id=%s AND occurrence_id=%s AND artwork_id=%s',(e['eid'],e['oid'],e['workID'])).fetchone()
   db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],e['eid'],OP,e['id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['source']['data']),Jsonb(ev)))
   title=next(x['content']for x in e['source']['data']['identified_by']if x.get('_label')=='Preferred Title')
   db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,'Exact Getty native identity and reciprocal exhibition history; existing holding and accession match.')",(e['id'],e['eid'],e['sid'],e['oid'],e['workID'],o['id'],title,'; '.join(o['creator']),'; '.join(o['dateLabel']),'; '.join(o['medium']),Jsonb(ev)))
   for a in [a for a in p['artistLinks']if a['artwork_id']==e['workID']]:
    if db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(e['eid'],a['artist_id'])).fetchone():continue
    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/artist/'+e['eid']+'/'+a['artist_id']),e['eid'],e['sid'],a['artist_id'],a['display_name'],Jsonb(ev)));participants+=1
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],newParticipants=participants));print('Committed',p['counts'],'participants',participants)
def verify():
 p=c.load(OUT/'plan.json.gz');verified=[]
 for eid in sorted({e['eid']for e in p['entries']}):
  items=[];after=None
  while True:
   params=dict(limit=100)
   if after:params['after']=after
   r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid+'/entries',params=params,timeout=40);r.raise_for_status();page=r.json();items.extend(page['items']);after=page.get('nextCursor')
   if not after:break
  expected={e['id']:e['workID']for e in p['entries']if e['eid']==eid};selected=[x for x in items if x['id']in expected];assert {x['id']:x['artworkId']for x in selected}==expected and all(x.get('image')for x in selected);verified.append(dict(eventID=eid,entries=len(selected)))
 with c.connect()as db:
  for w in p['works']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w
 result=dict(at=c.now(),counts=p['counts'],verified=verified,allNewAPIImagesVerified=True,mainArtworkRecordsPreserved=True,realLocalWrites=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-poussin-connection-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
