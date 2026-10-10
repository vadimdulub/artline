"""Audit the bounded 450-record Spathario metadata index; no image downloading."""
import importlib.util,json,math,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-spathario-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def page(n):
    params={'portalSearches[0].providerInstitytionShortNames':':Mar_Spathareio','sortResults':'TITLE','resultsMode':'GRID','language':'en','page.page':n}
    url=src.BASE+'/aggregator/portal/advancedSearch/search?'+urlencode(params)
    doc,rc=src.capture('metadata-index-'+str(n).zfill(3)+'-001',url);cards=[]
    for el in doc.select('.edm-entity-result'):
        pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
        if not pairs:continue
        a,u=pairs[0];sid=u.split('/aggregator/edm/')[1].split('?')[0];assert sid.startswith('Mar_Spathareio/000223-')
        text=src.clean(el.get_text(' ',strip=True));date=re.search(r' Date (.*?) (?:Item type|Creator|Place|Institution) ',text);kind=re.search(r' Item type (.*?) (?:Creator|Place|Institution) ',text)
        cards.append(dict(source_id=sid,url=u,title=src.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    pager=doc.select_one('.results-pagination .text-muted');text=src.clean(pager.get_text(' ',strip=True));numbers=[int(x.replace(',','')) for x in re.findall(r'[\d,]+',text)];assert len(numbers)==3
    first,last,total=numbers;assert total==450 and first==(n-1)*30+1 and 0<len(cards)==last-first+1<=30
    return dict(page=n,receipt=rc,cards=cards,pagination=text,total=total)

def main():
    dest=RUN/'bounded-metadata-index-001.json.gz';assert not dest.exists()
    nav=m.load(RUN/'source-navigation-001.json.gz')['rows'][0]
    form=next(x for x in nav['forms'] if x['action']=='/aggregator/portal/advancedSearch/search');assert form['method']=='GET'
    assert any(x['name']=='portalSearches[0].providerInstitytionShortNames' for x in form['selects'])
    first=page(1);pages=[first]
    print(json.dumps(dict(page=1,count=len(first['cards']))),flush=True)
    for n in range(2,math.ceil(first['total']/30)+1):
        row=page(n);pages.append(row);print(json.dumps(dict(page=n,count=len(row['cards']))),flush=True)
    cards=[x for pg in pages for x in pg['cards']];assert len(cards)==len({x['source_id'] for x in cards})==450
    existing=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']['identifiers'];known={x['external_id']:x['entity_id'] for x in existing if x['scheme']=='searchculture-edm'}
    for card in cards:card['existing_artwork_id']=known.get(card['source_id'])
    m.save(dest,dict(at=m.now(),pages=pages,cards=cards,source_total=450,script_reference=c.ref(Path(__file__).resolve()),policy='Institution-scoped metadata-only index, bounded to the observed450records. TITLE retains unknown dates. Creation dates, art scope and individual object/version identity require separate review before selection or image retrieval. No images or catalogue writes.'))
    print(json.dumps(dict(metadata=len(cards),existing=sum(bool(x['existing_artwork_id']) for x in cards))),flush=True)

if __name__=='__main__':main()
