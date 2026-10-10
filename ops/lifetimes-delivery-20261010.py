#!/usr/bin/env python3
"""Pinned, audited production-only lifetime updates. The local catalogue stays read-only."""
import collections,concurrent.futures,importlib.util,json,subprocess,uuid
from pathlib import Path
from urllib.parse import urlsplit
from psycopg import sql
from psycopg.types.json import Jsonb
import requests
s=importlib.util.spec_from_file_location('plan',Path(__file__).with_name('lifetimes-plan-20261010.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
r=p.r;m=r.m;RUN=r.RUN;BACKUP=r.BACKUP;ACTOR=m.ACTOR
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,r.OP+'/'+key))
def pin():
    data=r.load(RUN/'final-correction-plan.json.gz');held=[];rows=[]
    for row in data['rows']:
        if row['artist_id']=='f1177096-beb1-4c4f-9c99-a8c3ebcc56d9':
            held.append(dict(**row,reason='NGA literal born 1962 contradicts all three native linked prints dated c.1935–1943. Source identity/date conflict requires object-authority investigation; no new birth value applied.'))
        else:rows.append(row)
    data.update(at=r.now(),rows=rows);r.save(RUN/'verified-correction-plan.json.gz',data);r.save(RUN/'held-corrections.json.gz',held)
    r.save(RUN/'verified-plan-digest.json',dict(sha256=r.sha((RUN/'verified-correction-plan.json.gz').read_bytes()),artists=len(rows)))
    print('Pinned source-backed artists',len(rows),'held',len(held),flush=True)
def backup():
    rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=10','--format=json'],text=True))
    row=next(x for x in rows if x.get('description')=='Before painter lifetime review 20261010');assert row['status']=='SUCCESSFUL'
    BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);r.save(RUN/'cloud-backup.json',row);r.save(BACKUP/'cloud-backup.json',row);print('Backup verified',row['id'],flush=True)
def pinned():
    name='complete-execution' if (RUN/'complete-execution-plan.json.gz').exists() else 'execution'
    path=RUN/(name+'-plan.json.gz');digest=r.sha(path.read_bytes());assert r.load(RUN/(name+'-plan-digest.json'))['sha256']==digest
    return r.load(path),digest
def execution_plan():
    data=r.load(RUN/'verified-correction-plan.json.gz')
    for row in data['rows']:
        if row['updates'].get('timeline_basis')=='mixed' and row['evidence'].get('literal','').startswith('active') and 'died' in row['evidence']['literal']:
            # A known death is not evidence of continued artistic activity until that year.
            row['updates']['active_end_year']=None
            row['basis']+=' The death endpoint is not an activity-end assertion.'
    data['at']=r.now();r.save(RUN/'execution-plan.json.gz',data)
    r.save(RUN/'execution-plan-digest.json',dict(sha256=r.sha((RUN/'execution-plan.json.gz').read_bytes()),artists=len(data['rows'])))
    print('Execution plan',len(data['rows']),flush=True)
