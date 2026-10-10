"""Observe Larissa collection discovery and preserve the unchanged production baseline."""
import csv
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.m
RUN=m.RUN/'native/larissa-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)
IID='d843489b-7a33-5cbb-916a-4eecb0dac8b8'
BASE='https://www.searchculture.gr'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/larissa-20261010'

def index(soup):
    rows=[];seen=set()
    for a in soup.select('a[href]'):
        u=urljoin(BASE,a['href']);title=q.clean(a.get_text(' ',strip=True))
        if not u.startswith(BASE+'/aggregator/edm/larisa_gallery/000143-')or not title or u in seen:continue
        if u.endswith('/xml')or u.endswith('/json'):continue
        p=a
        while p and 'edm-entity-result'not in p.get('class',[]):p=p.parent
        if p is None:continue
        seen.add(u);text=q.clean(p.get_text(' ',strip=True))
        date=re.search(r' Date (.*?) Item type ',text);kind=re.search(r' Item type (.*?) (?:Creator|Institution|Place) ',text)
        rows.append(dict(url=u,source_id=u.split('/aggregator/edm/')[1],title=title,text=text,index_date=date[1]if date else None,index_type=kind[1]if kind else None))
    return rows

def main():
    historical=[r for r in csv.DictReader((m.ROOT/'docs/research/greek-museums-20261008/delivery.csv').open(encoding='utf-8-sig'))if r['museum_id']==IID]
    assert len(historical)==18
    soup,rc=q.q.capture('collection-profile-001',BASE+'/aggregator/portal/collections/larisa_gallery?language=en')
    form=soup.find('form',id='edmSearchForm');assert form['method'].upper()=='GET'
    links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href']))for a in soup.select('a[href]')]
    data=dict(at=m.now(),institution_id=IID,receipt=rc,text=q.clean(soup.get_text(' ',strip=True)),links=links,historical_records=historical,first_cards=index(soup),
        form=dict(action=form['action'],method=form['method'],controls=[dict(tag=e.name,type=e.get('type'),name=e.get('name'),value=e.get('value'))for e in form.select('input[name]')],selects=[dict(name=e.get('name'),id=e.get('id'),options=[dict(value=o.get('value'),text=q.clean(o.get_text()))for o in e.select('option')])for e in form.select('select')]),
        previous_research_checkpoint=q.s.ref(m.RUN/'native/chania-20261010/research-checkpoint-001.json'),
        previous_checkpoint_pins_verified=dict(artifacts=1108,external=420),previous_goal_turn='progress',
        auth='Eighth consecutive continuation: gcloud token refresh exit1, Reauthentication failed, cannot prompt during non-interactive execution. No token printed, credential search, substitute identity or production mutation. Public research remains available.',
        last_verified_counts=dict(catalogue=18,date_eligible=15,at='2026-10-09'),script_reference=q.s.ref(Path(__file__).resolve()))
    m.save(RUN/'source-discovery-001.json.gz',data)
    print(json.dumps(dict(profile=data['text'][:2300],form=data['form'],cards=data['first_cards'][:8]),ensure_ascii=False),flush=True)
    native,nrc=q.q.capture('native-homepage-001','https://www.katsigrasmuseum.gr/homepage/')
    nlinks=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(nrc['final_url'],a['href']))for a in native.select('a[href]')]
    m.save(RUN/'native-discovery-001.json.gz',dict(at=m.now(),receipt=nrc,text=q.clean(native.get_text(' ',strip=True)),links=nlinks,script_reference=q.s.ref(Path(__file__).resolve())))
    print(json.dumps(dict(native_text=q.clean(native.get_text(' ',strip=True))[:3200],native_links=[v for v in nlinks if any(x in (v['title']+' '+v['url']).lower()for x in ['collection','συλλογ','digital','ψηφι','work'])]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
