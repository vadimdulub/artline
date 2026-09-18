#!/usr/bin/env python3
"""Read-only source, identity, review-state, media and delivery verification."""
import argparse,base64,collections,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row
from PIL import Image
from google.cloud import storage
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-painters-20260913'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
SCHEME='european-smk-statens-museum-for-kunst-object';SOURCE='danish-painters-20260913'
def connections():return [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]

def metadata(label):
 manifest=json.loads((RUN/'batch/manifest.json').read_bytes());expected={}
 for c in manifest['chunks']:
  path=RUN/'batch'/c['file'];assert core.sha(path.read_bytes())==c['sha256']
  for w in json.loads(path.read_bytes())['works']:expected[w['source_object_id']]=w
 assert len(expected)==10000
 reports={};plans={}
 for target,dsn in connections():
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
   works=db.execute("""SELECT e.external_id,a.slug,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.medium_text,a.dimensions_text,a.status,a.unlinked_creator_label,
    artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
    (SELECT jsonb_agg(x.external_id ORDER BY x.external_id) FROM artwork_artists aa JOIN external_identifiers x ON x.entity_type='artist' AND x.entity_id=aa.artist_id AND x.scheme='smk-person' WHERE aa.artwork_id=a.id) painters,
    (SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_links,
    (SELECT count(*) FROM artwork_location_assertions l JOIN institutions i ON i.id=l.institution_id WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='accepted' AND l.superseded_by IS NULL AND i.slug='statens-museum-for-kunst') holdings,
    (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display') display_claims,
    (SELECT count(*) FROM curated_collection_items c WHERE c.artwork_id=a.id) selections,
    r.source_checksum,r.raw_json->>'id' raw_source_id,r.normalized_json->>'painter' source_painter
    FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN import_records r ON r.matched_entity_type='artwork' AND r.matched_entity_id=a.id JOIN import_jobs j ON j.id=r.import_job_id AND j.source_id=%s
    WHERE e.entity_type='artwork' AND e.scheme=%s AND e.source_id=%s""",(sid,SCHEME,sid)).fetchall()
   assert len(works)==10000 and len({w['external_id'] for w in works})==10000
   works.sort(key=lambda w:w['external_id'])
   authors=json.loads((RUN/'selected-authors.json').read_bytes())
   for w in works:
    source=expected[w['external_id']]
    assert all(w[k]==source[k] for k in ('title','date_display','work_type'))
    assert (w['creation_year_start'],w['creation_year_end'],w['date_precision'])==(source['creation_date']['first'],source['creation_date']['last'],source['creation_date']['precision'])
    assert w['medium_text']==(source['medium'] or None) and w['dimensions_text']==(source['dimensions'] or None)
    assert w['alternate_title']==('; '.join(source['aliases']) or None)
    assert w['status']=='review' and w['holdings']==1 and w['display_claims']==0 and w['selections']==0
    assert w['source_painter']==source['painter'] and w['raw_source_id']==source['raw']['id']
    assert w['source_checksum']==core.sha(core.encode(source['raw']))
    if w['unlinked_creator_label']:
     assert w['artist_links']==0 and not w['painters'] and w['unlinked_creator_label']==authors[source['painter']]['name']
    else:assert w['artist_links']==1 and w['painters']==[source['painter']]
   jobs=db.execute('SELECT idempotency_key,status FROM import_jobs WHERE source_id=%s ORDER BY idempotency_key',(sid,)).fetchall()
   assert len(jobs)==40 and all(j['status']=='needs_review' for j in jobs)
   creators=db.execute("SELECT count(DISTINCT a.id) n,count(DISTINCT a.id) FILTER(WHERE a.status<>'review') unsafe FROM import_records r JOIN import_jobs j ON j.id=r.import_job_id JOIN artists a ON a.id=r.matched_entity_id WHERE j.source_id=%s AND r.matched_entity_type='artist' AND r.outcome='created'",(sid,)).fetchone();assert creators['unsafe']==0
   created=db.execute("""SELECT DISTINCT e.external_id,a.display_name,a.birth_year,a.death_year,a.timeline_basis,a.timeline_start_year,a.timeline_end_year
    FROM import_records r JOIN import_jobs j ON j.id=r.import_job_id JOIN artists a ON a.id=r.matched_entity_id
    JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='smk-person'
    WHERE j.source_id=%s AND r.matched_entity_type='artist' AND r.outcome='created'""",(sid,)).fetchall()
   for a in created:
    source=authors[a['external_id']];assert a['display_name']==source['name']
    if source['birth'] is not None and source['death'] is not None:
     assert (a['birth_year'],a['death_year'],a['timeline_start_year'],a['timeline_end_year'],a['timeline_basis'])==(source['birth'],source['death'],source['birth'],source['death'],'life')
    else:
     assert a['birth_year'] is None and a['death_year'] is None
     assert (a['timeline_start_year'],a['timeline_end_year'],a['timeline_basis'])==(source['start'],source['end'],'activity')
   missing=db.execute("""SELECT count(DISTINCT aa.artist_id) n FROM artwork_artists aa
    JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=aa.artwork_id AND e.source_id=%s AND e.scheme=%s
    WHERE NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=aa.artist_id AND c.country_code='DK' AND c.relationship_type='cultural_affiliation')""",(sid,SCHEME)).fetchone()['n'];assert missing==0
   scopes=dict(collections.Counter(w['date_scope'] for w in works));assert scopes=={'eligible':9199,'review':801}
   reports[target]={'artworks':10000,'new_painter_profiles':creators['n'],'linked_painters':len({p for w in works for p in (w['painters'] or [])}),'unlinked_artworks':sum(bool(w['unlinked_creator_label']) for w in works),'types':dict(collections.Counter(w['work_type'] for w in works)),'date_scopes':scopes,'works':works,'jobs':jobs}
   plans[target]=db.execute("EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id,a.title FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s",(SCHEME,works[0]['external_id'])).fetchone()
 assert reports['local']['works']==reports['production']['works']
 core.save_new(RUN/(label+'-metadata-verification.json'),reports);core.save_new(RUN/(label+'-query-plans.json'),plans)
 print({t:{k:v for k,v in r.items() if k not in ('works','jobs')} for t,r in reports.items()},flush=True)

