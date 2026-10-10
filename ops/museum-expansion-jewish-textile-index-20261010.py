"""Bounded585embroidery metadata records for selected decorative-art and physical-unit review."""
import importlib.util,json,math,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-jewish-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN
TYPES=['Εργόχειρο (Κεντητική, πλεκτική)']

def controls():
    nav=next(x for x in m.load(RUN/'source-navigation-001.json.gz')['rows'] if x['key']=='collection-advanced-001');out=[]
    for label in TYPES:
        matches=[x for x in nav['controls'] if x['label']==label and 'dc_type_hierarchy' in x['control']];assert len(matches)==1;out.extend(matches)
    form=next(x for x in nav['forms'] if x['action']=='/aggregator/portal/advancedSearch/search');assert form['method']=='GET'
    assert any(x['name']=='portalSearches[0].providerInstitytionShortNames' for x in form['selects'])
    return out

def page(n,control):
    params={'portalSearches[0].providerInstitytionShortNames':':jewishmuseum','sortResults':'TITLE','resultsMode':'GRID','language':'en','page.page':n,control['control']:'true',control['control'].replace('.checked','.value'):control['value'],control['field_control']:control['field_value']}
    url=src.BASE+'/aggregator/portal/advancedSearch/search?'+urlencode(params);doc,rc=src.capture('textile-type-'+control['value'].rsplit('/',1)[-1]+'-'+str(n).zfill(3)+'-001',url);cards=[]
    for el in doc.select('.edm-entity-result'):
        pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
        if not pairs:continue
        a,u=pairs[0];sid=u.split('/aggregator/edm/')[1].split('?')[0];assert sid.startswith('jewishmuseum/000141-')
        text=src.clean(el.get_text(' ',strip=True));date=re.search(r' Date (.*?) (?:Item type|Creator|Place|Institution) ',text);kind=re.search(r' Item type (.*?) (?:Creator|Place|Institution) ',text)
        cards.append(dict(source_id=sid,url=u,title=src.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    pager=doc.select_one('.results-pagination .text-muted');text=src.clean(pager.get_text(' ',strip=True));numbers=[int(x.replace(',','')) for x in re.findall(r'[\d,]+',text)];assert len(numbers)==3
    first,last,total=numbers;assert 0<len(cards)<=30 and first==(n-1)*30+1 and len(cards)==last-first+1 and total<=585
    return dict(page=n,receipt=rc,cards=cards,pagination=text,total=total)

def main():
    dest=RUN/'bounded-textile-index-001.json.gz';assert not dest.exists();selected=controls();pages=[];byid={};observed=[]
    for control in selected:
        first=page(1,control);total=first['total'];expected=int(re.search(r'\((\d+)\)',control['text'])[1]);assert total==expected;group=[first]
        for n in range(2,math.ceil(total/30)+1):
            row=page(n,control);assert row['total']==total;group.append(row)
        cards=[x for pg in group for x in pg['cards']];assert len(cards)==len({x['source_id'] for x in cards})==total
        for card in cards:
            sid=card['source_id']
            if sid not in byid:byid[sid]=dict(card,selected_type_labels=[])
            assert byid[sid]['url']==card['url'];byid[sid]['selected_type_labels'].append(control['label'])
        pages.extend(dict(pg,selected_type=control['label']) for pg in group);observed.append(dict(label=control['label'],count=total,pages=len(group)));print(json.dumps(dict(label=control['label'],count=total,distinct_so_far=len(byid)),ensure_ascii=False),flush=True)
    cards=list(byid.values());assert len(cards)==585
    m.save(dest,dict(at=m.now(),pages=pages,cards=cards,type_counts=observed,controls=selected,source_total=13533,script_reference=c.ref(Path(__file__).resolve()),policy='Observed585embroidery/craftfacet metadataonly, bounded20TITLEpages. Museumcollectioncontext identifies historicOttomanritualtextiles as a corecollection. Select actualeligiblephysicaltextiles after literaldate,component/patch/view andholdingreview; no full13kindex or image downloading. No databasewrites.'))
    print(json.dumps(dict(selected_metadata=len(cards),pages=len(pages))),flush=True)

if __name__=='__main__':main()
