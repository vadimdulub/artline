"""Select dated objects before downloading museum metadata; preserve unselected leads."""
import importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
n=module('n','museum-expansion-leeds-drawings-native-20261009.py');old=module('old','museum-expansion-leeds-additions-objects-20261009.py');m=n.m;RUN=n.RUN;ref=n.ref;parsed=old.parsed;date=old.date;PRIOR=m.RUN/'native/leeds-additions-20261009'
def selection():
 seen={v['source_id'] for v in m.load(PRIOR/'editorial-reviewed-002.json.gz')['decisions']};selected=[];remaining=[];drawings=0
 for name in ['watercolour-index-001','drawing-index-001']:
  src=RUN/(name+'.json.gz')
  for r in m.load(src)['data']['hits']:
   oid=r['objectID'].split('/')[-1];assert r['type']=='Works of Art' and r['reference'].startswith('LEEAG.') and r['url']=='https://cotmania.org/works-of-art/'+oid
   if oid in seen:remaining.append(dict(source_id=oid,state='previously_reviewed',index=r,index_reference=ref(src)));continue
   d=date(r.get('date'))
   if d is None:remaining.append(dict(source_id=oid,state='date_text_needs_review',index=r,index_reference=ref(src)));continue
   if r['objectname']=='Drawing' and drawings>=100:remaining.append(dict(source_id=oid,state='outside_bounded_selection',index=r,index_reference=ref(src)));continue
   selected.append(dict(source_id=oid,index=r,date=d,index_reference=ref(src)));drawings+=int(r['objectname']=='Drawing');seen.add(oid)
 assert drawings==100 and len(selected)==104;return selected,remaining
def main():
 dest=RUN/'selected-objects-001.json.gz';assert not dest.exists();selected,remaining=selection();m.save(RUN/'object-selection-001.json.gz',dict(at=m.now(),rows=selected,remaining_leads=remaining,prior_review_reference=ref(PRIOR/'editorial-reviewed-002.json.gz'),policy='Four remaining Watercolour leads and first100new source-dated Drawing leads from120-hit page,selected before object fetch. Known prior50objects excluded,including missing work. Nonstandard date text remains queued. No quota waives object/creator/holding review.'))
 out=[];failures=0
 for number,r in enumerate(selected,1):
  try:
   raw,cap=n.n.capture('cotmania',r['index']['url']);p=parsed(raw);row=dict(number=number,**r,capture=cap,parsed=p);failures=0
  except Exception as e:row=dict(number=number,**r,error=type(e).__name__+': '+str(e));failures+=1
  m.save(RUN/'selected-objects-001'/('%03d.json'%number),row);out.append(row);print(json.dumps(dict(number=number,source_id=r['source_id'],title=row.get('parsed',{}).get('fields',{}).get('Title'),error=row.get('error'))),flush=True)
  if failures>=3 or any(t in row.get('error','') for t in ['403','429']):break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(RUN/'object-selection-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Selected native object metadata only,no image/archive downloads. Exact number of physical works and mounted group relationships still reviewed.'))
if __name__=='__main__':main()
