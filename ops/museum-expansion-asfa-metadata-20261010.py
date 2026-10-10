"""Capture selected dated artworks and existing comparators; no image delivery."""
import concurrent.futures,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-asfa-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN,q=src.c,src.m,src.RUN,src.q

def main():
    assert not (RUN/'selected-source-records-001.json.gz').exists()
    index=m.load(RUN/'bounded-index-001.json.gz');old=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];oldids={x['external_id']:x for x in old['identifiers'] if x['scheme']=='searchculture-edm'};selected=[dict(x,number=i+1,historical_source_match=x['source_id'] in oldids) for i,x in enumerate(index['selected'])]
    sids={x['source_id'] for x in selected}
    for sid,v in sorted(oldids.items()):
        if sid not in sids:selected.append(dict(source_id=sid,url=v['canonical_url'],number=len(selected)+1,historical_source_match=True,selection_reason='additional_existing_comparator'))
    assert len(selected)==258
    p=RUN/'metadata-selection-001.json'
    if not p.exists():m.save(p,dict(at=m.now(),selected=selected,index_reference=c.ref(RUN/'bounded-index-001.json.gz'),policy='250new dated-artwork leads and8existing comparators; no documents, image capture or database writes.'))
    else:assert m.load(p)['selected']==selected
    def capture(card):
        sid=card['source_id'];doc,rc=q.q.capture('object-'+sid.split('000187-')[1]+'-001',card['url']);literal,enrichment=q.fields(doc)
        assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Ανώτατη Σχολή Καλών Τεχνών']
        native=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if a['href'].startswith('https://exhibition.asktdigital.gr/exhibits/')});assert len(native)==1
        im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        rights=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href']})
        authorities=[dict(label=q.clean(a.get_text(' ',strip=True)),url=urljoin(card['url'],a['href'])) for a in doc.select('.panel-enrichment a[href]') if '/persons/' in a['href'] or 'semantics.gr/authorities/persons/' in a['href']]
        return dict(number=card['number'],source_id=sid,source_url=card['url'],native_url=native[0],index=card,fields=literal,enrichment=enrichment,creator_authorities=authorities,thumbnail_url=urljoin(card['url'],im['src']) if im else None,rights_links=rights,receipt=rc,decision='unreviewed_metadata')
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(capture,selected):
            rows.append(row)
            if len(rows)%25==0:print(json.dumps(dict(captured=len(rows),selected=len(selected))),flush=True)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=c.ref(p),script_reference=c.ref(Path(__file__).resolve()),policy='Individual institution-supplied metadata, literal/enriched fields separated. Pending physical-unit, date and visual review. No images or production writes.'))
    print(json.dumps(dict(captured=len(rows))),flush=True)

if __name__=='__main__':main()
