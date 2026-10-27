"""Foreground continuation: fresh production snapshots and explicitly audited merges."""
import argparse
import json
import shutil
import uuid
from pathlib import Path

import exhibitions_common as c
from psycopg.types.json import Jsonb

OP = 'catalogue-deduplication-resume-20261027'
E = c.ROOT / 'docs/research/catalogue-deduplication-20261026/continuation-20261027'
D = Path.home() / 'Library/Application Support/Artline/source-metadata/catalogue-deduplication-20261026'
B = Path.home() / 'Library/Application Support/Artline/backups' / OP
EDITOR = 'local-european-research'
TABLES = {'institutions': 'id', 'artworks': 'current_institution_id',
          'artwork_location_assertions': 'institution_id', 'institution_venues': 'institution_id',
          'curated_collections': 'institution_id', 'exhibition_occurrences': 'institution_id',
          'exhibition_participants': 'institution_id', 'exhibition_source_coverage': 'institution_id',
          'source_institutions': 'institution_id'}


def uid(k):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + k))


def rows(db, table, column, ids):
    return [r['v'] for r in db.execute('SELECT to_jsonb(t)v FROM ' + table + ' t WHERE ' + column + '=ANY(%s::uuid[])', (ids,))]


def ordered(v):
    return sorted(v, key=lambda x: json.dumps(x, sort_keys=True))


def snapshot():
    pairs = c.load(E.parent / 'museum-additional-alias-source-preparation.json')['pairs']
    ids = [r[k] for r in pairs for k in ['alias_id', 'canonical_id']]
    images = c.load(D / 'rouen-image-delivery-preparation.json.gz')['images']
    aids = [r['artwork_id'] for r in images]
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        tables = {t: rows(db, t, col, ids) for t, col in TABLES.items()}
        cols = [r['id'] for r in tables['curated_collections']]
        tables['curated_collection_items'] = rows(db, 'curated_collection_items', 'collection_id', cols)
        c.save(E / 'museum-fresh-preimages.json.gz', dict(at=c.now(), pairs=pairs, ids=ids, tables=tables))
        selected = {t: rows(db, t, col, aids) for t, col in {
            'artworks': 'id', 'artwork_artists': 'artwork_id', 'artwork_media': 'artwork_id',
            'artwork_location_assertions': 'artwork_id'}.items()}
        selected['existing_assets'] = [r['v'] for r in db.execute('SELECT to_jsonb(m)v FROM media_assets m WHERE id=ANY(%s::uuid[]) OR checksum_sha256=ANY(%s) OR source_page_url=ANY(%s)', ([r['provisional_media_id'] for r in images], [r['sha256'] for r in images], [r['source_page'] for r in images]))]
        c.save(D / 'rouen-fresh-image-preimages-20261027.json.gz', dict(at=c.now(), tables=selected))
        schema = db.execute("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=ANY(%s) ORDER BY table_name,ordinal_position", (['media_assets','media_rights_evidence','artwork_media','sources','citations','exhibitions','slug_redirects'],)).fetchall()
        constraints = db.execute("SELECT conrelid::regclass::text table_name,conname,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE conrelid=ANY(%s::regclass[]) ORDER BY conrelid,conname", (['media_assets','media_rights_evidence','artwork_media','sources','citations','exhibitions','slug_redirects'],)).fetchall()
        sources = db.execute("SELECT to_jsonb(s)v FROM sources s WHERE lower(name) LIKE '%joconde%' OR lower(name) LIKE '%ministry%' OR base_url LIKE '%culture.gouv.fr%' LIMIT 30").fetchall()
        c.save(E / 'delivery-schema.json.gz',dict(at=c.now(),columns=schema,constraints=constraints,sources=[r['v'] for r in sources]))
    print(json.dumps(dict(museums=[{k:r[k] for k in ['id','slug','name','canonical_institution_id']} for r in tables['institutions']], table_counts={t:len(r) for t,r in tables.items()}, images=dict(selected=len(images), currently_illustrated=sum(r['primary_media_id'] is not None for r in selected['artworks']), existing_matching_assets=len(selected['existing_assets']))),indent=2))


def audit(db, changes, operation):
    with db.cursor() as cur:
        cur.executemany('INSERT INTO audit_log(id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,%s,%s,%s,%s,%s,%s)',
                        [(uid(operation + '/' + r['table'] + '/' + r['key']), 'catalogue_identity_reconciliation', r['table'], r.get('entity_id', r['key']), operation, Jsonb(r['before']), Jsonb(r['after'])) for r in changes])
    assert db.execute('SELECT count(*)n FROM audit_log WHERE id=ANY(%s::uuid[])',([uid(operation+'/'+r['table']+'/'+r['key']) for r in changes],)).fetchone()['n'] == len(changes)


