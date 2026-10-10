"""One bounded authority request for existing unlinked creator labels."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN
import types
f=types.SimpleNamespace(ref=n.ref,rows=lambda:m.load(RUN/'candidate-facts-001.json.gz')['rows'])

def main():
 dest=RUN/'unlinked-creator-authorities-001.json.gz';assert not dest.exists();rows=[v for v in f.rows() if 'creator_authority_requires_reconciliation' in v['issues']];qids=sorted({v['facts']['creator_qid'] for v in rows});url='https://www.wikidata.org/w/api.php';params=dict(action='wbgetentities',ids='|'.join(qids),props='labels|aliases|claims',format='json');req=requests.Request('GET',url,params=params).prepare();root=RUN/'creator-capture-001';root.mkdir();receipt=dict(at=m.now(),url=req.url,requested_qids=qids)
 try:
  response=requests.get(req.url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected creator authority metadata)'},timeout=(12,45));raw=response.content;assert len(raw)<3_000_000;path=root/'body.json.gz';path.write_bytes(gzip.compress(raw,mtime=0));receipt.update(status=response.status_code,final_url=response.url,raw_sha256=hashlib.sha256(raw).hexdigest(),body_reference=f.ref(path));m.save(root/'receipt.json',receipt);response.raise_for_status();assert response.url==req.url;es=json.loads(raw)['entities'];assert set(es)==set(qids);decisions=[]
  for r in rows:
   e=es[r['facts']['creator_qid']];labels={v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs};exact=m.norm(r['facts']['creator_label']) in {m.norm(v) for v in labels};decisions.append(dict(number=r['number'],qid=e['id'],existing_label=r['facts']['creator_label'],label_match=exact,entity=e))
  m.save(dest,dict(at=m.now(),rows=decisions,requested_qids=qids,capture_reference=f.ref(root/'receipt.json'),body_reference=f.ref(path),script_reference=f.ref(Path(__file__).resolve()),policy='Source labels verify existing unlinked creator text only. No painter record creation/link or biography/date inference.'));print(json.dumps(dict(qids=len(qids),rows=len(rows),exact_labels=sum(v['label_match'] for v in decisions))),flush=True)
 except Exception as e:
  if not (root/'receipt.json').exists():m.save(root/'receipt.json',dict(receipt,error=type(e).__name__+': '+str(e)))
  raise
if __name__=='__main__':main()
