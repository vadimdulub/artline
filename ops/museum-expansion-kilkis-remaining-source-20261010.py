"""Read18previously unreviewed museum-source objects; no automatic selection or images."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
q=c.module('q','museum-expansion-kazantzakis-selection-20261009.py')
m,RUN=c.m,c.RUN
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)

def main():
    assert not(RUN/'remaining-source-records-001.json.gz').exists()
    cards=m.load(c.RESEARCH/'remaining-research-001.json')['remaining_unselected_index_cards'];assert len(cards)==18
    m.save(RUN/'remaining-source-selection-001.json',dict(at=m.now(),rows=cards,rationale='Review18bounded previously unreviewed source objects for decorative/specialist-art scope and independent physical-unit identity. Plain epigraphy or unclear assemblage components are not automatically selected to fill a quota. Metadata first; no images at this stage.',reference=c.ref(c.RESEARCH/'remaining-research-001.json'),web_observation='SearchCulture5044A web.open returned inaccessible-tool internal error, no HTTP403/429 reported. Observed public catalogue URL is requested normally; any actual denial stops capture.'))
    rows=[]
    for number,v in enumerate(cards,30):
        sid=v['url'].split('/aggregator/edm/')[1];soup,rc=q.q.capture('remaining-'+sid.replace('/','-')+'-001',v['url']);fields,enrichment=q.fields(soup)
        urls=sorted({urljoin(v['url'],a['href']) for a in soup.select('a[href]') if 'efa-kilkis.gr/artworks/' in a['href'] and a['href'].rstrip('/')!='https://www.efa-kilkis.gr/artworks'});assert len(urls)==1,(sid,urls)
        u=urls[0];native,nrc=q.q.capture('remaining-native-'+sid.split('/')[-1]+'-001',u);main=native.find('main') or native;attrs={}
        for el in main.select('.pt-attribute'):
            key=q.clean(el.parent.find('label').get_text(' ',strip=True));assert key not in attrs;attrs[key]=q.clean(el.get_text(' ',strip=True))
        period=q.clean(main.select_one('.CardTitle__subtitle').get_text(' ',strip=True));title=q.clean(main.select_one('.CardTitle__title').get_text(' ',strip=True));description=[q.clean(x.get_text(' ',strip=True)) for x in main.select('.ContentBlock__body-inner')]
        image=soup.find('img',src=lambda value:value and '/thumbnails/edm-record/'+sid in value)
        native_images=[dict(src=urljoin(u,x['src']),alt=x.get('alt'),srcset=x.get('srcset')) for x in main.select('img[src]')]
        row=dict(number=number,source_id=sid,source_url=v['url'],native_url=u,title=title,inventory_literal=attrs.get('Αριθμός Έργου'),date_display=period,first=None,last=None,date_precision='unknown',creator_label=None,native_fields=attrs,native_description=description,aggregator_literal=fields,aggregator_enrichment=enrichment,source_receipt=rc,native_receipt=nrc,thumbnail_url=urljoin(v['url'],image['src']) if image else None,native_images=native_images,decision='unreviewed_metadata_only')
        rows.append(row);print(json.dumps(dict(number=number,source_id=sid,period=period,description=description),ensure_ascii=False),flush=True)
    m.save(RUN/'remaining-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=c.ref(RUN/'remaining-source-selection-001.json'),script_reference=c.ref(Path(__file__).resolve()),actual_added=0,images_downloaded=0))

if __name__=='__main__':main()
