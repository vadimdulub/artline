#!/usr/bin/env python3
"""Evidence-backed decisions for 170 same-title pairs; no DB mutations."""
import collections,csv,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'duplicates/same-title-deep-review'
def inventory(r):
 if r.get('inventory'):return r['inventory'],'Current museum object inventory'
 values=r.get('inventories',[])
 for label in ('Inventario corrente','Inventario nucleo Autori','Inventario nucleo Durini','Inventario M.G. Borghi'):
  valid=[v for v in values if v['label']==label and re.search(r'\d',v['number'])]
  if len(valid)==1:return valid[0]['number'],label
 valid=[v for v in values if v['label'] is None and re.fullmatch(r'\d+(?:\.\d+)?',v['number'])]
 if len(valid)==1:return valid[0]['number'],'Museum inventory, label absent in extracted section'
 return None,None
def main():
 dest=RUN/'final-pair-decisions.json'
 if dest.exists():return
 candidates=json.loads((RUN/'candidates.json').read_text());index={}
 for path in (RUN/'inventory-review').glob('*.json'):
  row=json.loads(path.read_text());index[row['slug']]=row
 out=[]
 for n,pair in enumerate(candidates['pairs'],1):
  rows=[index[w['slug']] for w in pair['works']];assert len(rows)==2
  sources=[r['reviews'][0] for r in rows];assert all(len(r['reviews'])==1 and not r['reviews'][0].get('error') for r in rows)
  keys=[inventory(r) for r in sources];assert all(k[0] for k in keys),(n,keys)
  for r in sources:assert CORE.sha(Path(r['capture']).read_bytes())==r['receipt']['sha256']
  inst=pair['key'][0];decision='keep_separate';reason='Different explicit object inventories in the same museum. Same title and creator do not establish a duplicate; separate studies, versions and print impressions remain separately catalogued.'
  if n in (17,18):
   assert keys[0][0]==keys[1][0] and inst=='musei-civici-pavia';decision='confirmed_duplicate_pending_application';reason='Same current Pavia inventory, maker, dimensions, provenance and individually inspected primary painting image. Reviewed consolidation plan is staged; Cloud reauthentication interrupted application. Circa and conflicting source details preserved.'
  elif n in (99,102):
   assert 'Recto' in keys[0][0] and 'Verso' in keys[1][0];decision='keep_recto_verso_depictions';reason='Two distinct drawings on opposite sides of one support. Preserve both artwork depictions and source records; do not collapse them as duplicate images. Future physical-support grouping is separate backend/editorial work.'
  elif n==96:
   assert keys[0][0]=='140 B 57' and keys[1][0]=='144 B 61';reason='Distinct Autori inventories and GAM4217/4216; primary dimensions and explanatory text describe two studies. Shared1255/12 is an acquisition register, not the physical-object accession.'
  elif n in (128,129,130,131,132,133):
   assert all(k[1]=='Inventario M.G. Borghi' for k in keys);reason='Different explicit Borghi object inventories support separate catalogue objects. Current inventory is incomplete (DS without a number); shared historical461 is not sufficient identity evidence. Keep separate and request complete current inventories.'
  else:assert keys[0][0]!=keys[1][0],(n,keys)
  out.append(dict(pair_number=n,institution_slug=inst,title=pair['works'][0]['title'],artist_slugs=pair['key'][2],first_slug=rows[0]['slug'],second_slug=rows[1]['slug'],first_inventory=keys[0][0],first_inventory_context=keys[0][1],second_inventory=keys[1][0],second_inventory_context=keys[1][1],first_source_url=sources[0]['receipt'].get('final_url') or sources[0]['receipt']['url'],second_source_url=sources[1]['receipt'].get('final_url') or sources[1]['receipt']['url'],first_dimensions=sources[0].get('dimensions'),second_dimensions=sources[1].get('dimensions'),decision=decision,reason=reason,source_capture_sha256=[r['receipt']['sha256'] for r in sources]))
 result=dict(at=CORE.now(),pairs=len(out),objects=len(index),counts=dict(collections.Counter(r['decision'] for r in out)),scope='170 prioritized same-title/creator/institution pairs,340 primary objects. This is not an exhaustive ruling on all database title groups. Decisions preserve source distinctions; no automatic deletions.',decisions=out);CORE.save_new(dest,result)
 with (RUN/'final-pair-decisions.csv').open('x',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader()
  for row in out:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in row.items()})
 print(result['counts'],flush=True)
if __name__=='__main__':main()
