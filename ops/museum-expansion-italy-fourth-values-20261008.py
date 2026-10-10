"""Fetch explicit measurement value/unit nodes for source-screened objects."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-italy-fourth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN;c=f.c;c.ROOT=RUN/'measurement-values-001'
def main():
 dest=RUN/'measurement-values-001.json.gz';assert not dest.exists();source=RUN/'native-candidates-001.json.gz';rows=m.load(source)['rows']
 selected=[r for r in rows if r['state']=='candidate'];uris=sorted({u for r in selected for v in r['facts']['measurements'] for u in v['value_nodes']});triples=[];components=[];failures=[]
 for start in range(0,len(uris),20):
  if c.STOP.is_set():break
  group=uris[start:start+20]
  try:
   vs,comp=c.subjects(group);triples+=vs;components.append(comp)
   print(json.dumps(dict(done=start+len(group),total=len(uris),triples=len(triples))),flush=True)
  except Exception as error:failures.append(dict(subjects=group,error=repr(error)))
 m.save(dest,dict(at=m.now(),numbers=[r['number'] for r in selected],requested=uris,triples=triples,components=components,failures=failures,stopped=c.STOP.is_set(),source_reference=f.ref(source),script_reference=f.ref(Path(__file__).resolve()),database_writes=0,images=0))
if __name__=='__main__':main()
