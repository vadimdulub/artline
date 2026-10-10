"""Reuse captured first page and finish bounded 205-record M0284 selection."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-girodet-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
def main():
 first=m.load(RUN/'captures/joconde-current-002.json');raw=gzip.decompress((m.ROOT/first['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==first['sha256'];data=json.loads(raw);assert data['meta']['total']==205 and len(data['data'])==200
 url=data['links']['next'];assert url.startswith('https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/?Code_Museofile__exact=M0284&')
 response=requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded single museum metadata)'},timeout=(15,60));raw=response.content;assert len(raw)<1_000_000;body=RUN/'captures/joconde-page2-001.body.gz';assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),body_path=str(body.relative_to(m.ROOT)));m.save(RUN/'captures/joconde-page2-001.json',rc);response.raise_for_status();last=response.json();assert last['meta']['total']==205 and len(last['data'])==5 and not last['links']['next'];rows=data['data']+last['data'];assert len({v['Reference'] for v in rows})==205 and all(v['Code_Museofile']=='M0284' for v in rows)
 m.save(RUN/'joconde-current-003.json.gz',dict(at=m.now(),receipts=[first,rc],rows=rows,policy='205 current records, one museum, bounded 250 metadata ceiling. No image downloads or database writes.'))
 for v in sorted(rows,key=lambda v:v['Reference']):print(' | '.join(str(v.get(k) or '') for k in ['Reference','Titre','Auteur','Millesime_de_creation','Periode_de_creation','Domaine','Numero_inventaire','MANQUANT','Lieu_de_depot']),flush=True)
if __name__=='__main__':main()
