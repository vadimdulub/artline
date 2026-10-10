"""At most120 museum object metadata records; no exhaustive catalogue/image fetch."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-rhodes-source-20261009.py'));src=importlib.util.module_from_spec(z);z.loader.exec_module(src)
m=src.m;RUN=src.RUN
rows=[];pages=[]
for page in range(1,6):
 d,rc=src.capture('children-page'+str(page)+'-001','/public/containers/'+src.PARENT+'/children?page='+str(page)+'&size=20');assert d['number']==page;pages.append(dict(page=page,receipt=rc,total=d['totalElements'],rows=[{k:v[k]for k in ['uuid','label','parent']}for v in d['content']]))
 for j,v in enumerate(d['content']):
  assert v['parent']==src.PARENT
  obj,receipt=src.capture('object-'+v['uuid']+'-001','/v2/public/containers/'+v['uuid']);f=src.fields(obj);row=dict(n=page*20+j,uuid=v['uuid'],fields=f,receipt=receipt,source_url='https://portal.mgamuseum.gr/collections/'+v['uuid']);rows.append(row)
 print(json.dumps(dict(page=page,details=len(rows),total=d['totalElements'])),flush=True)
m.save(RUN/'native-selection-001.json.gz',dict(at=m.now(),pages=pages,rows=rows,sample_reference=src.s.ref(RUN/'native-sample-001.json.gz'),policy='120 of1502 metadata objects across initial6pages for individual date/object review; stop at this boundary. No image fetch. Not full artwork coverage.'))
