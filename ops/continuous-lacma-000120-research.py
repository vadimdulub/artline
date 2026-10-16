"""Bounded LACMA source capture and read-only production reconciliation."""
import importlib.util,json,csv,fcntl,subprocess,datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000120'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000120'
E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
def save(n,v):h.save(E/n,v)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  save('production-target-verification.json',b.target())
  paths=[ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')]+[ROOT/'docs'/n for n in ['ARTLINE_IMAGE_USE.md','DATA_AND_IMAGE_COLLECTION_PROMPT.md','LOCAL_DATA_LOCATIONS.md']]
  registry=list(csv.DictReader(paths[1].open()));assert len(registry)==111
  save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in paths],registry_rows=111))
  save('source-register.json',dict(at=h.now(),registry=[r for r in registry if r['source_id']=='lacma'],policy_reference='docs/ARTLINE_IMAGE_USE.md',image_downloads=0))
  with b.connect() as db:
   p=h.load(E.parent/'000114/batch107-live-reconciliation.json');assert h.snapshot(db,list(p['live']))==p['live'];save('batch107-live-reconciliation.json',dict(at=h.now(),verified_ids=list(p['live']),snapshot_equal=True,prior_receipt_sha256=h.sha((E.parent/'000114/batch107-live-reconciliation.json').read_bytes()),new_increments=0))
   p=h.load(E.parent/'000109/independent-production-verification.json');assert h.snapshot(db,list(p['after']))==p['after'];save('batch109-live-reconciliation.json',dict(at=h.now(),verified_ids=list(p['after']),snapshot_equal=True,new_increments=0))
  captures=[]
  for nid in ['40124','59982','28991','22450','198584','148372','158374','165148','167381']:
   url='https://collections.lacma.org/object/'+nid
   p=E/'captures'/f'{nid}.json'
   if p.exists():cap=h.load(p)
   else:
    r=requests.get(url,timeout=45);raw=r.content
    body=E/'captures'/f'{nid}.html';body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(raw)
    soup=BeautifulSoup(raw,'html.parser')
    cap=dict(at=h.now(),native_id=nid,url=url,final_url=r.url,status=r.status_code,sha256=h.sha(raw),body=str(body.relative_to(ROOT)),text=soup.get_text(' ',strip=True))
    save('captures/'+nid+'.json',cap)
   captures.append(cap)
   if cap['status'] in [401,403,429]:break
  with b.connect() as db:
   inst=[dict(x) for x in db.execute("SELECT id::text,name,slug FROM institutions WHERE name ILIKE '%Los Angeles County%' OR slug ILIKE '%lacma%' LIMIT 20")]
   save('institution-reconciliation.json',dict(at=h.now(),institutions=inst))
   ids=[r['id'] for r in inst]
   rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,status,primary_media_id::text,unlinked_creator_label,current_institution_id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND (title ~* 'Guadalupe|Adoration|Funerary|Dancing Soldiers|Archangel Michael|Marriage of the Virgin|Education of the Virgin') LIMIT 100",(ids,))]
   urls=[v for c in captures for v in [c['url'],c['url'].replace('/object/','/node/')]]
   refs=[dict(r) for r in db.execute("SELECT entity_id::text,canonical_url url,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) UNION ALL SELECT entity_id::text,source_url,NULL,NULL FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,urls))]
   allids=sorted({r['id'] for r in rows}|{r['entity_id'] for r in refs})
   save('production-reconciliation.json',dict(at=h.now(),read_only=True,rows=rows,source_matches=refs,states=h.snapshot(db,allids)))
  print(json.dumps(dict(captures=[dict(native_id=c['native_id'],status=c['status']) for c in captures],production_candidates=rows),default=str))
