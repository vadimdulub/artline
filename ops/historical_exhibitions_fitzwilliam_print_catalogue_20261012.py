#!/usr/bin/env python3
"""Selected native Fitzwilliam prints and exact exhibition-entry attachments."""
import sys,json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_rembrandt_release_20261012 as h
c=h.c;n=h.n
OUT=h.r.OUT/'catalogue-release';BACKUP=h.BACKUP/'catalogue-release'
OP='historical-exhibitions-fitzwilliam-print-catalogue-20261012';SID=c.uid(OP+'/source');IID='5dc5171c-7a3d-5f36-bc85-6c56f6afeb64';ACTOR='local-european-research'
def plan():
 p=c.load(h.OUT/'plan.json.gz');records={}
 for entry in p['entries']:
  nid=entry['nativeID']
  if nid in records:continue
  src=entry['source'];h.validate_receipt(src['receipt']);d=src['data'];cr=d['lifecycle']['creation'][0];dt=cr['date'][0];qualified=entry['qualified']
  assert [x['summary_title']for x in d['owners']]==['The Fitzwilliam Museum']
  assert all(x['date'][0]['latest']<=1933 for x in d['lifecycle']['acquisition'])
  first,last=(None,None)if qualified else(dt['earliest'],dt['latest']);assert first is None or 1600<=first<=last<=1669
  circa=dt.get('precision')=='circa'or any(dt.get(k,{}).get('precision')=='circa'for k in ['from','to'])
  precision='unknown'if qualified else ('circa_range'if circa else 'range')if dt.get('range')else ('circa'if circa else 'exact')
  dimensions='; '.join(x['name']+': '+', '.join(str(v['value'])+' '+v['units']+' '+v['dimension'].lower()for v in x.get('measurements',{}).get('dimensions',[]))for x in d.get('component',[])if x.get('measurements',{}).get('dimensions'))
  records[nid]=dict(id=c.uid(OP+'/artwork/'+nid),slug='fitzwilliam-print-'+nid,nativeID=nid,title=entry['title'],accession=entry['accession'],creator=entry['creator'],date=entry['date'],first=first,last=last,precision=precision,medium=entry['medium'],dimensions=dimensions or None,qualified=qualified,source=src,notes=entry['notes'])
 with c.connect()as db:
  assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='fitzwilliam-native-object' AND external_id=ANY(%s)",(list(records),)).fetchone()
  # Bound duplicate audit to documented institution and known Rembrandt creator.
  candidates=n.normal(db.execute("SELECT a.* FROM artworks a WHERE a.current_institution_id=%s OR a.id IN(SELECT artwork_id FROM artwork_artists WHERE artist_id=%s)",(IID,h.ARTIST)).fetchall())
  accessions={v['accession']for v in records.values()};assert not any(a['accession_number']in accessions for a in candidates)
  entries=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in p['entries']],)).fetchall());assert len(entries)==235 and all(e['artwork_id']is None for e in entries)
  artist=n.normal(db.execute('SELECT * FROM artists WHERE id=%s',(h.ARTIST,)).fetchone());assert artist['display_name']=='Rembrandt van Rijn'
 result=dict(at=c.now(),records=list(records.values()),entriesBefore=entries,candidatesBefore=candidates,artistBefore=artist,counts=dict(newArtworks=105,newImages=0,newArtistLinks=103,exhibitionEntriesLinked=235,newHoldings=105))
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz')
 for r in p['records']:h.validate_receipt(r['source']['receipt'])
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  before=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([e['id']for e in p['entriesBefore']],)).fetchall());assert before==sorted(p['entriesBefore'],key=lambda x:x['id'])
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='fitzwilliam-native-object' AND external_id=ANY(%s)",([r['nativeID']for r in p['records']],)).fetchone()
  current=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([a['id']for a in p['candidatesBefore']],)).fetchall());assert sorted(current,key=lambda x:x['id'])==sorted(p['candidatesBefore'],key=lambda x:x['id'])
  assert n.normal(db.execute('SELECT * FROM artists WHERE id=%s',(h.ARTIST,)).fetchone())==p['artistBefore']
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,OP,'Fitzwilliam selected historical Rembrandt exhibition prints','collection_page','https://data.fitzmuseum.cam.ac.uk'))
  bynative={r['nativeID']:r for r in p['records']}
  with db.pipeline():
   for r in p['records']:
    rc=r['source']['receipt'];url='https://data.fitzmuseum.cam.ac.uk/id/object/'+r['nativeID'];note=json.dumps(dict(operation=OP,nativeID=r['nativeID'],accession=r['accession'],captureSHA=rc['sha256'],capturePath=rc['body_path'],sourceCreationNotes=r['notes'],qualifiedImpression=r['qualified'],impressionDateUnknown=r['qualified'],basis='Exact museum native record and accession. Source owner and acquisition evidence support holdings, not current display. Original JSON preserves all dates, attributions, component dimensions and print states.'))
    db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,current_institution_id,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'print',%s,%s,%s,'review',true,%s,%s,%s,%s)",(r['id'],r['slug'],r['title'],c.norm(r['title']),r['date'],r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],r['accession'],r['creator']if r['qualified']else None,IID,ACTOR,ACTOR))
    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'fitzwilliam-native-object',%s,%s,%s,%s)",(r['id'],r['nativeID'],url,SID,rc['retrieved_at']))
    db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'native_exhibition_print_metadata',%s,%s,%s,%s,%s,%s)",(r['id'],SID,r['nativeID'],url,note,rc['retrieved_at'],ACTOR))
    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['id'],IID,SID,url,note,rc['retrieved_at']))
    if not r['qualified']:db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES(%s,%s,'primary')",(r['id'],h.ARTIST))
   for e in p['entriesBefore']:
    r=bynative[e['source_artwork_id'].split('/')[-1]];evidence=e['evidence']|dict(mainCatalogueMatch='Exact native ID and accession',artworkID=r['id'],catalogueOperation=OP)
    db.execute('UPDATE exhibition_entries SET artwork_id=%s,evidence=%s,match_basis=%s WHERE id=%s AND artwork_id IS NULL',(r['id'],Jsonb(evidence),'Exact Fitzwilliam native object and accession; source impression qualifiers preserved.',e['id']))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');ids=[r['id']for r in p['records']]
 with c.connect()as db:
  rows=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall());assert len(rows)==105 and all(x['status']=='review'and x['primary_media_id']is None and x['current_institution_id']==IID for x in rows)
  assert db.execute('SELECT count(*)n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==103
  es=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in p['entriesBefore']],)).fetchall());assert len(es)==235 and all(e['artwork_id']in ids for e in es)
  for e in es:
   old=next(x for x in p['entriesBefore']if x['id']==e['id'])
   for k in ['title_label','creator_label','date_label','catalogue_number','source_artwork_id','participation']:assert e[k]==old[k]
  for a in rows:
   r=next(x for x in p['records']if x['id']==a['id']);assert a['accession_number']==r['accession']and a['date_precision']==r['precision']and a['creation_year_start']==r['first']and a['creation_year_end']==r['last']
 for eid in sorted({e['exhibition_id']for e in p['entriesBefore']}):
  resp=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid+'/entries',params=dict(limit=100),timeout=40);resp.raise_for_status();data=resp.json();expected={e['id']:e['artwork_id']for e in es if e['exhibition_id']==eid};assert not data.get('nextCursor')and {x['id']:x['artworkId']for x in data['items']}==expected and all(not x.get('image')for x in data['items'])
 result=dict(at=c.now(),counts=p['counts'],all235APIArtworkLinksVerified=True,qualifiedImpressionsRetained=2,realLocalWrites=False,imagesStillMissing=105)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-print-catalogue-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','apply','verify'];globals()[sys.argv[1]]()
