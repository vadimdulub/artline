"""Bounded object metadata from the public collection interface used by MSU."""
import importlib.util,json,re,sys
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('b','ops/balkans-deep-20261011.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
    index=m.h.load(m.RUN/'msu-collection-index.json')['records']
    chosen={'1771','2391','2085','1801','2117','1810','2556','1991','2228','2211','2739','1979','1851'}
    # Older source file labels are discovery clues only; object captions decide dates.
    for x in index:
        if any(t in x['creator']for t in ['Пикасо','Леже','Мартинов','Мартинo','Кондов','Лазески','Протуѓ','Корубин']):chosen.add(x['id'])
    result=[]
    for x in index:
        if x['id']not in chosen:continue
        u='https://msu.mk/wp-json/api/v1/collection?id='+x['id'];raw,rc=m.h.capture(u);assert rc['status']==200;data=json.loads(raw)
        m.h.save(m.RUN/'msu-artists'/(x['id']+'.json'),dict(index=x,receipt=rc,response=data))
        # At most eight source-selected images per selected artist, metadata only.
        for image in data.get('gallery',[])[:8]:
            u='https://msu.mk/wp-json/api/v1/getMediaDescription?id='+image['id']+'&lang=mk'
            raw,receipt=m.h.capture(u);assert receipt['status']==200;obj=json.loads(raw)
            desc=BeautifulSoup(obj.get('description',''),'html.parser').get_text('\n',strip=True)
            result.append(dict(creator=data['title'],artist_id=x['id'],media=image,source_url=u,receipt=receipt,description=desc,raw=obj,artist_receipt=rc,artist_description=data['description']))
        print('MSU',x['id'],data['title'],len(data.get('gallery',[])),flush=True)
    m.h.save(m.RUN/'msu-selected-object-metadata.json',result)
    print('OBJECT METADATA',len(result),flush=True)

if __name__=='__main__':main()