def museums():
    """Fresh locked institution aliases; retain all source associations and queues."""
    before = c.load(E / 'museum-fresh-preimages.json.gz')
    evidence = c.load(E / 'museum-source-decisions.json')
    assert len(evidence['decisions']) == 4
    inst = {r['id']:r for r in before['tables']['institutions']}
    aliases = [p['alias_id'] for p in before['pairs']]
    assert all(inst[i]['canonical_institution_id'] is None and inst[i]['status'] != 'archived' for i in before['ids'])
    assert not any(r['institution_id'] in aliases for r in before['tables']['curated_collections'])
    assert not any(r['institution_id'] in aliases for r in before['tables']['institution_venues'])
    operation = OP + '-museums-four'
    changes = []
    B.mkdir(parents=True,exist_ok=True); B.chmod(0o700)
    assert shutil.disk_usage(B).free > 15*1024**3
    c.save(B / 'museum-plan.json.gz',dict(before=before,evidence=evidence))
    with c.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(202610053)')
        db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(before['ids'],)).fetchall()
        db.execute('SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(before['ids'],)).fetchall()
        for t,col in TABLES.items():
            assert ordered(rows(db,t,col,before['ids'])) == ordered(before['tables'][t]),('Changed preimage',t)
        c.save(B / 'museum-locked-preimages.json.gz',before)
        mapping = {p['alias_id']:p['canonical_id'] for p in before['pairs']}
        for alias,canonical in mapping.items():
            work_ids=[r['id'] for r in before['tables']['artworks'] if r['current_institution_id']==alias]
            db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now() WHERE id=%s',(canonical,alias))
            db.execute('UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s',(canonical,alias))
            db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])',(canonical,EDITOR,work_ids))
        allowed = {'institutions':{'canonical_institution_id','updated_at'},'artwork_location_assertions':{'institution_id'},'artworks':{'current_institution_id','revision','updated_at','updated_by'}}
        for t,col in TABLES.items():
            actual=rows(db,t,col,before['ids'])
            if t not in allowed:
                assert ordered(actual)==ordered(before['tables'][t]),('Protected table changed',t)
                continue
            actual={r['id']:r for r in actual}
            assert set(actual)=={r['id'] for r in before['tables'][t]}
            for old in before['tables'][t]:
                new=actual[old['id']]
                assert all(new[k]==v for k,v in old.items() if k not in allowed[t]),(t,old['id'])
                if old==new:continue
                if t=='artworks':assert new['current_institution_id']==mapping[old['current_institution_id']] and new['revision']==old['revision']+1
                changes.append(dict(table=t,key=old['id'],before=old,after=new))
        cols=[r['id'] for r in before['tables']['curated_collections']]
        assert ordered(rows(db,'curated_collection_items','collection_id',cols))==ordered(before['tables']['curated_collection_items'])
        audit(db,changes,operation)
        c.save(B/'museum-transaction-after.json.gz',dict(at=c.now(),operation=operation,changes=changes))
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for t in {r['table'] for r in changes}:
            expected={r['key']:r['after'] for r in changes if r['table']==t}
            assert {r['id']:r for r in rows(db,t,'id',list(expected))}==expected
        aa=db.execute('SELECT entity_type,entity_id,before_json,after_json FROM audit_log WHERE request_id=%s',(operation,)).fetchall()
        audits={(r['entity_type'],str(r['entity_id'])):r for r in aa}
        assert len(audits)==len(changes)
        assert all(audits[(r['table'],r['key'])]['before_json']==r['before'] and audits[(r['table'],r['key'])]['after_json']==r['after'] for r in changes)
        assert not rows(db,'artworks','current_institution_id',aliases)
        counts=db.execute("SELECT i.slug,count(a.id)FILTER(WHERE a.status<>'archived')active,count(a.id)FILTER(WHERE a.status<>'archived'AND a.primary_media_id IS NOT NULL)illustrated FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id WHERE i.id=ANY(%s::uuid[])GROUP BY i.slug ORDER BY i.slug",(list(mapping.values()),)).fetchall()
    c.save(E/'museum-four-verification.json',dict(at=c.now(),passed=True,operation=operation,aliases=4,changed_rows=len(changes),atomic_audits=len(audits),museum_counts=counts,protected_metadata_and_images_preserved=True))
    print('Four museum aliases committed and independently verified:',len(changes),'rows/audits',flush=True)


