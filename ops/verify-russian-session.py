#!/usr/bin/env python3
"""Read-only batch, media, storage and API verification for this research pass."""
import argparse, collections, hashlib, importlib.util, json, re, subprocess
from pathlib import Path
import psycopg, requests
from psycopg.rows import dict_row
from PIL import Image
from google.cloud import storage

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/russian-painters-20260913'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
SCHEME='european-russian-session-museum-object'

def metadata(label):
    reports={}; plans={}
    expected={}; authors={}; unlinked=set(); chunk_count=0; total_unknown=0
    for folder in ('combined-batch','date-review-batch'):
        manifest=json.loads((RUN/folder/'manifest.json').read_bytes())
        chunk_count+=len(manifest['chunks']);total_unknown+=manifest['unknown_dates']
        for chunk in manifest['chunks']:
            data=json.loads((RUN/folder/chunk['file']).read_bytes());authors.update(data['authors'])
            for w in data['works']:
                assert w['source_object_id'] not in expected
                expected[w['source_object_id']]=w
                if folder=='date-review-batch':unlinked.add(w['source_object_id'])
    for target,connection in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
        with psycopg.connect(connection,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            works=db.execute("""SELECT e.external_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.primary_media_id::text,a.unlinked_creator_label,a.cultural_context,
             artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
             (SELECT jsonb_agg(x.external_id ORDER BY x.external_id) FROM artwork_artists aa JOIN external_identifiers x ON x.entity_type='artist' AND x.entity_id=aa.artist_id AND x.scheme='wikidata' WHERE aa.artwork_id=a.id) painters,
             (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='accepted' AND l.superseded_by IS NULL) holdings,
             (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='on_view') display_claims
             FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s ORDER BY e.external_id""",(SCHEME,)).fetchall()
            # Local and Cloud SQL use different text collations. Compare by
            # source identity with one ordering, not database row positions.
            works.sort(key=lambda w:w['external_id'])
            jobs=db.execute("SELECT idempotency_key,status FROM import_jobs WHERE idempotency_key LIKE 'russian-painters-20260913-%' ORDER BY idempotency_key").fetchall()
            creators=db.execute("""SELECT count(DISTINCT a.id) count,count(DISTINCT a.id) FILTER(WHERE a.status<>'review') unsafe FROM import_records r JOIN import_jobs j ON j.id=r.import_job_id JOIN artists a ON a.id=r.matched_entity_id WHERE j.idempotency_key LIKE 'russian-painters-20260913-%' AND r.matched_entity_type='artist' AND r.outcome='created'""").fetchone()
            assert len(works)==len(expected),(target,len(works))
            assert len(jobs)==chunk_count and all(j['status']=='needs_review' for j in jobs)
            assert all(w['status']=='review' and w['scope'] in ('eligible','review') and w['holdings']==1 and w['display_claims']==0 for w in works)
            assert creators['unsafe']==0
            for w in works:
                source=expected[w['external_id']]
                assert all(w[k]==source[k] for k in ('title','date_display','work_type'))
                assert (w['creation_year_start'],w['creation_year_end'],w['date_precision'])==(source['creation_date']['first'],source['creation_date']['last'],source['creation_date']['precision'])
                if w['external_id'] in unlinked:
                    assert not w['painters'] and w['unlinked_creator_label']==authors[source['painter']]['native_name']
                    assert w['cultural_context']==authors[source['painter']]['affiliation_evidence']
                else:
                    assert w['painters']==[source['painter']]
            assert len({q for w in works for q in (w['painters'] or [])})==519
            assert sum(w['scope']=='review' for w in works)==total_unknown
            reports[target]={'works':works,'jobs':jobs,'new_painters':creators['count'],'counts':dict(collections.Counter(w['work_type'] for w in works)),'date_scopes':dict(collections.Counter(w['scope'] for w in works))}
            sample=works[0]
            plans[target]=db.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id,a.title FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s",(SCHEME,sample['external_id'])).fetchone()
    differences=[{'external_id':a['external_id'],'fields':{k:[a[k],b[k]] for k in a if a[k]!=b[k]}} for a,b in zip(reports['local']['works'],reports['production']['works']) if a!=b]
    if differences:
        core.save_new(RUN/(label+'-database-differences.json'),differences)
        raise AssertionError(f'{len(differences)} source records differ between databases; inspect saved evidence')
    core.save_new(RUN/(label+'-metadata-verification.json'),reports)
    core.save_new(RUN/(label+'-query-plans.json'),plans)
    print({target:{k:v for k,v in data.items() if k not in ('works','jobs')}|{'works':len(data['works']),'jobs':len(data['jobs'])} for target,data in reports.items()},flush=True)

def images(label):
    receipts=[json.loads(p.read_bytes()) for p in (RUN/'images/images/russian-commons').glob('*.json')]
    latest={}
    for line in (RUN/'images/events.jsonl').read_text().splitlines():
        e=json.loads(line)
        if e.get('artwork_id'):latest[e['artwork_id']]=e
    receipts=[r for r in receipts if latest.get(r['artwork_id'],{}).get('outcome')=='complete']
    assert receipts,'No completed images'
    cloud=storage.Client(project='artline-508319',credentials=core.GcloudCredentials())
    import base64
    blobs={b.name:b for b in cloud.list_blobs(core.BUCKET,prefix='assets/artworks/open-museums/russian-commons/')}
    for r in receipts:
        data=(ROOT/'apps/web/public'/r['path'].lstrip('/')).read_bytes()
        assert len(data)==r['bytes']<=100000 and core.sha(data)==r['sha256']
        with Image.open(ROOT/'apps/web/public'/r['path'].lstrip('/')) as image:
            assert image.size==(r['width'],r['height']);image.verify()
        blob=blobs[r['path'].lstrip('/')]
        assert blob.size==len(data) and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
    targets={};apis=[]
    for target,connection in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
        with psycopg.connect(connection,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            rows=db.execute("""SELECT m.id::text,m.storage_path,m.checksum_sha256,m.byte_size,m.creator_credit,m.attribution_text,m.rights_status,m.license_url,a.id::text artwork_id,a.title,a.status,e.external_id,r.source_checksum,r.source_image_url FROM media_assets m JOIN media_rights_evidence r ON r.media_id=m.id JOIN artworks a ON a.primary_media_id=m.id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=%s WHERE m.id=ANY(%s::uuid[])""",(SCHEME,[r['media_id'] for r in receipts])).fetchall()
            assert len(rows)==len(receipts)
            byid={r['id']:r for r in rows}
            for r in receipts:
                d=byid[r['media_id']]
                assert d['status']=='review' and d['external_id']==r['external_id']
                assert d['creator_credit']==r['creator_credit'] and d['attribution_text']==r['attribution_text']
                assert d['checksum_sha256']==r['sha256'] and d['byte_size']==r['bytes']
                assert d['rights_status']==r['rights_status'] and d['license_url']==r['policy_url']
                assert d['source_checksum']==core.sha(core.encode(r['raw'])) and d['source_image_url']==r['source_image_url']
            candidates=db.execute("SELECT count(*) n FROM citations c JOIN sources s ON s.id=c.source_id WHERE s.slug='russian-commons-image-research' AND c.field_name='image_candidate'").fetchone()['n']
            targets[target]={'attached':len(rows),'image_candidates':candidates}
            assert candidates==231
            if target=='local':
                env=(ROOT/'apps/server/.env').read_text();token=re.search(r'^ARTLINE_EDITOR_TOKEN=(.*)$',env,re.M)[1].strip().strip('\"\'');base='http://127.0.0.1:8080';web='http://localhost:3000'
            else:
                token=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-editor-token','--project=artline-508319'],text=True).strip();base='https://artline-api-lpuqqlugnq-ew.a.run.app';web='https://artline-web-lpuqqlugnq-ew.a.run.app'
            first=rows[0]
            url=base+'/api/v1/museums/state-russian-museum/works/'+first['artwork_id']+'?preview=1'
            response=requests.get(url,headers={'Authorization':'Bearer '+token},timeout=30)
            assert response.status_code==200,(target,response.status_code)
            detail=response.json();assert detail['title']==first['title'] and detail['status']=='review' and detail.get('media_url') and detail.get('display') is None
            asset=requests.get(web+first['storage_path'],timeout=30);assert asset.status_code==200 and hashlib.sha256(asset.content).hexdigest()==first['checksum_sha256']
            page=requests.get(base+'/api/v1/museums/state-russian-museum/works?preview=1&image_only=1&limit=3',headers={'Authorization':'Bearer '+token},timeout=30)
            assert page.status_code==200 and len(page.json()['items'])==3
            apis.append({'target':target,'artwork_detail':200,'served_image_hash':'matched','bounded_image_page':3})
    report={'images':len(receipts),'bytes':sum(r['bytes'] for r in receipts),'max_bytes':max(r['bytes'] for r in receipts),'databases':targets,'api_checks':apis,'errors':[]}
    core.save_new(RUN/(label+'-image-verification.json'),report);print(report,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['metadata','images']);p.add_argument('--label',required=True);a=p.parse_args();globals()[a.phase](a.label)
