#!/usr/bin/env python3
"""Twenty-five historical London exhibition references with reciprocal object evidence."""
import sys,json,requests
import historical_exhibitions_fitzwilliam_london_early_discovery_20261012 as r
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_medium_cohort_20261012 as m
import historical_exhibitions_fitzwilliam_rembrandt_release_20261012 as h
c=m.f.c;n=m.f.n
OP='historical-exhibitions-fitzwilliam-london_early-20261012';OUT=m.f.OUT/'london-early-release';BACKUP=n.BACKUP.parent/'fitzwilliam-london-early'
SELECTED=c.load(r.OUT/'release-selection-review.json')['selectedReferences']
def plan():
 events=[];entries=[];held=[]
 nativeIDs=sorted({x['nativeID']for key in SELECTED for x in c.load(r.OUT/(key+'.json'))['objects']})
 with c.connect()as db:
  matched=n.normal(db.execute("SELECT x.external_id,a.* FROM external_identifiers x JOIN artworks a ON a.id=x.entity_id WHERE x.scheme='fitzwilliam-native-object'AND x.external_id=ANY(%s)",(nativeIDs,)).fetchall());assert len({x['external_id']for x in matched})==len(matched)
  nearby=c.load(r.OUT/'production-duplicate-audit.json.gz')['candidates']
  for key in SELECTED:
   d=c.load(m.OUT/(key+'.json'))['data']
   assert not any(c.norm(x['title'])==c.norm(d['summary_title'])for x in nearby)
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  count=db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 for key in SELECTED:
  source=c.load(m.OUT/(key+'.json'));h.validate_receipt(source['receipt']);d=source['data'];dates=d['venues'][0]['@link']['date'][0];start=dates.get('from',{}).get('value') or dates.get('value');end=dates.get('to',{}).get('value')
  if start is None:
   assert key=='exhibition-1337' and end=='1984' and dates['earliest']==dates['latest']==1984
   start='1984';end=None
  precise=bool(len(start)==10 and end and len(end)==10)
  eid=c.uid(OP+'/'+key);oid=c.uid(OP+'/venue/'+key)
  ev=dict(id=eid,sid=c.uid(OP+'/source/'+key),oid=oid,key=key,title=d['summary_title'],year=int(start[:4]),endYear=int(end[:4])if end else None,startDate=start if precise else None,endDate=end if precise else None,display=start+(' – '+end if end else ''),precision='day'if precise else ('month'if len(start)==7 else 'year'),source=source);events.append(ev)
  for obj in c.load(r.OUT/(key+'.json'))['objects']:
   nid=obj['nativeID'];src=c.load(r.OUT/'objects'/(nid+'.json'));h.validate_receipt(src['receipt']);d=src['data'];types=[x['reference']['summary_title']for x in d['name']]
   if types==['album']:held.append(dict(eventID=eid,nativeID=nid,reason='Bound album; individual-leaf participation unresolved'));continue
   assert len(types)==1 and types[0]in ['drawing','painting','miniature (painting)','print']
   cs=d.get('lifecycle',{}).get('creation',[]);dates=[x for cr in cs for x in cr.get('date',[])];assert not any(x.get('latest',0)>1970 for x in dates)
   refs=[x for x in d['exhibitions']if x['admin']['id']==key];assert len(refs)==1
   acc=next(x['value']for x in d['identifier']if x.get('primary')and x.get('type')=='accession number');w=next((x for x in matched if x['external_id']==nid),None)
   if w:assert w['accession_number']==acc
   makers=[x for cr in cs for x in cr.get('maker',[])];labels=[]
   for maker in makers:
    qualifier=maker.get('@link',{}).get('qualifier');labels.append(maker['summary_title']+(' ('+str(qualifier)+')'if qualifier else ''))
   entries.append(dict(id=c.uid(OP+'/entry/'+key+'/'+nid),sid=c.uid(OP+'/object/'+key+'/'+nid),eid=eid,oid=oid,nid=nid,title=d['title'][0]['value'],creator='; '.join(labels)or'Unknown',date='; '.join(h.year_label(x)for x in dates)or None,medium=types[0],catalogue=refs[0].get('@link',{}).get('catalogue'),accession=acc,work=w,source=src))
 assert len(events)==25 and len(entries)==47 and len(held)==0
 result=dict(at=c.now(),events=events,entries=entries,held=held,nearby=nearby,beforeActive=count,counts=dict(newEvents=25,newEntries=47,existingArtworkLinks=sum(bool(e['work'])for e in entries),newArtworks=0,newImages=0,heldAlbums=0),basis='Official museum exhibition records and reciprocal native object histories. Source London city is explicit; exact building/institution is unresolved. Twenty-five reviewed pre-1930 London references. Nine ambiguous or out-of-medium references remain excluded from this release. Original date strings take precedence over malformed derived year bounds in the source. Unknown creation dates and qualified creator labels retained; title years and artist lifetimes are not inferred artwork dates. Checklist partial.')
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
    db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,end_year,start_date,end_date,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['year'],e['endYear'],e['startDate'],e['endDate'],e['display'],e['precision'],p['basis'],OP));source(e,e['id'],e['key'])
    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],'London (exact venue unresolved)','London','United Kingdom','GB',e['display'],Jsonb(base)))
   for e in p['entries']:
    source(e,e['eid'],e['eid']+'/'+e['nid']);aid=e['work']['id']if e['work']else None
    db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",(e['id'],e['eid'],e['sid'],e['oid'],aid,'fitzwilliam/'+e['nid'],e['catalogue'],e['title'],e['creator'],e['date'],e['medium'],Jsonb(base|dict(accession=e['accession'],nativeObjectID=e['nid'],groupCatalogueNumbersCanRepeat=True)),'Exact native object and reciprocal exhibition reference; '+('native ID/accession match to existing work.'if aid else 'internal work match unresolved.')))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');events=[]
 for e in p['events']:
  base='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(base,timeout=40);r.raise_for_status();d=r.json();assert d['startYear']==e['year']and d['datePrecision']==e['precision']and d.get('startDate')==e['startDate']and d.get('endDate')==e['endDate']and d.get('endYear')==e['endYear']
  items=[];cursor=None
  while True:
   params=dict(limit=100)
   if cursor:params['after']=cursor
   rr=requests.get(base+'/entries',params=params,timeout=40);rr.raise_for_status();page=rr.json();items.extend(page['items']);cursor=page.get('nextCursor')
   if not cursor:break
  expected={x['id']:x['work']['id']if x['work']else None for x in p['entries']if x['eid']==e['id']};assert {x['id']:x.get('artworkId')for x in items}==expected ;events.append(dict(id=e['id'],title=e['title'],entries=len(items),illustratedEntries=sum(bool(x.get('image'))for x in items)))
 with c.connect()as db:
  totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']==p['beforeActive']+25
  for e in p['entries']:
   if e['work']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(e['work']['id'],)).fetchone())=={k:v for k,v in e['work'].items()if k!='external_id'}
 result=dict(at=c.now(),counts=p['counts'],events=events,totals=totals,allAPIEntriesVerified=True,mainArtworkRecordsPreserved=True,realLocalWrites=False,checklistsComplete=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-london_early-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
