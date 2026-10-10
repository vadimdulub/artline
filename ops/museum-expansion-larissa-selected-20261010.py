"""Capture selected object metadata and native links before any image requests."""
import concurrent.futures
import importlib.util
import json
import threading
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,q=c.m,c.RUN,c.q
STOP=threading.Event()

def native_fields(soup):
    dl=soup.find('dl',title=lambda t:t and t.startswith('Στοιχεία έργου'))
    assert dl is not None
    fields={}
    for dt in dl.select('dt'):
        dd=dt.find_next_sibling('dd');assert dd is not None
        label=q.clean(dt.get_text(' ',strip=True));assert label not in fields
        fields[label]=q.clean(dd.get_text(' ',strip=True))or None
    box=next((h.parent for h in soup.select('h2')if q.clean(h.get_text())=='Περιγραφή'),None)
    desc=None
    if box is not None:
        desc=q.clean(box.get_text(' ',strip=True));assert desc.startswith('Περιγραφή');desc=desc[len('Περιγραφή'):].strip()or None
    return fields,desc

def fetch(item):
    number,card=item
    if STOP.is_set():raise RuntimeError('Selected source capture stopped')
    try:
        soup,rc=q.q.capture('selected-'+str(number).zfill(3)+'-001',card['url']);f,enrichment=q.fields(soup)
        assert f.get('Πάροχος')and f.get('Τίτλος'),number
        native_urls={urljoin(card['url'],a['href'])for a in soup.select('a[href]')if 'larissa-katsigras-gallery.gr/gallery/el/work/'in a['href']}
        assert len(native_urls)==1,(number,native_urls);native_url=native_urls.pop()
        if STOP.is_set():raise RuntimeError('Selected source capture stopped')
        native,nrc=q.q.capture('native-selected-'+str(number).zfill(3)+'-001',native_url)
        nf,desc=native_fields(native);assert nf.get('Τίτλος έργου'),number
        imgs=[dict(image.attrs,absolute_url=urljoin(nrc['final_url'],image['src']))for image in native.select('img[src]')if '/uploads/gallery/'in image['src']]
        assert len(imgs)==1,(number,imgs)
        artist_urls=sorted({urljoin(nrc['final_url'],a['href'])for a in native.select('a[href]')if '/gallery/el/artist/'in a['href']})
        thumb=soup.find('img',src=lambda x:x and '/thumbnails/edm-record/'+card['source_id']in x);assert thumb is not None
        return dict(number=number,source_id=card['source_id'],source_url=card['url'],index=card,role='existing_comparator'if card['historical_source_match']else'new_description_lead',
            receipt=rc,fields=f,enrichment=enrichment,native_url=native_url,native_receipt=nrc,native_fields=nf,native_description=desc,
            native_page_title=q.clean(native.title.get_text())if native.title else None,native_images=imgs,native_artist_urls=artist_urls,
            thumbnail_url=urljoin(card['url'],thumb['src']),rights_links=sorted({a['href']for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']}))
    except Exception:
        STOP.set();raise

def main():
    index=m.load(RUN/'bounded-date-index-001.json.gz');cards=[row for page in index['pages']for row in page['cards']]
    hist=m.load(RUN/'source-discovery-001.json.gz')['historical_records'];known={row['source_id']for row in cards}
    selected=list(cards)
    for row in hist:
        if row['source_id']not in known:selected.append(dict(source_id=row['source_id'],url=row['source_url'],title=row['title'],historical_source_match=True,index_date=None,index_type=None))
    assert len(selected)==216 and sum(not row['historical_source_match']for row in selected)==198
    m.save(RUN/'object-selection-001.json',dict(at=m.now(),selected=selected,new_description_leads=198,existing_comparators=18,
        source_reference=q.s.ref(RUN/'bounded-date-index-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='First210 date-ordered sources through starts1952 plus6 historical comparator sources. A date range ending later than1955 is not image-eligible merely because its first endpoint is earlier. Selected metadata review before images; print/edition/copy identity and native dates remain to verify. The separately captured1961 album print sample is a deferred discovery lead, not added to this selection.'))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
        futures=[pool.submit(fetch,item)for item in enumerate(selected,1)]
        try:
            for future in concurrent.futures.as_completed(futures):
                rows.append(future.result())
                if len(rows)%30==0:print(json.dumps(dict(captured=len(rows),total=216)),flush=True)
        except Exception:
            STOP.set()
            for f in futures:f.cancel()
            raise
    rows.sort(key=lambda r:r['number'])
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=q.s.ref(RUN/'object-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Public object pages only. Login/registration controls on the repository were not used. Literal source creators and enrichment separate; no inventory inferred from filenames, no painter IDs, no DB writes or image requests.'))
    print(json.dumps(dict(rows=len(rows),artists=len({u for row in rows for u in row['native_artist_urls']}),missing_native_dates=sum(not row['native_fields'].get('Χρονολογία έργου')for row in rows))),flush=True)

if __name__=='__main__':main()
