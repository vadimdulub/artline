"""Recover exact retained IWM primary pages for15 additional pending objects."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-iwm-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
def parsed(raw,url):
 sp=BeautifulSoup(raw,'html.parser');fields=collections.defaultdict(list)
 for dt in sp.select('dt'):
  dd=dt.find_next_sibling('dd')
  if dd:fields[dt.get_text(' ',strip=True)].append(dd.get_text(' ',strip=True))
 assert sp.h1 and fields.get('Catalogue number') and 'Imperial War Museums' in sp.get_text(' ',strip=True)
 return dict(title=sp.h1.get_text(' ',strip=True),fields=dict(fields),url=url)
def main():
 dest=RUN/'source-context-002.json.gz';assert not dest.exists();base=m.load(RUN/'source-context-001.json.gz');initial=m.load(RUN/'initial-scope-001.json.gz');arts={v['id']:v for v in initial['snapshot']['artworks']};old=m.ROOT/'docs/research/artwork-locations-20261004';group_path=old/'remaining-wikidata-groups-20261005c.json.gz';group={v['artwork_id']:v for v in m.load(group_path)['Q23315190']};refs={v['path']:v for v in base['body_references']};rows=[dict(v,source_format='wikidata') for v in base['rows']];cache={}
 def read(path,sha):
  key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;cache[key]=raw;refs[ref(path)['path']]=ref(path)
  return cache[key]
 for h in base['source_holds']:
  assert len(h['assertions'])==1;assertion=h['assertions'][0];note=json.loads(assertion['evidence_note']);assert note['scheme']=='iwm-object';v=group[h['artwork_id']];raw=read(m.ROOT/v['receipt']['body_path'],v['receipt']['sha256']);assert json.loads(raw)['entities'][v['qid']]==v['entity'];path=m.ROOT/note['evidence_path'];body=read(path,note['source_response_sha256']);native=parsed(body,assertion['source_url']);prior_path=old/'iwm-selected-objects-20261005c'/(note['object_id']+'.json.gz');prior=m.load(prior_path);assert native==prior['object'];assert prior['source_receipt']['sha256']==note['source_response_sha256'];refs[ref(prior_path)['path']]=ref(prior_path)
  rows.append(dict(number=len(rows)+1,institution_id=s.NETWORK,museum_qid=s.QIDS[s.NETWORK],artwork=arts[h['artwork_id']],pending_assertion=assertion,additional_pending_assertions=[],original_evidence=note,source_id=v['qid'],entity=v['entity'],body_reference=ref(m.ROOT/v['receipt']['body_path']),raw_sha256=v['receipt']['sha256'],source_format='wikidata_and_retained_native',native_object=native,native_reference=ref(path),native_raw_sha256=note['source_response_sha256'],native_capture=prior['source_receipt'],native_id=note['object_id']))
 authpath=old/'iwm-museum-authority-20261005c.json';auth=m.load(authpath);cap=auth['museum_receipt'];body=read(m.ROOT/cap['body_path'],cap['sha256']);text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True);assert text==auth['museum_text'];assert 'Our Five Museums' in text and 'IWM’s collection' in text;refs[ref(authpath)['path']]=ref(authpath)
 m.save(RUN/'retained-institution-context-001.json.gz',dict(at=m.now(),source_reference=ref(authpath),body_reference=ref(m.ROOT/cap['body_path']),raw_sha256=cap['sha256'],receipt=cap,text=text,policy='Retained5October primary collection overview distinguishes a shared IWM collection and five museum branches. Not a current display assertion. No fresh native request after access refusal.'))
 assert len(rows)==len({v['artwork']['id'] for v in rows})==103;m.save(dest,dict(at=m.now(),rows=rows,source_holds=[],body_references=list(refs.values()),initial_reference=ref(RUN/'initial-scope-001.json.gz'),previous_source_reference=ref(RUN/'source-context-001.json.gz'),selection_reference=ref(group_path),institution_context_reference=ref(RUN/'retained-institution-context-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='88 secondary objects plus15 exact retained native objects. Original source-parser holds were format limitations,not lost objects. All date wording differences remain for explicit review; no date or metadata rewriting.'))
 print(json.dumps(dict(rows=103,native=15,retained_references=len(refs),network_context_verified=True)),flush=True)
if __name__=='__main__':main()
