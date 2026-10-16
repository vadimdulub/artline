#!/usr/bin/env python3
"""Reconciled historical Getty exhibition venues and exact illustrated object connections."""
import sys,json,re,requests
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT as RESEARCH
OP='historical-exhibitions-getty-venues-20261012';OUT=RESEARCH/'venue-release';BACKUP=n.BACKUP.parent/'getty-venues';ACTOR='local-european-research'
def dates(d):
 t=d['timespan'];display='; '.join(x['content']for x in t.get('identified_by',[]));first=t['begin_of_the_begin'][:10];last=t['end_of_the_end'][:10];precision='day'if len(re.findall(r'\b\d{1,2}, \d{4}',display))==2 else'month'if re.search(r'[A-Za-z]{3}',display)else'year'
 return dict(firstYear=int(first[:4]),lastYear=int(last[:4]),start=first if precision=='day'else None,end=last if precision=='day'else None,display=display,precision=precision)
def plan():
 grouped=c.load(RESEARCH/'event-reconciliation.json.gz');decisions={d['sourceID']:d for d in c.load(RESEARCH/'editorial-reconciliation.json')['decisions']};objects=c.load(RESEARCH/'discovery.json.gz')['objects'];main=c.load(RESEARCH/'ten-drawings-release/plan.json.gz')['records'];byobj={r['objectID']:r for r in main};stag=next(o for o in objects if o['accession']=='83.GC.214');byobj[stag['id']]=dict(id='515160f2-f13a-59a5-8a3f-7a53e72793fb',title='Stag Beetle',date='1505',medium='Watercolor and gouache',creator='Albrecht Dürer',artistID='1e6dc7e2-7c1d-4ec6-b3a6-25c05bfe4a93')
 old=c.load(RESEARCH/'cleveland-tour-preimage.json.gz');events=[];occurrences=[];entries=[]
 for g in grouped['groups']:
  decision=decisions[g['sourceID']]
  if decision['decision']=='hold-event-identity':continue
  eid=decision['existingEventID']or c.uid(OP+'/event/'+g['sourceID']);new=not decision['existingEventID'];ds=[dates(a['data'])for a in g['activities']];precision='year'if any(d['precision']=='year'for d in ds)else'month'if any(d['precision']=='month'for d in ds)else'day';first=min(d['firstYear']for d in ds);last=max(d['lastYear']for d in ds)
  start=min(d['start']for d in ds)if precision=='day'else None;end=max(d['end']for d in ds)if precision=='day'else None
  display=ds[0]['display']if len(ds)==1 else(str(first)if first==last else str(first)+'–'+str(last));events.append(dict(id=eid,title=g['title'],new=new,sourceID=g['sourceID'],sid=c.uid(OP+'/event-source/'+g['sourceID']),source=g['parent'],first=first,last=last,start=start,end=end,precision=precision,display=display))
  for source in g['activities']:
   d=source['data'];dt=dates(d);places=d['took_place_at'];assert len(places)==1;venue=places[0]['_label'];existing=not new and 'Cleveland' in venue;oid=old['occurrences'][0]['id']if existing else c.uid(OP+'/venue/'+d['id']);sid=c.uid(OP+'/activity-source/'+d['id']);occurrences.append(dict(id=oid,eid=eid,sid=sid,sourceID=d['id'],source=source,venue=venue,existing=existing,dates=dt))
   memberids={x['id']for s in d.get('used_specific_object',[])for x in s.get('member',[])}
   for o in objects:
    if not any(a['id']==d['id']for a in o['otherExhibitions']):continue
    assert o['id']in memberids;oWork=byobj[o['id']];assert int(o['dateBounds']['end_of_the_end'][:4])<=dt['lastYear']
    entries.append(dict(id=c.uid(OP+'/entry/'+d['id']+'/'+o['id']),eid=eid,oid=oid,sid=sid,objectID=o['id'],accession=o['accession'],work=oWork,source=o['source']))
 assert len(events)==35 and sum(e['new']for e in events)==34
 with c.connect()as db:
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone();assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s',(old['event']['id'],)).fetchone())==old['event'];assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(old['event']['id'],)).fetchall())==old['occurrences']
  works=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([w['id']for w in byobj.values()],)).fetchall());assert len(works)==11 and all(w['primary_media_id']for w in works)
  active=db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
  for e in events:
   if e['new']:assert not db.execute("SELECT 1 FROM exhibitions WHERE status<>'archived'AND normalized_title=%s AND start_year<=%s AND coalesce(end_year,start_year)>=%s",(c.norm(e['title']),e['last'],e['first'])).fetchone()
 p=dict(at=c.now(),events=events,occurrences=occurrences,entries=entries,old=old,works=works,beforeActive=active,counts=dict(newExhibitions=34,extendedTours=1,newOccurrences=sum(not x['existing']for x in occurrences),illustratedEntries=len(entries),newImages=0,newArtworks=0),basis='Exact reciprocal Getty native object/activity references and explicit parent exhibition IDs. Partial selected-drawing checklists. Six parent travel activities are not extra venues. Existing Cleveland precise occurrence dates preserved; uncertain Burlington winter show excluded.')
 c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');base=dict(operation=OP,basis=p['basis'],currentDisplayClaim=False,checklistComplete=False)
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  assert n.normal(db.execute('SELECT * FROM exhibitions WHERE id=%s FOR UPDATE',(p['old']['event']['id'],)).fetchone())==p['old']['event']
  assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE exhibition_id=%s',(p['old']['event']['id'],)).fetchall())==p['old']['occurrences']
  for w in p['works']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w
  for e in p['events']:
   if e['new']:assert not db.execute("SELECT 1 FROM exhibitions WHERE status<>'archived'AND normalized_title=%s AND start_year<=%s AND coalesce(end_year,start_year)>=%s",(c.norm(e['title']),e['last'],e['first'])).fetchone()
  def source(sid,eid,key,src):
   rc=src['receipt'];db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(sid,eid,OP,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(src['data']),Jsonb(base)))
  for e in p['events']:
   if e['new']:
    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,start_date,end_date,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['first'],e['last'],e['start'],e['end'],e['display'],e['precision'],p['basis'],OP))
   else:
    db.execute("UPDATE exhibitions SET start_year=%s,end_year=%s,start_date=NULL,end_date=NULL,date_display=%s,date_precision='year',checklist_state='partial',state_basis=%s,updated_at=now()WHERE id=%s",(e['first'],e['last'],e['display'],p['basis'],e['id']))
   source(e['sid'],e['id'],e['sourceID'],e['source'])
  for o in p['occurrences']:
   source(o['sid'],o['eid'],o['sourceID'],o['source'])
   if not o['existing']:
    d=o['dates'];db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,source_venue_id,venue_label,start_date,end_date,date_display,evidence)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(o['id'],o['eid'],o['sid'],o['sourceID'],o['venue'],d['start'],d['end'],d['display'],Jsonb(base|dict(sourceDateBounds=o['source']['data']['timespan'],datePrecision=d['precision']))))
  for e in p['entries']:
   w=e['work'];db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,'Exact reciprocal Getty object/activity IDs; exact accession and internal artwork mapping.')",(e['id'],e['eid'],e['sid'],e['oid'],w['id'],e['objectID'],w['title'],w['creator'],w['date'],w['medium'],Jsonb(base|dict(objectSource=e['source'],accession=e['accession'],chronologyVerified=True))))
  participants={}
  for e in p['entries']:
   w=e['work'];participants.setdefault((e['eid'],w['artistID']or w['creator']),e)
  for (eid,key),e in participants.items():
   w=e['work'];assert not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s AND name_label=%s',(eid,w['creator'])).fetchone();db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/artist/'+eid+'/'+key),eid,e['sid'],w['artistID'],w['creator'],Jsonb(base|dict(artworkID=w['id']))))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],participants=len(participants)));print('Committed',p['counts'],'participants',len(participants))
