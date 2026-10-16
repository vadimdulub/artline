#!/usr/bin/env python3
"""Three early London exhibitions with native object evidence; no main catalogue writes."""
import sys,json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_medium_cohort_20261012 as m
import historical_exhibitions_fitzwilliam_rembrandt_release_20261012 as h
c=m.f.c;n=m.f.n
OP='historical-exhibitions-fitzwilliam-early-london-20261012';OUT=m.f.OUT/'early-london-release';BACKUP=n.BACKUP.parent/'fitzwilliam-early-london'
SPECS=[('exhibition-1139',1833,'1833-06 – 1833-07','month'),('exhibition-1615',1836,'1836','year'),('exhibition-94',1896,'1896','year')]
def plan():
 events=[];entries=[]
 with c.connect()as db:
  matched=n.normal(db.execute("SELECT x.external_id,a.* FROM external_identifiers x JOIN artworks a ON a.id=x.entity_id WHERE x.scheme='fitzwilliam-native-object'AND x.external_id=ANY(%s)",(['13951','7589','784','785','786'],)).fetchall());assert {x['external_id']for x in matched}=={'784','786'}
  nearby=n.normal(db.execute('SELECT id,title,start_year FROM exhibitions WHERE start_year=ANY(%s)',([1833,1836,1896],)).fetchall());assert not any(any(t in c.norm(x['title'])for t in ['turner','tenth','medieval','mediaeval'])for x in nearby)
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  count=db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 for key,year,display,precision in SPECS:
  source=c.load(m.OUT/(key+'.json'));h.validate_receipt(source['receipt']);eid=c.uid(OP+'/'+key);oid=c.uid(OP+'/venue/'+key)
  events.append(dict(id=eid,sid=c.uid(OP+'/source/'+key),oid=oid,key=key,title=source['data']['summary_title'],year=year,display=display,precision=precision,source=source))
  for obj in c.load(m.f.OUT/(key+'-html.json'))['objects']:
   nid=obj['url'].rsplit('/',1)[-1];src=c.load(m.f.OUT/'early-london-objects'/('object-'+nid+'.json'));h.validate_receipt(src['receipt']);d=src['data'];cr=d['lifecycle']['creation'][0];refs=[x for x in d['exhibitions']if x['admin']['id']==key];assert len(refs)==1
   acc=next(x['value']for x in d['identifier']if x.get('primary')and x.get('type')=='accession number');w=next((x for x in matched if x['external_id']==nid),None)
   if w:assert w['accession_number']==acc and w['current_institution_id']=='5dc5171c-7a3d-5f36-bc85-6c56f6afeb64'
   entries.append(dict(id=c.uid(OP+'/entry/'+key+'/'+nid),sid=c.uid(OP+'/object/'+key+'/'+nid),eid=eid,oid=oid,nid=nid,title=d['title'][0]['value'],creator='; '.join(x['summary_title']for x in cr['maker']),date='; '.join(h.year_label(x)for x in cr.get('date',[]))or None,medium=d['name'][0]['reference']['summary_title'],catalogue=refs[0].get('@link',{}).get('catalogue'),accession=acc,work=w,source=src))
 assert len(events)==3 and len(entries)==5
 result=dict(at=c.now(),events=events,entries=entries,nearby=nearby,beforeActive=count,counts=dict(newEvents=3,newEntries=5,existingArtworkLinks=2,newArtworks=0,newImages=0),basis='Official Fitzwilliam exhibition and reciprocal native object references. Source London location preserved; exact venue not established from these records. Date strings retain original precision; Turner malformed numerical date derivatives retained only as source evidence. Complete checklist unknown. Recto/verso sheet represented once; shared catalogue 22 retained for distinct Passion panels.')
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')
 for e in p['events']+p['entries']:h.validate_receipt(e['source']['receipt'])
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  for e in p['entries']:
   if e['work']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['work']['id'],)).fetchone())=={k:v for k,v in e['work'].items()if k!='external_id'}
  base=dict(operation=OP,basis=p['basis'],currentDisplayClaim=False,checklistComplete=False)
  def source(e,eid,key):
   rc=e['source']['receipt'];db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],eid,OP,key,rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e['source']['data']),Jsonb(base)))
  with db.pipeline():
   for e in p['events']:
    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['year'],e['display'],e['precision'],p['basis'],OP));source(e,e['id'],e['key'])
    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],'London (exact venue unresolved)','London','United Kingdom','GB',e['display'],Jsonb(base)))
   for e in p['entries']:
    source(e,e['eid'],e['eid']+'/'+e['nid']);aid=e['work']['id']if e['work']else None
    db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eid'],e['sid'],e['oid'],aid,'fitzwilliam/'+e['nid'],e['catalogue'],e['title'],e['creator'],e['date'],e['medium'],Jsonb(base|dict(accession=e['accession'],nativeObjectID=e['nid'],groupCatalogueNumbersCanRepeat=True)),'Exact native object and reciprocal exhibition reference; '+('native ID/accession match to existing work.'if aid else 'internal work match unresolved.')))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');events=[]
 for e in p['events']:
  base='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(base,timeout=40);r.raise_for_status();d=r.json();assert d['startYear']==e['year']and d['datePrecision']==e['precision']and not d.get('startDate')and not d.get('endDate')
  r=requests.get(base+'/entries',params=dict(limit=100),timeout=40);r.raise_for_status();items=r.json()['items'];expected={x['id']:x['work']['id']if x['work']else None for x in p['entries']if x['eid']==e['id']};assert {x['id']:x.get('artworkId')for x in items}==expected and all(not x.get('image')for x in items);events.append(dict(id=e['id'],title=e['title'],entries=len(items)))
 with c.connect()as db:
  totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+3
  for e in p['entries']:
   if e['work']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['work']['id'],)).fetchone())=={k:v for k,v in e['work'].items()if k!='external_id'}
 result=dict(at=c.now(),counts=p['counts'],events=events,totals=totals,allAPIEntriesVerified=True,mainArtworkRecordsPreserved=True,realLocalWrites=False,checklistsComplete=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-early-london-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
