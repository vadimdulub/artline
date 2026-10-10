#!/usr/bin/env python3
"""Resumable source-backed expansion toward one million catalogue artworks.

Production writes require pinned selections and recovery backups; local stays read-only.
"""
import argparse,collections,datetime,gzip,hashlib,importlib.util,json,os,re,subprocess,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1];OP='million-catalogue-20261010';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
DATA=Path.home()/'Library/Application Support/Artline/source-metadata'/OP
ACTOR='local-european-research';TARGET=1000000
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
save,load,sha,now,chunks,norm=m.save,m.load,m.sha,m.now,m.chunks,m.norm
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def baseline():
    path=RUN/'baseline.json.gz'
    if path.exists():print('Existing immutable baseline');return
    with m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        counts=dict(artists=db.execute("SELECT count(*) total,count(*) FILTER(WHERE status<>'archived') active FROM artists").fetchone(),artworks=db.execute("""SELECT count(*) total,count(*) FILTER(WHERE status<>'archived') active,
          count(*) FILTER(WHERE status<>'archived' AND primary_media_id IS NOT NULL) illustrated,
          count(*) FILTER(WHERE status<>'archived' AND creation_year_end<=1970) through_1970,
          count(*) FILTER(WHERE status<>'archived' AND (creation_year_start IS NULL OR creation_year_end IS NULL)) unknown_date,
          count(*) FILTER(WHERE status<>'archived' AND creation_year_start>1970) after_1970,
          count(*) FILTER(WHERE status<>'archived' AND creation_year_start<=1970 AND creation_year_end>1970) crosses_1970
          FROM artworks""").fetchone())
        schemes=db.execute("SELECT e.scheme,count(*) n,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) illustrated FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND a.status<>'archived' GROUP BY e.scheme ORDER BY n DESC").fetchall()
        institutions=db.execute("SELECT i.id::text,i.name,i.slug,i.website_url,count(*) n,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) illustrated FROM institutions i JOIN artworks a ON a.current_institution_id=i.id WHERE a.status<>'archived' GROUP BY i.id ORDER BY n DESC").fetchall()
        types=db.execute("SELECT work_type,count(*) n FROM artworks WHERE status<>'archived' GROUP BY work_type ORDER BY n DESC").fetchall()
        sources=db.execute('SELECT id::text,slug,name,base_url,adapter_key FROM sources ORDER BY slug').fetchall()
        indexes=db.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename IN ('artworks','external_identifiers','artwork_artists') ORDER BY tablename,indexname").fetchall()
        views=db.execute("SELECT matviewname FROM pg_matviews WHERE schemaname='public'").fetchall()
    with m.connect(local=True) as db:
        local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','artwork_artists','media_assets']}
    value=dict(at=now(),target='production',counts=counts,source_schemes=schemes,institutions=institutions,work_types=types,sources=sources,indexes=indexes,materialized_views=views,local_readonly_counts=local)
    save(path,value);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'baseline.json.gz',value)
    save(RUN/'authorization.json',dict(at=now(),user_instruction="ok, our goal is - add more painters and more artworks and more images our goal is 1mln artowrks! don't stop while u have not finished!",target=TARGET,production_bulk_ingestion_authorized=True,local_database_read_only=True,scope='Existing content/date/image policies retained; no placeholders or duplicate/version inflation.'))
    print(json.dumps(dict(counts=counts,remaining_active_records=TARGET-counts['artworks']['active'],largest_sources=schemes[:25],largest_collections=institutions[:20],work_types=types),indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['baseline']);args=p.parse_args();globals()[args.command]()
