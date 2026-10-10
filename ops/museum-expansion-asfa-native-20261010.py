"""Inspect exact native exhibit pages already linked by selected source records."""
import concurrent.futures,importlib.util,json,gzip
from pathlib import Path
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-asfa-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN,q=src.c,src.m,src.RUN,src.q

def main():
    assert not (RUN/'native-source-records-001.json.gz').exists()
    selected=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    def capture(row):
        url=row['native_url'];native_id=url.rstrip('/').split('/')[-1];key='native-landscape-110162-001' if native_id=='110162' else 'native-exhibit-'+native_id+'-001'
        doc,rc=q.q.capture(key,url);doc=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()).decode('utf-8'),'html.parser');title=doc.select_one('h1');blocks=[q.clean(x.get_text(' ',strip=True)) for x in doc.select('.row.description > div > span')]
        assert title is not None and blocks,(row['number'],url)
        images=sorted({x['href'] for x in doc.select('.img-wrap a[href]') if '/wp-content/uploads/' in x['href']});assert len(images)==1
        return dict(number=row['number'],source_id=row['source_id'],url=url,native_id=native_id,title=q.clean(title.get_text(' ',strip=True)),description_blocks=blocks,image_url=images[0],receipt=rc)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(capture,selected):
            rows.append(row)
            if len(rows)%40==0:print(json.dumps(dict(native_captured=len(rows),selected=len(selected))),flush=True)
    m.save(RUN/'native-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=c.ref(RUN/'selected-source-records-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),policy='Native title, labelled order of descriptive spans, physical inventory identifier and exact linked image URL retained. No images downloaded; final metadata/version decisions pending.'))
    print(json.dumps(dict(native_captured=len(rows))),flush=True)

if __name__=='__main__':main()
