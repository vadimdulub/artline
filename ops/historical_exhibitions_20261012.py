#!/usr/bin/env python3
"""Evidence-pinned historical exhibition metadata delivery (real local DB read-only).

Source capture/preparation is separate. plan is read-only; apply writes only the
reviewed production exhibition batch, never main artwork or artist fixtures.
"""
from pathlib import Path
import sys,json,collections
from psycopg.types.json import Jsonb
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'
BATCH='historical-exhibitions-20261012'
RA_ID='cd993eb7-5c3e-5c38-bfb7-0f6dfc8a1c94'

def plan():
 ra=c.load(OUT/'royal-academy/records.json');orsay=c.load(OUT/'orsay-prepared.json');review=c.load(OUT/'historical-existing-reconciliation.json')
 assert len(ra)==221 and not review['exactTitleYearCandidates']
 held={r['id']for r in review['orsayExtractionHolds']}
 records=[]
 for r in ra:
  year=r['year'];id=c.uid('royal-academy/summer/'+str(year));rc=r['pageReceipt']
  records.append(dict(id=id,title=r['title'],year=year,endYear=None,startDate=None,endDate=None,dateDisplay=str(year),datePrecision='year',series='Royal Academy Summer Exhibition',provider='royal-academy',nativeID=str(year),url=r['sourceURL'],receipt=rc,payload=r,venue='Royal Academy of Arts',city='London',country='United Kingdom',countryCode='GB',institutionID=RA_ID,publications=[dict(url=m['url'],title=m['title'],sourceIdentifier=m['url'],evidence=dict(license=m['license'],canvasCount=m['canvasCount'],receipt=m['receipt']))for m in r['catalogues']],stateBasis='The institution-supported Royal Academy Chronicle documents this annual exhibition and supplies its digitized catalogue. Exact opening and closing dates have not been transcribed.',issues=['Mixed-media catalogue; only individually verified paintings, drawings, prints and icons will be added.','Year precision only. IIIF navigation dates are not exhibition opening dates.','The Royal Academy institutional link identifies the organizer, not ownership of exhibited works or its current building.']))
 pdf=OUT/'source-discovery/orsay-salons-1673-1961.pdf';rc=c.load(OUT/'source-discovery/orsay-salons-1673-1961-receipt.json');assert c.sha(pdf.read_bytes())==orsay['sourceSHA256']==rc['sha256']
 # This source receipt predates the normalized receipt format. Keep its original
 # bytes and use file mtime only as retrieval-time evidence, never an event date.
 import datetime
 receipt=dict(**rc,retrievedAt=datetime.datetime.fromtimestamp(pdf.stat().st_mtime,datetime.timezone.utc).isoformat(),path=str(pdf))
 for r in orsay['selected']:
  if r['id']in held:continue
  records.append(dict(id=r['id'],title=r['title'],year=r['startYear'],endYear=r['endYear'],startDate=r['startDate'],endDate=r['endDate'],dateDisplay=r['dateDisplay'],datePrecision=r['datePrecision'],series=None,provider='orsay-historical-index',nativeID=r['sourceID'],url=r['sourceURL'],receipt=receipt,payload=r,venue=r['venue'],city=r['city'],country=r['country'],countryCode=r['countryCode'],institutionID=None,publications=[],stateBasis='Documented in the Musée d’Orsay historical index Salons et expositions de 1673 à 1961. Source row, printed page and original date/venue labels are preserved.',issues=['Historical index establishes the event; no complete artwork checklist has yet been transcribed.','Venue labels are historical. Museum holdings and current display are not inferred.']))
 assert len(records)==1547 and len({r['id']for r in records})==1547
 assert all(1600<=r['year']<=1989 and (r['endYear']is None or r['endYear']<=1989)for r in records)
 # Exclude exact existing title/year matches across all providers. The earlier
 # reconciliation also reviewed Royal Academy-looking names and historical venues.
 with c.connect()as db:
  assert db.execute('SELECT id,name FROM institutions WHERE id=%s',(RA_ID,)).fetchone()['name']=='Royal Academy of Arts'
  existing=db.execute('SELECT id,title,start_year FROM exhibitions WHERE start_year BETWEEN 1600 AND 1989').fetchall()
  pairs={(e['start_year'],c.norm(e['title']))for e in existing}
  conflicts=[r for r in records if (r['year'],c.norm(r['title']))in pairs];assert not conflicts,[(r['year'],r['title'])for r in conflicts]
  assert db.execute('SELECT count(*) n FROM exhibitions WHERE id=ANY(%s::uuid[])',([r['id']for r in records],)).fetchone()['n']==0
  before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 c.save(OUT/'historical-import-plan.json',dict(at=c.now(),batch=BATCH,records=records,beforeActive=before,counts=dict(events=len(records),sources=len(records),occurrences=len(records),catalogues=sum(len(r['publications'])for r in records)),sourceRecordCounts=dict(collections.Counter(r['provider']for r in records)),authorization='User requests all historical exhibitions since 1600, through 1989, after production cleanup; paintings, drawings, prints and icons. Exact catalogue entries remain a separate checked ingestion.'))
 print('Prepared production historical events',len(records),flush=True)

