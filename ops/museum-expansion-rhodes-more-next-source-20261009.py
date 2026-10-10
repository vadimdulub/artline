"""Discover only60 next native index leads; defer individual records to next selection."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-rhodes-more-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
pages=[]
for page in range(14,17):
 d,rc=s.capture('children-page'+str(page)+'-discovery-001','/public/containers/'+s.PARENT+'/children?page='+str(page)+'&size=20');rows=[dict(number=page*20+j,uuid=v['uuid'],title=v['label'],parent=v['parent'])for j,v in enumerate(d['content'])];assert len(rows)==20 and all(v['parent']==s.PARENT for v in rows);pages.append(dict(page=page,receipt=rc,rows=rows,total=d['totalElements']));print(json.dumps(dict(page=page,titles=[v['title']for v in rows]),ensure_ascii=False),flush=True)
m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),pages=pages,script_reference=s.s.ref(Path(__file__).resolve()),policy='60 index leads only,numbers280–339. Individual detail dates,eligibility and version identity not yet reviewed. No artwork additions or image downloads from these leads.'))
