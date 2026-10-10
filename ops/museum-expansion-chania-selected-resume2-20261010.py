"""Continue after a missing optional source title, without discarding the real object."""
import concurrent.futures
import gzip
import importlib.util
import json
import threading
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-chania-selected-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m,RUN,q=s.m,s.RUN,s.q
STOP=threading.Event()

def capture(key,url):
    if STOP.is_set():raise RuntimeError('Source pass stopped after another request failed')
    try:return q.q.capture(key,url)
    except Exception as e:
        STOP.set()
        rp=RUN/'captures'/(key+'-failure-002.json')
        if not rp.exists():m.save(rp,dict(at=m.now(),url=url,error_type=type(e).__name__,message=str(e),policy='No automatic retry; stop remaining new requests. Cached captures retained.'))
        raise

def object_row(pair):
    number,card=pair;sid=card['source_id'].rsplit('-',1)[1]
    key='historical-sample-1037-001'if sid=='1037'else'selected-'+sid+'-001'
    doc,rc=capture(key,card['url']);f,enrichment=q.fields(doc)
    assert f.get('Πάροχος')  # Some legitimate source objects have no title field.
    urls={urljoin(card['url'],a['href']).rstrip('/')for a in doc.select('a[href]')if a['href'].startswith('https://amch.gr/collection/')and a['href'].rstrip('/')!='https://amch.gr/collection'}
    assert len(urls)==1,(sid,urls)
    native_url=urls.pop();key='native-historical-1037-001'if sid=='1037'else'native-selected-'+sid+'-001'
    native,nrc=capture(key,native_url);nf=s.native_fields(native);assert nf.get('Κωδικός'),(sid,nf)
    dynamic=[q.clean(e.get_text(' ',strip=True))for e in native.select('.jet-listing-dynamic-field__content')]
    images=[dict(e.attrs)for e in native.select('a.jet-listing-dynamic-image__link[data-elementor-open-lightbox] img')]
    if not images:images=[dict(e.attrs)for e in native.select('img.jet-listing-dynamic-image__img')if e.get('alt')in f.get('Τίτλος',[])]
    thumb=doc.find('img',src=lambda u:u and '/thumbnails/edm-record/'+card['source_id']in u);assert thumb is not None
    return dict(number=number,source_id=card['source_id'],source_url=card['url'],role='existing_comparator'if card['historical_source_match']else'new_description_lead',index=card,
        fields=f,enrichment=enrichment,receipt=rc,native_url=native_url,native_receipt=nrc,native_fields=nf,native_dynamic_text=dynamic,
        native_page_title=q.clean(native.title.get_text())if native.title else None,native_images=images,
        thumbnail_url=urljoin(card['url'],thumb['src']),rights_links=sorted({a['href']for a in doc.select('a[href]')if 'creativecommons.org/licenses/'in a['href']}))

def main():
    m.save(RUN/'missing-title-continuation-001.json',dict(at=m.now(),terminal_session=48173,exit_code=1,source_id='AMusChania/000039-150',reason='Aggregator omitted title; provider, description and native object link present. Preserve absent title and use verified native title later. No source access failure in this continuation.',previous_script=q.s.ref(Path(__file__).with_name('museum-expansion-chania-selected-resume-20261010.py').resolve())))
    selected=m.load(RUN/'object-selection-001.json')['selected'];assert len(selected)==212
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
        futures=[pool.submit(object_row,(i,card))for i,card in enumerate(selected,1)]
        try:
            for fut in concurrent.futures.as_completed(futures):
                rows.append(fut.result())
                if len(rows)%20==0:print(json.dumps(dict(objects=len(rows),total=212)),flush=True)
        except Exception:
            STOP.set()
            for f in futures:f.cancel()
            raise
    rows.sort(key=lambda r:r['number'])
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=q.s.ref(RUN/'object-selection-001.json'),
        script_reference=q.s.ref(Path(__file__).resolve()),initial_script_reference=q.s.ref(Path(__file__).with_name('museum-expansion-chania-selected-20261010.py').resolve()),
        policy='212 selected paired museum/aggregator pages, cached responses reused after verified terminal transient failure. No images or DB access. Dates and artistic scope still require source review.'))
    print(json.dumps(dict(total=len(rows),native_dates=sum(bool(r['native_fields'].get('Χρονολόγηση'))for r in rows))),flush=True)

if __name__=='__main__':main()