def creators():
    import re
    p=c.load(E/'rouen-creator-delivery-selection.json.gz')
    selected=p['selected'];assert len(selected)==66
    initial=c.load(E/'rouen-creator-fresh-preimages.json.gz')['tables']
    artists={r['id']:r for r in initial['artists']}
    for r in selected:
        a=artists[r['artist']['id']]
        assert a['status']!='archived'
        label=r['current_source_creator_label'];text=label+' '+(r['current_source_author_precision'] or '')
        assert not re.search(r"attribu|atelier|ecole|école|entourage|suiveur|d.apr[eè]s|copie|anonyme",label,re.I)
        years=set(map(int,re.findall(r'\b(1[0-9]{3})\b',text)))
        assert a['birth_year'] in years and a['death_year'] in years
    changes=[];operation=OP+'-rouen-creators';ids=[r['artwork_id'] for r in selected]
    with c.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(202610053)')
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        current=rows(db,'artworks','id',ids)
        expected=[r for r in initial['artworks'] if r['id'] in ids]
        assert ordered(current)==ordered(expected),'Fresh artwork preimage changed'
        assert not rows(db,'artwork_artists','artwork_id',ids),'Concurrent creator delivery requires reconciliation'
        actual_artists=rows(db,'artists','id',[r['artist']['id'] for r in selected])
        assert all(artists[r['id']]==r for r in actual_artists)
        holdings=rows(db,'artwork_location_assertions','artwork_id',ids)
        c.save(B/'creator-locked-preimages.json.gz',dict(at=c.now(),artworks=current,artists=actual_artists,holdings=holdings,selection=p))
        source=db.execute("SELECT id::text FROM sources WHERE slug='joconde-m0729'").fetchone()['id']
        for r in selected:
            aid=r['artwork_id'];artist=r['artist']['id']
            note='Exact Ministry Joconde source maker label, canonical name/alias identity and both life years corroborated. Literal maker label and source wording retained in the companion citation; no life dates or work metadata rewritten.'
            link=db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,representative_order,attribution_note)VALUES(%s,%s,'primary',1,%s) RETURNING to_jsonb(artwork_artists)v",(aid,artist,note+' '+r['source_url']+' Operation: '+operation)).fetchone()['v']
            citation=db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artwork',%s,'rouen_canonical_creator',%s,%s,%s,%s,now(),%s) RETURNING to_jsonb(citations)v",(uid('creator-citation/'+aid),aid,source,r['native_id'],r['source_url'],json.dumps(dict(operation=operation,source_label=r['current_source_creator_label'],source_author_precision=r['current_source_author_precision'],source_snapshot=r['source_snapshot'],artist_id=artist,identity_basis=note),ensure_ascii=False),EDITOR)).fetchone()['v']
            changes.extend([dict(table='artwork_artists',key=aid+'/'+artist,entity_id=aid,before=None,after=link),dict(table='citations',key=citation['id'],before=None,after=citation)])
        assert ordered(rows(db,'artworks','id',ids))==ordered(current)
        assert ordered(rows(db,'artwork_location_assertions','artwork_id',ids))==ordered(holdings)
        audit(db,changes,operation)
        c.save(B/'creator-transaction-after.json.gz',dict(at=c.now(),changes=changes,operation=operation))
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        assert ordered(rows(db,'artworks','id',ids))==ordered(current)
        assert ordered(rows(db,'artwork_location_assertions','artwork_id',ids))==ordered(holdings)
        assert ordered(rows(db,'artwork_artists','artwork_id',ids))==ordered([r['after'] for r in changes if r['table']=='artwork_artists'])
        cites=[r['after'] for r in changes if r['table']=='citations']
        assert ordered(rows(db,'citations','id',[r['id'] for r in cites]))==ordered(cites)
        aa=db.execute('SELECT id,before_json,after_json,request_id FROM audit_log WHERE id=ANY(%s::uuid[])',([uid(operation+'/'+r['table']+'/'+r['key']) for r in changes],)).fetchall()
        aa={str(r['id']):r for r in aa};assert len(aa)==len(changes)
        assert all(aa[uid(operation+'/'+r['table']+'/'+r['key'])]['before_json']==r['before'] and aa[uid(operation+'/'+r['table']+'/'+r['key'])]['after_json']==r['after'] for r in changes)
    c.save(E/'rouen-creator-verification.json',dict(at=c.now(),passed=True,canonical_creator_links=len(selected),distinct_existing_profiles=len({r['artist']['id'] for r in selected}),atomic_audits=len(changes),artwork_metadata_images_holdings_preserved=True,new_artists=0,prior_creator_deliveries_not_replayed=True))
    print('Committed and independently verified',len(selected),'Rouen canonical maker links and',len(changes),'row audits.',flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['snapshot','museums','creators'])
    args = p.parse_args()
    globals()[args.phase]()
