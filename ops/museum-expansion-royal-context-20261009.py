"""Retain selected identity-comparison source records and verify available raw bodies."""
import collections,csv,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-royal-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
def wikiart(raw):
 s=n.n.BeautifulSoup(raw,'html.parser');p=s.select_one('.wiki-layout-artwork-info');assert p is not None;fields={}
 for li in p.select('li'):
  text=li.get_text(' ',strip=True)
  if ':' in text:
   k,v=text.split(':',1)
   if len(k)<40:fields[k.strip()]=v.strip()
 return dict(title=p.select_one('h1').get_text(' ',strip=True),creator=p.select_one('h2').get_text(' ',strip=True),fields=fields,text=p.get_text(' ',strip=True))
def glasgow(raw):
 s=n.n.BeautifulSoup(raw,'html.parser');details=s.select_one('#frTab1');assert details;fields={};repeated={}
 for dt in details.select('dt'):
  dd=dt.find_next_sibling('dd');assert dd;label=dt.get_text(' ',strip=True);value=dd.get_text(' ',strip=True)
  if label in fields:repeated.setdefault(label,[fields[label]]).append(value)
  else:fields[label]=value
 return dict(fields=fields,repeated=repeated,maker_links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in details.select('a[href]') if 'type=701' in a['href']])

def main():
 dest=RUN/'comparison-source-context-001.json.gz';assert not dest.exists();x=m.load(RUN/'identity-001.json.gz');cs=m.load(RUN/'identity-citations-001.json.gz')['citations'];wanted={r['existing_artwork_id'] for r in x['rows']}|{h['id'] for c in x['comparisons'] for h in c['hits'] if h['same_creator'] or h['same_museum'] and 'inventory' in h['hit_types']};rows=[];bodies={};missing=[]
 for c in cs:
  if c['entity_id'] not in wanted:continue
  try:note=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(note,dict):continue
  path=None;sha=None
  if note.get('source_receipt',{}).get('body_path'):cap=note['source_receipt'];path=m.ROOT/cap['body_path'];sha=cap['sha256']
  elif note.get('artwork_receipt'):
   cap=note['artwork_receipt'];key=hashlib.sha256(cap['url'].encode()).hexdigest();options=[m.ROOT/('docs/research/'+folder+'/captures')/(key+'.body') for folder in ['wikiart-artist-coverage-20260920','wikiart-selected-images-20260919','uk-painters-20260920','uk-painters-20260920/wikiart-supplement','women-wikiart-20260920','wikiart-top100-20260920']];matches=[p for p in options if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==cap['sha256']]
   if matches:path=matches[0];sha=cap['sha256']
  elif note.get('evidence_path') and note.get('source_response_sha256'):path=m.ROOT/note['evidence_path'];sha=note['source_response_sha256']
  elif note.get('entity_receipt'):cap=note['entity_receipt'];path=m.ROOT/'docs/research/uk-painters-20260920/captures'/(hashlib.sha256(cap['url'].encode()).hexdigest()+'.json');sha=cap['sha256']
  row=dict(artwork_id=c['entity_id'],citation_id=c['id'],source_url=c['source_url'],source_id=c['source_record_id'],source_note=note)
  if path and path.exists():
   raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;proof=ref(path);bodies[proof['path']]=proof;row.update(body_reference=proof,raw_sha256=sha)
   if 'wikiart.org/' in (c['source_url'] or ''):row.update(format='wikiart_html',parsed=wikiart(raw))
   elif 'collections.glasgowmuseums.com/' in (c['source_url'] or ''):row.update(format='glasgow_html',parsed=glasgow(raw))
   else:
    try:row.update(format='json',data=json.loads(raw))
    except (ValueError,UnicodeDecodeError):row.update(format='html' if b'<html' in raw[:1000].lower() or b'<!doctype html' in raw[:1000].lower() else 'csv_or_text')
  else:row['body_reference']=None;missing.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],reason='No reconstructed exact raw-body path; stored source note retained only'))
  rows.append(row)
 m.save(dest,dict(at=m.now(),requested_ids=sorted(wanted),rows=rows,body_references=list(bodies.values()),unreconstructed_bodies=missing,identity_reference=ref(RUN/'identity-001.json.gz'),citations_reference=ref(RUN/'identity-citations-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Retained source citations and checksum-verified available raw bodies. Pixel dimensions in WikiArt source_metadata are not physical object dimensions. Some citations have no reconstructed raw body; no stronger provenance claim. No requests,images or database changes.'))
 print(json.dumps(dict(wanted=len(wanted),rows=len(rows),bodies=len(bodies),unreconstructed=len(missing),wikiart_rows=sum(r.get('format')=='wikiart_html' for r in rows))),flush=True)
if __name__=='__main__':main()
