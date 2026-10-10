"""Select a bounded date-sorted painting index using observed public form controls."""
import argparse, gzip, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def observed():
    receipt=m.load(RUN/'captures/advanced-001.json')
    doc=BeautifulSoup(gzip.decompress((m.ROOT/receipt['body_path']).read_bytes()).decode(),'html.parser')
    label=next(x for x in doc.select('span.labels') if src.clean(x.get_text())=='Έργο ζωγραφικής')
    check=label.parent.parent.select_one('input[type=checkbox]');name=check['name'];value=doc.find('input',attrs={'name':name.replace('.checked','.value')})['value']
    assert value=='http://semantics.gr/authorities/ekt-item-types/zwgrafikh'
    form=doc.find('form',attrs={'action':'/aggregator/portal/advancedSearch/search'})
    assert form and form.get('method')=='GET' and form.find('select',attrs={'name':'portalSearches[0].providerInstitytionShortNames'})
    field=name.split('.values')[0]+'.field';fv=doc.find('input',attrs={'name':field})['value']
    return dict(receipt=receipt,control=name,value=value,field_control=field,field_value=fv,label=src.clean(label.parent.parent.get_text(' ',strip=True)),action=form['action'])

def params(page,controls):
    return {'portalSearches[0].providerInstitytionShortNames':':EIM',controls['control']:'true',controls['control'].replace('.checked','.value'):controls['value'],controls['field_control']:controls['field_value'],'sortResults':'YEAR_ASC','resultsMode':'GRID','language':'en','page.page':page}

def page(n,controls):
    doc,receipt=src.capture('paintings-date-index-'+str(n).zfill(3),src.BASE+controls['action']+'?'+urlencode(params(n,controls)))
    cards=src.index(doc)
    assert len(cards)==30 and all(x['source_id'].startswith('EIM/') and x['index_type'] and 'Painting' in x['index_type'] for x in cards)
    pager=doc.select_one('.results-pagination .text-muted')
    return dict(page=n,receipt=receipt,cards=cards,pagination=src.clean(pager.get_text(' ',strip=True)))

def first():
    dest=RUN/'painting-index-selection-001.json';assert not dest.exists()
    controls=observed();result=page(1,controls)
    m.save(dest,dict(at=m.now(),controls=controls,first_page=result,selected_pages=8,source_total=4727,painting_facet_total=1006,policy='Oldest eight painting-result pages selected for individual metadata review, not blanket eligibility. Date sorting excludes unknown dates and may include dates referring to sitters/subjects. No images or writes.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(result,ensure_ascii=False),flush=True)

def index():
    dest=RUN/'bounded-painting-index-001.json.gz';assert not dest.exists();selection=m.load(RUN/'painting-index-selection-001.json')
    pages=[selection['first_page']]
    for n in range(2,9):
        row=page(n,selection['controls']);pages.append(row)
        print(json.dumps(dict(page=n,pagination=row['pagination'],first_date=row['cards'][0]['index_date'],last_date=row['cards'][-1]['index_date'])),flush=True)
    cards=[card for pg in pages for card in pg['cards']];assert len(cards)==len({x['source_id'] for x in cards})==240
    m.save(dest,dict(at=m.now(),pages=pages,cards=cards,source_total=4727,painting_facet_total=1006,selection_reference=c.ref(RUN/'painting-index-selection-001.json'),script_reference=c.ref(Path(__file__).resolve()),policy='240 painting index cards provisionally selected for detail/date/version review. No creation date inferred from index-only numeric range; no images or production writes.'))
    print(json.dumps(dict(painting_cards=len(cards))),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['first','index']);args=parser.parse_args();globals()[args.command]()
