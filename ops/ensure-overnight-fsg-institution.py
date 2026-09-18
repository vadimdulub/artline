#!/usr/bin/env python3
"""Create the source-documented holding museum in existing schema, idempotently."""
import importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/overnight-images-20260915/fsg'
s=importlib.util.spec_from_file_location('fsg',ROOT/'ops/overnight-fsg-images.py');fsg=importlib.util.module_from_spec(s);s.loader.exec_module(fsg);core=fsg.core
def main():
    path=RUN/'institution.html';receipt_path=RUN/'institution.receipt.json'
    if not path.exists():
        raw,headers=core.Fetcher(RUN/'institution-capture').get(fsg.POLICY,3_000_000)
        core.save_new(path,raw);core.save_new(receipt_path,{'url':fsg.POLICY,'retrieved_at':core.now(),'sha256':core.sha(raw),'headers':headers})
    raw=path.read_bytes();receipt=json.loads(receipt_path.read_text());assert core.sha(raw)==receipt['sha256'] and receipt['url']==fsg.POLICY
    assert all(v in raw.decode() for v in ('National Museum of Asian Art','Washington','1050 Independence','CC0'))
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/fsg';results=[]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
            before=db.execute("SELECT to_jsonb(i) institution FROM institutions i WHERE slug=%s OR website_url='https://asia.si.edu/' OR name ILIKE '%%Freer%%' OR name ILIKE '%%Sackler%%' OR name ILIKE '%%National Museum of Asian Art%%'",(fsg.SLUG,)).fetchall()
            if not (backup/(target+'-institution-before.json')).exists():core.save_new(backup/(target+'-institution-before.json'),before)
            places=db.execute("SELECT id FROM places WHERE name='Washington, DC' AND country_code='US'").fetchall();assert len(places)==1
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                assert not before or (len(before)==1 and before[0]['institution']['id']==fsg.INSTITUTION_ID),'Existing museum identity requires reconciliation'
                db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('overnight-fsg-primary-20260915','National Museum of Asian Art: public Smithsonian catalogue and exact CC0 media','museum_api','https://asia.si.edu/',%s) ON CONFLICT(slug) DO NOTHING",(fsg.POLICY,))
                sid=db.execute("SELECT id FROM sources WHERE slug='overnight-fsg-primary-20260915'").fetchone()['id']
                db.execute("INSERT INTO institutions(id,slug,name,normalized_name,kind,status,website_url,place_id) VALUES(%s,%s,%s,'national museum of asian art','museum','review','https://asia.si.edu/',%s) ON CONFLICT(id) DO NOTHING",(fsg.INSTITUTION_ID,fsg.SLUG,fsg.NAME,places[0]['id']))
                actual=db.execute('SELECT name,slug,website_url,place_id FROM institutions WHERE id=%s',(fsg.INSTITUTION_ID,)).fetchone()
                assert actual=={'name':fsg.NAME,'slug':fsg.SLUG,'website_url':'https://asia.si.edu/','place_id':places[0]['id']}
                if not db.execute("SELECT 1 FROM citations WHERE entity_type='institution' AND entity_id=%s AND source_id=%s",(fsg.INSTITUTION_ID,sid)).fetchone():
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at) VALUES('institution',%s,%s,'identity_and_location',%s,%s,%s)",(fsg.INSTITUTION_ID,sid,fsg.POLICY,json.dumps({'official_name':fsg.NAME,'address':'1050 Independence Avenue SW, Washington, DC, United States','metadata_capture':receipt,'collection_policy':'Individual source records retain Freer/Sackler collection names and donor credit. Institution country never establishes painter nationality.'}),receipt['retrieved_at']))
            results.append({'target':target,'institution_id':fsg.INSTITUTION_ID});print(target,'FSG institution verified',flush=True)
    core.save_new(RUN/'institution-verified.json',results)
if __name__=='__main__':main()
