"""Bounded historic textile metadata and native physical-object evidence; no images."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,unquote
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-jewish-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN
fields=c.module('parser','museum-expansion-war-metadata-20261010.py').fields
ART_NUMBERS=[44,46,48,71,74,75,76,77,79,80,82,86,87,144,145,147,153,154,155,156,157,158,159,173,175,185,187,192]

def native(row):
    n=row['number'];url=row['native_links'][0];prefix='textile' if n>=1001 else 'art'
    d,rc=src.capture('native-'+prefix+'-'+str(n)+'-001',url)
    im=next((x for x in d.select('img') if '/uploads/artifacts/' in x.get('src','')),None)
    text=src.clean(d.get_text(' ',strip=True)).split(' Related Artifacts ')[0]
    assert 'The Jewish Museum of Greece' in text
    return dict(receipt=rc,text=text,primary_image_url=im['src'] if im else None,format_literal=re.search(r' Format: (.*?) Source:',text)[1] if ' Format: ' in text else None,file_name=unquote(im['src'].rsplit('/',1)[1]) if im else None)

def main():
    dest=RUN/'textile-source-records-001.json.gz';assert not dest.exists()
    cards=m.load(RUN/'bounded-textile-index-001.json.gz')['cards'];chosen=[];later=[]
    for n,card in enumerate(cards,1001):
        match=re.fullmatch(r'(\d{4})(?: - (\d{4}))?',card['index_date'] or '')
        r=dict(card,number=n,historical_source_match=False)
        if match and int(match[2] or match[1])<=1955 and '000141-photograph-' not in r['source_id'] and len(chosen)<280:chosen.append(r)
        else:later.append(r)
    assert len(chosen)==280
    selection=RUN/'textile-metadata-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),selected=chosen,remaining_index_leads=later,policy='First280 historic textile art leads in source TITLE order, numeric index upper bound by1955, no photographic surrogate records. Metadata only; source literal dates, complete object versus detail and secondary-use assembly still require editorial review. Remaining305 leads retained, no artwork/image ingestion.'))
    rows=[];held=[];failures=0
    for card in chosen:
        if failures>=3:held.append(dict(number=card['number'],reason='Unattempted after3source failures'));continue
        sid=card['source_id'];key='object-'+sid.split('000141-')[1]+'-001'
        try:
            doc,rc=src.capture(key,card['url']);literal,enrichment,links=fields(doc)
            assert literal.get('Πάροχος')==['Εβραϊκό Μουσείο της Ελλάδος']
            im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
            row=dict(number=card['number'],source_id=sid,source_url=card['url'],index=card,fields=literal,enrichment=enrichment,field_enrichment_links=links,thumbnail_url=urljoin(card['url'],im['src']) if im else None,rights_links=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href'] or 'rightsstatements.org/' in a['href']}),native_links=sorted({a['href'] for a in doc.select('a[href]') if 'artifacts.jewishmuseum.gr/artifacts/' in a['href']}),receipt=rc,decision='unreviewed_metadata')
            row['native']=native(row);rows.append(row)
        except Exception as e:held.append(dict(number=card['number'],source_id=sid,error=type(e).__name__,message=str(e)[:300]));failures+=1
        if len(rows)%20==0:print(json.dumps(dict(textile_metadata=len(rows),held=len(held))),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,held=held,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve())))
    art=[]
    for r in m.load(RUN/'art-source-records-001.json.gz')['rows']:
        if r['number'] not in ART_NUMBERS:continue
        try:art.append(dict(number=r['number'],native=native(r)))
        except Exception as e:held.append(dict(number=r['number'],error=type(e).__name__,message=str(e)[:300]))
    m.save(RUN/'selected-art-native-evidence-001.json.gz',dict(at=m.now(),rows=art,held=held,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(textile_metadata=len(rows),art_native=len(art),held=len(held))),flush=True)

if __name__=='__main__':main()
