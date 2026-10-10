"""Bounded pre-1971 discovery for the Zongolopoulos Foundation; no DB access."""
import csv
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlencode

spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.m
RUN=m.RUN/'native/zongolopoulos-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)
IID='763803c5-3657-5d75-9cf8-9927a5c6a4de'
BASE='https://www.searchculture.gr'


def index(soup):
    rows=[];seen=set()
    for a in soup.select('a[href]'):
        url=urljoin(BASE,a['href'])
        if not re.fullmatch(BASE+r'/aggregator/edm/ZoggopoulosF/000041-\d+',url):continue
        title=q.clean(a.get_text(' ',strip=True))
        if not title or url in seen:continue
        seen.add(url);parent=a
        while parent and 'edm-entity-result'not in parent.get('class',[]):parent=parent.parent
        assert parent is not None
        text=q.clean(parent.get_text(' ',strip=True))
        date=re.search(r' Date (.*?) Item type ',text)
        kind=re.search(r' Item type (.*?) (?:Creator|Institution|Place) ',text)
        rows.append(dict(url=url,source_id=url.split('/aggregator/edm/')[1],title=title,text=text,
            index_date=date[1]if date else None,index_type=kind[1]if kind else None))
    return rows


def main():
    with (m.ROOT/'docs/research/greek-museums-20261008/delivery.csv').open(encoding='utf-8-sig')as f:
        historical=[v for v in csv.DictReader(f)if v['museum_id']==IID]
    assert len(historical)==18
    known={v['source_id']for v in historical}
    url=BASE+'/aggregator/portal/collections/ZoggopoulosF?language=en'
    soup,receipt=q.q.capture('collection-profile-001',url)
    form=soup.find('form',id='edmSearchForm');select=form.find('select',id='sortResults')
    assert form['method'].upper()=='GET' and select['name']=='sortResults'
    assert form['action']=='/aggregator/portal/collections/ZoggopoulosF/search'
    m.save(RUN/'source-discovery-001.json.gz',dict(at=m.now(),institution_id=IID,receipt=receipt,
        text=q.clean(soup.get_text(' ',strip=True)),historical_records=historical,
        links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(url,a['href']))for a in soup.select('a[href]')],
        form=dict(action=form['action'],method='GET',control=select['name'],value='YEAR_ASC',
            tooltip=select.find('option',value='YEAR_ASC')['title']),
        auth='Fifth consecutive continuation token refresh failed, confirmed terminal exit 1. Production unavailable; public research continues. No credential search or alternate account used.',
        last_verified_counts=dict(catalogue=18,date_eligible=18,at='2026-10-09'),
        script_reference=q.s.ref(Path(__file__).resolve())))
    pages=[];allrows=[]
    for page in range(1,7):
        url=BASE+form['action']+'?'+urlencode({'page.page':page,'resultsMode':'GRID','sortResults':'YEAR_ASC','language':'en'})
        doc,rc=q.q.capture('dated-index-page-'+str(page)+'-001',url)
        assert doc.select_one('#sortResults option[selected]')['value']=='YEAR_ASC'
        cards=index(doc);assert len(cards)==30
        assert not ({v['source_id']for v in cards}&{v['source_id']for v in allrows})
        for card in cards:card['historical_source_match']=card['source_id']in known
        pages.append(dict(page=page,receipt=rc,cards=cards));allrows.extend(cards)
        print(json.dumps(dict(page=page,cards=len(cards),dates=[cards[0]['index_date'],cards[-1]['index_date']],historical=sum(v['historical_source_match']for v in cards))),flush=True)
        if all(v['index_date']and re.match(r'^\d{4}',v['index_date'])and int(v['index_date'][:4])>1970 for v in cards):break
    m.save(RUN/'bounded-index-001.json.gz',dict(at=m.now(),pages=pages,cards=len(allrows),
        policy='At most six earliest-date index pages; stop on an entirely post-1970 page. Select metadata before image capture. Unknown dates excluded by source date-sort UI, not by catalogue policy. Historical records retained.',
        discovery_reference=q.s.ref(RUN/'source-discovery-001.json.gz')))


if __name__=='__main__':main()
