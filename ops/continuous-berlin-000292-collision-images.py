import importlib.util,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
ids=['826518d4-5da4-5497-91d6-aaae06aee7ad']
D=Path.home()/'Library/Application Support/Artline/source-images'/b.OP/'identity-review';D.mkdir(parents=True,exist_ok=True)
with h.connect() as db:
 rows=[dict(x) for x in db.execute('SELECT a.id::text,m.storage_path,m.checksum_sha256 FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
for r in rows:
 url='https://artlines.org'+r['storage_path'];res=requests.get(url,timeout=(15,40));res.raise_for_status();assert h.sha(res.content)==r['checksum_sha256'];p=D/(r['id']+'.jpg');p.write_bytes(res.content);r.update(path=str(p),sha256=h.sha(res.content),status=res.status_code)
h.save(b.E/'collision-image-captures.json',dict(at=h.now(),images=rows));print([(x['id'],x['path']) for x in rows])
