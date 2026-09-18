#!/usr/bin/env python3
"""Add independently corroborated NGA IDs to existing artist identities."""
import argparse,csv,hashlib,importlib.util,json,re
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('overnight-nga-commons.py'));nga=importlib.util.module_from_spec(s);s.loader.exec_module(nga);core=nga.core
SOURCE='overnight-nga-creator-authorities-20260915'
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],required=True);a=p.parse_args();r=a.run;rows=json.loads((r/'discovery.json').read_text())['records'];reference=r.parent/'nga/metadata';receipt=json.loads((reference/'constituents.receipt.json').read_text())
 with (reference/'constituents.csv').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['sha256']
 with (reference/'constituents.csv').open() as f:people={c['constituentid']:c for c in csv.DictReader(f)}
 dsn='postgres://localhost/artline' if a.target=='local' else core.cloud_dsn();out=[];backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/r.name
 with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
  with db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260915)');before=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artist' AND scheme='nga-constituent' AND external_id=ANY(%s)",([c['person']['constituentid'] for c in rows],)).fetchall();path=backup/(a.target+'-before.json')
   if not path.exists():core.save_new(path,{'at':core.now(),'rows':json.loads(json.dumps(before,default=str))})
   db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'NGA: verified existing artist authorities','museum_api','https://github.com/NationalGalleryOfArt/opendata',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,nga.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
   for c in rows:
    person=c['person'];artist=c['artist'];pid=person['constituentid'];assert people[pid]==person and person['constituenttype']=='individual' and person['wikidataid']==artist['qid'] and c['selected_objects']
    hits=db.execute("SELECT a.id::text,a.slug,a.birth_year,a.death_year FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(artist['qid'],)).fetchall();assert len(hits)==1 and hits[0]['slug']==artist['slug'];target=hits[0]
    assert all(re.fullmatch(r'\d{4}',person[k]) and target[f]==int(person[k]) for k,f in [('beginyear','birth_year'),('endyear','death_year')])
    prior=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='nga-constituent' AND external_id=%s",(pid,)).fetchall()
    if prior:assert prior==[{'entity_id':target['id']}];out.append({'source_creator_id':pid,'artist_id':target['id'],'outcome':'already_present'});continue
    # The native authority's exact record is reproducible from this pinned
    # official CSV and ID. Do not invent a public artist page URL.
    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,source_id,retrieved_at) VALUES('artist',%s,'nga-constituent',%s,%s,%s)",(target['id'],pid,sid,receipt['retrieved_at']))
    facts={k:person[k] for k in ('constituentid','constituenttype','forwarddisplayname','beginyear','endyear','wikidataid')};evidence={'person_facts':facts,'source_capture':receipt,'identity_review':'Existing unique Wikidata identity and both birth/death years agree exactly. No artist merged and no biography, nationality or editorial state changed.','selected_artwork_ids':c['selected_objects']}
    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artist',%s,%s,'museum_creator_authority',%s,%s,%s,%s,%s)",(target['id'],sid,pid,receipt['url'],json.dumps(evidence,ensure_ascii=False),receipt['retrieved_at'],core.ACTOR));out.append({'source_creator_id':pid,'artist_id':target['id'],'outcome':'inserted'})
  checked=db.execute("SELECT count(*) n FROM external_identifiers WHERE entity_type='artist' AND scheme='nga-constituent' AND external_id=ANY(%s)",([c['person']['constituentid'] for c in rows],)).fetchone()['n'];assert checked==len(rows)
 core.save_new(r/(a.target+'-links-verified.json'),{'at':core.now(),'count':checked,'records':out});print(a.target,'Verified NGA creator links',checked,flush=True)
if __name__=='__main__':main()