def supplement_plan():
    base=r.load(RUN/'production-snapshot.json.gz');artists={x['record']['id']:x for x in base['artists']};rows=[]
    specs=[
      ('24c8b1ac-371c-53bf-84c0-3d86308a1008','beardmore',dict(birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision=None,death_precision=None,active_start_year=1822,active_end_year=1826,activity_display='active 1822–1826',timeline_basis='activity',timeline_display='active 1822–1826'),'William Beardmore (fl. 1822-1826)','Auction house catalogue explicitly labels the imported years as floruit, not birth/death.'),
      ('afc95d0b-1ac0-43e8-9ecc-d24be112f1a1','roovers-getty',dict(birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision=None,death_precision=None,active_start_year=1663,active_end_year=1663,activity_display='active c. 1663',timeline_basis='activity',timeline_display='active c. 1663'),'active: ca. 1663','Getty ULAN identifies the exact museum creator name and describes activity circa 1663; identical imported birth/death copied the work year. Nationality disagreement is outside this date correction.'),
      ('cff69b4f-0b31-508f-8b72-020f45c7976c','thom-dnb',dict(birth_year=1785,birth_display='c. 1785',birth_precision='circa',death_year=None,death_display=None,death_precision=None,active_start_year=1808,active_end_year=1816,activity_display='documented exhibitions 1808–1816',timeline_start_year=1785,timeline_end_year=1816,timeline_basis='mixed',timeline_display='born c. 1785; documented 1808–1816; death unknown'),'Another artist of the same name, James Thom ( fl . 1815), subject-painter, was born in Edinburgh about 1785.','Dictionary of National Biography explicitly distinguishes the subject painter from the sculptor. Its documented Edinburgh exhibition period matches the imported activity years; do not use the sculptor’s 1802–1850 lifespan.'),
      ('f483335f-356f-5427-9017-9fb1ec01245f','carlill-library',dict(birth_year=1859,birth_display='1859',birth_precision='exact',timeline_start_year=1859,timeline_display='1859–1903'),'Carlill, S. B. (Stephen Briggs), 1859-1903','Project Gutenberg bibliographic creator authority supplies 1859–1903; the exact V&A artist identity and nineteenth-century works independently contradict the imported birth 1903.'),
    ]
    for aid,name,update,literal,basis in specs:
        src=r.load(RUN/'primary-pages'/(name+'.json.gz'));assert literal in src['text'];ar=artists[aid]['record'];updates={k:v for k,v in update.items() if ar[k]!=v}
        rows.append(dict(artist_id=aid,name=ar['display_name'],before=ar,updates=updates,source_url=src['receipt']['url'],receipt=src['receipt'],basis=basis,evidence=dict(literal=literal,source_page=name)))
    supplemental=dict(at=r.now(),target='production',rows=rows);r.save(RUN/'supplement-plan.json.gz',supplemental)
    complete=r.load(RUN/'execution-plan.json.gz');complete['rows']+=rows;complete['at']=r.now();r.save(RUN/'complete-execution-plan.json.gz',complete);r.save(RUN/'complete-execution-plan-digest.json',dict(sha256=r.sha((RUN/'complete-execution-plan.json.gz').read_bytes()),artists=len(complete['rows'])))
    print('Supplement',len(rows),'complete',len(complete['rows']),flush=True)
