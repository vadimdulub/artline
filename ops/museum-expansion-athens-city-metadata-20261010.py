"""Capture selected art records, excluding explicit post1970 index dates first."""
import collections
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-athens-city-source-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
c,q,m,RUN=v.c,v.q,v.m,v.RUN

def main():
    assert not(RUN/'selected-source-records-001.json.gz').exists()
    index=m.load(RUN/'bounded-index-001.json.gz');selected=[];held=[]
    for number,card in enumerate(index['unique_cards'],1):
        value=dict(card,number=number);date=card['index_date'];years=[int(x) for x in re.findall(r'\b\d{4}\b',date or '')]
        if years and min(years)>1970:value['selection_state']='excluded_explicit_post1970';held.append(value)
        elif years and max(years)>1970:value['selection_state']='hold_date_crosses1970';held.append(value)
        else:value['selection_state']='selected_metadata_review';selected.append(value)
    sp=RUN/'metadata-selection-001.json'
    if not sp.exists():m.save(sp,dict(at=m.now(),selected=selected,deferred=held,index_reference=c.ref(RUN/'bounded-index-001.json.gz'),policy='Date fields only, not years inside titles. Capture unknown-date and existing comparison entries for review; no automatic eligibility. No images. Explicit post1970 objects excluded before detail capture.'))
    else:assert m.load(sp)['selected']==selected and m.load(sp)['deferred']==held
    rows=[]
    for card in selected:
        sid=card['source_id'];uuid=sid.split('000190-')[1];url=card['url'];soup,rc=q.q.capture('object-'+uuid+'-001',url);literal,enrichment=q.fields(soup)
        assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Μουσείον της Πόλεως των Αθηνών – Ίδρυμα Βούρου – Ευταξία']
        native=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if a['href'].startswith('https://portal.athenscitymuseum.gr/artworks/')});assert len(native)==1
        image=soup.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(url,a['href'])) for a in soup.select('a[href]') if 'preservation' in a['href'] or 'repox.athenscitymuseum' in a['href']]
        rows.append(dict(number=card['number'],source_id=sid,source_url=url,native_url=native[0],index=card,fields=literal,enrichment=enrichment,thumbnail_url=urljoin(url,image['src']) if image else None,additional_media_links=links,receipt=rc,decision='unreviewed_metadata'))
        if len(rows)%10==0:print(json.dumps(dict(captured=len(rows),selected=len(selected),excluded=len(held))),flush=True)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=c.ref(sp),script_reference=c.ref(Path(__file__).resolve()),policy='Museum-supplied literal metadata and EKT enrichment stored separately. Public object pages only; no native authorization values reused and no image bytes downloaded. All metadata awaits physical-unit/version/date review.'))
    print(json.dumps(dict(captured=len(rows),deferred=len(held),existing_comparators=sum(x['index']['historical_source_match'] for x in rows))),flush=True)

if __name__=='__main__':main()
