"""Two observed photograph-category pages for the next bounded metadata review."""
import gzip,importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-delivery-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    assert not(RUN/'next-photograph-index-001.json.gz').exists()
    v=c.module('v','museum-expansion-athens-city-source-20261010.py');q=v.q.q;q.RUN=RUN;q.CAP=RUN/'next-index-captures';q.CAP.mkdir(parents=True,exist_ok=True)
    receipt=m.load(c.RESEARCH/'captures/searchculture-facets-001.json');soup=BeautifulSoup(gzip.decompress((m.ROOT/receipt['body_path']).read_bytes()),'html.parser')
    label=next(x for x in soup.select('span.labels') if x.get_text(' ',strip=True)=='Photo');node=label.parent.parent;ch=node.select_one('input[type=checkbox]');value=soup.find('input',attrs={'name':ch['name'].replace('.checked','.value')})['value'];assert value=='http://semantics.gr/authorities/ekt-item-types/fwtografia'
    field='ekt_proxy_dc_type_hierarchy_uri';prefix='facets['+field+']';params={prefix+'.field':field,prefix+'.values[0].checked':'true',prefix+'.values[0].value':value,'resultsMode':'GRID','sortResults':'YEAR_ASC','language':'en'}
    initial=m.load(RUN/'production-initial-scope-001.json.gz');known={x['external_id'] for x in initial['snapshot']['identifiers'] if x['scheme']=='searchculture-edm'}
    known|={x['facts']['source_id'] for x in m.load(RUN/'editorial-reviewed-001.json.gz')['records']};pages=[];cards=[]
    for page in [1,2]:
        url='https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum/search?'+urlencode(dict(params,**{'page.page':page}));doc,rc=q.capture('photo-index-'+str(page).zfill(3),url);rows=v.index(doc);assert len(rows)==30 and not{r['source_id'] for r in rows}&{r['source_id'] for r in cards}
        for row in rows:row['already_catalogued_source']=row['source_id'] in known
        pages.append(dict(page=page,receipt=rc,cards=rows));cards+=rows
    m.save(RUN/'next-photograph-index-001.json.gz',dict(at=m.now(),pages=pages,cards=cards,source_total_observed=1634,metadata_cards=60,already_catalogued=sum(x['already_catalogued_source'] for x in cards),observed_facet=dict(label='Photo',value=value,text=node.get_text(' ',strip=True),receipt=receipt),query_parameters=params,ready_candidates=0,detail_downloads=0,image_downloads=0,policy='Index leads only, sorted by source year ascending. Source date may describe capture, depicted event, reproduction or physical print; full object and version review is required. No additional artworks or images applied by this script.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(cards=60,already_catalogued=sum(x['already_catalogued_source'] for x in cards),date_labels=sorted({x['index_date'] or 'unknown' for x in cards}))),flush=True)

if __name__=='__main__':main()
