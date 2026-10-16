#!/usr/bin/env python3
"""Five source-backed Cambridge print exhibitions; exact native impressions, no image substitution."""
import sys,json,gzip,requests
from pathlib import Path
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_rembrandt_discovery_20261012 as r
c=r.f.c;n=r.f.n
OUT=r.OUT/'release';BACKUP=n.BACKUP.parent/'fitzwilliam-rembrandt-five-shows'
OP='historical-exhibitions-fitzwilliam-rembrandt-five-shows-20261012'
ARTIST='a08fbe07-1cb4-4423-b9e5-a17529eb64d9'
def validate_receipt(rc):
 assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes()))==rc['sha256']
def year_label(d):
 if d.get('range'):return year_label(d['from'])+'–'+year_label(d['to'])
 return ('c. 'if d.get('precision')=='circa'else '')+d.get('value','Date unknown')
def plan():
 discovery=c.load(r.OUT/'discovery.json');events=[];entries=[]
 for show in discovery['events']:
  key=show['eventID'];src=c.load(r.f.OUT/'selected-details'/(key+'.json'));validate_receipt(src['receipt']);d=src['data'];vs=d['venues'];assert len(vs)==1 and vs[0]['summary_title']=='Cambridge (Cambs.)'
  dt=vs[0]['@link']['date'][0];start=dt['from']['value'];end=dt['to']['value'];sy=int(start[:4]);ey=int(end[:4]);assert 1600<=sy<=ey<1990
  precise=len(start)==len(end)==10;ev=dict(id=c.uid(OP+'/'+key),sid=c.uid(OP+'/source/'+key),oid=c.uid(OP+'/venue/'+key),key=key,title=d['summary_title'],startYear=sy,endYear=ey,startDate=start if precise else None,endDate=end if precise else None,dateDisplay=start+' – '+end,precision='day'if precise else 'month',source=src);events.append(ev)
  for obj in show['objects']:
   nid=obj['url'].rsplit('/',1)[-1];source=c.load(r.OUT/'objects'/(nid+'.json'));validate_receipt(source['receipt']);od=source['data'];assert [x['reference']['summary_title']for x in od['name']]==['print']
   refs=[x for x in od['exhibitions']if x['admin']['id']==key];assert len(refs)==1
   cs=od['lifecycle']['creation'];assert len(cs)==1;creation=cs[0];makers=creation['maker'];assert makers[0]['admin']['id']=='agent-113833'
   qualified=nid in ['48135','81182'];assert len(makers)==(2 if qualified else 1)
   accession=[x['value']for x in od['identifier']if x.get('type')=='accession number'and x.get('primary')];assert len(accession)==1
   dates='; '.join(year_label(x)for x in creation.get('date',[]));notes='; '.join(x['value']for x in creation.get('note',[]));creator='Rembrandt Harmensz. van Rijn'+('; reworked by an unknown maker'if qualified else '')
   if qualified:dates='Source plate date: '+dates+'; impression date unresolved'
   entries.append(dict(id=c.uid(OP+'/entry/'+key+'/'+nid),sid=c.uid(OP+'/object-source/'+key+'/'+nid),eventID=ev['id'],occurrenceID=ev['oid'],nativeID=nid,title=od['title'][0]['value'],creator=creator,date=dates,medium=', '.join(x['reference']['summary_title']for x in od.get('techniques',[])),catalogue=refs[0].get('@link',{}).get('catalogue'),accession=accession[0],notes=notes,source=source,qualified=qualified))
 assert len(events)==5 and len(entries)==235 and len({x['nativeID']for x in entries})==105
 with c.connect()as db:
  nearby=n.normal(db.execute("SELECT e.*,o.venue_label,o.city_label FROM exhibitions e LEFT JOIN exhibition_occurrences o ON o.exhibition_id=e.id WHERE e.start_year=ANY(%s) AND (e.title ILIKE '%%Rembrandt%%' OR o.city_label ILIKE '%%Cambridge%%' OR o.venue_label ILIKE '%%Fitz%%')",([e['startYear']for e in events],)).fetchall())
  assert len(nearby)==3 and all(x['city_label']in ['Washington, D.C.','Raleigh']for x in nearby)
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='fitzwilliam-native-object'AND external_id=ANY(%s)",([e['nativeID']for e in entries],)).fetchone()
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  artist=n.normal(db.execute('SELECT * FROM artists WHERE id=%s',(ARTIST,)).fetchone());assert artist['display_name']=='Rembrandt van Rijn'and artist['status']!='archived'
  count=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 p=dict(at=c.now(),events=events,entries=entries,nearby=nearby,artistBefore=artist,beforeActive=count,counts=dict(newEvents=5,documentedEntries=235,distinctNativePrints=105,artistConnections=5,newArtworks=0,newImages=0),basis='Official exhibition detail pages and reciprocal object references establish participation and exact impression identities. Public connected-record lists do not prove complete original checklists. Cambridge is explicit; exact building/institution remains unresolved. ISO date strings take precedence over malformed numerical derivatives; month precision preserved.')
 c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print(p['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')
 for e in p['events']+p['entries']:validate_receipt(e['source']['receipt'])
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
  assert n.normal(db.execute('SELECT * FROM artists WHERE id=%s',(ARTIST,)).fetchone())==p['artistBefore']
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  base=dict(operation=OP,basis=p['basis'],currentDisplayClaim=False,checklistComplete=False,mainCataloguePreserved=True)
  def source(e,eid,key):
   rc=e['source']['receipt'];db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],eid,OP,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['source']['data']),Jsonb(base)))
  with db.pipeline():
   for e in p['events']:
    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,start_date,end_date,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['startYear'],e['endYear'],e['startDate'],e['endDate'],e['dateDisplay'],e['precision'],p['basis'],OP))
    source(e,e['id'],e['key'])
    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],'Cambridge (exact venue unresolved)','Cambridge','United Kingdom','GB',e['startDate'],e['endDate'],e['dateDisplay'],Jsonb(base)))
    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/artist/'+e['key']),e['id'],e['sid'],ARTIST,'Rembrandt van Rijn',Jsonb(base)))
   for e in p['entries']:
    source(e,e['eventID'],e['eventID']+'/'+e['nativeID'])
    evidence=base|dict(nativeObjectID=e['nativeID'],accession=e['accession'],sourceCreationNotes=e['notes'],qualifiedImpression=e['qualified'],catalogueNumber=e['catalogue'],mainCatalogueMatch='unresolved')
    db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eventID'],e['sid'],e['occurrenceID'],'fitzwilliam/'+e['nativeID'],e['catalogue'],e['title'],e['creator'],e['date'],e['medium'],Jsonb(evidence),'Exact native museum impression and reciprocal exhibition reference; internal artwork match unresolved.'))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');results=[]
 for e in p['events']:
  base='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];res=requests.get(base,timeout=40);res.raise_for_status();d=res.json();assert d['startYear']==e['startYear']and d['endYear']==e['endYear']and d['datePrecision']==e['precision'];assert d.get('startDate')==e['startDate']and d.get('endDate')==e['endDate'];assert d['participants'][0]['artist_id']==ARTIST
  res=requests.get(base+'/entries',params=dict(limit=100),timeout=40);res.raise_for_status();data=res.json();items=data['items'];expected={x['id']:x for x in p['entries']if x['eventID']==e['id']};assert not data.get('nextCursor')and {x['id']for x in items}==set(expected);assert all(not x.get('artworkId')and not x.get('image')for x in items)
  results.append(dict(id=e['id'],title=e['title'],dates=e['dateDisplay'],entries=len(items)))
 with c.connect()as db:
  totals=n.normal(db.execute("SELECT count(*) active,count(*)FILTER(WHERE event_state='held') held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+5
 result=dict(at=c.now(),events=results,counts=p['counts'],totals=totals,allAPIEntriesVerified=True,illustratedEntries=0,realLocalWrites=False,checklistsComplete=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-rembrandt-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
