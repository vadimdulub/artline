"""Six bounded painting-index pages via observed public GET-form fields."""
import collections
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlencode

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-source-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
m,q,RUN=d.m,d.q,d.RUN


def main():
    facet=m.load(RUN/'facet-discovery-001.json.gz')
    names={v['attributes']['name']:v for v in facet['inputs']if 'name'in v['attributes']}
    field='facets[ekt_proxy_dc_type_hierarchy_uri].field'
    key='facets[ekt_proxy_dc_type_hierarchy_uri].values[3]'
    assert names[key+'.checked']['label']=='Painting (262)'
    params={k:names[k]['attributes']['value']for k in [field,key+'.checked',key+'.value']}
    assert params[key+'.value']=='http://semantics.gr/authorities/ekt-item-types/zwgrafikh'
    params.update(resultsMode='GRID',sortResults='SCORE',language='en')
    old={v['source_id']for v in m.load(d.OLD/'selected-source-records-001.json.gz')['rows']}
    pages=[];seen=set()
    for page in range(1,7):
        url=d.z.BASE+'/aggregator/portal/collections/ZoggopoulosF/search?'+urlencode(dict(params,**{'page.page':page}))
        soup,rc=q.q.capture('painting-index-page-'+str(page)+'-001',url)
        text=q.clean(soup.get_text(' ',strip=True));assert 'from 262 items'in text
        cards=d.z.index(soup);assert len(cards)==30
        assert all(v['index_type']=='Painting'for v in cards)
        assert not ({v['source_id']for v in cards}&seen)
        for v in cards:
            v['prior_source_review']=v['source_id']in old;seen.add(v['source_id'])
            ys=[int(x)for x in re.findall(r'\d{4}',v['index_date']or'')]
            v['index_date_scope']='unknown'if not ys else'eligible'if ys[-1]<=1970 else'post_1970'if ys[0]>1970 else'crosses_1970'
        pages.append(dict(page=page,receipt=rc,cards=cards))
        print(json.dumps(dict(page=page,dates=dict(collections.Counter(v['index_date_scope']for v in cards)),previous=sum(v['prior_source_review']for v in cards))),flush=True)
    m.save(RUN/'bounded-painting-index-001.json.gz',dict(at=m.now(),pages=pages,observed_painting_records=262,
        form_fields=params,facet_reference=q.s.ref(RUN/'facet-discovery-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='180 painting cards only, leaving82 uninspected in this filtered index. Retain unknown creation dates for editorial review. Index dates are discovery hints; object descriptions and inscriptions require review before selection decisions. No images or DB access.'))


if __name__=='__main__':main()
