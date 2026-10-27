"""Thirty reviewed maker identities from exact native notices and closed biographies."""
import gzip
import importlib.util
import json
import re
import sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

s=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=m.E/'additional-creators';B=m.B/'additional-creators';OP=m.OP+'-additional-creators'
QUALIFIED=re.compile(r'genre de|mani[eè]re de|cercle|imitat|style de|[ée]l[eè]ve|follower|after|workshop|school|attribu|atelier|[ée]cole|entourage|suiveur|d.apr[eè]s|copie|anonyme|\?',re.I)


def plan():
    selected=c.load(m.E/'rouen-additional-creator-selection.json.gz')['selected']
    for r in c.load(m.E/'rouen-creator-full-name-extension-review.json.gz')['candidates']:
        native=c.load(m.D/'rouen-notices'/(r['native_id']+'.json.gz'))
        selected.append(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],artist=r['artist'],
                             current_source_creator_label=r['label'],current_source_author_precision=r['precision'],
                             source_url=native['receipt']['url'],source_snapshot=native['receipt'],
                             name_basis='Reviewed abbreviated given names are compatible with the uniquely matching full name/alias and both explicit life years.'))
    assert len(selected)==30 and len({r['artwork_id']for r in selected})==30
    for r in selected:
        assert not QUALIFIED.search(r['current_source_creator_label'])
        text=r['current_source_creator_label']+' '+r['current_source_author_precision']
        years=set(map(int,re.findall(r'\b(1\d{3})\b',text)))
        assert years=={r['artist']['birth_year'],r['artist']['death_year']}and len(years)==2
        assert not re.search(r'\?|vers|circa|avant|après|apres|probabl|actif',r['current_source_author_precision'],re.I)
        assert c.sha(gzip.decompress(Path(r['source_snapshot']['body_path']).read_bytes()))==r['source_snapshot']['sha256']
    ids=[r['artwork_id']for r in selected]
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        tables={t:m.rows(db,t,col,ids)for t,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id')]}
        assert not tables['artwork_artists']
        artists=m.rows(db,'artists','id',[r['artist']['id']for r in selected]);live={a['id']:a for a in artists}
        aliases=m.rows(db,'artist_aliases','artist_id',list(live))
        works={a['id']:a for a in tables['artworks']}
        for r in selected:
            assert all(live[r['artist']['id']][k]==v for k,v in r['artist'].items()if k!='aliases')
            assert set(r['artist']['aliases'])<={v['alias']for v in aliases if v['artist_id']==r['artist']['id']}
            n=c.load(m.D/'rouen-notices'/(r['native_id']+'.json.gz'))
            assert c.norm(works[r['artwork_id']]['title'])==c.norm(n['fields']['Titre'])
            if works[r['artwork_id']]['accession_number']:
                assert c.norm(works[r['artwork_id']]['accession_number'])==c.norm(n['fields']["Numéro d'inventaire"])
            assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork'AND entity_id=%s AND(source_record_id=%s OR source_url=%s) LIMIT 1",(r['artwork_id'],r['native_id'],r['source_url'])).fetchone()
        source=db.execute("SELECT id::text FROM sources WHERE slug='joconde-m0729'").fetchone()['id']
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    c.save(B/'plan.json.gz',dict(at=c.now(),selected=selected,tables=tables,artists=artists,artist_aliases=aliases,source_id=source))
    c.save(E/'plan-pin.json',dict(at=c.now(),path=str(B/'plan.json.gz'),sha256=c.sha((B/'plan.json.gz').read_bytes()),creator_links=30,new_artists=0))
    print('Pinned30 exact native works and reviewed existing maker identities.',flush=True)


def apply():
    assert c.sha((B/'plan.json.gz').read_bytes())==c.load(E/'plan-pin.json')['sha256'];p=c.load(B/'plan.json.gz');ids=[r['artwork_id']for r in p['selected']];changes=[]
    with c.connect(write=True)as db:
        m.acquire_locks(db)
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall()
        for t,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id')]:
            assert m.ordered(m.rows(db,t,col,ids))==m.ordered(p['tables'][t]),('Changed preimage',t)
        assert m.ordered(m.rows(db,'artists','id',[a['id']for a in p['artists']]))==m.ordered(p['artists'])
        assert m.ordered(m.rows(db,'artist_aliases','artist_id',[a['id']for a in p['artists']]))==m.ordered(p['artist_aliases'])
        c.save(B/'locked-before.json.gz',dict(at=c.now(),plan=p))
        for r in p['selected']:
            aid=r['artwork_id'];artist=r['artist']['id']
            note='Exact source maker and both explicit closed life years agree with the reviewed existing full name/alias. Abbreviated given names do not introduce another person. Source qualifications, artwork facts and profile life dates unchanged. '+r['source_url']
            link=db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,representative_order,attribution_note)VALUES(%s,%s,'primary',1,%s)RETURNING to_jsonb(artwork_artists)v",(aid,artist,note)).fetchone()['v']
            citation=db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artwork',%s,'rouen_closed_biography_creator',%s,%s,%s,%s,now(),%s)RETURNING to_jsonb(citations)v",(m.uid(OP+'/citation/'+aid),aid,p['source_id'],r['native_id'],r['source_url'],json.dumps(dict(operation=OP,reviewed_identity=r,qualification_test=QUALIFIED.pattern,identity_basis=note),ensure_ascii=False),m.EDITOR)).fetchone()['v']
            changes.extend([dict(table='artwork_artists',key=aid+'/'+artist,entity_id=aid,before=None,after=link),dict(table='citations',key=citation['id'],before=None,after=citation)])
        for t,col in [('artworks','id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id')]:assert m.ordered(m.rows(db,t,col,ids))==m.ordered(p['tables'][t])
        m.audit(db,changes,OP);c.save(B/'transaction-after.json.gz',dict(at=c.now(),changes=changes,operation=OP))
    verify()


def verify():
    p=c.load(B/'plan.json.gz');tx=c.load(B/'transaction-after.json.gz');ids=[r['artwork_id']for r in p['selected']]
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for t,col in [('artworks','id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id')]:assert m.ordered(m.rows(db,t,col,ids))==m.ordered(p['tables'][t])
        for t,col in [('artwork_artists','artwork_id'),('citations','entity_id')]:
            expected=[r['after']for r in tx['changes']if r['table']==t];live=m.rows(db,t,col,ids)
            assert all(r in live for r in expected)
        keys=[m.uid(OP+'/'+r['table']+'/'+r['key'])for r in tx['changes']]
        aa={str(r['id']):r for r in db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',(keys,))}
        assert len(aa)==60 and all(aa[k]['before_json']==r['before']and aa[k]['after_json']==r['after']for k,r in zip(keys,tx['changes']))
    public=[];session=requests.Session()
    for r in p['selected']:
        response=session.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/atlas/artworks/'+r['artwork_id'],timeout=(10,35))
        assert response.status_code==200 and r['artist']['id']in response.text
        public.append(dict(artwork_id=r['artwork_id'],artist_id=r['artist']['id'],status=200))
    c.save(E/'final-verification.json',dict(at=c.now(),passed=True,creator_links=30,distinct_existing_profiles=len(p['artists']),atomic_audits=60,public=public,metadata_images_holdings_profiles_preserved=True,new_artists=0))
    print('Thirty additional Rouen maker links independently and publicly verified.',flush=True)


if __name__=='__main__':globals()[sys.argv[1]]()
