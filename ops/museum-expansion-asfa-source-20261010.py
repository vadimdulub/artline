"""Observed public date-sort selection and facet controls; no object or image capture."""
import gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
q=c.module('q','museum-expansion-kazantzakis-selection-20261009.py');q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)

def index(doc):
    out=[]
    for el in doc.select('.edm-entity-result'):
        pairs=[(a,urljoin('https://www.searchculture.gr',a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
        if not pairs:continue
        a,url=pairs[0];text=q.clean(el.get_text(' ',strip=True));date=re.search(r' Date (.*?) Item type ',text);kind=re.search(r' Item type (.*?) (?:Creator|Institution|Place) ',text)
        out.append(dict(url=url,source_id=url.split('/aggregator/edm/')[1],title=q.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    assert len({x['source_id'] for x in out})==len(out);return out

def main():
    assert not(RUN/'source-selection-discovery-001.json').exists();previous=m.load(c.PREVIOUS/'next-source-discovery-001.json.gz');src=next(x for x in previous['rows'] if x['institution_id']==c.IID);raw=gzip.decompress((m.ROOT/src['receipt']['body_path']).read_bytes()).decode();form=src['forms'][0]
    assert form['action']=='/aggregator/portal/collections/DigASFA/search' and form['method']=='GET' and any(x['value']=='YEAR_ASC' for x in form['sort_options'])
    assert "var collectionShortName = 'DigASFA'" in raw and "var context = '/aggregator'" in raw and "+ '/onlyFacetPanel?language=' + lang" in raw
    facets,fr=q.q.capture('facets-001','https://www.searchculture.gr/aggregator/portal/collections/DigASFA/onlyFacetPanel?language=en')
    doc,rc=q.q.capture('date-index-001','https://www.searchculture.gr'+form['action']+'?'+urlencode({'resultsMode':'GRID','sortResults':'YEAR_ASC','language':'en','page.page':1}));cards=index(doc);assert len(cards)==30
    controls=[]
    for span in facets.select('span.labels'):
        node=span.parent.parent;check=node.select_one('input[type=checkbox]')
        if check:
            value=facets.find('input',attrs={'name':check['name'].replace('.checked','.value')});controls.append(dict(label=q.clean(span.get_text(' ',strip=True)),text=q.clean(node.get_text(' ',strip=True)),control=check['name'],value=value.get('value') if value else None))
    m.save(RUN/'source-selection-discovery-001.json',dict(at=m.now(),collection_reference=src['receipt'],form=form,facet_receipt=fr,facets=controls,first_date_page=dict(receipt=rc,cards=cards),source_total=4012,policy='First30source date-sorted cards and observed public facet controls. Collection total is not eligible-artwork count. No object details or images captured.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(cards=cards,facets=controls),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
