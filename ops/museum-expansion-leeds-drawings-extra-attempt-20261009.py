import importlib.util,gzip,hashlib,json,csv,io
from pathlib import Path
root=Path.cwd();z=importlib.util.spec_from_file_location('n',root/'ops/museum-expansion-leeds-drawings-native-20261009.py');n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;n.n.SITES['met']='https://www.metmuseum.org'
dest=RUN/'comparison-native-extra-001.json.gz'
if not dest.exists():
 rows=[]
 for provider,url in [('cotmania','https://cotmania.org/works-of-art/43916'),('met','https://www.metmuseum.org/art/collection/search/373905')]:
  raw,cap=n.n.capture(provider,url);rows.append(dict(provider=provider,url=url,capture=cap,parsed=n.parsed(raw)))
 m.save(dest,dict(at=m.now(),rows=rows,policy='Two selected primary physical-version comparators; metadata only.'))
x=m.load(dest)
for r in x['rows']:
 text=r['parsed']['text'];print(r['url'],len(text));print(text[:14000])
ctx=m.load(RUN/'comparison-source-context-001.json.gz');out=[]
for r in ctx['rows']:
 v={k:x for k,x in r.items() if k not in ['data']}
 if 'data' in r:
  data=r['data'];sid=r.get('source_id');ent=data.get('entities',{}) if isinstance(data,dict) else {}
  v['selected_data']=ent.get(sid) if sid in ent else None
  v['raw_batch_omitted_from_summary']=True
 if r.get('format')=='csv_or_text' and r['artwork_id'] in ['81af8f49-cd5a-588d-8aa6-1524436f3f47','72b26198-706d-5692-91ee-4c69ed4d2aff']:
  p=root/r['body_reference']['path'];raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes();txt=raw.decode();needle='30853' if r['artwork_id'].startswith('81a') else '41057';v['matching_text_lines']=[line for line in txt.splitlines() if needle in line];print('YALE',r['artwork_id'],r['source_id'],v['matching_text_lines'][:3])
 out.append(v)
small=dict(ctx,rows=out,full_context_reference=n.ref(RUN/'comparison-source-context-001.json.gz'));m.save(RUN/'comparison-source-context-compact-001.json.gz',small);print('COMPACT',len(out))
