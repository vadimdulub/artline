#!/usr/bin/env python3
"""Apply catalogue-backed Danish Golden Age exhibition entries, preserving unlinked checklist rows."""
import argparse,datetime,hashlib,importlib.util,json,uuid
from pathlib import Path
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/danish-golden-age-20261013'
DATA=RUN/'catalogue-checklists/getty-beyond-the-light-2023.json'
EVENT='7bcb748c-5750-5be1-9432-0353961bd1bf';OCC='4308c0d6-753d-5848-8566-721e199118e3'
URL='https://www.getty.edu/art/exhibitions/denmark/downloads/denmark_checklist.pdf'
SHA='343238470423d2564c2000f29a4dc24d78bfa4ac2202a07b8de81cfc7e655a88'
OP='danish-golden-age-catalogue-checklists-20261013';NS=uuid.UUID('8169e541-2388-42d3-96ba-778ff87266ef')
s=importlib.util.spec_from_file_location('c',ROOT/'ops/catalogue-expansion-20261008.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def uid(v):return str(uuid.uuid5(NS,OP+'/'+v))
def compact(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def plan():
 items=json.loads(DATA.read_text())
 assert len(items)==81 and [x['number'] for x in items]==list(range(1,82))
 assert all(not x.get('selected_artwork_id') or int(x['title'].split()[-1].rstrip(',.').split('-')[0])<1980 for x in items if x['title'].split()[-1].rstrip(',.').split('-')[0].isdigit())
 with c.connect() as db:
  event=db.execute('SELECT to_jsonb(e) row FROM exhibitions e WHERE id=%s',(EVENT,)).fetchone()['row']
  occurrence=db.execute('SELECT to_jsonb(o) row FROM exhibition_occurrences o WHERE id=%s AND exhibition_id=%s',(OCC,EVENT)).fetchone()['row']
  ids=[x['selected_artwork_id'] for x in items if x.get('selected_artwork_id')]
  works={r['id']:r for r in db.execute("SELECT id::text,title,status,creation_year_start,creation_year_end FROM artworks WHERE id=ANY(%s::uuid[])",(ids,))}
  assert len(works)==len(set(ids)) and all(works[x]['status']!='archived' for x in works)
  assert not db.execute("SELECT 1 FROM exhibition_source_records WHERE source_key='getty' AND source_record_id=%s",(OP+'/beyond-the-light',)).fetchone()
 p={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,'occurrence':occurrence,'items':items,'works':works,'totals':{'entries':81,'linked':len(ids),'unlinked':81-len(ids)}}
 (RUN/'catalogue-checklists/getty-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2,default=str)+'\n');print(p['totals'])
def apply():
 p=json.loads((RUN/'catalogue-checklists/getty-plan.json').read_text());items=p['items'];sid=uid('source/beyond-the-light');pub=uid('publication/beyond-the-light')
 assert json.loads((RUN/'cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with c.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101304)')
  assert db.execute('SELECT to_jsonb(e) row FROM exhibitions e WHERE id=%s FOR SHARE',(EVENT,)).fetchone()['row']==p['event']
  assert db.execute('SELECT to_jsonb(o) row FROM exhibition_occurrences o WHERE id=%s FOR SHARE',(OCC,)).fetchone()['row']==p['occurrence']
  nowworks={r['id']:r for r in db.execute("SELECT id::text,title,status,creation_year_start,creation_year_end FROM artworks WHERE id=ANY(%s::uuid[])",([x['selected_artwork_id'] for x in items if x.get('selected_artwork_id')],))}
  assert nowworks==p['works']
  payload={'title':'Beyond the Light: Identity and Place in Nineteenth-Century Danish Art','venue':'The J. Paul Getty Museum at the Getty Center','dates':'May 23 to August 20, 2023','checklist_entries':items}
  db.execute("INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,'getty',%s,%s,now(),%s,%s,%s,%s)",(sid,EVENT,OP+'/beyond-the-light',URL,URL,SHA,Jsonb(payload),Jsonb({'scope':'Official seven-page Getty occurrence checklist, 81 numbered entries.','matching':'Only lender accessions or exact reconciliation to an independently documented SMK object-history identity are linked. Unresolved catalogue entries remain explicit and unlinked.','date_cutoff':'All checklist objects were created before 1980.'})))
  db.execute("INSERT INTO exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence) VALUES(%s,%s,%s,'checklist',%s,'J. Paul Getty Museum','May 22, 2023',%s,%s,'7 pages',%s)",(pub,EVENT,sid,payload['title'],URL,SHA,Jsonb({'entry_count':81,'complete_for_occurrence':True,'venue':payload['venue']})))
  for x in items:
   details=x['details'];dims=next((z for z in details if any(k in z for k in ('Unframed:','Image:','Page:'))),None)
   lender=' '.join(z for z in details if z!=dims and not z.startswith('EX.')) or None
   db.execute("""INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,medium_label,dimensions_label,lender_label,participation,source_page,evidence,match_basis)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s,%s)""",(uid('entry/'+str(x['number'])),EVENT,sid,OCC,x.get('selected_artwork_id'),x.get('source_artwork_id'),str(x['number']),x['title'],x['creator'],x['medium'],dims,lender,str((x['number']-1)//12+1),Jsonb({'official_checklist_identifiers':x['identifiers'],'raw_lines':x['raw'],'source_sha256':SHA,'creation_cutoff_review':'Title/date label is before 1980; no new artwork record was created.'}),x.get('match_basis')))
  db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) SELECT %s,institution_id,'getty',%s,2023,2023,'source_exhausted',%s FROM exhibition_occurrences WHERE id=%s",(uid('coverage/beyond-the-light'),URL,Jsonb({'scope':'Official occurrence checklist','entries':81,'linked':p['totals']['linked'],'unlinked':p['totals']['unlinked']}),OCC))
 with c.connect() as db:
  out=dict(db.execute("SELECT count(*) entries,count(artwork_id) linked,count(*) filter(where artwork_id is null) unlinked FROM exhibition_entries WHERE source_record_id=%s",(sid,)).fetchone())
 assert out==p['totals'];(RUN/'catalogue-checklists/getty-applied.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**out},indent=2)+'\n');print(out)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['plan','apply']);globals()[a.parse_args().phase]()
