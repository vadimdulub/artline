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
    url=src.BASE+'/aggregator/portal/advancedSearch/search?'+urlencode(params);doc,rc=src.capture('art-index-'+str(n).zfill(3)+'-001',url);cards=[]
    for el in doc.select('.edm-entity-result'):
        pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
        if not pairs:continue
        a,u=pairs[0];sid=u.split('/aggregator/edm/')[1];assert sid.startswith('DigWAR/000181-')
        text=src.clean(el.get_text(' ',strip=True));date=re.search(r' Date (.*?) (?:Item type|Creator|Place|Institution) ',text);kind=re.search(r' Item type (.*?) (?:Creator|Place|Institution) ',text)
        cards.append(dict(source_id=sid,url=u,title=src.clean(a.get_text(' ',strip=True)),text=text,index_date=date[1] if date else None,index_type=kind[1] if kind else None))
    pager=doc.select_one('.results-pagination .text-muted');text=src.clean(pager.get_text(' ',strip=True));numbers=[int(x.replace(',','')) for x in re.findall(r'[\d,]+',text)];assert len(numbers)==3
    first,last,total=numbers;assert 0<len(cards)<=30 and first==(n-1)*30+1 and len(cards)==last-first+1 and total<=234
    return dict(page=n,receipt=rc,cards=cards,pagination=text,total=total)

def first():
    dest=RUN/'art-index-selection-001.json';assert not dest.exists();selected=controls();result=page(1,selected)
    m.save(dest,dict(at=m.now(),controls=selected,first_page=result,maximum_selected_records=234,source_total=1888,script_reference=c.ref(Path(__file__).resolve()),policy='Selected visual art, sculpture, religious art, relief, medallic art and maps for metadata review. TITLE order retains undated entries. Type membership is not eligibility; event/prototype dates, modern copies, utilities, document-like diagrams and post1970 objects require exclusion or explicit review. No object images or writes.'))
    print(json.dumps(dict(total=result['total'],first_page=result['cards']),ensure_ascii=False),flush=True)

def index():
    dest=RUN/'bounded-art-index-001.json.gz';assert not dest.exists();selection=m.load(RUN/'art-index-selection-001.json');pages=[selection['first_page']];total=pages[0]['total']
    for n in range(2,math.ceil(total/30)+1):
        row=page(n,selection['controls']);assert row['total']==total;pages.append(row);print(json.dumps(dict(page=n,pagination=row['pagination'])),flush=True)
    cards=[card for pg in pages for card in pg['cards']];assert len(cards)==len({x['source_id'] for x in cards})==total
    m.save(dest,dict(at=m.now(),pages=pages,cards=cards,selection_reference=c.ref(RUN/'art-index-selection-001.json'),script_reference=c.ref(Path(__file__).resolve()),policy='Bounded type-selected metadata index only. Selected category total is not eligible artwork total. No blank or placeholder artworks, no utilities/documents used to pad museum counts.'))
    print(json.dumps(dict(index_cards=len(cards))),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['first','index']);args=parser.parse_args();globals()[args.command]()