def apply(phase='main'):
    if phase=='main':
        path=RUN/'execution-plan.json.gz';plan=r.load(path);digest=r.sha(path.read_bytes());assert r.load(RUN/'execution-plan-digest.json')['sha256']==digest
    else:
        assert phase=='supplement' and (RUN/'applied.json').exists();path=RUN/'supplement-plan.json.gz';plan=r.load(path);digest=r.sha(path.read_bytes())
        complete,_=pinned();by={x['artist_id']:x for x in complete['rows']};assert all(by[x['artist_id']]==x for x in plan['rows'])
    receipt_path=RUN/('applied.json' if phase=='main' else 'supplement-applied.json');backup_dir=BACKUP if phase=='main' else BACKUP/'supplement'
    if receipt_path.exists():assert r.load(receipt_path)['plan_sha256']==digest;print('Already applied; zero writes');return
    assert r.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL';rows=plan['rows'];ids=[x['artist_id'] for x in rows];assert len(ids)==len(set(ids))
    with m.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        actual={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))};assert actual=={x['artist_id']:x['before'] for x in rows},'Concurrent artist edit'
        r.save(backup_dir/'locked-artist-preimages.json.gz',dict(plan_sha256=digest,artists=actual))
        sources={urlsplit(x['source_url']).hostname for x in rows}
        for host in sorted(sources):
            db.execute('INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key,priority) VALUES(%s,%s,%s,%s,%s,%s,10) ON CONFLICT(id) DO NOTHING',(uid('source/'+host),r.OP+'-'+host.replace('.','-'),host+' — painter lifetime review','authority_data','https://'+host,r.OP))
        after={}
        allowed={'birth_year','death_year','birth_display','death_display','birth_precision','death_precision','active_start_year','active_end_year','activity_display','timeline_start_year','timeline_end_year','timeline_display','timeline_basis','entity_type','biography_md'}
        for row in rows:
            update=row['updates'];assert set(update)<=allowed
            query=sql.SQL('UPDATE artists SET {},revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in update))
            db.execute(query,[*update.values(),ACTOR,row['artist_id']])
            note=dict(plan_sha256=digest,basis=row['basis'],evidence=row['evidence'],receipt=row['receipt'],before={k:row['before'][k] for k in update},updates=update,publication_changes=False,artwork_changes=False)
            db.execute('INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,source_record_id,evidence_note,retrieved_at,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(uid('citation/'+row['artist_id']),'artist',row['artist_id'],'lifetime_timeline_review',uid('source/'+urlsplit(row['source_url']).hostname),row['source_url'],row['before']['slug'],json.dumps(note,ensure_ascii=False),row['receipt']['at'],ACTOR))
            ar=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(row['artist_id'],)).fetchone()['v'];after[ar['id']]=ar
            assert all(ar[k]==v for k,v in update.items())
            assert all(ar[k]==v for k,v in row['before'].items() if k not in set(update)|{'revision','updated_by','updated_at'})
            assert ar['revision']==row['before']['revision']+1
            db.execute('INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(uid('audit/'+ar['id']),ACTOR,'lifetime_timeline_source_review','artist',ar['id'],r.OP,Jsonb(row['before']),Jsonb(ar)))
        r.save(backup_dir/'transaction-artist-postimages.json.gz',dict(plan_sha256=digest,artists=after))
    receipt=dict(at=r.now(),target='production',plan_sha256=digest,artists_changed=len(rows),citations_added=len(rows),artwork_changes=0,publication_changes=0,local_database_changes=0)
    r.save(receipt_path,receipt);print(json.dumps(receipt,indent=2),flush=True)
def apply_supplement():apply('supplement')
def verify():
    plan,digest=pinned();ids=[x['artist_id'] for x in plan['rows']]
    with m.connect() as db:
        after={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))}
        counts={table:db.execute('SELECT count(*) n FROM '+table).fetchone()['n'] for table in ['artists','artworks','artwork_artists','media_assets']}
        audits=db.execute('SELECT count(*) n FROM audit_log WHERE request_id=%s AND action=%s',(r.OP,'lifetime_timeline_source_review')).fetchone()['n']
        citations=db.execute("SELECT count(*) n FROM citations WHERE field_name='lifetime_timeline_review' AND id=ANY(%s::uuid[])",([uid('citation/'+i) for i in ids],)).fetchone()['n']
    assert audits==citations==len(ids)
    for row in plan['rows']:
        ar=after[row['artist_id']];assert all(ar[k]==v for k,v in row['updates'].items());assert all(ar[k]==v for k,v in row['before'].items() if k not in set(row['updates'])|{'updated_at','updated_by','revision'})
    assert counts==r.load(RUN/'production-snapshot.json.gz')['counts']
    with m.connect(local=True) as db:
        local_artists=[dict(record=x['v']) for x in db.execute('SELECT to_jsonb(a) v FROM artists a ORDER BY id')]
        local_counts={table:db.execute('SELECT count(*) n FROM '+table).fetchone()['n'] for table in ['artists','artworks','artwork_artists','media_assets']}
    baseline=r.load(RUN/'local-snapshot.json.gz');assert local_artists==[dict(record=x['record']) for x in baseline['artists']];assert local_counts==baseline['counts']
    r.save(RUN/'verified-production-artists.json.gz',after)
    result=dict(at=r.now(),artists_verified=len(ids),audit_rows=audits,citation_rows=citations,counts_unchanged=True,publication_and_unedited_fields_preserved=True,local_artist_records_identical=True,local_counts_unchanged=True)
    r.save(RUN/'database-verification.json',result);print(json.dumps(result,indent=2),flush=True)
def public():
    plan,digest=pinned();results=[]
    def one(row):
        url='https://artlines.org/api/backend/v1/artists/'+row['before']['slug'];response=requests.get(url,timeout=(15,45));data=response.json() if response.status_code==200 else {};ar=data.get('artist',data)
        expected={**row['before'],**row['updates']};checks={k:ar.get(k)==expected[k] for k in ['timeline_start_year','timeline_end_year','timeline_display','timeline_basis'] if k in ar}
        return dict(artist_id=row['artist_id'],url=url,status=response.status_code,checks=checks,ok=response.status_code==200 and len(checks)==4 and all(checks.values()),keys=list(data) if not checks else None)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(one,plan['rows']):
            results.append(result)
            if len(results)%100==0:print('Public timeline verification',len(results),flush=True)
    r.save(RUN/'public-verification.json.gz',dict(at=r.now(),results=results));assert all(x['ok'] for x in results);print('Verified public timelines',len(results),flush=True)
if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