def apply():
 p=c.load(OUT/'historical-import-plan.json');records=p['records'];assert len(records)==1547
 for name in ['date-removal-delivered.json','main-removal-delivered.json','medium-removal-delivered.json']:assert(OUT/name).exists()
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(BATCH,)).fetchone()['n']==0,'Batch already present; inspect delivery receipt'
  with db.pipeline():
   for r in records:
    source=c.uid('source/'+r['provider']+'/'+r['nativeID']);occurrence=c.uid('occurrence/'+r['provider']+'/'+r['nativeID'])
    db.execute("""INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,series_label,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'held',%s,'physical','unknown',%s,'review',%s)""",(r['id'],r['title'],c.norm(r['title']),r['startDate'],r['endDate'],r['year'],r['endYear'],r['dateDisplay'],r['datePrecision'],r['stateBasis'],r['series'],BATCH))
    db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(source,r['id'],r['provider'],r['nativeID'],r['url'],r['receipt']['retrievedAt'],r['receipt']['path'],r['receipt']['sha256'],Jsonb(r['payload']),Jsonb(dict(research_issues=r['issues'],operation=BATCH))))
    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(occurrence,r['id'],source,r['institutionID'],r['venue'],r['city'],r['country'],r['countryCode'],r['startDate'],r['endDate'],r['dateDisplay'],Jsonb(dict(sourceURL=r['url'],sourcePage=r['payload'].get('sourcePage'),originalLabels=r['payload'].get('rawCells'),holdingClaim=False,currentDisplayClaim=False))))
    for n,pub in enumerate(r['publications']):
     db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,publication_date_label,url,source_identifier,evidence)VALUES(%s,%s,%s,'catalogue',%s,%s,%s,%s,%s)",(c.uid('publication/'+r['provider']+'/'+r['nativeID']+'/'+str(n)),r['id'],source,pub['title'],str(r['year']),pub['url'],pub['sourceIdentifier'],Jsonb(pub['evidence'])))
  for provider,years,sourceurl,details in [
   ('royal-academy',(1769,1989),'https://chronicle250.com/',dict(documentedEvents=221,catalogueEntryTranscription='partial, 1769 under review',geography='London; no worldwide-completeness claim')),
   ('orsay-historical-index',(1673,1961),records[-1]['url'],dict(documentedEvents=1326,tableRows=2800,initialHeldRows=1464,extractionHeldRows=8,duplicateRows=2,coverage='Selected documented visual-art exhibitions. Rows outside selected media and unresolved dates/identities retained as research leads.'))]:
   db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,claimed_start_year,claimed_end_year,inspected_start_year,inspected_end_year,research_state,details)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'partial',%s)",(c.uid('coverage/'+BATCH+'/'+provider),RA_ID if provider=='royal-academy'else None,provider,sourceurl,*years,*years,Jsonb(details)))
  count=db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(BATCH,)).fetchone()['n'];assert count==1547
  active=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 c.save(OUT/'historical-import-delivered.json',dict(at=c.now(),batch=BATCH,counts=p['counts'],activeExhibitions=active,planSHA256=c.sha((OUT/'historical-import-plan.json').read_bytes()),realLocalDatabaseWrites=False,mainCatalogueWrites=False,artworkChecklistComplete=False))
 print('Historical exhibition records committed',count,'active',active,flush=True)
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply']:raise SystemExit('Use plan or apply')
 globals()[sys.argv[1]]()
