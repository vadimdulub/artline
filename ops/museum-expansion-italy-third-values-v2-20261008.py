"""Fetch explicit measurement value/unit nodes for source-screened objects."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-italy-third-facts-v2-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN;c=f.c;c.ROOT=RUN/'measurement-values-002'
def main():
 dest=RUN/'measurement-values-002.json.gz';assert not dest.exists();source=RUN/'native-candidates-002.json.gz';rows=m.load(source)['rows']
 selected=[r for r in rows if r['state']=='candidate'];uris=sorted({u for r in selected for v in r['facts']['measurements'] for u in v['value_nodes']});prior=m.load(RUN/'measurement-values-001.json.gz');assert not prior['failures'] and not prior['stopped'];todo=sorted(set(uris)-set(prior['requested']));triples=list(prior['triples']);components=list(prior['components']);failures=[]
 for start in range(0,len(todo),20):
  if c.STOP.is_set():break
  group=todo[start:start+20]
  try:
   vs,comp=c.subjects(group);triples+=vs;components.append(comp)
   print(json.dumps(dict(done=start+len(group),total=len(todo),triples=len(triples))),flush=True)
  except Exception as error:failures.append(dict(subjects=group,error=repr(error)))
 m.save(dest,dict(at=m.now(),numbers=[r['number'] for r in selected],requested=uris,previous_reference=f.ref(RUN/'measurement-values-001.json.gz'),newly_requested=todo,triples=triples,components=components,failures=failures,stopped=c.STOP.is_set(),source_reference=f.ref(source),script_reference=f.ref(Path(__file__).resolve()),database_writes=0,images=0))
if __name__=='__main__':main()
