#!/usr/bin/env python3
"""Link exact surviving objects documented in the official 1830 Charlottenborg catalogue."""
import argparse,datetime,hashlib,importlib.util,json,uuid
from pathlib import Path
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013/catalogue-checklists'
EVENT='41b52f79-6880-5589-8b45-e281d578f670';OCC='b0c3df03-f67b-5d8b-8fc6-1a1a4a9cac6d';OP='danish-golden-age-charlottenborg-1830-20261013'
URL='https://kunstbiblioteket.kb.dk/objekter/udstillingskataloger/Udst_0663.pdf';SHA='ad6c715927f757f03e2e93de6b9e3aaa0ede02bb67397b75282bcda0ce7987dd';NS=uuid.UUID('15887edb-0e8e-4a4f-bb1c-462e7bd63349')
ITEMS=[
 {'number':'34','page':'5','source_title':'Vinterlandskab. I Forgrunden en forstyrret Kæmpegrav. Motivet taget af Vordingborgs Omegn. Udført ifølge Bestilling til Christiansborgslot.','creator':'C. Dahl','accession':'KMS167','artwork_id':'e0156801-59d9-4cf5-a4db-e5090d070cad'},
 {'number':'58','page':'6','source_title':'Et Familie-Malerie.','creator':'W. Bendz','accession':'KMS8003','artwork_id':'f31dfe71-6716-4eae-9d31-6977a9afb218'},
]
s=importlib.util.spec_from_file_location('c',ROOT/'ops/catalogue-expansion-20261008.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def uid(v):return str(uuid.uuid5(NS,OP+'/'+v))
def plan():
 with c.connect() as db:
  event=db.execute('select to_jsonb(e) row from exhibitions e where id=%s',(EVENT,)).fetchone()['row'];occ=db.execute('select to_jsonb(o) row from exhibition_occurrences o where id=%s',(OCC,)).fetchone()['row']
  works={r['accession_number']:dict(r) for r in db.execute('select id::text,accession_number,title,status,creation_year_start,creation_year_end from artworks where accession_number=any(%s)',([x['accession'] for x in ITEMS],))}
  assert set(works)=={'KMS167','KMS8003'} and all(works[x['accession']]['id']==x['artwork_id'] and works[x['accession']]['status']!='archived' for x in ITEMS)
  assert not db.execute("select 1 from exhibition_source_records where source_key='royal-danish-library' and source_record_id=%s",(OP,)).fetchone()
 p={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,'occurrence':occ,'works':works,'items':ITEMS};(RUN/'charlottenborg-1830-plan.json').write_text(json.dumps(p,indent=2,ensure_ascii=False,default=str)+'\n');print({'catalogue_entries_inspected':165,'exact_links':2})
def apply():
 p=json.loads((RUN/'charlottenborg-1830-plan.json').read_text());sid=uid('source');assert json.loads((ROOT/'docs/research/danish-golden-age-20261013/cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with c.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101305)')
  assert db.execute('select to_jsonb(e) row from exhibitions e where id=%s for share',(EVENT,)).fetchone()['row']==p['event'];assert db.execute('select to_jsonb(o) row from exhibition_occurrences o where id=%s for share',(OCC,)).fetchone()['row']==p['occurrence']
  db.execute("insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,'royal-danish-library',%s,%s,now(),%s,%s,%s,%s)",(sid,EVENT,OP,URL,URL,SHA,Jsonb({'title':'Fortegnelse over de ved det Kongelige Akademie for de skønne Kunster offentligen udstillede Kunstværker','year':1830,'pages':15,'numbered_through':165}),Jsonb({'scope':'Complete official exhibition catalogue inspected. This wave links only object identities corroborated by current museum catalogue records that cite the same 1830 catalogue number.','unresolved':'Remaining historical catalogue entries retain a reconciliation backlog; no title-only production links.'})))
  db.execute("insert into exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence) values(%s,%s,%s,'catalogue',%s,'Det Kongelige Akademie for de skønne Kunster','1830',%s,%s,'15 pages',%s)",(uid('publication'),EVENT,sid,'Fortegnelse over de ved det Kongelige Akademie for de skønne Kunster offentligen udstillede Kunstværker',URL,'Udst_0663',Jsonb({'repository':'Royal Danish Library / Danish Art Library','catalogue_number_extent':'1–165'})))
  for x in ITEMS:
   db.execute("insert into exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,participation,source_page,evidence,match_basis) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s,%s)",(uid('entry/'+x['number']),EVENT,sid,OCC,x['artwork_id'],x['accession'],x['number'],x['source_title'],x['creator'],x['page'],Jsonb({'official_catalogue_sha256':SHA,'museum_accession':x['accession'],'creation_cutoff_review':'Documented by the 1830 catalogue; before 1980.'}),'Official catalogue number plus the current SMK object record citation and unique SMK accession resolve the exact surviving object.'))
  db.execute("insert into exhibition_source_coverage(id,source_key,source_url,claimed_start_year,claimed_end_year,inspected_start_year,inspected_end_year,research_state,details) values(%s,'royal-danish-library',%s,1830,1830,1830,1830,'partial',%s)",(uid('coverage'),URL,Jsonb({'catalogue':'Udst_0663','full_catalogue_inspected':True,'numbered_through':165,'exact_object_links_applied':2,'remaining_identity_reconciliation':True})))
 with c.connect() as db:
  out=dict(db.execute('select count(*) entries,count(artwork_id) linked from exhibition_entries where source_record_id=%s',(sid,)).fetchone());assert out=={'entries':2,'linked':2};(RUN/'charlottenborg-1830-applied.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**out},indent=2)+'\n');print(out)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['plan','apply']);globals()[a.parse_args().phase]()
