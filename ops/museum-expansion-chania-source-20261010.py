"""Observe public museum collection sources and preserve a read-only baseline."""
import csv
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.m
RUN=m.RUN/'native/chania-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)
IID='80780566-c37f-51e6-a861-f43c834027d8'
BASE='https://www.searchculture.gr'

def index(soup):
    rows=[];seen=set()
    for a in soup.select('a[href]'):
        u=urljoin(BASE,a['href']);title=q.clean(a.get_text(' ',strip=True))
        if not re.fullmatch(BASE+r'/aggregator/edm/AMusChania/000039-\d+',u)or not title or u in seen:continue
        seen.add(u);p=a
        while p and 'edm-entity-result'not in p.get('class',[]):p=p.parent
        assert p is not None
        text=q.clean(p.get_text(' ',strip=True));date=re.search(r' Date (.*?) Item type ',text)
        kind=re.search(r' Item type (.*?) (?:Creator|Institution|Place) ',text)
        rows.append(dict(url=u,source_id=u.split('/aggregator/edm/')[1],title=title,text=text,index_date=date[1]if date else None,index_type=kind[1]if kind else None))
    return rows

def main():
    historical=[r for r in csv.DictReader((m.ROOT/'docs/research/greek-museums-20261008/delivery.csv').open(encoding='utf-8-sig'))if r['museum_id']==IID]
    assert len(historical)==18
    url=BASE+'/aggregator/portal/collections/AMusChania?language=en'
    soup,receipt=q.q.capture('collection-profile-001',url)
    form=soup.find('form',id='edmSearchForm');assert form['method'].upper()=='GET'
    links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(url,a['href']))for a in soup.select('a[href]')]
    data=dict(at=m.now(),institution_id=IID,receipt=receipt,text=q.clean(soup.get_text(' ',strip=True)),historical_records=historical,
        links=links,first_cards=index(soup),form=dict(action=form['action'],method=form['method'],controls=[dict(name=e.get('name'),value=e.get('value'))for e in form.select('input[name]')],sort_options=[dict(value=e.get('value'),text=q.clean(e.get_text()))for e in form.select('#sortResults option')]),
        previous_research_checkpoint=q.s.ref(m.RUN/'native/zongolopoulos-paintings-20261010/research-checkpoint-001.json'),
        auth='Seventh consecutive continuation refresh failure; terminal exit1 and non-interactive reauthentication error. Public research remains possible. No credentials printed, search or alternate identity used.',
        last_verified_counts=dict(catalogue=18,date_eligible=0,at='2026-10-09'),script_reference=q.s.ref(Path(__file__).resolve()))
    m.save(RUN/'source-discovery-001.json.gz',data)
    assert any(v['url']=='https://amch.gr/collection/'for v in links)
    native,nrc=q.q.capture('native-collection-profile-001','https://amch.gr/collection/')
    m.save(RUN/'native-discovery-001.json.gz',dict(at=m.now(),receipt=nrc,text=q.clean(native.get_text(' ',strip=True)),
        links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(nrc['final_url'],a['href']))for a in native.select('a[href]')],
        forms=[dict(attributes=f.attrs,text=q.clean(f.get_text(' ',strip=True)))for f in native.select('form')],
        script_sources=[urljoin(nrc['final_url'],s['src'])for s in native.select('script[src]')],script_reference=q.s.ref(Path(__file__).resolve())))
    sample=next(v for v in historical if v['source_id'].endswith('-1037'))
    doc,rc=q.q.capture('historical-sample-1037-001',sample['source_url']);fields,enrichment=q.fields(doc)
    m.save(RUN/'historical-sample-001.json',dict(at=m.now(),receipt=rc,fields=fields,enrichment=enrichment,
        links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href']))for a in doc.select('a[href]')if 'amch.gr'in a['href']]))
    print(json.dumps(dict(profile=data['text'][:2800],first_cards=data['first_cards'][:8],native_text=q.clean(native.get_text(' ',strip=True))[-3000:],sample=fields),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