def images(label):
 receipts=[json.loads(p.read_bytes()) for p in (RUN/'images/images/smk-danish').glob('*.json')]
 events={}
 for line in (RUN/'images/events.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e.get('artwork_id'):events[e['artwork_id']]=e
 assert len(receipts)==500 and all(events[r['artwork_id']]['outcome']=='complete' and events[r['artwork_id']]['local']=='attached' and events[r['artwork_id']]['cloud']=='attached' for r in receipts)
 client=storage.Client(project='artline-508319',credentials=core.GcloudCredentials());blobs={b.name:b for b in client.list_blobs(core.BUCKET,prefix='assets/artworks/open-museums/smk-danish/')}
 for r in receipts:
  p=ROOT/'apps/web/public'/r['path'].lstrip('/');data=p.read_bytes();assert len(data)==r['bytes']<=100000 and core.sha(data)==r['sha256']
  with Image.open(p) as im:assert im.size==(r['width'],r['height']);im.verify()
  b=blobs[r['path'].lstrip('/')];assert b.size==len(data) and b.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
 results={}
 for target,dsn in connections():
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   rows=db.execute("""SELECT m.id::text,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,m.creator_credit,m.license_url,a.id::text artwork_id,a.title,a.status,e.external_id,r.source_checksum,r.source_image_url
    FROM media_assets m JOIN media_rights_evidence r ON r.media_id=m.id JOIN artworks a ON a.primary_media_id=m.id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=%s WHERE m.id=ANY(%s::uuid[])""",(SCHEME,[r['media_id'] for r in receipts])).fetchall()
   assert len(rows)==500;byid={r['id']:r for r in rows}
   for r in receipts:
    d=byid[r['media_id']];assert d['external_id']==r['external_id'] and d['status']=='review' and d['creator_credit']==r['artist']
    assert d['checksum_sha256']==r['sha256'] and d['byte_size']==r['bytes'] and d['rights_status']=='public_domain' and d['license_url']==r['policy_url']
    assert d['source_checksum']==core.sha(core.encode(r['raw'])) and d['source_image_url']==r['source_image_url']
   n=db.execute("SELECT count(*) n FROM citations c JOIN sources s ON s.id=c.source_id WHERE s.slug=%s AND c.field_name='image_candidate'",(SOURCE,)).fetchone()['n'];assert n==1460
   if target=='local':
    token=re.search(r'^ARTLINE_EDITOR_TOKEN=(.*)$',(ROOT/'apps/server/.env').read_text(),re.M)[1].strip().strip('\"\'');api='http://127.0.0.1:8080';web='http://localhost:3000'
   else:
    token=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-editor-token','--project=artline-508319'],text=True).strip();api='https://artline-api-lpuqqlugnq-ew.a.run.app';web='https://artline-web-lpuqqlugnq-ew.a.run.app'
   first=rows[0];response=requests.get(api+'/api/v1/museums/statens-museum-for-kunst/works/'+first['artwork_id']+'?preview=1',headers={'Authorization':'Bearer '+token},timeout=30)
   assert response.status_code==200;d=response.json();assert d['title']==first['title'] and d['status']=='review' and d['media_url'] and d.get('display') is None
   response=requests.get(web+first['storage_path'],timeout=30);assert response.status_code==200 and core.sha(response.content)==first['checksum_sha256']
   page=requests.get(api+'/api/v1/museums/statens-museum-for-kunst/works?preview=1&image_only=1&limit=3',headers={'Authorization':'Bearer '+token},timeout=30);assert page.status_code==200 and len(page.json()['items'])==3
   results[target]={'attached_images':500,'image_candidates':n,'artwork_api':200,'served_image_checksum':'matched','bounded_image_page':3}
 report={'images':500,'bytes':sum(r['bytes'] for r in receipts),'largest_image_bytes':max(r['bytes'] for r in receipts),'targets':results,'errors':[]}
 core.save_new(RUN/(label+'-image-verification.json'),report);print(report,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['metadata','images']);p.add_argument('--label',required=True);a=p.parse_args();globals()[a.phase](a.label)
