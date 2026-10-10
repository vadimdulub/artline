"""Read individual records selected by bounded museum metadata; dates are provisional."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-spathario-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN
fields=c.module('parser','museum-expansion-war-metadata-20261010.py').fields

def main():
    dest=RUN/'selected-source-records-001.json.gz';assert not dest.exists()
    cards=m.load(RUN/'bounded-metadata-index-001.json.gz')['cards'];selected=[];excluded=[]
    for card in cards:
        value=card['index_date']
        if value is not None and value.isdigit() and int(value)>1970:
            excluded.append(dict(card,selection_reason='Index date after1970; outside selected metadata pass, no individual record or image downloaded.'));continue
        selected.append(dict(card,number=len(selected)+1,historical_source_match=bool(card['existing_artwork_id']),selection_reason='Date<=1970 or unknown; verify literal dates, artistic scope and object identity.'))
    selection=RUN/'metadata-selection-001.json';assert not selection.exists()
    m.save(selection,dict(at=m.now(),selected=selected,excluded=excluded,index_reference=c.ref(RUN/'bounded-metadata-index-001.json.gz'),policy='Metadata only. Individual objects needed to distinguish actual creation, design/prototype dates, performances and modern copies. Unknown dates require explicit editorial review.'))
    rows=[];held=[];failures=0
    for card in selected:
        sid=card['source_id'];key='object-'+sid.split('000223-')[1]+'-001';rp=RUN/'captures'/(key+'.json')
        if failures>=3:
            held.append(dict(number=card['number'],source_id=sid,reason='Unattempted after3source failures'));continue
        if rp.exists() and m.load(rp)['status']!=200:
            held.append(dict(number=card['number'],source_id=sid,reason='Previously failed source capture; no retry',receipt=m.load(rp)));failures+=1;continue
        try:doc,rc=src.capture(key,card['url'])
        except Exception as exc:
            held.append(dict(number=card['number'],source_id=sid,reason=type(exc).__name__,receipt=m.load(rp) if rp.exists() else None));failures+=1;continue
        literal,enrichment,links=fields(doc);assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Σπαθάρειο Μουσείο - Δήμος Αμαρουσίου']
        im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        filelinks=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if '/aggregator/edm/'+sid+'/files/' in a['href']})
        rights=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href']})
        native=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if 'karagiozismuseum.gr' in a['href']})
        rows.append(dict(number=card['number'],source_id=sid,source_url=card['url'],index=card,fields=literal,enrichment=enrichment,field_enrichment_links=links,thumbnail_url=urljoin(card['url'],im['src']) if im else None,file_links=filelinks,rights_links=rights,native_links=native,receipt=rc,decision='unreviewed_metadata'))
        if len(rows)%10==0:print(json.dumps(dict(captured=len(rows),selected=len(selected),held=len(held))),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,held=held,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),parser_reference=c.ref(Path(__file__).with_name('museum-expansion-war-metadata-20261010.py')),policy='Literal fields separated from enrichment and referenced people. Bilingual labels are one maker, not two. Individual editorial review pending; no images or database writes.'))
    print(json.dumps(dict(captured=len(rows),old=sum(x['index']['historical_source_match'] for x in rows),held=len(held),later_index_only=len(excluded))),flush=True)

if __name__=='__main__':main()
