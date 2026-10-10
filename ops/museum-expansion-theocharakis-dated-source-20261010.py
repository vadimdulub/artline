"""Bounded date-sorted discovery using the collection's observed public GET form."""
import gzip
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('t',Path(__file__).with_name('museum-expansion-theocharakis-source-20261010.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
m,q=t.m,t.q
OLD=t.RUN
RUN=m.RUN/'native/theocharakis-dated-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)


def main():
    old_receipt=m.load(OLD/'captures/searchculture-collection-001.json')
    html=gzip.decompress((m.ROOT/old_receipt['body_path']).read_bytes()).decode()
    soup=BeautifulSoup(html,'html.parser');form=soup.find('form',id='edmSearchForm');select=form.find('select',id='sortResults')
    assert form['method'].upper()=='GET' and form['action']=='/aggregator/portal/collections/theocharakis/search'
    assert select['name']=='sortResults' and select.find('option',value='YEAR_DESC')
    assert "$('.select-sorting-results').show().change(" in html
    known={v['source_id']for v in m.load(OLD/'selected-source-records-001.json.gz')['rows']}
    known.add('theocharakis/000163-111578')
    pages=[];seen=set()
    for page in range(1,4):
        url=t.BASE+form['action']+'?'+urlencode({'page.page':page,'resultsMode':'GRID','sortResults':'YEAR_DESC','language':'en'})
        doc,receipt=q.q.capture('dated-index-page-'+str(page)+'-001',url)
        assert doc.select_one('#sortResults option[selected]')['value']=='YEAR_DESC'
        cards=t.index(doc);assert len(cards)==30 and not({v['source_id']for v in cards}&seen)
        for card in cards:
            match=re.search(r' Date (.*?) Item type ',card['text']);assert match,(page,card)
            card['index_date']=match[1];card['prior_source_review']=card['source_id']in known
            seen.add(card['source_id'])
        pages.append(dict(page=page,receipt=receipt,cards=cards))
        print(json.dumps(dict(page=page,cards=len(cards),known=sum(v['prior_source_review']for v in cards),dates=[cards[0]['index_date'],cards[-1]['index_date']])),flush=True)
    m.save(RUN/'dated-index-001.json.gz',dict(at=m.now(),pages=pages,previous_source_ids=sorted(known),
        form_evidence=dict(source_receipt=old_receipt,action=form['action'],method='GET',control=select['name'],value='YEAR_DESC',
          tooltip=select.find('option',value='YEAR_DESC')['title'],response_selected_option_verified=True),
        policy='Only three date-sorted index pages (90 cards). Sorting excludes undated records according to the source UI. Dates are discovery hints until the individual native artwork page is checked. No full collection or image download.',
        script_reference=q.s.ref(Path(__file__).resolve())))


if __name__=='__main__':main()
