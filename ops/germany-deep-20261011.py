#!/usr/bin/env python3
"""Selected German museum research; immutable receipts and a read-only local audit."""
import collections,concurrent.futures,importlib.util,json,sys
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/germany-deep-20261011'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
s=importlib.util.spec_from_file_location('de_sources',ROOT/'ops/cyprus-deep-20261010.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
h=base.h;h.RUN=RUN;h.BACKUP=BACKUP;base.RUN=RUN;page=base.page
def baseline():
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=120000')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        institutions=db.execute("""SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,i.status,p.country_code,p.name city,
        ARRAY(SELECT DISTINCT vp.country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id) venue_countries
        FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE i.status<>'archived' ORDER BY i.name""").fetchall()
        assert len(institutions)<10000
        museums=[i for i in institutions if i['country_code']=='DE'or'DE'in i['venue_countries']]
        ids=[i['id']for i in museums]
        works=[r['v']for r in db.execute("""WITH selected AS MATERIALIZED(
        SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
        UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND claim_type='holding' AND review_state IN('review','accepted') AND superseded_by IS NULL)
        SELECT to_jsonb(a)v FROM artworks a JOIN selected s ON s.id=a.id WHERE a.status<>'archived' ORDER BY a.id""",(ids,ids))]
        aids=[a['id']for a in works]
        assertions=db.execute("SELECT artwork_id::text,institution_id::text,source_url,review_state FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])AND claim_type='holding'AND superseded_by IS NULL",(aids,)).fetchall()
        citations=db.execute("SELECT entity_id::text,field_name,source_url,source_record_id FROM citations WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(aids,)).fetchall()
        media=db.execute("SELECT a.id::text artwork_id,m.storage_path,m.source_page_url,m.license_label,m.creator_credit FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])",(aids,)).fetchall()
        artists=db.execute("SELECT aa.artwork_id::text,aa.artist_id::text,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])",(aids,)).fetchall()
        meta=db.execute("SELECT now() snapshot_at,current_database()database,current_setting('transaction_read_only')read_only").fetchone()
    for mu in museums:
        a={x['id']:x for x in works if x['current_institution_id']==mu['id']}
        for x in assertions:
            if x['institution_id']==mu['id']and x['review_state']in['review','accepted']:
                a.update({w['id']:w for w in works if w['id']==x['artwork_id']})
        mu['artworks']=len(a);mu['images']=sum(bool(x['primary_media_id'])for x in a.values())
    h.save(RUN/'local-reference-audit.json.gz',dict(at=h.now(),target='real local database; read-only reference, not a production parity claim',snapshot=meta,museums=museums,institution_register=institutions,artworks=works,holding_assertions=assertions,citations=citations,media=media,artist_links=artists))
    print('LOCAL READ ONLY',len(museums),'institutions',len(works),'distinct artworks',len(media),'primary media')
    for mu in museums:print(mu['name'],mu['artworks'],mu['images'],mu['website_url'])
def capture():
    def one(url):
        try:
            p=page(url);return [p['receipt']['status'],url,p['title'],len(p['images'])]
        except Exception as e:return ['FAILED',url,type(e).__name__,str(e)[:180]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for x in pool.map(one,sys.argv[2:]):print(json.dumps(x,ensure_ascii=False),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
