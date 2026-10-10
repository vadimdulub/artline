"""Bounded visual/decorative artwork index from observed type controls, retaining undated entries."""
import argparse,importlib.util,json,math,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-war-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN
TYPES=['Δισδιάστατα γραφικά','Γλυπτό','Έργο θρησκευτικής τέχνης','Ανάγλυφο','Μετάλλιο','Χάρτης']

def controls():
    nav=m.load(RUN/'art-navigation-001.json.gz')['rows'][0]
    out=[next(x for x in nav['controls'] if x['label']==label and 'dc_type_hierarchy' in x['control']) for label in TYPES]
    form=next(x for x in nav['forms'] if x['action']=='/aggregator/portal/advancedSearch/search');assert form['method']=='GET'
    assert any(x['name']=='portalSearches[0].providerInstitytionShortNames' for x in form['selects'])
    return out

def page(n,selected):
    params={'portalSearches[0].providerInstitytionShortNames':':DigWAR','sortResults':'TITLE','resultsMode':'GRID','language':'en','page.page':n}
    for x in selected:params.update({x['control']:'true',x['control'].replace('.checked','.value'):x['value'],x['field_control']:x['field_value']})
    url=src.BASE+'/aggregator/portal/advancedSearch/search?'+urlencode(params);doc,rc=src.capture('art-type-'+selected[0]['value'].rsplit('/',1)[-1]+'-'+str(n).zfill(3)+'-001',url);cards=[]
    for el in doc.select('.edm-entity-result'):
        pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
        if not pairs:continue
        a,u=pairs[0];sid=u.split('/aggregator/edm/')[1];assert sid.startswith('DigWAR/000181-')
        text=src.clean(el.get_text(' ',strip=True));date=re.search(r' Date (.*?) (?:Item type|Creator|Place|Institution) ',text);kind=re.search(r' Item type (.*?) (?:Creator|Place|Institution) ',text)
        cards.append(dict(source_id=sid,url=u,title=src.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    pager=doc.select_one('.results-pagination .text-muted');text=src.clean(pager.get_text(' ',strip=True));numbers=[int(x.replace(',','')) for x in re.findall(r'[\d,]+',text)];assert len(numbers)==3
    first,last,total=numbers;assert 0<len(cards)<=30 and first==(n-1)*30+1 and len(cards)==last-first+1 and total<=234
    return dict(page=n,receipt=rc,cards=cards,pagination=text,total=total)

def main():
    dest=RUN/'bounded-art-index-001.json.gz';assert not dest.exists();selected=controls();pages=[];byid={};observed=[]
    for control in selected:
        first=page(1,[control]);total=first['total'];expected=int(re.search(r'\((\d+)\)',control['text'])[1]);assert total==expected
        group=[first]
        for n in range(2,math.ceil(total/30)+1):
            row=page(n,[control]);assert row['total']==total;group.append(row)
        cards=[x for pg in group for x in pg['cards']];assert len(cards)==len({x['source_id'] for x in cards})==total
        for card in cards:
            sid=card['source_id']
            if sid not in byid:byid[sid]=dict(card,selected_type_labels=[])
            assert byid[sid]['url']==card['url'];byid[sid]['selected_type_labels'].append(control['label'])
        pages.extend(dict(pg,selected_type=control['label']) for pg in group);observed.append(dict(label=control['label'],count=total,pages=len(group)))
        print(json.dumps(dict(label=control['label'],count=total,distinct_so_far=len(byid)),ensure_ascii=False),flush=True)
    cards=list(byid.values());assert len(cards)<=234
    m.save(dest,dict(at=m.now(),pages=pages,cards=cards,type_counts=observed,controls=selected,source_total=1888,script_reference=c.ref(Path(__file__).resolve()),policy='Separate source-observed type facets combined by object ID offline; the public UI applies AND when several checks are selected, so initial combined request returned no results. No cap relaxed, no unknown dates removed: TITLE sort. Type membership is metadata selection, not artwork/date eligibility. No image downloads or production writes.'))
    m.save(RUN/'index-query-correction-001.json',dict(at=m.now(),failed_script_reference=c.ref(Path(__file__).with_name('museum-expansion-war-index-20261010.py')),failed_request_reference=c.ref(RUN/'captures/art-index-001-001.json'),difference='Multiple chosen type facets combine withAND. Use each exact observed type control independently and deduplicate returned source IDs, retaining membership labels.',database_writes=False,images_downloaded=0))
    print(json.dumps(dict(selected_metadata=len(cards),pages=len(pages))),flush=True)

if __name__=='__main__':main()
