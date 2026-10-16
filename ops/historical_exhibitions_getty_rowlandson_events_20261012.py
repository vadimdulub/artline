#!/usr/bin/env python3
"""Four reciprocal Rowlandson histories, reusing Royal Academy1785."""
import sys,json,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_venue_release_20261012 import dates
R=c.DATA/'getty-rowlandson';OP='historical-exhibitions-getty-rowlandson-events-20261012';OUT=R/'event-release';BACKUP=n.BACKUP.parent/'getty-rowlandson-events'
def plan():
 audit=c.load(R/'production-audit.json');workPlan=c.load(R/'work-release/plan.json.gz');w=workPlan['records'][0];events=[]
 for a in c.load(R/'historical-scope.json')['historical']:
  key=a['id'].rsplit('/',1)[-1];src=c.load(R/'activities'/(key+'.json'));d=dates(src['data']);parent=a['exhibition'][0];psrc=c.load(R/'exhibitions'/(parent['id'].rsplit('/',1)[-1]+'.json'));new=d['firstYear']!=1785;eid=c.uid(OP+'/event/'+parent['id'])if new else audit['existingEvent']['id'];oid=c.uid(OP+'/venue/'+key)if new else audit['occurrences'][0]['id']
  events.append(dict(id=eid,new=new,oid=oid,sid=c.uid(OP+'/source/'+key),entryID=c.uid(OP+'/entry/'+key),title=parent['_label'],sourceID=parent['id'],source=src,parentSource=psrc,dates=d,venue=a['venues'][0]['_label'],catalogueNumber={1785:None,1927:None,1948:'15',1962:'65'}[d['firstYear']]))
 with c.connect()as db:
  current=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone());assert current['primary_media_id']==w['mid'];old=n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(audit['existingEvent']['id'],)).fetchone());assert old==audit['existingEvent'];occ=n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(audit['occurrences'][0]['id'],)).fetchone());assert occ==audit['occurrences'][0]
  nearby=n.normal(db.execute("SELECT id,title,start_year,end_year FROM exhibitions WHERE status<>'archived' AND title ILIKE '%%rowlandson%%'").fetchall());assert not any(c.norm(e['title'])==c.norm(x['title'])and x['start_year']==e['dates']['firstYear']for e in events if e['new']for x in nearby)
  for e in events:assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_url=%s',(e['source']['receipt']['url'],)).fetchone()
 p=dict(at=c.now(),events=events,work=w,workBefore=current,oldEvent=old,oldOccurrence=occ,nearby=nearby,counts=dict(newExhibitions=3,reusedExhibitions=1,newOccurrences=3,illustratedEntries=4),basis='Getty exact object/activity reciprocal identity with captured parent exhibition records. Museum1988 catalogue confirms1785,1948,1962; native history independently confirmsTate1927–28. Preserve historical title and attribution uncertainty; no later etched-version substitution or current display claim.')
 c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');w=p['work'];participants=0
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone();assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==p['workBefore'];assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(p['oldEvent']['id'],)).fetchone())==p['oldEvent'];assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(p['oldOccurrence']['id'],)).fetchone())==p['oldOccurrence']
  for e in p['events']:
   d=e['dates'];rc=e['source']['receipt'];ev=dict(operation=OP,basis=p['basis'],objectSource=w['source'],activitySource=e['source'],parentSource=e['parentSource'],datePrecision=d['precision'],checklistComplete=False,currentDisplayClaim=False,historicalAttributionNote='1785 catalogue title differs. Wigstead attribution is a research lead, not substituted for modern Getty attribution.')
   if e['new']:db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)VALUES(%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),d['firstYear'],d['lastYear'],d['display'],d['precision'],p['basis'],OP))
   db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],e['id'],OP,e['sourceID'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['source']['data']),Jsonb(ev)))
   if e['new']:db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],e['venue'],'Reading'if d['firstYear']==1962 else'London','United Kingdom','GB',d['display'],Jsonb(ev)))
   title='The Back of the Boxes at the Theatre, Covent Garden'if d['firstYear']==1785 else w['title'];db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'Thomas Rowlandson','1785',%s,'exhibited',%s,'Getty original drawing84.GG.645; exact reciprocal object/activity identity.')",(e['entryID'],e['id'],e['sid'],e['oid'],w['id'],w['objectID'],e['catalogueNumber'],title,w['medium'],Jsonb(ev)))
   if not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND artist_id=%s',(e['id'],w['artistID'])).fetchone():
    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,'Thomas Rowlandson','artist',%s)",(c.uid(OP+'/artist/'+e['id']),e['id'],e['sid'],w['artistID'],Jsonb(ev)));participants+=1
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],newParticipants=participants));print('Committed',p['counts'],'participants',participants)
def verify():
 p=c.load(OUT/'plan.json.gz');w=p['work'];verified=[]
 for e in p['events']:
  url='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(url,timeout=40);r.raise_for_status();detail=r.json();assert detail['startYear']==e['dates']['firstYear']and detail['datePrecision']==e['dates']['precision'];assert w['artistID']in {x.get('artist_id')for x in detail['participants']};items=[];after=None
  while True:
   params=dict(limit=100)
   if after:params['after']=after
   r=requests.get(url+'/entries',params=params,timeout=40);r.raise_for_status();page=r.json();items+=page['items'];after=page.get('nextCursor')
   if not after:break
  row=next(x for x in items if x['id']==e['entryID']);assert row['artworkId']==w['id']and row.get('image');verified.append(dict(id=e['id'],title=e['title'],new=e['new']))
 with c.connect()as db:
  assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==p['workBefore'];assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(p['oldEvent']['id'],)).fetchone())==p['oldEvent'];assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(p['oldOccurrence']['id'],)).fetchone())==p['oldOccurrence'];totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone())
 result=c.load(OUT/'delivered.json')|dict(verifiedAt=c.now(),events=verified,totals=totals,allLiveImagesAndArtistLinksVerified=True,original1785EventPreserved=True,realLocalWrites=False);c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-rowlandson-events-delivery.json',result);print(result)
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
