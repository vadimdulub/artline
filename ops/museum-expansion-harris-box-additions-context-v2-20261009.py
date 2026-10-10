"""Reconstruct exact comparator evidence without repeating entire Wikidata batches."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=m.RUN/'native/harris-box-additions-20261009';n.RUN=RUN;ref=n.ref
def wikiart(raw):
 soup=n.BeautifulSoup(raw,'html.parser');p=soup.select_one('.wiki-layout-artwork-info');assert p;fields={}
 for li in p.select('li'):
  text=li.get_text(' ',strip=True)
  if ':' in text:
   k,v=text.split(':',1)
   if len(k)<40:fields[k.strip()]=v.strip()
 return dict(title=p.select_one('h1').get_text(' ',strip=True),creator=p.select_one('h2').get_text(' ',strip=True),fields=fields,text=p.get_text(' ',strip=True))
def main():
 dest=RUN/'comparison-source-context-002.json.gz';assert not dest.exists();identity=m.load(RUN/'identity-002.json.gz');cs=m.load(RUN/'identity-citations-002.json.gz')['citations'];wanted={h['entity_id'] for c in identity['comparisons'] for h in c['source_hits']}|{h['id'] for c in identity['comparisons'] for h in c['hits']};rows=[];groups=collections.defaultdict(list);missing=[];bodies={}
 for c in cs:
  if c['entity_id'] not in wanted:continue
  try:note=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(note,dict):continue
  path=None;sha=None
  if note.get('source_record',{}).get('decision',{}).get('source_capture'):
   cap=note['source_record']['decision']['source_capture'];path=m.ROOT/cap['body_path'];sha=cap['receipt']['sha256']
  elif note.get('source_receipt',{}).get('body_path'):cap=note['source_receipt'];path=m.ROOT/cap['body_path'];sha=cap.get('sha256') or cap['receipt']['sha256']
  elif note.get('artwork_receipt'):
   cap=note['artwork_receipt'];key=hashlib.sha256(cap['url'].encode()).hexdigest();options=[m.ROOT/('docs/research/'+folder+'/captures')/(key+'.body') for folder in ['wikiart-artist-coverage-20260920','wikiart-selected-images-20260919','uk-painters-20260920','uk-painters-20260920/wikiart-supplement','women-wikiart-20260920','wikiart-top100-20260920']];matches=[p for p in options if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==cap['sha256']]
   if matches:path=matches[0];sha=cap['sha256']
  elif note.get('evidence_path') and note.get('source_response_sha256'):path=m.ROOT/note['evidence_path'];sha=note['source_response_sha256']
  elif note.get('entity_receipt'):cap=note['entity_receipt'];path=m.ROOT/'docs/research/uk-painters-20260920/captures'/(hashlib.sha256(cap['url'].encode()).hexdigest()+'.json');sha=cap['sha256']
  row=dict(artwork_id=c['entity_id'],citation_id=c['id'],source_url=c['source_url'],source_id=c['source_record_id'],source_note=note);rows.append(row)
  if path and path.exists():groups[str(path)].append((row,sha))
  else:row['body_reference']=None;missing.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],reason='Exact raw body not reconstructed; retained source note only'))
 for path,group in groups.items():
  p=Path(path);stored=p.read_bytes();raw=gzip.decompress(stored) if p.suffix=='.gz' else stored;digest=hashlib.sha256(raw).hexdigest();proof=ref(p);bodies[proof['path']]=proof
  try:data=json.loads(raw)
  except (ValueError,UnicodeDecodeError):data=None
  for row,sha in group:
   assert digest==sha;row.update(body_reference=proof,raw_sha256=sha)
   if 'wikiart.org/' in (row['source_url'] or ''):row.update(format='wikiart_html',parsed=wikiart(raw))
   elif isinstance(data,dict) and 'entities' in data:
    sid=row['source_id'];row.update(format='wikidata_entity',data=data['entities'].get(sid),full_batch_omitted=True)
    if row['data'] is None:row['missing_exact_entity_in_raw_batch']=True
   elif data is not None:
    row.update(format='json',data=data if len(raw)<100000 else None,large_raw_json_omitted=len(raw)>=100000)
   else:
    html=b'<html' in raw[:1000].lower() or b'<!doctype html' in raw[:1000].lower();row.update(format='html' if html else 'xml_or_text')
    if html:row['parsed']=n.parsed(raw)
 m.save(dest,dict(at=m.now(),requested_ids=sorted(wanted),rows=rows,body_references=list(bodies.values()),unreconstructed_bodies=missing,identity_reference=ref(RUN/'identity-002.json.gz'),citations_reference=ref(RUN/'identity-citations-002.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Stored citations and exact available raw bodies,not fresh native confirmations. Retain only selected entity per Wikidata body; complete body is pinned. Pixel dimensions are not physical dimensions. No network or database changes.'))
 print(json.dumps(dict(wanted=len(wanted),rows=len(rows),bodies=len(bodies),unreconstructed=len(missing),wikiart_rows=sum(r.get('format')=='wikiart_html' for r in rows))),flush=True)
if __name__=='__main__':main()
