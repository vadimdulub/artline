"""Capture selected museum-supplied painting metadata and all existing comparators."""
import concurrent.futures, importlib.util, json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-war-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def fields(doc):
    literal,enriched,links={},{},{}
    for group in doc.select('.form-group'):
        label=group.select_one('label.control-label')
        if label is None:continue
        key=src.clean(label.get_text(' ',strip=True));assert key not in literal
        enriched[key]=[src.clean(v.get_text(' ',strip=True)) for v in group.select('.panel-enrichment')]
        links[key]=[dict(label=src.clean(a.get_text(' ',strip=True)),url=urljoin(src.BASE,a['href'])) for a in group.select('.panel-enrichment a[href]')]
        clean_group=BeautifulSoup(str(group),'html.parser')
        for panel in clean_group.select('.panel-enrichment'):panel.decompose()
        literal[key]=[src.clean(v.get_text(' ',strip=True)) for v in clean_group.select('.item-control-static') if src.clean(v.get_text(' ',strip=True))]
    return literal,{k:v for k,v in enriched.items() if v},{k:v for k,v in links.items() if v}

def main():
    dest=RUN/'selected-source-records-001.json.gz';assert not dest.exists()
    index=m.load(RUN/'bounded-art-index-001.json.gz');old=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']
    oldids={v['external_id']:v for v in old['identifiers'] if v['scheme']=='searchculture-edm'}
    selected=[dict(card,number=i+1,historical_source_match=card['source_id'] in oldids,selection_reason='bounded_visual_art_metadata_review') for i,card in enumerate(index['cards'])]
    sids={x['source_id'] for x in selected}
    for sid,v in sorted(oldids.items()):
        if sid not in sids:selected.append(dict(source_id=sid,url=v['canonical_url'],number=len(selected)+1,historical_source_match=True,selection_reason='existing_comparator'))
    selection=RUN/'metadata-selection-001.json'
    if not selection.exists():m.save(selection,dict(at=m.now(),selected=selected,index_reference=c.ref(RUN/'bounded-art-index-001.json.gz'),policy='233 type-selected visual/decorative-art leads and any additional old comparators; not yet accepted as eligible. Metadata first, no images or database writes.'))
    else:assert m.load(selection)['selected']==selected
    def capture(card):
        sid=card['source_id'];doc,rc=src.capture('object-'+sid.split('000181-')[1]+'-001',card['url']);literal,enrichment,links=fields(doc)
        assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Πολεμικό Μουσείο']
        im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        filelinks=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if '/aggregator/edm/'+sid+'/files/' in a['href']})
        rights=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href']})
        return dict(number=card['number'],source_id=sid,source_url=card['url'],index=card,fields=literal,enrichment=enrichment,field_enrichment_links=links,thumbnail_url=urljoin(card['url'],im['src']) if im else None,file_links=filelinks,rights_links=rights,receipt=rc,decision='unreviewed_metadata')
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(capture,selected):
            rows.append(row)
            if len(rows)%25==0:print(json.dumps(dict(captured=len(rows),selected=len(selected))),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),policy='Museum literal metadata excludes aggregator enrichment panels; creator and sitter authorities retained by field. Literal creation century/ranges retained separately from index enrichment and depicted event dates; no automatic cutoff or image eligibility. Bilingual creator labels must not become multiple people. Detail and visual/editorial review pending.'))
    print(json.dumps(dict(captured=len(rows),old=sum(x['index']['historical_source_match'] for x in rows))),flush=True)

if __name__=='__main__':main()
