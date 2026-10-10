"""Selected Guildhall publisher metadata, excluding documentation and detail cards."""
import hashlib,importlib.util,json,time
from pathlib import Path
z=importlib.util.spec_from_file_location('g',Path(__file__).with_name('museum-expansion-britain-seven-gac-selected-20261009.py'));g=importlib.util.module_from_spec(z);z.loader.exec_module(g);m=g.m;OLD=g.RUN;RUN=m.RUN/'native/guildhall-additions-20261009';g.p.n.RUN=RUN
ref=lambda p:dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 dest=RUN/'native-captured-001.json.gz';assert not dest.exists();index=OLD/'guildhall-gac-indexes-001.json.gz';caveat=m.load(OLD/'next-native-object-caveats-001.json');assert ref(index)==caveat['index_reference'];excluded=set(caveat['exclude_documentation_cards']+caveat['exclude_detail_crops']);already={}
 for v in m.load(OLD/'guildhall-gac-selected-001.json.gz')['rows']:
  p=m.ROOT/v['reference']['path'];assert ref(p)==v['reference'];row=m.load(p);already[row['card']['source_id']]=v['reference']
 rows=m.load(index)['rows'];selected=[v for v in rows if v['source_id'] not in excluded|set(already)];assert len(rows)==46 and len(selected)==36
 m.save(RUN/'native-selection-001.json',dict(at=m.now(),rows=selected,excluded_documentation_or_details=sorted(excluded),already_captured=already,index_reference=ref(index),caveat_reference=ref(OLD/'next-native-object-caveats-001.json'),policy='36 selected physical-work leads,not approvals. Creation dates,museum holdings versus loans,and versions require detail review. No image download. Denied sources remain untouched.'))
 out=[];failures=0;stopped=False
 for number,card in enumerate(selected,1):
  path=RUN/'native-selected-001'/('%03d.json'%number);assert not path.exists();row=dict(number=number,card=card)
  try:
   raw,cap=g.p.n.capture('guildhall_gac',card['url']);row.update(state='captured_metadata',capture=cap,parsed=g.parsed(raw));failures=0
  except Exception as e:failures+=1;row.update(state='source_error',error=type(e).__name__+': '+str(e));stopped=failures>=3 or any(t in str(e) for t in ['403','429'])
  m.save(path,row);out.append(dict(number=number,state=row['state'],reference=ref(path)));print(json.dumps(dict(number=number,state=row['state'])),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(RUN/'native-selection-001.json'),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,unprocessed_numbers=list(range(len(out)+1,len(selected)+1)),policy='Selected metadata only. Partner branding is not collection evidence. Existing paintings,loans,studies,copies and duplicate presentations must be distinguished.'))
if __name__=='__main__':main()
