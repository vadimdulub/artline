"""Retain exact previously captured primary museum metadata for physical-version checks."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
WANTED={'1c2bfc09-ffe7-4581-beaf-2c92776aefef':'tate-accession','c71d1de9-446b-472f-88f2-7c4f3486452f':'tate-accession','f21910aa-ed7c-5c81-adca-681c5fbe88dc':'agsa-object'}
def main():
 dest=RUN/'retained-primary-comparisons-001.json.gz';assert not dest.exists();cs=m.load(RUN/'identity-citations-001.json.gz')['citations'];out=[]
 for c in cs:
  if c['entity_id'] not in WANTED:continue
  try:x=json.loads(c['evidence_note'])
  except (ValueError,TypeError):continue
  if x.get('scheme')!=WANTED[c['entity_id']]:continue
  p=m.ROOT/x['evidence_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==x['source_response_sha256'];fmt='json' if x['scheme']=='tate-accession' else 'html';data=json.loads(raw) if fmt=='json' else n.parsed(raw);out.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_url=c['source_url'],source_record=x['object_id'],format=fmt,body_reference=ref(p),raw_sha256=x['source_response_sha256'],data=data));print(json.dumps(dict(artwork_id=c['entity_id'],format=fmt,data=data if fmt=='json' else data['text'][-8000:]),ensure_ascii=False),flush=True)
 assert len(out)==3;m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),policy='Retained original primary museum source bodies,not new fetches. Exact dimensions,medium and accession aid version comparisons; no image downloads or rights inference.'))
if __name__=='__main__':main()
