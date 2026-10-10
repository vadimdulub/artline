"""Four bounded observed Guildhall metadata facets before exact-object selection."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('g',Path(__file__).with_name('museum-expansion-britain-seven-gac-20261009.py'));g=importlib.util.module_from_spec(z);z.loader.exec_module(g);p=g.p;m=g.m;RUN=g.RUN
def main():
 dest=RUN/'guildhall-gac-indexes-001.json.gz';assert not dest.exists();probe=RUN/'guildhall-gac-probe-001.json';x=m.load(probe);names=['Oil paint 85','Canvas 59','Paper 26','Briton Rivière 1'];rows={v['source_id']:dict(v,index_references=[p.ref(probe)]) for v in x['rows']};refs=[]
 for number,name in enumerate(names,1):
  urls={g.BASE+v['href'] for v in x['parsed']['links'] if v['text']==name and v['href'].startswith('/explore/collections/guildhall-art-gallery?')};assert len(urls)==1;url=urls.pop();raw,cap=p.n.capture('guildhall_gac',url);rs=g.cards(raw);assert len(rs)<=20;path=RUN/'guildhall-gac-indexes-001'/('%03d.json'%number);assert not path.exists();m.save(path,dict(at=m.now(),name=name,url=url,capture=cap,rows=rs,discovery_reference=p.ref(probe)));ref=p.ref(path);refs.append(ref)
  for v in rs:
   if v['source_id'] in rows:assert {k:rows[v['source_id']][k] for k in v}==v
   else:rows[v['source_id']]=dict(v,index_references=[])
   rows[v['source_id']]['index_references'].append(ref)
  print(json.dumps(dict(name=name,rows=len(rs),distinct=len(rows))),flush=True)
 m.save(dest,dict(at=m.now(),rows=list(rows.values()),index_references=refs,probe_reference=p.ref(probe),script_reference=p.ref(Path(__file__).resolve()),policy='At most four initial20 metadata facets plus31 partner-page cards; no pagination or image downloads. Cards include crops,details and duplicate publisher presentations,so counts are not physical artwork counts. Select exact pending museum object matches before detail capture.'))
if __name__=='__main__':main()
