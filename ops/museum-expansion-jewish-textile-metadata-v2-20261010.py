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
    dest=RUN/'textile-source-records-002.json.gz';assert not dest.exists()
    prior=m.load(RUN/'textile-source-records-001.json.gz');assert m.load(RUN/'unattempted-source-probe-001.json')['success']
    unattempted={x['number'] for x in prior['held'] if x.get('reason','').startswith('Unattempted')}
    chosen=[x for x in m.load(RUN/'textile-metadata-selection-001.json')['selected'] if x['number'] in unattempted]
    assert len(chosen)==159
    selection=RUN/'textile-metadata-selection-002.json';assert not selection.exists();m.save(selection,dict(at=m.now(),selected=chosen,prior_reference=c.ref(RUN/'textile-source-records-001.json.gz'),probe_reference=c.ref(RUN/'unattempted-source-probe-001.json'),policy='Continue only159 previouslyunattempted objects after successful1136probe. No retriesor alternateaccess to1132/1133/1134failedURLs. Stopagain after3newfailures. Noimages.'))
    rows=list(prior['rows']);held=[x for x in prior['held'] if 'error' in x];failures=0
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
    print(json.dumps(dict(textile_metadata=len(rows),held=len(held))),flush=True)

if __name__=='__main__':main()
