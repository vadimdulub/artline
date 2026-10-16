"""Archive selected reference publications, then extract a page-text index."""
import concurrent.futures,importlib.util,json,sys
from pathlib import Path
import requests,pymupdf
spec=importlib.util.spec_from_file_location('b','ops/balkans-deep-20261011.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SOURCES={
 'piraeus':'https://www.latsis-foundation.org/content/elib/book_9/piraeus_en.pdf',
 'aigai':'https://www.aigai.gr/assets/site/content/pdf/Kottaridi_Academia_edu/PRINCESSES_The_Lady_of_Aigai_413.pdf',
 'mk-profane':'https://arhiva.zaum.mk/wp-content/uploads/2019/09/2013_11_04_Makedonsko_profano_slikarstvo_XIX_pocetok_na_XX_vek.pdf',
 'mk-africa':'https://museum.org.mk/codeframe/external/media/source/каталози/Afrika%20vo%20Makedonija.pdf',
}
def one(key):
    dest=m.ORIGINALS/'publications'/(key+'.pdf');rcp=m.RUN/'publications'/(key+'.json')
    if not dest.exists():
        r=requests.get(SOURCES[key],stream=True,timeout=(15,60));r.raise_for_status();raw=b''
        for chunk in r.iter_content(131072):raw+=chunk;assert len(raw)<65_000_000
        assert raw.startswith(b'%PDF');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        m.h.save(rcp,dict(url=SOURCES[key],final_url=r.url,status=r.status_code,sha256=m.h.sha(raw),bytes=len(raw),retrieved_at=m.h.now(),original_path=str(dest),selection='Selected museum reference catalogue; only individually reviewed eligible objects and illustrations may be delivered.'))
    d=pymupdf.open(dest);pages=[dict(index=i,text=p.get_text(),images=len(p.get_images()))for i,p in enumerate(d)]
    m.h.save(m.RUN/'publications'/(key+'-pages.json'),pages)
    print(key,len(d),'pages',dest.stat().st_size,'bytes',flush=True)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for f in [pool.submit(one,k)for k in sys.argv[1:]or SOURCES]:
            try:f.result()
            except Exception as e:print('FAILED',type(e).__name__,str(e)[:200],flush=True)