def verify():
 p=c.load(OUT/'plan.json.gz');verified=[]
 for e in p['events']:
  baseURL='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(baseURL,timeout=40);r.raise_for_status();d=r.json();assert d['startYear']==e['first']and d['endYear']==e['last']and d['datePrecision']==e['precision']
  r=requests.get(baseURL+'/entries',params=dict(limit=100),timeout=40);r.raise_for_status();items=r.json()['items'];expected={x['id']:x['work']['id']for x in p['entries']if x['eid']==e['id']};assert {x['id']:x['artworkId']for x in items}==expected and all(x.get('image')for x in items)
  expectedArtists={x['work']['artistID']for x in p['entries']if x['eid']==e['id']and x['work']['artistID']};assert expectedArtists<={x['artist_id']for x in d['participants']};verified.append(dict(id=e['id'],title=e['title'],illustratedEntries=len(items)))
 with c.connect()as db:
  totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']>=p['beforeActive']+34
  old=p['old']['occurrences'][0];assert n.normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(old['id'],)).fetchone())==old
  for w in p['works']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(w['id'],)).fetchone())==w
 result=dict(at=c.now(),counts=p['counts'],events=verified,totals=totals,allAPIImagesAndLinksVerified=True,ClevelandExactDatesPreserved=True,realLocalWrites=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-venue-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
