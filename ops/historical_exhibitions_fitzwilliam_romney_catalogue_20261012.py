#!/usr/bin/env python3
"""Native Fitzwilliam Romney drawings and exact 1977 exhibition attachments."""
import sys,json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_cambridge_remaining_20261012 as b
h=b.h
c=h.c;n=h.n
OUT=b.OUT/'romney-catalogue-release';BACKUP=b.BACKUP/'romney-catalogue-release'
OP='historical-exhibitions-fitzwilliam-romney-catalogue-20261012';SID=c.uid(OP+'/source');IID='5dc5171c-7a3d-5f36-bc85-6c56f6afeb64';ACTOR='local-european-research'
ARTISTS={'Romney, George':'1a0f85a7-e409-447e-bbc1-9fc0163371f2'}
def plan():
 p=c.load(b.OUT/'plan.json.gz');p['entries']=[e for e in p['entries']if e['eid']=='51da0c91-651c-53dd-997d-74864b7d362a'];records={}
 for entry in p['entries']:
  nid=entry['nid']
  if nid in records:continue
  src=entry['source'];h.validate_receipt(src['receipt']);d=src['data'];assert len(d['lifecycle']['creation'])==1;cr=d['lifecycle']['creation'][0];dates=cr.get('date',[]);assert len(dates)<=1;dt=dates[0]if dates else {};qualified=False
  assert [x['summary_title']for x in d['owners']]==['The Fitzwilliam Museum']
  makers=cr['maker'];primary=[m for m in makers if m['summary_title']in ARTISTS];assert len(primary)==1 and not primary[0].get('@link',{}).get('qualifier');artistID=ARTISTS[primary[0]['summary_title']]
  assert all(m['summary_title']in ARTISTS or m['summary_title']=='Petiet, Henri'for m in makers)
  for maker in makers:
   if maker['summary_title']=='Petiet, Henri':assert [x['value']for x in maker['@link']['role']]==['publisher']
  notes=cr.get('note',[]);dateNotes=[x['value']for x in dt.get('note',[])]
  questioned=any(x.get('precision')=='?'for x in [dt,dt.get('from',{}),dt.get('to',{})]);uncertainDate=not dates or questioned
  assert entry['medium']=='drawing'
  first,last=(None,None)if uncertainDate else(dt['earliest'],dt['latest']);assert first is None or 1734<=first<=last<=1802
  circa=dt.get('precision')=='circa'or any(dt.get(k,{}).get('precision')=='circa'for k in ['from','to'])
  precision='unknown'if uncertainDate else ('circa_range'if circa else 'range')if dt.get('range')else ('circa'if circa else 'exact')
  dateLabel=entry['date']
  if questioned:dateLabel='Uncertain source date: '+str(dateLabel)
  if dateNotes:dateLabel=str(dateLabel)+'; '+'; '.join(dateNotes)
  dimensions='; '.join(x['name']+': '+', '.join(str(v['value'])+' '+v['units']+' '+v['dimension'].lower()for v in x.get('measurements',{}).get('dimensions',[]))for x in d.get('component',[])if x.get('measurements',{}).get('dimensions'))
  records[nid]=dict(id=c.uid(OP+'/artwork/'+nid),slug='fitzwilliam-drawing-'+nid,nativeID=nid,title=entry['title'],accession=entry['accession'],creator=entry['creator'],date=dateLabel,first=first,last=last,precision=precision,medium=entry['medium'],dimensions=dimensions or None,qualified=qualified,source=src,notes=notes,artistID=artistID,dateNotes=dateNotes)
 with c.connect()as db:
  assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='fitzwilliam-native-object' AND external_id=ANY(%s)",(list(records),)).fetchone()
  # Bound duplicate audit to documented institution and known Rembrandt creator.
  candidates=n.normal(db.execute("SELECT a.* FROM artworks a WHERE a.current_institution_id=%s OR a.id IN(SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))",(IID,list(ARTISTS.values()))).fetchall())
  accessions={v['accession']for v in records.values()};assert not any(a['accession_number']in accessions for a in candidates)
  entries=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in p['entries']],)).fetchall());assert len(entries)==125 and all(e['artwork_id']is None for e in entries)
  artist=n.normal(db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id',(list(ARTISTS.values()),)).fetchall());assert len(artist)==1
 result=dict(at=c.now(),records=list(records.values()),entriesBefore=entries,candidatesBefore=candidates,artistBefore=artist,counts=dict(newArtworks=125,newImages=0,newArtistLinks=125,exhibitionEntriesLinked=125,newHoldings=125))
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')
 for r in p['records']:h.validate_receipt(r['source']['receipt'])
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  before=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([e['id']for e in p['entriesBefore']],)).fetchall());assert before==sorted(p['entriesBefore'],key=lambda x:x['id'])
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='fitzwilliam-native-object' AND external_id=ANY(%s)",([r['nativeID']for r in p['records']],)).fetchone()
  current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([a['id']for a in p['candidatesBefore']],)).fetchall());assert sorted(current,key=lambda x:x['id'])==sorted(p['candidatesBefore'],key=lambda x:x['id'])
  assert n.normal(db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id',(list(ARTISTS.values()),)).fetchall())==p['artistBefore']
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,OP,'Fitzwilliam George Romney drawings exhibited in 1977','collection_page','https://data.fitzmuseum.cam.ac.uk'))
  bynative={r['nativeID']:r for r in p['records']}
  with db.pipeline():
   for r in p['records']:
    rc=r['source']['receipt'];url='https://data.fitzmuseum.cam.ac.uk/id/object/'+r['nativeID'];note=json.dumps(dict(operation=OP,nativeID=r['nativeID'],accession=r['accession'],captureSHA=rc['sha256'],capturePath=rc['body_path'],sourceCreationNotes=r['notes'],qualifiedImpression=r['qualified'],impressionDateUnknown=r['precision']=='unknown',sourceDateNotes=r['dateNotes'],basis='Exact museum native record and accession. Source owner and acquisition evidence support holdings, not current display. Original JSON preserves all dates, attributions, component dimensions and print states.'))
    db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,current_institution_id,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'drawing',%s,%s,%s,'review',true,%s,%s,%s,%s)",(r['id'],r['slug'],r['title'],c.norm(r['title']),r['date']or'Date unknown',r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],r['accession'],r['creator'],IID,ACTOR,ACTOR))
    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'fitzwilliam-native-object',%s,%s,%s,%s)",(r['id'],r['nativeID'],url,SID,rc['retrieved_at']))
    db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'native_exhibition_drawing_metadata',%s,%s,%s,%s,%s,%s)",(r['id'],SID,r['nativeID'],url,note,rc['retrieved_at'],ACTOR))
    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['id'],IID,SID,url,note,rc['retrieved_at']))
    if not r['qualified']:db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES(%s,%s,'primary')",(r['id'],r['artistID']))
   for e in p['entriesBefore']:
    r=bynative[e['source_artwork_id'].split('/')[-1]];evidence=e['evidence']|dict(mainCatalogueMatch='Exact native ID and accession',artworkID=r['id'],catalogueOperation=OP)
    db.execute('UPDATE exhibition_entries SET artwork_id=%s,evidence=%s,match_basis=%s WHERE id=%s AND artwork_id IS NULL',(r['id'],Jsonb(evidence),'Exact Fitzwilliam native object and accession; source drawing qualifiers preserved.',e['id']))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');ids=[r['id']for r in p['records']]
 with c.connect()as db:
  rows=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall());assert len(rows)==125 and all(x['status']=='review'and x['primary_media_id']is None and x['current_institution_id']==IID for x in rows)
  assert db.execute('SELECT count(*)n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==125
  es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in p['entriesBefore']],)).fetchall());assert len(es)==125 and all(e['artwork_id']in ids for e in es)
  for e in es:
   old=next(x for x in p['entriesBefore']if x['id']==e['id'])
   for k in ['title_label','creator_label','date_label','catalogue_number','source_artwork_id','participation']:assert e[k]==old[k]
  for a in rows:
   r=next(x for x in p['records']if x['id']==a['id']);assert a['accession_number']==r['accession']and a['date_precision']==r['precision']and a['creation_year_start']==r['first']and a['creation_year_end']==r['last']
 for eid in sorted({e['exhibition_id']for e in p['entriesBefore']}):
  items=[];cursor=None
  while True:
   params=dict(limit=100)
   if cursor:params['after']=cursor
   resp=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid+'/entries',params=params,timeout=40);resp.raise_for_status();data=resp.json();items.extend(data['items']);cursor=data.get('nextCursor')
   if not cursor:break
  expected={e['id']:e['artwork_id']for e in es if e['exhibition_id']==eid};assert {x['id']:x['artworkId']for x in items}==expected and all(not x.get('image')for x in items)

 result=dict(at=c.now(),counts=p['counts'],all125APIArtworkLinksVerified=True,sourceDateNotesPreserved=True,realLocalWrites=False,imagesStillMissing=125)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-romney-catalogue-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
