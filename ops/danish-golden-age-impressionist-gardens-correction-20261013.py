#!/usr/bin/env python3
"""Correct nine OCR date/title edges and remove approximate page labels from the 2010 catalogue wave."""
import argparse,datetime,importlib.util,json,uuid
from pathlib import Path
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013/catalogue-checklists';DATA=RUN/'impressionist-gardens-2010.json';NS=uuid.UUID('c737734b-acbe-478d-94f7-26aa6cbba4fb');OP='danish-golden-age-impressionist-gardens-20261013';SOURCE='danish-golden-age-impressionist-gardens-20261013'
s=importlib.util.spec_from_file_location('c',ROOT/'ops/catalogue-expansion-20261008.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def uid(v):return str(uuid.uuid5(NS,OP+'/'+v))
def plan():
 items=json.loads(DATA.read_text());ids=[uid('entry/'+str(x['number'])) for x in items]
 with c.connect() as db:before=[dict(r) for r in db.execute('select id::text,title_label,date_label,source_page,evidence from exhibition_entries where id=any(%s::uuid[]) order by id',(ids,))]
 assert len(before)==97;p={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'items':items};(RUN/'impressionist-gardens-correction-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2,default=str)+'\n');print({'rows':97,'ocr_edge_fixes':9})
def apply():
 p=json.loads((RUN/'impressionist-gardens-correction-plan.json').read_text());ids=[x['id'] for x in p['before']]
 with c.connect(True) as db,db.transaction():
  db.execute("set local lock_timeout='120s'");db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");now=[dict(r) for r in db.execute('select id::text,title_label,date_label,source_page,evidence from exhibition_entries where id=any(%s::uuid[]) order by id for update',(ids,))];assert now==p['before']
  for x in p['items']:
   evidence={'source_line':x['source_line'],'creation_year_start':x['year_start'],'creation_year_end':x['year_end'],'before_1980':True,'source_capture_sha256':'215fb1f8f4a60180e81a9584f1d33e9d52667dd2ff862ec4b5db65f713571179','ocr_review':'All date labels reviewed; two-digit range endings expanded only in structured evidence.'}
   db.execute('update exhibition_entries set title_label=%s,date_label=%s,source_page=%s,evidence=%s where id=%s',(x['title'],x['date_label'],'Catalogue pp. 141–173',Jsonb(evidence),uid('entry/'+str(x['number']))))
 with c.connect() as db:
  n=db.execute("select count(*) n from exhibition_entries x join exhibition_source_records s on s.id=x.source_record_id where s.source_record_id=%s and (x.evidence->>'before_1980')::boolean",(SOURCE,)).fetchone()['n'];assert n==97
 (RUN/'impressionist-gardens-correction-applied.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':n},indent=2)+'\n');print({'rows':n})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['plan','apply']);globals()[a.parse_args().phase]()
