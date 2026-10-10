"""Bounded next60 official Rhodes records; reuse captured index and no images."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-rhodes-final-common-20261009.py');prior=module('prior','museum-expansion-rhodes-source-20261009.py');m=s.m;RUN=s.RUN;OLD=m.RUN/'native/rhodes-more-20261009';prior.RUN=RUN;capture=prior.capture;fields=prior.fields;PARENT=prior.PARENT

def main():
 saved=m.load(OLD/'next-source-discovery-001.json.gz');rows=[];pages=[]
 for page in range(14,17):
  if page<17:
   old=next(v for v in saved['pages']if v['page']==page);index=old['rows'];rc=old['receipt'];total=old['total']
  else:
   data,rc=capture('children-page'+str(page)+'-001','/public/containers/'+PARENT+'/children?page='+str(page)+'&size=20');index=[dict(number=page*20+j,uuid=v['uuid'],title=v['label'],parent=v['parent'])for j,v in enumerate(data['content'])];total=data['totalElements']
  assert len(index)==20 and all(v['parent']==PARENT for v in index);pages.append(dict(page=page,receipt=rc,rows=index,total=total))
  for v in index:
   obj,receipt=capture('object-'+v['uuid']+'-001','/v2/public/containers/'+v['uuid']);rows.append(dict(n=v['number'],uuid=v['uuid'],fields=fields(obj),receipt=receipt,source_url='https://portal.mgamuseum.gr/collections/'+v['uuid']))
  print(json.dumps(dict(page=page,metadata_records=len(rows),source_total=total)),flush=True)
 assert len(rows)==60 and len({v['uuid']for v in rows})==60
 m.save(RUN/'native-selection-001.json.gz',dict(at=m.now(),rows=rows,pages=pages,prior_discovery_reference=s.ref(OLD/'next-source-discovery-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='At most60 further individual public metadata records,280–339, for source-backed selection toward200. Previous280 decisions preserved; no exhaustive metadata or image download. Administrative identity and repository timestamps excluded from artwork dates.'))
if __name__=='__main__':main()
