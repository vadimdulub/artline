#!/usr/bin/env python3
"""Ingest the complete event-level catalogue for Impressionist Gardens (2010–11)."""
import argparse,datetime,hashlib,importlib.util,json,uuid
from pathlib import Path
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013/catalogue-checklists';DATA=RUN/'impressionist-gardens-2010.json'
EVENT='ec7121d4-0bbf-53e8-9980-0e276ec38a67';OP='danish-golden-age-impressionist-gardens-20261013';NS=uuid.UUID('c737734b-acbe-478d-94f7-26aa6cbba4fb')
ITEM='impressionist-gardens';URL='https://archive.org/details/impressionist-gardens';TEXT_URL='https://archive.org/download/impressionist-gardens/impressionist%20gardens%E6%89%AB%E6%8F%8F%E6%BA%90%E6%96%87%E4%BB%B6_djvu.txt';SHA='215fb1f8f4a60180e81a9584f1d33e9d52667dd2ff862ec4b5db65f713571179'
s=importlib.util.spec_from_file_location('c',ROOT/'ops/catalogue-expansion-20261008.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def uid(v):return str(uuid.uuid5(NS,OP+'/'+v))
def plan():
 items=json.loads(DATA.read_text());assert len(items)==97 and [x['number'] for x in items]==list(range(1,98));assert all(not x.get('year_end') or x['year_end']<1980 for x in items)
 with c.connect() as db:
  event=db.execute('select to_jsonb(e) row from exhibitions e where id=%s',(EVENT,)).fetchone()['row'];before=[dict(r) for r in db.execute('select id::text,artwork_id::text,source_artwork_id,title_label,creator_label from exhibition_entries where exhibition_id=%s order by id',(EVENT,))];assert len(before)==1
  assert not db.execute("select 1 from exhibition_source_records where source_key='internet-archive' and source_record_id=%s",(OP,)).fetchone()
 p={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,'existing_entries':before,'items':items,'totals':{'entries':97,'linked':0,'unlinked':97}};(RUN/'impressionist-gardens-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2,default=str)+'\n');print(p['totals'])
def apply():
 p=json.loads((RUN/'impressionist-gardens-plan.json').read_text());sid=uid('source');assert json.loads((ROOT/'docs/research/danish-golden-age-20261013/cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with c.connect(True) as db,db.transaction():
  db.execute("set local lock_timeout='120s'");db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101306)')
  assert db.execute('select to_jsonb(e) row from exhibitions e where id=%s for share',(EVENT,)).fetchone()['row']==p['event'];assert [dict(r) for r in db.execute('select id::text,artwork_id::text,source_artwork_id,title_label,creator_label from exhibition_entries where exhibition_id=%s order by id',(EVENT,))]==p['existing_entries']
  payload={'title':'Impressionist Gardens','author':'Clare A. P. Willsdon','publisher':'Thames & Hudson','isbn':'978-0-500-28881-8','catalogue_pages':'141–173','entries':97,'tour':['National Galleries of Scotland, Edinburgh','Museo Thyssen-Bornemisza, Madrid']}
  db.execute("insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,'internet-archive',%s,%s,now(),%s,%s,%s,%s)",(sid,EVENT,OP,URL,TEXT_URL,SHA,Jsonb(payload),Jsonb({'scope':'All 97 consecutively numbered catalogue entries parsed from the readable exhibition book.','participation':'Entries are event-level and recorded as catalogued because the book covers the Edinburgh and Madrid tour and explicitly marks at least one venue-only work.','identity':'No production artwork passed exact normalized title, compatible creator, and compatible date matching; all entries remain unlinked.','existing_source_conflict':'The existing SMK-derived KMS2059 association does not appear in this 97-work book; absence is recorded without deleting the independent object-history assertion.'})))
  db.execute("insert into exhibition_publications(id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence) values(%s,%s,%s,'catalogue','Impressionist Gardens','Clare A. P. Willsdon','2010',%s,'ISBN 978-0-500-28881-8','Catalogue pp. 141–173',%s)",(uid('publication'),EVENT,sid,URL,Jsonb({'publisher':'Thames & Hudson','copyright_holder':'Trustees of the National Galleries of Scotland','entry_count':97,'touring_catalogue':True})))
  for x in p['items']:
   evidence={'source_line':x['source_line'],'creation_year_start':x.get('year_start'),'creation_year_end':x.get('year_end'),'before_1980':True,'source_capture_sha256':SHA}
   db.execute("insert into exhibition_entries(id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,participation,source_page,evidence,match_basis) values(%s,%s,%s,null,null,%s,%s,%s,%s,'catalogued',%s,%s,null)",(uid('entry/'+str(x['number'])),EVENT,sid,str(x['number']),x['title'],x['creator'],x.get('date_label'),str(141+(x['number']-1)*33//97),Jsonb(evidence)))
  db.execute("insert into exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) values(%s,'internet-archive',%s,2010,2011,'source_exhausted',%s)",(uid('coverage'),URL,Jsonb({'document':'Complete readable catalogue','catalogue_entries':97,'exact_artwork_links':0,'unresolved_entries':97,'existing_non_catalogue_assertion':'KMS2059'})))
 with c.connect() as db:
  out=dict(db.execute('select count(*) entries,count(artwork_id) linked,count(*) filter(where artwork_id is null) unlinked from exhibition_entries where source_record_id=%s',(sid,)).fetchone());assert out==p['totals'];(RUN/'impressionist-gardens-applied.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**out},indent=2)+'\n');print(out)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['plan','apply']);globals()[a.parse_args().phase]()
