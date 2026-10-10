"""Capture independent official collection context and one observed digital-file wrapper."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-war-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    assert not (RUN/'focused-context-001.json.gz').exists()
    rows=m.load(RUN/'selected-source-records-001.json.gz')['rows'];out=[]
    targets=[('official-athens-001','https://warmuseum.gr/τα-μουσεία/πολεμικό-μουσείο-αθήνας/'),('selected-file-2773-001',rows[11]['file_links'][0])]
    for key,url in targets:
        try:
            doc,rc=src.capture(key,url);links=[dict(label=src.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href'])) for a in doc.select('a[href]')]
            images=[dict(src=urljoin(rc['final_url'],x.get('src','')),alt=x.get('alt')) for x in doc.select('img[src]')]
            row=dict(key=key,receipt=rc,text=src.clean(doc.get_text(' ',strip=True)),links=links,images=images)
        except Exception as e:
            rp=RUN/'captures'/(key+'.json');row=dict(key=key,url=url,error=type(e).__name__,receipt=m.load(rp) if rp.exists() else None,policy='No retry or alternate route for this failed endpoint.')
        out.append(row);print(json.dumps(dict(key=key,status=row.get('receipt',{}).get('status') if row.get('receipt') else None,error=row.get('error'),text=row.get('text','')[:1000],images=row.get('images',[]) if key.startswith('selected') else []),ensure_ascii=False),flush=True)
    rights=[]
    for row in rows:
        raw=gzip.decompress((m.ROOT/row['receipt']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==row['receipt']['sha256']
        doc=src.BeautifulSoup(raw.decode('utf-8'),'html.parser');matches=[]
        for a in doc.select('a[href]'):
            if 'creativecommons.org' in a['href']:matches.append(dict(url=a['href'],text=src.clean(a.get_text(' ',strip=True)),parent_text=src.clean(a.parent.get_text(' ',strip=True)),parent_class=a.parent.get('class'),html=str(a.parent)))
        rights.append(dict(number=row['number'],matches=matches,source_receipt=row['receipt']))
    m.save(RUN/'focused-context-001.json.gz',dict(at=m.now(),rows=out,item_rights=rights,script_reference=c.ref(Path(__file__).resolve()),policy='Official Athens collection narrative supports museum context, not individual execution dates or fresh per-object display claims. One source-observed file-wrapper probe only, no highresolution image download. Cached195item rights contexts inspected separately from websitefooter.'))

if __name__=='__main__':main()
