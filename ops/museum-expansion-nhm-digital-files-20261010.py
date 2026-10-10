"""Discover source-advertised original files for176 already selected dated works."""
import concurrent.futures,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    dest=RUN/'selected-digital-files-001.json.gz';assert not dest.exists()
    review=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];selected=[x for x in review if x['decision']=='proposed_review_artwork' and x['last'] is not None and x['last']<=1955];assert len(selected)==176
    records={x['number']:x for x in m.load(RUN/'selected-source-records-001.json.gz')['rows']}
    selection=RUN/'selected-digital-files-scope-001.json'
    if not selection.exists():m.save(selection,dict(at=m.now(),numbers=[x['number'] for x in selected],source_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),policy='Only176 individually reviewed source-dated pre1956works. Two distinct bridge inventories supported by native pages, with final image comparison pending. Wrapper discovery only; no catalogue writes or unselected image downloading.'))
    def one(row):
        n=row['number'];record=records[n];assert len(record['file_links'])==1;url=record['file_links'][0]
        if n==7:
            rc=m.load(RUN/'digital-file-discovery-001.json')['result'];raw=Path(rc['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256'];doc=BeautifulSoup(raw,'html.parser')
        else:doc,rc=src.capture('file-page-'+str(n).zfill(3)+'-001',url)
        nodes=doc.select('img.files-thumbnail');assert len(nodes)==1
        node=nodes[0];anchor=node.find_parent('a');assert anchor and anchor.get('href')
        original=urljoin(url,anchor['href']);preview=urljoin(url,node['src']);assert original.startswith('https://www.searchculture.gr/aggregator/digital-files-from-preservator/file/')
        fields={src.clean(dt.get_text(' ',strip=True)):src.clean(dt.find_next_sibling('dd').get_text(' ',strip=True)) for dt in doc.select('dl dt') if dt.find_next_sibling('dd')}
        assert fields['Τύπος αρχείου']=='TIFF'
        return dict(number=n,source_id=row['source_id'],source_url=row['source_url'],wrapper_url=url,original_url=original,preview_url=preview,fields=fields,receipt=rc)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(one,selected):
            rows.append(row)
            if len(rows)%25==0:print(json.dumps(dict(file_pages=len(rows),selected=len(selected))),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),policy='Only source-observed TIFF download links. File-wrapper CC BY4.0 conflicts with item CC BY-NC-ND4.0; retain both and conservative restricted classification. Source originals not downloaded by this script.'))
    print(json.dumps(dict(files=len(rows),advertised_sizes=[x['fields']['Μέγεθος αρχείου'] for x in rows])),flush=True)

if __name__=='__main__':main()
