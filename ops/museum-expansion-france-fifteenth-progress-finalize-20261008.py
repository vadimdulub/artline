"""Finalize the progress writer log after completion; preserve the original checkpoint."""
import copy,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
def main():
 m=f.m;prior=f.RUN/'review-progress-checkpoint-001.json';dest=f.RUN/'review-progress-checkpoint-002.json';receipt=f.RUN/'progress-log-finalization-001.json'
 assert not dest.exists() and not receipt.exists();x=m.load(prior)
 assert f.ref(prior)['sha256']=='11bbf1acb987d6c1ff244058e51049a303888f5a6293623ef825636c1ae1087a'
 for dep in x['references']:f.checked(dep)
 log=Path('/Users/vadimdulub/Library/Logs/artline-france-fifteenth-review-progress-001-20261008.log');old=next(v for v in x['external_references'] if v['path']==str(log))
 assert old['sha256']==hashlib.sha256(b'').hexdigest()
 lines=log.read_text().splitlines();assert len(lines)==1
 result=json.loads(lines[0]);assert result['checkpoint']==f.ref(prior) and result['database_writes']==0 and result['reviewed']==360
 for dep in x['external_references']:
  if dep['path']!=str(log):assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 final=dict(path=str(log),sha256=hashlib.sha256(log.read_bytes()).hexdigest())
 m.save(receipt,dict(at=m.now(),prior_checkpoint=f.ref(prior),before=old,after=final,reason='The checkpoint writer hashed its own still-empty output log before printing its terminal receipt. Finalize only that log pin after process completion. All research artifacts and every other log pin remain identical. Original checkpoint retained; this is not evidence loss or a catalogue change.',finalizer_reference=f.ref(Path(__file__).resolve())))
 out=copy.deepcopy(x);out['at']=m.now();out['supersedes_checkpoint']=f.ref(prior);out['log_finalization_reference']=f.ref(receipt)
 out['external_references']=[final if v==old else v for v in out['external_references']]
 out['references']+= [f.ref(prior),f.ref(receipt),f.ref(Path(__file__).resolve())]
 m.save(dest,out);print(json.dumps(dict(checkpoint=f.ref(dest),research_unchanged=True,reviewed=360,provisional_supported=316,held=44,database_writes=0)),flush=True)
if __name__=='__main__':main()
