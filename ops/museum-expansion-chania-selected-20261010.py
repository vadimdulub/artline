"""Capture bounded object descriptions and observed native pages before image selection."""
import gzip
import importlib.util
import json
import time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-chania-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,q=c.m,c.RUN,c.q

def native_fields(soup):
    out={}
    for tr in soup.select('table.jet-table tr'):
        cells=tr.select('td');values=[q.clean(x.get_text(' ',strip=True))for x in cells]
        if len(values)==2 and values[0]:
            assert values[0]not in out
            out[values[0]]=values[1]or None
    return out

def main():
    discovery=m.load(RUN/'source-discovery-001.json.gz');cards=[v for p in m.load(RUN/'bounded-index-001.json.gz')['pages']for v in p['cards']]
    existing={v['source_id']:v for v in discovery['historical_records']}
    selected=list(cards);known={v['source_id']for v in cards}
    for s in existing.values():
        if s['source_id']not in known:selected.append(dict(source_id=s['source_id'],url=s['source_url'],title=s['title'],historical_source_match=True,index_type=None,index_date=None))
    assert len(selected)==212 and sum(s['historical_source_match']for s in selected)==18
    m.save(RUN/'object-selection-001.json',dict(at=m.now(),selected=selected,new_description_leads=194,existing_comparators=18,
        index_reference=q.s.ref(RUN/'bounded-index-001.json.gz'),policy='194 new object-description leads plus18 existing comparators. Metadata only before final art-scope, date and physical-identity decisions; no images downloaded. Plain tools, administrative tablets, unclear fragment sets and other scope/identity cases can be held.'))
    rows=[]
    for number,card in enumerate(selected,1):
        sid=card['source_id'].rsplit('-',1)[1]
        if sid=='1037':
            rc=m.load(RUN/'captures/historical-sample-1037-001.json');doc=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()),'html.parser')
        else:doc,rc=q.q.capture('selected-'+sid+'-001',card['url'])
        f,enrichment=q.fields(doc);assert f.get('Τίτλος')and f.get('Πάροχος')
        native_urls={urljoin(card['url'],a['href']).rstrip('/')for a in doc.select('a[href]')if a['href'].startswith('https://amch.gr/collection/')and a['href'].rstrip('/')!='https://amch.gr/collection'}
        assert len(native_urls)==1,(sid,native_urls)
        native_url=native_urls.pop()
        if sid=='1037':
            nrc=m.load(RUN/'captures/native-historical-1037-001.json');native=BeautifulSoup(gzip.decompress((m.ROOT/nrc['body_path']).read_bytes()),'html.parser')
        else:native,nrc=q.q.capture('native-selected-'+sid+'-001',native_url)
        nf=native_fields(native);assert nf.get('Κωδικός'),(sid,nf)
        dynamic=[q.clean(e.get_text(' ',strip=True))for e in native.select('.jet-listing-dynamic-field__content')]
        images=[dict(e.attrs)for e in native.select('a.jet-listing-dynamic-image__link[data-elementor-open-lightbox] img')]
        if not images:images=[dict(e.attrs)for e in native.select('img.jet-listing-dynamic-image__img')if e.get('alt')in f['Τίτλος']]
        thumb=doc.find('img',src=lambda u:u and '/thumbnails/edm-record/'+card['source_id']in u);assert thumb is not None
        rows.append(dict(number=number,source_id=card['source_id'],source_url=card['url'],role='existing_comparator'if card['historical_source_match']else'new_description_lead',index=card,
            fields=f,enrichment=enrichment,receipt=rc,native_url=native_url,native_receipt=nrc,native_fields=nf,native_dynamic_text=dynamic,
            native_page_title=q.clean(native.title.get_text())if native.title else None,native_images=images,
            thumbnail_url=urljoin(card['url'],thumb['src']),
            rights_links=sorted({a['href']for a in doc.select('a[href]')if 'creativecommons.org/licenses/'in a['href']})))
        if number%20==0:print(json.dumps(dict(objects=number,total=212,native_accessions=len(rows))),flush=True)
        time.sleep(.08)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=q.s.ref(RUN/'object-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Museum-supplied and EKT-enriched values preserved separately; native code and chronology are independent evidence. An index period, photograph date, excavation year or empty native field is not an invented creation date. No images or DB access.'))
    print(json.dumps(dict(total=len(rows),native_dates=sum(bool(r['native_fields'].get('Χρονολόγηση'))for r in rows))),flush=True)

if __name__=='__main__':main()
