"""Fresh primary object evidence for18existing unillustrated Kilkis records."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
q=c.module('q','museum-expansion-kazantzakis-selection-20261009.py');m,RUN=c.m,c.RUN
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)

def main():
    assert not(RUN/'existing-source-records-001.json.gz').exists();snap=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];arts={v['id']:v for v in snap['artworks']};ids=[v for v in snap['identifiers'] if v['scheme']=='searchculture-edm'];assert len(ids)==18
    rows=[]
    for number,x in enumerate(ids,1):
        sid=x['external_id'];url=x['canonical_url'];assert sid.startswith('Efa_Kilkis_col/') and url.startswith('https://www.searchculture.gr/aggregator/edm/')
        soup,rc=q.q.capture('existing-'+sid.replace('/','-')+'-001',url);fields,enrichment=q.fields(soup)
        urls=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if 'efa-kilkis.gr/artworks/' in a['href'] and a['href'].rstrip('/')!='https://www.efa-kilkis.gr/artworks'});assert len(urls)==1,(sid,urls)
        u=urls[0];native,nrc=q.q.capture('existing-native-'+sid.split('/')[-1]+'-001',u);main=native.find('main') or native;attrs={}
        for el in main.select('.pt-attribute'):
            key=q.clean(el.parent.find('label').get_text(' ',strip=True));assert key not in attrs;attrs[key]=q.clean(el.get_text(' ',strip=True))
        period=q.clean(main.select_one('.CardTitle__subtitle').get_text(' ',strip=True));title=q.clean(main.select_one('.CardTitle__title').get_text(' ',strip=True));description=[q.clean(v.get_text(' ',strip=True)) for v in main.select('.ContentBlock__body-inner')]
        image=soup.find('img',src=lambda value:value and '/thumbnails/edm-record/'+sid in value)
        native_images=[dict(src=urljoin(u,v['src']),alt=v.get('alt'),srcset=v.get('srcset')) for v in main.select('img[src]')]
        row=dict(number='old-'+str(number),artwork_id=x['entity_id'],source_id=sid,source_url=url,native_url=u,title=title,inventory_literal=attrs.get('Αριθμός Έργου'),date_display=period,first=None,last=None,date_precision='unknown',creator_label=None,native_fields=attrs,native_description=description,aggregator_literal=fields,aggregator_enrichment=enrichment,source_receipt=rc,native_receipt=nrc,thumbnail_url=urljoin(url,image['src']) if image else None,native_images=native_images,decision='existing_record',catalogue_title=arts[x['entity_id']]['title'])
        rows.append(row);print(json.dumps(dict(source_id=sid,period=period,inventory=row['inventory_literal']),ensure_ascii=False),flush=True)
    m.save(RUN/'existing-source-records-001.json.gz',dict(at=m.now(),rows=rows,script_reference=c.ref(Path(__file__).resolve()),scope='Read-only existing identity and image review. Current catalogue metadata and unknown dates remain unchanged.'))

if __name__=='__main__':main()
