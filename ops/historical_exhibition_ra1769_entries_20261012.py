#!/usr/bin/env python3
"""Fifteen visually checked entries from the 1769 catalogue, pages 5 and 8.
Two exact canonical painting links have independent museum exhibition histories.
"""
from pathlib import Path
import sys,json
from psycopg.types.json import Jsonb
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/royal-academy/1769'
EID=c.uid('royal-academy/summer/1769');SID=c.uid('source/royal-academy/1769')
PEOPLE=[('cipriani','J. Baptist Cipriani','bafc6b74-a165-50d1-8368-a2a16064a60b'),('clarke','Thomas Clarke',None),('francis-cotes','Francis Cotes','5526ab45-f65e-46e2-b2e2-ebcd43a40c0b'),('samuel-cotes','Samuel Cotes',None),('kauffman','Angelica Kauffman','590d1184-0c0b-476f-b972-1cbe01a0ae61')]
ROWS=[
(19,'cipriani','Cephalus and Procris.',None),(20,'cipriani','The Annunciation.',None),(21,'clarke','A portrait in oil.','oil'),
(22,'francis-cotes','A portrait of a lady, whole length.',None),(23,'francis-cotes','Ditto of a young gentleman.',None),(24,'francis-cotes','Ditto of a lady, half length.',None),(25,'francis-cotes','Ditto of a gentleman.',None),(26,'francis-cotes','Ditto, of a lady and gentleman at chess.',None),(27,'francis-cotes','A portrait in crayons of his Royal Highness the Duke of Gloucester.','crayons'),(28,'francis-cotes','A young lady ditto in the character of Hebe.','crayons; catalogue ditto refers to no. 27'),(29,'samuel-cotes','A portrait in miniature of Mrs. Yates, in the character of Electra.','miniature'),
(61,'kauffman','The interview of Hector and Andromache.',None),(62,'kauffman','Achilles discovered by Ulysses amongst the attendants of Deidamia.',None),(63,'kauffman','Venus shewing Æneas and Achates the way to Carthage.','oil on canvas'),(64,'kauffman','Penelope taking down the bow of Ulysses for the trial of her wooers.','oil on canvas')]
MATCHES={63:('59d99d94-0b90-573c-be17-0f5994646cf5','872178'),64:('50b0cfb0-95de-5566-a491-4a8fe932b27d','872173')}

def plan():
 manifest=c.load(OUT/'manifest-0.json');records=[];people={k:(name,aid)for k,name,aid in PEOPLE}
 for num,key,title,medium in ROWS:
  page=5 if num<60 else 8;canvas=manifest['sequences'][0]['canvases'][page-1]
  image=c.load(OUT/f'catalogue-page-{page}-image-receipt.json')if page==5 else c.load(OUT/f'catalogue-page-{page}.jpg.receipt.json')
  evidence=dict(primaryCatalogue='The Exhibition of the Royal Academy MDCCLXIX. The First',printedPage=page,catalogueNumber=str(num),canvas=canvas['@id'],manifestURL=manifest['@id'],scanReceipt=image,transcription='Visually checked against the catalogue scan; long-s normalized. Ditto retained. Medium unknown unless stated or independently identified.',sourceCreatorLabel=people[key][0])
  if num in MATCHES:
   aid,native=MATCHES[num];evidence['independentMuseumHistory']=dict(url='https://www.nationaltrustcollections.org.uk/object/'+native,nativeObjectID=native,finding='Museum object record explicitly documents Royal Academy 1769. Same creator, composition, date and Saltram painting identity; checked against the retained WikiArt reproduction.',retrievalReceipt=c.load(OUT/('nt-'+native+'.html.receipt.json')))
   evidence['identityReview']=dict(editorialConfidence=.98,qualified=False,versionNote='The 1768 Saltram painting, not later Kauffman versions, prints, or copies. Existing media preserved.')
  records.append(dict(id=c.uid('entry/royal-academy/1769/'+str(num)),number=str(num),personKey=key,title=title,creator=people[key][0],medium=medium,page=str(page),artworkID=MATCHES[num][0]if num in MATCHES else None,participation='exhibited'if num in MATCHES else'catalogued',date='1768'if num in MATCHES else None,evidence=evidence))
 with c.connect()as db:
  assert db.execute('SELECT title FROM exhibitions WHERE id=%s',(EID,)).fetchone()['title']=='Royal Academy Summer Exhibition 1769'
  works=db.execute('SELECT id,title,creation_year_start,primary_media_id,revision FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['artworkID']for r in records if r['artworkID']],)).fetchall();assert len(works)==2 and all(r['primary_media_id']for r in works)
 c.save(OUT/'entry-delivery-plan.json',dict(at=c.now(),exhibitionID=EID,entries=records,people=PEOPLE,pinnedArtworks=works,fullCatalogueChecklist=False,remainingCatalogueNumbers='Other pages remain untranscribed; sculpture and architecture excluded from this selected page pass.'))
 print('Prepared 15 catalogue entries, 5 named participants, 2 exact illustrated painting links',flush=True)

def apply():
 p=c.load(OUT/'entry-delivery-plan-v2.json')
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert db.execute('SELECT count(*) n FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchone()['n']==0
  current=db.execute('SELECT id,title,creation_year_start,primary_media_id,revision FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR SHARE',([r['artworkID']for r in p['entries']if r['artworkID']],)).fetchall();assert json.loads(json.dumps(current,default=str))==p['pinnedArtworks']
  with db.pipeline():
   for key,name,aid in p['people']:
    db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)VALUES(%s,%s,%s,%s,%s,'Artist',%s,%s)",(c.uid('participant/royal-academy/1769/'+key),EID,SID,aid,name,key,Jsonb(dict(catalogueYear=1769,printedPage='8'if key=='kauffman'else'5',canonicalIdentity='Named historical painter reconciled to existing record'if aid else'Unresolved canonical artist; original creator label retained'))))
   for e in p['entries']:
    db.execute('INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,source_page,evidence,match_basis)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['id'],EID,SID,e['artworkID'],'RA1769/'+e['number'],e['number'],e['title'],e['creator'],e['date'],e['medium'],e['participation'],e['page'],Jsonb(e['evidence']),'Original catalogue number plus explicit museum exhibition history and same-object visual/metadata check'if e['artworkID']else None))
   db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s",(EID,))
  assert db.execute('SELECT count(*) n,count(artwork_id) linked FROM exhibition_entries WHERE exhibition_id=%s',(EID,)).fetchone()==dict(n=15,linked=2)
 c.save(OUT/'entry-delivery-receipt.json',dict(at=c.now(),entries=15,participants=5,canonicalPaintingLinks=2,existingImagesPreserved=2,newImages=0,exhibitionID=EID,mainCatalogueWrites=False,localDatabaseWrites=False,planSHA256=c.sha((OUT/'entry-delivery-plan-v2.json').read_bytes())))
 print('15 catalogue entries and 2 illustrated painting links committed',flush=True)
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1]not in ['plan','apply']:raise SystemExit('Use plan or apply')
 globals()[sys.argv[1]]()
