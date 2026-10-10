"""Forty further metadata records after first60 yielded only24 in-scope date leads."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-final-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
pages=[];rows=[]
for page in range(17,19):
 d,rc=s.capture('children-page'+str(page)+'-001','/public/containers/'+s.PARENT+'/children?page='+str(page)+'&size=20');index=[dict(number=page*20+j,uuid=v['uuid'],title=v['label'],parent=v['parent'])for j,v in enumerate(d['content'])];assert len(index)==20 and all(v['parent']==s.PARENT for v in index);pages.append(dict(page=page,receipt=rc,rows=index,total=d['totalElements']))
 for v in index:
  obj,receipt=s.capture('object-'+v['uuid']+'-001','/v2/public/containers/'+v['uuid']);rows.append(dict(n=v['number'],uuid=v['uuid'],fields=s.fields(obj),receipt=receipt,source_url='https://portal.mgamuseum.gr/collections/'+v['uuid']))
 print(json.dumps(dict(page=page,metadata_records=len(rows))),flush=True)
assert len(rows)==40 and len({v['uuid']for v in rows})==40
m.save(RUN/'native-selection-002.json.gz',dict(at=m.now(),rows=rows,pages=pages,script_reference=s.s.ref(Path(__file__).resolve()),policy='Forty additional public objects340–379; total bounded selection100 this wave. No images. Date and identity review precede any addition.'))
