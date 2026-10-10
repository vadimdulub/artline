"""Bounded source discovery for three other under-target Greek museum collections."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    assert not(RUN/'next-source-discovery-001.json.gz').exists();q=c.module('q','museum-expansion-kazantzakis-source-20261009.py');q.RUN=RUN;q.CAP=RUN/'next-source-captures';q.CAP.mkdir(parents=True,exist_ok=True)
    cp=m.load(c.CP);register=m.load(c.checked(cp['production_institution_register_reference']))['rows'];rows=[]
    for iid,key in [('612b52d8-d6b9-5cfe-b068-5caf0d070653','nikaia'),('ecc56326-95ff-5063-9e7c-defe30001f0f','spathario'),('a4b7823c-f659-5413-9766-60c2306d8844','war-museum')]:
        inst=next(x for x in register if x['id']==iid);url=inst['website_url'];doc,receipt=q.capture(key+'-collection-001',url);text=doc.get_text(' ',strip=True);cards=[]
        for el in doc.select('.edm-entity-result'):
            pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
            if not pairs:continue
            a,u=pairs[0];cards.append(dict(url=u,title=a.get_text(' ',strip=True),text=el.get_text(' ',strip=True)))
        forms=[dict(action=f.get('action'),method=f.get('method'),input_names=sorted({x['name'] for x in f.select('[name]')}),sort_options=[dict(value=o.get('value'),label=o.get_text(' ',strip=True)) for o in f.select('select[name=sortResults] option')]) for f in doc.select('form') if '/collections/' in f.get('action','')]
        external=sorted({urljoin(url,a['href']) for a in doc.select('a[href]') if a['href'].startswith('http') and not any(h in a['href'] for h in ['searchculture.gr','semantics.gr','europeana.eu','facebook.com','twitter.com','creativecommons.org','ekt.gr'])})
        rows.append(dict(institution_id=iid,name=inst['name'],historical_catalogue_count=inst['verified_production_works'],historical_count_at=inst['production_catalogue_count_at'],url=url,receipt=receipt,text=text,first_page_cards=cards,forms=forms,external_links=external,policy='Source discovery only; collection count is not eligible-artwork count. Fresh production counts and object/version/date/source checks required. No image or object-detail download.'))
        print(json.dumps(dict(name=inst['name'],status=receipt['status'],first_page_cards=len(cards),text_excerpt=text[:1000],external_links=external[:12]),ensure_ascii=False),flush=True)
    m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),rows=rows,register_reference=cp['production_institution_register_reference'],script_reference=c.ref(Path(__file__).resolve()),policy='Three bounded public collection pages. No importable-candidate or complete-coverage claim. Existing native Averoff and other provider holds remain untouched.'))

if __name__=='__main__':main()
