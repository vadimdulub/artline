"""Bounded metadata-only investigation of Cyprus museum digitisation records."""
import importlib.util,json,concurrent.futures
from pathlib import Path
s=importlib.util.spec_from_file_location('cyprus','ops/cyprus-deep-20261010.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
FUNDS={'kykkos':'1394ec01-fd47-4ef2-859e-f55c429ff5b4','tamasos':'0affef79-2a92-464d-a195-091092c4367c','leventis-municipal':'f5fc55e7-45c3-4f3d-bb6c-339ad0ae43de'}
def catalogue(name,fid):
    p=m.page('https://historica.unibo.it/entities/fonds/'+fid)
    cache=json.loads(p['scripts'][-1]['text'])['NGRX_STATE']['core']['cache/object']
    entries=[v['data']for k,v in cache.items() if '/vocabularyEntryDetails/fonds:'in k and '/children'not in k and '/parent'not in k]
    rows=[r for r in entries if r.get('otherInformation',{}).get('hasChildren')=='false'and not r['display'].startswith(('OUC','AUTH','UNIBO','IAS-'))]
    assert len(rows)<=180
    m.h.save(m.RUN/'historica'/f'{name}-index.json',dict(fonds=fid,receipt=p['receipt'],entries=rows))
    result=[]
    for r in rows:
        url='https://historica.unibo.it/server/api/core/items/'+r['authority'];dest=m.RUN/'historica/objects'/(r['authority']+'.json')
        if dest.exists():v=m.h.load(dest)
        else:
            raw,rc=m.h.capture(url);v=dict(fonds=name,record=json.loads(raw),receipt=rc);m.h.save(dest,v)
        result.append(v)
        if len(result)%20==0:print(name,len(result),'/',len(rows),flush=True)
    print(name,'metadata objects',len(result),flush=True)
for name,fid in FUNDS.items():catalogue(name,fid)
