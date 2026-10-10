"""Bounded museum-supplied art-category metadata selection; no image downloads."""
import collections
import gzip
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin,urlencode
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
q=c.module('q','museum-expansion-kazantzakis-selection-20261009.py')
m,RUN=c.m,c.RUN
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)
BASE='https://www.searchculture.gr'
TYPES=['Painting','Engraving','Drawing','Lithography','Icon','Sculpture','Mixed media work of art','Mosaic']

def index(soup):
    rows=[];seen=set()
    for parent in soup.select('.edm-entity-result'):
        pairs=[(a,urljoin(BASE,a['href'])) for a in parent.select('a[href]')]
        pairs=[(a,u) for a,u in pairs if re.fullmatch(BASE+r'/aggregator/edm/DigAthensMuseum/000190-[0-9a-f-]+',u) and q.clean(a.get_text(' ',strip=True))]
        if not pairs:continue
        a,url=pairs[0]
        if url in seen:continue
        seen.add(url);text=q.clean(parent.get_text(' ',strip=True))
        date=re.search(r' Date (.*?) Item type ',text);kind=re.search(r' Item type (.*?) (?:Creator|Institution|Place) ',text)
        rows.append(dict(url=url,source_id=url.split('/aggregator/edm/')[1],title=q.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    return rows

def main():
    assert not(RUN/'bounded-index-001.json.gz').exists()
    fp=RUN/'captures/searchculture-facets-001.json';fr=m.load(fp);raw=gzip.decompress((m.ROOT/fr['body_path']).read_bytes());soup=BeautifulSoup(raw,'html.parser')
    field='ekt_proxy_dc_type_hierarchy_uri';params={'facets['+field+'].field':field,'resultsMode':'GRID','sortResults':'TITLE','language':'en'};selected=[]
    for i,title in enumerate(TYPES):
        label=next(x for x in soup.select('span.labels') if q.clean(x.get_text(' ',strip=True))==title)
        node=label.parent.parent;check=node.select_one('input[type=checkbox]');assert check is not None
        oldname=check['name'];value=soup.find('input',attrs={'name':oldname.replace('.checked','.value')})['value'];assert value.startswith('http://semantics.gr/')
        name='facets['+field+'].values['+str(i)+']'
        params[name+'.checked']='true';params[name+'.value']=value
        selected.append(dict(label=title,value=value,source_control=oldname,text=q.clean(node.get_text(' ',strip=True))))
    discovery=m.load(m.RUN/'native/kilkis-delivery-20261010/next-source-discovery-001.json.gz')
    form=discovery['rows'][0]['forms'][0];assert form['action']=='/aggregator/portal/collections/DigAthensMuseum/search' and form['method']=='GET'
    m.save(RUN/'category-selection-001.json',dict(at=m.now(),selected=selected,source_facet_receipt=fr,source_form=form,query_parameters=params,maximum_pages=6,maximum_cards=180,policy='Eight selected art categories from observed public filter controls. Capture metadata before selecting images. Unknown creation dates remain reviewable; title dates or represented events do not establish manufacture dates. Other categories remain unreviewed, not excluded globally.',script_reference=c.ref(Path(__file__).resolve())))
    known={x['external_id'] for x in m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']['identifiers'] if x['scheme']=='searchculture-edm'}
    pages=[];cards=[];total=None
    for page in range(1,7):
        url=BASE+form['action']+'?'+urlencode(dict(params,**{'page.page':page}))
        doc,rc=q.q.capture('selected-art-index-'+str(page).zfill(3),url)
        match=re.search(r"var itemsNum = '(\d+)'",str(doc));assert match is not None
        n=int(match[1]);total=n if total is None else total;assert n==total
        rows=index(doc);assert len(rows)<=30 and rows and not {x['source_id'] for x in rows}&{x['source_id'] for x in cards}
        for row in rows:row['historical_source_match']=row['source_id'] in known
        pages.append(dict(page=page,receipt=rc,cards=rows));cards.extend(rows)
        print(json.dumps(dict(page=page,total=total,cards=len(rows),types=dict(collections.Counter(x['index_type'] for x in rows)),historical=sum(x['historical_source_match'] for x in rows))),flush=True)
        if len(cards)>=total:break
    m.save(RUN/'bounded-index-001.json.gz',dict(at=m.now(),pages=pages,cards=len(cards),observed_filtered_total=total,selected_type_labels=TYPES,historical_matches=sum(x['historical_source_match'] for x in cards),category_selection_reference=c.ref(RUN/'category-selection-001.json'),policy='Bounded art-category indexes, at most180 cards. No object detail or image downloaded. Index category/date labels are leads, not approved imports.'))

if __name__=='__main__':main()
