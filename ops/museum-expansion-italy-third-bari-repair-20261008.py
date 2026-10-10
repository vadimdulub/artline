"""Resolve truncated Bari graphs without traversing a shared address backlink."""
import importlib.util,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-italy-third-capture-v2-20261008.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;d=c.d;RUN=c.RUN;INITIAL=c.ROOT;c.ROOT=RUN/'bari-repair-001'
def graph_batch(rows):
 uris=['https://w3id.org/arco/resource/'+v['index_record']['source_record_id'] for v in rows]
 roots,component=c.subjects(uris);triples=list(roots);components=[component]
 # A shared address has over10,000 inverse object links. Address nodes are
 # unnecessary here: exact object dc:coverage, current-location institute URI
 # and literal HTML address independently establish the required city scope.
 children=sorted({v['o'] for v in roots if v['p'] in c.LINKS and v['o'].startswith('https://w3id.org/arco/resource/') and '/resource/Address/' not in v['o']}-set(uris))
 for start in range(0,len(children),20):
  extra,comp=c.subjects(children[start:start+20]);triples+=extra;components.append(comp)
 measurements=sorted({v['o'] for v in triples if v['p']==c.a.DD+'hasMeasurement' and v['o'].startswith('https://w3id.org/arco/resource/')}-set(children)-set(uris))
 for start in range(0,len(measurements),20):
  extra,comp=c.subjects(measurements[start:start+20]);triples+=extra;components.append(comp)
 return triples,components
def main():
 manifest=RUN/'bari-repair-001.json';assert not manifest.exists();c.ROOT.mkdir(exist_ok=True);(c.ROOT/'batches').mkdir(exist_ok=True)
 discovery=m.load(RUN/'five-museum-discovery-001.json.gz');by={r['number']:r for r in discovery['rows']};done=[];old=[]
 for path in sorted((INITIAL/'batches').glob('*.json.gz')):
  b=m.load(path)
  if b['source_state']=='captured':continue
  assert b['institution_id']=='02ffcb8e-a207-5086-9ca2-960978e3f324' and b['error']=='AssertionError()'
  if c.STOP.is_set():break
  group=[by[n] for n in b['numbers']];dest=c.ROOT/'batches'/path.name;assert not dest.exists()
  try:
   triples,components=graph_batch(group)
   with ThreadPoolExecutor(max_workers=2) as pool:pages=list(pool.map(c.page,group))
   result=dict(at=m.now(),numbers=b['numbers'],institution_id=b['institution_id'],triples=triples,graph_components=components,pages=pages,source_state='captured',database_writes=0,images=0,previous_incomplete_reference=d.ref(path))
  except Exception as error:result=dict(at=m.now(),numbers=b['numbers'],institution_id=b['institution_id'],source_state='graph_source_failure',error=repr(error),database_writes=0,images=0,previous_incomplete_reference=d.ref(path))
  m.save(dest,result);done.append(d.ref(dest));old.append(d.ref(path));print(json.dumps(dict(numbers=b['numbers'],state=result['source_state'],failed_pages=sum('error' in p for p in result.get('pages',[])))),flush=True)
 m.save(manifest,dict(at=m.now(),batches=done,previous_incomplete=old,script_reference=d.ref(Path(__file__).resolve()),stopped=c.STOP.is_set(),policy='Earlier HTTP200 responses reached the10,000-row bound on a shared address inverse relation; they are preserved and rejected as incomplete. New queries omit unused Address-node traversal. No access denial or transient request is retried. Object root, exact current institute/city, attribution, dates and measurement facts still require full validation.'))
if __name__=='__main__':main()
