import importlib.util,json,csv,subprocess,gzip
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000096.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
q=h.load(b.E.parents[1]/'source-queue.json');b.save('source-queue-before.json',q)
paths=[b.ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),b.ROOT/'docs/ARTLINE_IMAGE_USE.md',b.ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',b.ROOT/'docs/LOCAL_DATA_LOCATIONS.md',b.E.parents[1]/'CHECKPOINT.json',b.E.parents[1]/'source-queue.json',b.E.parent/'000095/CHECKPOINT.json',b.E.parent/'000093/CHECKPOINT.json']
inputs=[]
for p in paths:
 raw=p.read_bytes();text=raw.decode();inputs.append(dict(path=str(p),sha256=h.sha(raw),bytes=len(raw),lines=len(text.splitlines())))
registry=list(csv.DictReader(open(paths[1])));assert len(registry)==111
holds=[]
for row in q['sources']:
 if row['source_id'] in ['national_gallery_athens','hermitage','tretyakov_gallery','national_museum_warsaw','yale_lux']:
  holds.append(row)
for p in [b.E.parent/'000095/source-register-final.json',b.E.parent/'000095/research-holds.json',b.ROOT/'docs/research/random-country-collections-20261009/source-access-holds.json']:
 if p.exists():inputs.append(dict(path=str(p),sha256=h.sha(p.read_bytes()),content=h.load(p)))
b.save('required-input-reconciliation.json',dict(at=h.now(),inputs=inputs,registry=registry,source_routes_and_holds=holds,precedence='Current instructions and source-specific approvals; real local catalogue read-only; original CSV authoritative'))
b.save('production-target-before-discovery.json',b.target())
prior=h.load(b.E.parent/'000095/norway/independent-production-verification.json');print('prior keys',list(prior))
with h.connect() as db:
 existing=db.execute("SELECT a.id::text,a.title,a.date_display,a.medium_text,a.dimensions_text,a.accession_number,a.primary_media_id::text,a.current_institution_id::text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s ORDER BY a.title,a.id",('d0b220dd-6817-4a2b-93a7-01193f38def3',)).fetchall();before=h.snapshot(db,[r['id'] for r in existing]);b.save('existing-parthenis-works.json',dict(at=h.now(),rows=existing));b.save('preserved-parthenis-before.json.gz',dict(at=h.now(),artworks=before));h.save(h.BACKUP/'preserved-parthenis-before.json.gz',h.load(b.E/'preserved-parthenis-before.json.gz'))
 priorrows=prior.get('rows',prior.get('records',[]));print('prior row keys',list(priorrows[0]) if priorrows else 'none')
form=dict(artist_id='91',lang='en',page=5,action='get_artist_artworks');url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php'
cp=b.E/'parthenis-page5-capture.json'
if cp.exists():rc=h.load(cp);raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256']
else:
 b.i.provider_slot('www.nationalgallery.gr');resp=b.i.session().post(url,data=form,timeout=(15,45));raw=resp.content;path=b.S/'parthenis-page5.json';path.write_bytes(raw);rc=dict(at=h.now(),url=url,method='POST',form=form,status=resp.status_code,retry_after=resp.headers.get('Retry-After'),sha256=h.sha(raw),body_path=str(path));b.save('parthenis-page5-capture.json',rc)
assert rc['status']==200
obj=json.loads(raw);print('response',str(obj)[:1500]);html=obj['data']['html'] if isinstance(obj.get('data'),dict) else obj.get('html',obj.get('data',''))
sp=BeautifulSoup(html,'html.parser');urls=list(dict.fromkeys(a['href'] for a in sp.select('a[href]') if '/en/artwork/' in a['href']));assert 0<len(urls)<=50
old=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');assert not set(urls)&set(old['resume_cursor']['processed_urls'])
b.save('parthenis-konstantinos-object-urls.json',urls);print('objects',len(urls));b.stage()
