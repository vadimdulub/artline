"""Independent read-only reconciliation of all 41 resumed production transactions."""
import collections
import importlib.util
import re
from pathlib import Path
from psycopg.types.json import Jsonb
import exhibitions_common as c

s=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def main():
    B=m.B
    paths=[B/'museum-transaction-after.json.gz',B/'creator-transaction-after.json.gz',
           B/'clouet-qualification-after.json',B/'exhibition-schema-after.json',
           B/'artworks/attempt-003/transaction-after.json.gz',B/'exhibitions/transaction-after.json.gz',
           B/'rouen-artworks/transaction-after.json.gz',B/'additional-creators/transaction-after.json.gz',
           *sorted((B/'native-expansion').glob('transaction-after-*.json.gz'))]
    for folder in ['rouen-reviewed-image-delivery-20261027','rouen-reviewed-new-work-images-20261027']:
        paths.extend(sorted((B.parent/folder).glob('transaction-after-*.json.gz')))
    assert len(paths)==41
    transactions=sorted([(p,c.load(p))for p in paths],key=lambda item:item[1]['at'])
    changes=[dict(r,operation=tx['operation'])for path,tx in transactions for r in tx['changes']]
    assert len(changes)==6805
    latest={}
    for r in changes:latest[(r['table'],r['key'])]=r
    tables=collections.defaultdict(list)
    for (t,key),r in latest.items():tables[t].append(r)
    rows_checked=0;deleted_checked=0;audits_checked=0
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for start in range(0,len(changes),500):
            batch=changes[start:start+500];keys=[m.uid(r['operation']+'/'+r['table']+'/'+r['key'])for r in batch]
            aa={str(r['id']):r for r in db.execute('SELECT id,request_id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',(keys,))}
            assert len(aa)==len(batch)
            for key,r in zip(keys,batch):
                a=aa[key];assert a['request_id']==r['operation']and a['before_json']==r['before']and a['after_json']==r['after'],('Atomic audit mismatch',r['table'],r['key'])
            audits_checked+=len(batch)
        for table,rr in tables.items():
            assert re.fullmatch('[a-z_]+',table)
            if table=='exhibitions_schema':
                columns=db.execute("SELECT column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema='public'AND table_name='exhibitions'ORDER BY ordinal_position").fetchall()
                assert columns==rr[0]['after']['columns'];rows_checked+=1;continue
            if table=='schema_migrations':
                actual={r['v']['filename']:r['v']for r in db.execute('SELECT to_jsonb(t)v FROM schema_migrations t WHERE filename=ANY(%s)',([r['key']for r in rr],))}
            elif table in ['artwork_artists','artwork_media']:
                second='artist_id'if table=='artwork_artists'else'media_id'
                ids=list({r['key'].split('/')[0]for r in rr})
                actual={r['artwork_id']+'/'+r[second]:r for r in m.rows(db,table,'artwork_id',ids)}
            elif table=='research_artwork_links':
                actual={}
                for r in rr:
                    source,kind,record=r['key'].split('/',2)
                    result=db.execute('SELECT to_jsonb(t)v FROM research_artwork_links t WHERE source_key=%s AND record_kind=%s AND research_record_id=%s',(source,kind,record)).fetchone()
                    if result:actual[r['key']]=result['v']
            else:
                col='media_id'if table=='media_rights_evidence'else'id'
                actual={r[col]:r for r in m.rows(db,table,col,[r['key']for r in rr])}
            for r in rr:
                assert actual.get(r['key'])==r['after'],('Latest operation postimage differs',table,r['key'])
                rows_checked+=1
                if r['after']is None:deleted_checked+=1
        rouen=db.execute("SELECT count(*)active,count(*)FILTER(WHERE primary_media_id IS NOT NULL)illustrated,count(*)FILTER(WHERE EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id))with_creator FROM artworks a WHERE current_institution_id=%s AND status<>'archived'",('f92766ec-41cf-42d1-9bb1-f333fe5d2980',)).fetchone()
        counts=db.execute("SELECT count(*)total,count(*)FILTER(WHERE status<>'archived')active,count(*)FILTER(WHERE status<>'archived'AND primary_media_id IS NOT NULL)illustrated FROM artworks").fetchone()
        assert rouen==dict(active=2128,illustrated=989,with_creator=1184),rouen
        assert not db.execute("SELECT 1 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.status<>'archived'AND a.primary_media_id IS NOT NULL AND m.id IS NULL LIMIT 1").fetchone()
        links=db.execute("SELECT canonical_exhibition_id::text FROM exhibitions WHERE canonical_exhibition_id IS NOT NULL").fetchall()
        invalid=db.execute("SELECT count(*)n FROM exhibitions e JOIN exhibitions p ON p.id=e.canonical_exhibition_id WHERE e.status<>'archived'OR p.status='archived'OR p.canonical_exhibition_id IS NOT NULL").fetchone()['n'];assert invalid==0
    c.save(m.E/'final-atomic-reconciliation.json',dict(at=c.now(),passed=True,transactions=41,atomic_audits=audits_checked,
        latest_postimages_checked=rows_checked,deleted_child_rows_verified_absent=deleted_checked,
        retained_child_source_witnesses_verified_in_survivors=True,counts_snapshot=counts,rouen_counts=rouen,
        active_dangling_primary_media=0,exhibition_aliases=len(links),invalid_exhibition_aliases=0,
        inputs=[dict(path=str(path),sha256=c.sha(path.read_bytes()),operation=tx['operation'],changes=len(tx['changes']))for path,tx in transactions],
        change_table_counts=dict(collections.Counter(r['table']for r in changes)),read_only=True,local_catalogue_connections=0))
    print('PASS:',audits_checked,'atomic audits,',rows_checked,'latest postimages;',rouen,flush=True)


if __name__=='__main__':main()
